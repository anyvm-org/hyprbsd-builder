# Runs inside the installed HyprBSD system over ssh, after the package step
# and just before the build VM is shut down and the image is exported.
#
# HyprBSD installs onto a single ZFS pool and this build adds packages on
# top. Freed ZFS blocks are neither zeroed nor trimmed, so they stay
# allocated in the qcow2 and the export-time sparsify cannot reclaim them;
# zero-filling does not help on ZFS (compression collapses the zeros).
# TRIM does: QEMU runs the build disk with discard=unmap, so trimmed blocks
# become holes. Same medicine as freebsd-builder and ghostbsd-builder.

echo "=== finalize: image cleanup ==="

# Drop fetched package archives (/var/cache/pkg).
pkg clean -ay || true

# TRIM all free space; -w waits for completion before the VM goes down.
for _pool in $(zpool list -H -o name 2>/dev/null); do
    echo "Trimming pool ${_pool}..."
    zpool trim -w "${_pool}" || echo "zpool trim ${_pool} failed (non-fatal)"
    zpool status -t "${_pool}" || true
done

df -h || true
echo "=== finalize: image cleanup done ==="
