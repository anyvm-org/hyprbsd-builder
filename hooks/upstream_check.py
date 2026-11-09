#!/usr/bin/env python3
# Print the newest FINAL HyprBSD release, e.g. "15.1". Empty output means
# "nothing detected" and is not an error; a non-zero exit means detection
# itself is broken (network error, HTTP error, or a page that no longer
# matches the expected shape) and must be reported by the caller, never
# swallowed. A failure must NEVER print a plausible-but-wrong version -- the
# version is only printed after every step below has succeeded.
#
# Source of truth: https://hyprbsd.org/releases/, the project's own release
# list. Fetched by hand 2026-11-09: every release is named there as
# "HyprBSD <major>.<minor>[-rc<n>]" (15.1-rc1, 15.1-rc2, 15.1-rc3 at the
# time) and the current ISO is linked as hyprbsd-<version>.iso.
#
# Release candidates are deliberately NOT reported. conf/hyprbsd-15.1.conf
# is already named for the final release and only its URL pins rc media;
# reporting "15.1" while upstream is still at an rc would make the watcher
# try to refresh the URL to a final ISO that does not exist yet, and its
# HEAD gate would then fail every night. Reporting only finals means:
# nothing happens until the final ISO is listed, and then the watcher's
# RC -> final refresh repoints the existing conf.
#
# The page must name at least one release and link at least one ISO (rc or
# final) for the parse to count as a success: a page with neither is a
# changed page shape, not "no new release".
#
# stdlib only (urllib.request, re, sys, os) -- no external dependencies.

import os
import re
import sys
import urllib.request

URL = "https://hyprbsd.org/releases/"
TIMEOUT = 60
USER_AGENT = "anyvm-org-upstream-watcher/1.0"

# "HyprBSD 15.1-rc3" / "HyprBSD 15.1": the release names, used only as the
# page-shape sanity check.
NAME_PATTERN = re.compile(r"HyprBSD (\d+\.\d+)(-rc\d+)?\b", re.I)
# "hyprbsd-15.1-rc3.iso" / "hyprbsd-15.1.iso": the downloadable media. A
# final is reported only when its ISO is linked -- prose that merely says
# "HyprBSD 15.1" is not a release anyone can build from. Group 1 is the
# version as conf VM_RELEASE spells it, group 2 the optional rc suffix.
ISO_PATTERN = re.compile(r"hyprbsd-(\d+\.\d+)(-rc\d+)?\.iso\b")


def resolve_natural_key():
    """Return the engine's own natural_key, or fail loudly.

    watch.yml clones base-builder INTO the builder repo root ("base-builder/"
    relative to this hook's cwd); a local checkout has it as a sibling
    ("../base-builder"). There is deliberately NO local fallback copy:
    ordering must be the single rule the engine uses."""
    for candidate in ("base-builder", os.path.join("..", "base-builder")):
        if not os.path.isdir(candidate):
            continue
        path = os.path.abspath(candidate)
        if path not in sys.path:
            sys.path.insert(0, path)
        try:
            import gendata
            return gendata.natural_key
        except ImportError:
            continue
    raise ImportError(
        "base-builder/gendata.py not importable from %s; expected it at "
        "./base-builder (CI) or ../base-builder (local checkout)"
        % os.getcwd())


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        if resp.status != 200:
            raise ValueError("HTTP %d from %s" % (resp.status, url))
        return resp.read().decode("utf-8", "replace")


def main():
    try:
        key = resolve_natural_key()
    except ImportError as e:
        sys.stderr.write("upstream_check: %s\n" % e)
        return 1
    try:
        page = fetch(URL)
    except Exception as e:
        sys.stderr.write("upstream_check: fetch of %s failed: %s\n"
                         % (URL, e))
        return 1
    if not NAME_PATTERN.search(page) or not ISO_PATTERN.search(page):
        sys.stderr.write("upstream_check: %s names no \"HyprBSD <version>\" "
                         "release or links no hyprbsd-<version>.iso; page "
                         "shape may have changed\n" % URL)
        return 1
    finals = sorted({ver for ver, rc in ISO_PATTERN.findall(page) if not rc},
                    key=key)
    if finals:
        print(finals[-1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
