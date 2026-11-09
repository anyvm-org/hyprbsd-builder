amd64 only: HyprBSD builds no other architecture, and it publishes one
installer ISO per release rather than a VM image, so this builder takes the
ISO path.

Release `15.1` is HyprBSD 15.1 (FreeBSD 15.1-RELEASE with the Hyprland
desktop). Upstream has not published a final 15.1 ISO yet, so the image is
built from the newest release candidate, `hyprbsd-15.1-rc3.iso`. The release
name is already the final one: when the final ISO appears, the upstream
watcher repoints the conf at it and the image keeps its name, the same way
netbsd-builder moved 11.0 from RC7 to final media.

The installed system boots through UEFI only (HyprBSD's installer writes an
EFI system partition and no BIOS boot code), so anyvm starts it with OVMF.

The image keeps HyprBSD's desktop installed but boots to a text console:
SDDM is disabled, because its Hyprland greeter needs a 3D-capable virtio-gpu
(VirGL) that anyvm's display does not provide -- left on, the VNC console just
shows a black screen. `service sddm onestart` brings the desktop back on a
VirGL-capable display. HyprBSD's default-deny `pf` firewall is also disabled,
so anyvm's port forwards reach the guest.
