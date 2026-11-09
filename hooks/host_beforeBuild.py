# host_beforeBuild.py -- the two build inputs HyprBSD needs besides the
# upstream ISO: UEFI firmware, and the CIDATA disk carrying the answers for
# HyprBSD's own unattended installer.
#
# WHY UEFI. HyprBSD's installer partitions the disk as efi + swap + zfs and
# copies loader.efi to EFI/BOOT/BOOTX64.EFI; there is no freebsd-boot
# partition and no pmbr, so the installed disk cannot boot under SeaBIOS at
# all. conf/hyprbsd-15.1.conf points VM_BIOS at the combined OVMF image;
# this hook makes sure the file is there before build.py launches QEMU.
#
# WHY CIDATA. The live ISO's /usr/local/libexec/hyprbsd-live/launch (run
# from root's .profile on the autologin console) scans /dev/msdosfs,
# /dev/iso9660 and /dev/ufs for a volume labelled CIDATA. If it holds
# hyprbsd.conf, launch copies it, prints a 10 s "press Enter to answer the
# questions instead" notice nobody answers, runs the installer with -c, and
# powers the machine off on success. The keys are the installer's own
# (install-lib.sh CONFIG_KEYS); anything else is refused by its parser. So
# the whole install is upstream's code path -- nothing is typed into the
# installer and the ISO is not remixed.
#
# Verified locally (KVM, WSL, QEMU 8.2.2, OVMF 2024.02): the CIDATA install
# ran unattended to "@@install-done" in about 4 minutes and powered off, and
# the installed disk booted under OVMF to a ttyu0 login prompt.
#
# Both outputs live under WORKDIR. clearVM() runs between this hook and
# createVM() but only removes .qcow2/.img/state files, never an .iso.

_bios = env("VM_BIOS")
if not _bios:
    log("FATAL: hyprbsd needs VM_BIOS (UEFI firmware); the conf does not set it")
    sys.exit(1)


def _apt_install(*pkgs):
    """apt-get install, with one `apt-get update` retry for a runner whose
    package lists are stale."""
    _env = {**os.environ, "DEBIAN_FRONTEND": "noninteractive"}
    cmd = ["sudo", "-E", "apt-get", "install", "-y", "-qq"] + list(pkgs)
    if subprocess.run(cmd, env=_env).returncode == 0:
        return True
    subprocess.run(["sudo", "-E", "apt-get", "update", "-qq"], env=_env)
    return subprocess.run(cmd, env=_env).returncode == 0


# --- 1. UEFI firmware ------------------------------------------------------
# ubuntu-24.04 ships /usr/share/ovmf/OVMF.fd in the ovmf package itself;
# on ubuntu-26.04 ovmf is a metapackage and the same path comes from
# ovmf-generic. Installing "ovmf" covers both.
if not os.path.exists(_bios):
    log("hyprbsd beforeBuild: %s missing, installing ovmf" % _bios)
    _apt_install("ovmf")
if not os.path.exists(_bios):
    log("FATAL: %s still missing after installing ovmf. Firmware files "
        "present:" % _bios)
    sh("ls -la /usr/share/ovmf /usr/share/OVMF /usr/share/qemu 2>&1 || true")
    sys.exit(1)
log("hyprbsd beforeBuild: UEFI firmware %s (%d bytes)"
    % (_bios, os.path.getsize(_bios)))
sh("dpkg-query -W 'ovmf*' 2>/dev/null || true")

# --- 2. the CIDATA answer disk ----------------------------------------------
_seed = env("VM_SEED_ISO")
if not _seed:
    log("FATAL: hyprbsd needs VM_SEED_ISO (the CIDATA answer disk); the conf "
        "does not set it")
    sys.exit(1)

if not shutil.which("xorriso"):
    log("hyprbsd beforeBuild: installing xorriso")
    _apt_install("xorriso")
if not shutil.which("xorriso"):
    log("FATAL: xorriso is required to build the CIDATA answer disk")
    sys.exit(1)

# disk=vtbd0: build.py puts the target disk on virtio-blk (no VM_DISK), and
# it is the only disk FreeBSD sees as vtbd*. The installer prefers
# disk_serial= and warns about a device name, but QEMU gives this disk no
# serial number to match. erase=yes is a no-op on the blank qcow2 and keeps
# a re-run on a used disk from stopping at "isn't blank".
#
# The installer insists on a regular user as well as root; it gets the same
# password. Every builder's root password is anyvm.org (VM_ROOT_PASSWORD).
_answers = "\n".join([
    "disk=vtbd0",
    "erase=yes",
    "hostname=hyprbsd",
    "timezone=UTC",
    "network=dhcp",
    "username=anyvm",
    "fullname=anyvm",
    "user_password=%s" % env("VM_ROOT_PASSWORD"),
    "root_password=%s" % env("VM_ROOT_PASSWORD"),
]) + "\n"

_seed_dir = wf("cidata")
os.makedirs(_seed_dir, exist_ok=True)
with open(os.path.join(_seed_dir, "hyprbsd.conf"), "w", newline="\n") as _f:
    _f.write(_answers)
os.makedirs(os.path.dirname(_seed) or ".", exist_ok=True)
try: os.remove(_seed)
except OSError: pass
# The volume id is what FreeBSD exposes as /dev/iso9660/CIDATA; launch
# matches the label case-insensitively, but keep it exact.
must_run(["xorriso", "-as", "mkisofs", "-V", "CIDATA", "-J", "-R",
          "-o", _seed, _seed_dir], "xorriso CIDATA")
log("hyprbsd beforeBuild: CIDATA answer disk %s (%d bytes), hyprbsd.conf:\n%s"
    % (_seed, os.path.getsize(_seed),
       _answers.replace(env("VM_ROOT_PASSWORD"), "***")))
