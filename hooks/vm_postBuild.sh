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
# upstream tests QEMU only with virtio-gpu + VirGL. On a plain virtio-vga
# display (no VirGL) the greeter exits within seconds and the screen stays
# black (seen in /var/log/sddm.log: "Greeter session started" then
# "Greeter stopped"). So SDDM is decided per boot: rc.conf says NO, and
# /etc/rc.conf.d/sddm (read by load_rc_config after rc.conf) turns it on
# only when the virtio-gpu driver negotiated VirGL. anyvm gives hyprbsd
# virtio-vga-gl + egl-headless when the host has a usable DRM render node,
# and plain virtio-vga otherwise; the first boots to the Hyprland login
# screen, the second to the ttyv0 text login.
#
# The check reads /var/run/dmesg.boot: kld_list loads virtio_gpu_drm in
# /etc/rc.d/kld, which rcorder puts before /etc/rc.d/dmesg, so the driver's
# "[drm] features: +virgl" line is already in the file when sddm starts.
# Delete /etc/rc.conf.d/sddm to keep the text login even with VirGL.
sysrc sddm_enable="NO"
mkdir -p /etc/rc.conf.d
cat >/etc/rc.conf.d/sddm <<'EOF'
# Written by hyprbsd-builder: start SDDM only when the virtio-gpu has VirGL.
# The Hyprland greeter cannot draw without 3D; without VirGL the console
# keeps the text login. Delete this file to keep the text login always.
if grep -q '\[drm\] features: +virgl' /var/run/dmesg.boot 2>/dev/null; then
	sddm_enable="YES"
fi
EOF
cat /etc/rc.conf.d/sddm

# sshd and the firewall were already set by enablessh.txt over the console;
# re-assert them here so the image does not depend on that file's wording.
# pf is HyprBSD's default-deny inbound firewall; left on, it would block
# anyvm's port forwards (-p host:guest) to anything but ssh.
sysrc sshd_enable="YES"
sysrc pf_enable="NO"

echo "postBuild done."
