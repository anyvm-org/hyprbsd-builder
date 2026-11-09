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
