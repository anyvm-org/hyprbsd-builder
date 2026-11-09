# host_installOpts.py -- watch HyprBSD's own unattended install; type nothing.
#
# hooks/host_beforeBuild.py attached a CIDATA disk with hyprbsd.conf, and the
# live ISO's launcher installs from it by itself. Under OVMF the loader picks
# a dual console with serial primary, which gives the live system TWO root
# autologins, and launch splits the work between them:
#
#   ttyv0 (the screen)  runs the installer: finds CIDATA, waits 10 s for an
#                       Enter nobody presses, installs, then `shutdown -p`.
#   ttyu0 (our chardev) prints "HyprBSD's installer runs on ttyv0. ...
#                       Following the log here" and `tail -F`s
#                       /tmp/hyprbsd-install.log.
#
# So the whole install log scrolls past on the serial console, and this hook
# only has to read it. The log's own markers decide the outcome (written by
# /usr/local/libexec/hyprbsd/install):
#
#   @@install-begin   the unattended run started (CIDATA was found)
#   @@install-done    every step passed; the machine powers off next
#   @@install-failed  a step failed; launch leaves the machine up
#
# Every wait is bounded and fatal. The whole serial log is searched, not the
# 50-line screen window waitForText() looks at: the install prints thousands
# of pkg lines and the poweroff follows "@@install-done" within seconds, so a
# marker can scroll out of the window between two polls.

_osname = env("VM_OS_NAME")
_log_path = serial_log(_osname)

# Live system up to its ttyu0 autologin: about 40 s under KVM. The ceiling
# is for a TCG runner.
_BOOT_MAX = 900
# From the ttyu0 log follower to "@@install-begin": the 10 s notice plus the
# installer's pre-write checks. If CIDATA was NOT found the interactive
# installer sits on ttyv0 forever, so this bound is what turns that into a
# one-line failure instead of the whole install ceiling.
_BEGIN_MAX = 600
# The install itself: about 4 minutes under KVM (the 3.7 GB ISO carries the
# whole package set, so nothing is downloaded). Generous for TCG.
_INSTALL_MAX = int(env("VM_INSTALL_MAX_SECONDS") or 5400)


def _serial_text():
    try:
        with open(_log_path, "rb") as _fh:
            return _fh.read().decode("utf-8", "replace")
    except OSError:
        return ""


def _wait_marker(markers, max_seconds, what, fail_markers=()):
    """Poll the full serial log every 10 s until one of `markers` shows up.
    Fails the build on a fail marker, on the VM going away first, or on the
    bound."""
    if isinstance(markers, str):
        markers = (markers,)
    t0 = time.time()
    while time.time() - t0 < max_seconds:
        time.sleep(10)
        fresh = _unseen_screen_text("")
        if fresh.strip():
            log(fresh.rstrip("\n"))
        text = _serial_text()
        for fm in fail_markers:
            if fm in text:
                log("FATAL: hyprbsd installOpts: %s -- the guest printed %r. "
                    "The VM is left running; the installer's log is "
                    "/tmp/hyprbsd-install.log in the live system."
                    % (what, fm))
                sys.exit(1)
        for marker in markers:
            if marker in text:
                mm, ss = divmod(int(time.time() - t0), 60)
                log("hyprbsd installOpts: %r after %dm%02ds"
                    % (marker, mm, ss))
                return
        if isRunning() != 0:
            log("FATAL: hyprbsd installOpts: the VM stopped before %r (%s)"
                % (markers, what))
            sys.exit(1)
    log("FATAL: hyprbsd installOpts: no %r within %d s (%s)"
        % (markers, max_seconds, what))
    sys.exit(1)


log("hyprbsd installOpts: unattended install from the CIDATA disk; "
    "following its log on ttyu0")

_wait_marker("Following the log here", _BOOT_MAX,
             "the live system never reached its ttyu0 log follower")
# "@@phase " as well: `tail -F` starts with the last 10 lines of the log, so
# if the ttyu0 login lost the race to the installer on ttyv0 the begin line
# itself may never be shown -- the first step's phase line then proves it.
_wait_marker(("@@install-begin", "@@phase "), _BEGIN_MAX,
             "the unattended install did not start -- was the CIDATA disk "
             "found? (without it the interactive installer waits on ttyv0)",
             fail_markers=("@@install-failed",))
_wait_marker("@@install-done", _INSTALL_MAX,
             "the unattended install did not finish",
             fail_markers=("@@install-failed",))

# launch runs `shutdown -p now` right after the installer returns 0; main()
# picks up from here at _wait_vm_down(what="install").
log("hyprbsd installOpts: install done; waiting for the live system to "
    "power off")
