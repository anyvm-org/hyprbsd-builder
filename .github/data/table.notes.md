amd64 only: HyprBSD builds no other architecture, and it publishes one
installer ISO per release rather than a VM image, so this builder takes the
ISO path.

Release `15.1` is HyprBSD 15.1 (FreeBSD 15.1-RELEASE with the Hyprland
desktop), built from upstream's final ISO, `hyprbsd-15.1-RELEASE.iso`. Up to
v2.0.2 the image came from the release candidate `hyprbsd-15.1-rc3.iso`; the
release name was already `15.1` then and did not change.

The installed system boots through UEFI only (HyprBSD's installer writes an
EFI system partition and no BIOS boot code), so anyvm starts it with OVMF.

The Hyprland desktop needs a 3D-capable virtio-gpu (VirGL). SDDM starts at
boot only when the virtio-gpu negotiated VirGL (`/etc/rc.conf.d/sddm`): anyvm
gives the guest `virtio-vga-gl` with an `egl-headless` display on a Linux host
with a usable DRM render node, and the VNC console then shows the Hyprland
login (user `anyvm`, password `anyvm.org`). On a plain virtio-vga display the
guest boots to a text login. HyprBSD's default-deny `pf` firewall is
disabled, so anyvm's port forwards reach the guest.
