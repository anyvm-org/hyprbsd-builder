

[![Build](https://github.com/anyvm-org/hyprbsd-builder/actions/workflows/build.yml/badge.svg)](https://github.com/anyvm-org/hyprbsd-builder/actions/workflows/build.yml)

Latest: v2.0.2


The image builder for `hyprbsd`


All the supported releases are here:



| Release | x86_64 |
|---------|---------|
| 15.1 | ✅ (rsync,scp,sshfs,nfs,tar) |

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

How the images are built:

Each image is built automatically in the
[anyvm-org/hyprbsd-builder](https://github.com/anyvm-org/hyprbsd-builder)
repo's GitHub Actions: it downloads the official HyprBSD installer ISO,
boots it in QEMU under UEFI (OVMF) with a small CIDATA disk carrying the
answers for HyprBSD's own unattended installer, lets that installer put
HyprBSD on the disk, enables ssh, pre-installs the packages listed in the
conf, and exports the installed disk as a compressed qcow2 image.

Upstream install media: the official HyprBSD ISOs linked from the
release page, https://hyprbsd.org/releases/.




How to build:

1. Use the [manual.yml](.github/workflows/manual.yml) to build manually.
   
    Run the workflow manually, you will get a view-only webconsole from the output of the workflow, just open the link in your web browser.
   
    You will also get an interactive VNC connection port from the output, you can connect to the vm by any vnc client.

2. Run the builder locally on your Ubuntu machine.

    Just clone the repo. and run:
    ```bash
    python3 build.py conf/hyprbsd-15.1.conf
    ```
   
