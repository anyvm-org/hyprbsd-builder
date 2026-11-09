# Runs inside the installed HyprBSD system as soon as the builder can ssh in.
# HyprBSD is FreeBSD 15.1 underneath, so this is the freebsd-builder /
# ghostbsd-builder tuning, kept to what an anyvm guest needs. Everything
# else HyprBSD configures is left as upstream ships it.

echo '=================== postBuild start ===='

# --- boot loader ------------------------------------------------------------
# HyprBSD's installer writes autoboot_delay="3": three seconds at the loader
# menu on every boot of every anyvm run. sysrc rewrites the existing line in
# place, so HyprBSD's branding lines in the same file stay untouched.
sysrc -f /boot/loader.conf autoboot_delay="0"

# Do not attach the Hyper-V VMBus driver. Under QEMU+WHPX (Windows hosts) the
# guest sees Hyper-V CPUID, attaches vmbus0 and stalls ~110 s in the
# root-mount hold waiting for a VMBus provider QEMU never supplies (measured
# on FreeBSD 15.1: boot 130 s -> 18 s). anyvm always runs this image under
# QEMU with virtio devices, so nothing is lost. (Appended rather than set
# with sysrc: the name is a loader hint, not a shell variable name.)
grep -q '^hint\.vmbus\.0\.disabled=' /boot/loader.conf ||
    echo 'hint.vmbus.0.disabled="1"' >>/boot/loader.conf
cat /boot/loader.conf

# --- services ---------------------------------------------------------------
# SDDM starts Hyprland as its greeter, which needs a DRM device with 3D:
# upstream tests QEMU only with virtio-gpu + VirGL. anyvm's display has no
# VirGL, the greeter exits within seconds and the screen stays black (seen
# in /var/log/sddm.log: "Greeter session started" then "Greeter stopped").
# With SDDM off the VNC console shows the ttyv0 login instead. The desktop
# itself stays installed: `service sddm onestart` (or sddm_enable=YES) on a
# VirGL-capable display brings it back.
sysrc sddm_enable="NO"

# sshd and the firewall were already set by enablessh.txt over the console;
# re-assert them here so the image does not depend on that file's wording.
# pf is HyprBSD's default-deny inbound firewall; left on, it would block
# anyvm's port forwards (-p host:guest) to anything but ssh.
sysrc sshd_enable="YES"
sysrc pf_enable="NO"

echo "postBuild done."
