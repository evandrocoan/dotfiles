"""Remove one authenticated review directory, without following links or mounts."""

import json
import os
from pathlib import Path
import re
import stat
import sys
import time


TEMPFAIL = 75
OPEN_DIRECTORY = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


def identity(info):
    return [info.st_dev, info.st_ino]


def mount_id(descriptor):
    for line in Path(f'/proc/self/fdinfo/{descriptor}').read_text().splitlines():
        if line.startswith('mnt_id:'):
            return int(line.split()[1])
    raise RuntimeError('scratch mount identity is unavailable')


def verify_owned(descriptor, owner, expected, label):
    info = os.fstat(descriptor)
    if info.st_uid != owner or info.st_mode & 0o022 or identity(info) != expected:
        raise RuntimeError(f'{label} ownership or identity changed before deletion')


def verify_name(parent, name, descriptor):
    if identity(os.stat(name, dir_fd=parent, follow_symlinks=False)) != identity(os.fstat(descriptor)):
        raise RuntimeError('scratch name changed during deletion')


def empty(directory, expected_mount, check_budget):
    with os.scandir(directory) as entries:
        for entry in entries:
            check_budget()
            original = entry.stat(follow_symlinks=False)
            if not stat.S_ISDIR(original.st_mode):
                os.unlink(entry.name, dir_fd=directory)
                continue
            child = os.open(entry.name, OPEN_DIRECTORY, dir_fd=directory)
            try:
                if identity(os.fstat(child)) != identity(original):
                    raise RuntimeError('scratch child identity changed before deletion')
                if mount_id(child) != expected_mount:
                    raise RuntimeError('scratch contains a mounted filesystem')
                empty(child, expected_mount, check_budget)
                check_budget()
                verify_name(directory, entry.name, child)
                os.rmdir(entry.name, dir_fd=directory)
            finally:
                os.close(child)


def remove_scratch(base, name, base_identity, root_identity, owner, check_budget):
    parent = os.open(base.parent, OPEN_DIRECTORY)
    try:
        base_fd = os.open(base.name, OPEN_DIRECTORY, dir_fd=parent)
        try:
            verify_owned(base_fd, owner, base_identity, 'scratch base')
            root = os.open(name, OPEN_DIRECTORY, dir_fd=base_fd)
            try:
                verify_owned(root, owner, root_identity, 'scratch directory')
                expected_mount = mount_id(base_fd)
                if mount_id(parent) != expected_mount or mount_id(root) != expected_mount:
                    raise RuntimeError('scratch base or directory is a mount point')
                empty(root, expected_mount, check_budget)
                check_budget()
                verify_name(parent, base.name, base_fd)
                verify_name(base_fd, name, root)
                os.rmdir(name, dir_fd=base_fd)
            finally:
                os.close(root)
        finally:
            os.close(base_fd)
    finally:
        os.close(parent)


def main():
    try:
        owner = int(os.environ['SUDO_UID'])
        base, name, base_identity, root_identity, deadline = json.loads(sys.argv[1])
        if (os.geteuid() != 0 or owner <= 0
                or base != '/tmp/codex-monitor'
                or not re.fullmatch(r'review-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', name)):
            raise ValueError('invalid privileged scratch target or caller')
        deadline = min(deadline, time.monotonic() + 300)

        def check_budget():
            if time.monotonic() >= deadline:
                raise TimeoutError('privileged scratch removal reached its deadline')

        check_budget()
        remove_scratch(Path(base), name, base_identity, root_identity,
                       owner, check_budget)
    except TimeoutError as error:
        print(error, file=sys.stderr)
        return TEMPFAIL
    except (OSError, RuntimeError, ValueError, KeyError, TypeError, IndexError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
