#!/usr/bin/python3
"""Provision the private Saildroid Binder device at boot."""
import argparse
import fcntl
import json
import os
import pwd
import stat
import struct
import subprocess
import tempfile
from pathlib import Path

BINDER_CTL_ADD = 0xc1086201
BINDER_VERSION = 0xc0046209
RUNTIME = Path('/run/saildroid-binder')
FILESYSTEM = RUNTIME / 'binderfs'
SOURCE = FILESYSTEM / 'binder'
DIRECTORY = Path('/home/art/runtime/binder')
TARGET = DIRECTORY / 'binder'
METADATA = DIRECTORY / 'provision.json'
SCHEMA = 'saildroid-binderfs-provision-v1'


def root_directory(path, mode):
    if path.resolve() != path:
        raise RuntimeError('Linked directory: ' + str(path))
    path.mkdir(mode=mode, exist_ok=True)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_gid != 0 or stat.S_IMODE(info.st_mode) != mode:
        raise RuntimeError('Untrusted directory: ' + str(path))


def prepare_directories(account):
    root_directory(Path('/home/art'), 0o755)
    # Validate both directories before migrating existing ownership.
    for path, allowed in ((DIRECTORY.parent, {'binder'}),
                          (DIRECTORY, {'binder', 'provision.json'})):
        if path.resolve() != path:
            raise RuntimeError('Linked runtime directory: ' + str(path))
        if not path.exists():
            continue
        info = path.lstat()
        if not stat.S_ISDIR(info.st_mode):
            raise RuntimeError('Runtime path is not a directory: ' + str(path))
        if info.st_uid == account.pw_uid and stat.S_IMODE(info.st_mode) == 0o700:
            if {entry.name for entry in path.iterdir()} - allowed:
                raise RuntimeError('Unexpected runtime directory contents: ' + str(path))
        else:
            root_directory(path, 0o755)
    for path in (DIRECTORY.parent, DIRECTORY):
        path.mkdir(mode=0o755, exist_ok=True)
        info = path.lstat()
        if info.st_uid == account.pw_uid and stat.S_IMODE(info.st_mode) == 0o700:
            os.chown(path, 0, 0)
            os.chmod(path, 0o755)
        root_directory(path, 0o755)


def fsync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def existing_external_device(account):
    if not METADATA.exists() or METADATA.is_symlink():
        return False
    info = METADATA.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o644:
        raise RuntimeError('Untrusted existing provisioning metadata')
    metadata = json.loads(METADATA.read_text())
    if metadata.get('schema') == SCHEMA:
        return False
    node = TARGET.lstat()
    if not stat.S_ISCHR(node.st_mode) or node.st_uid != account.pw_uid or stat.S_IMODE(node.st_mode) != 0o600:
        raise RuntimeError('Untrusted existing private Binder device')
    descriptor = os.open(TARGET, os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        version = bytearray(struct.pack('i', 0))
        fcntl.ioctl(descriptor, BINDER_VERSION, version, True)
        if struct.unpack('i', version)[0] != 8:
            raise RuntimeError('Incompatible existing Binder protocol')
    finally:
        os.close(descriptor)
    print('SAILDROID_BINDER_READY external provisioning preserved')
    return True


def install_service(account):
    helper = Path('/usr/local/sbin/saildroid-binder-setup')
    unit = Path('/etc/systemd/system/saildroid-binder.service')
    unit_data = ('[Unit]\nDescription=Saildroid private Binder device\n'
                 'After=local-fs.target\nRequiresMountsFor=/home/art/runtime\n'
                 'Before=user@' + str(account.pw_uid) + '.service\n\n'
                 '[Service]\nType=oneshot\nExecStart=' + str(helper) + '\n'
                 'RemainAfterExit=yes\n\n[Install]\nWantedBy=multi-user.target\n').encode()
    helper_data = Path(__file__).read_bytes()
    for path, data, mode in ((helper, helper_data, 0o755), (unit, unit_data, 0o644)):
        root_directory(path.parent, 0o755)
        if path.exists() or path.is_symlink():
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != mode:
                raise RuntimeError('Untrusted service file: ' + str(path))
            previous = path.read_bytes()
            if path == unit and previous != unit_data:
                raise RuntimeError('Existing Binder service has a different configuration')
            if path == helper and b'Provision the private Saildroid Binder device at boot.' not in previous[:200]:
                raise RuntimeError('Existing Binder helper is not managed by Saildroid')
    for path, data, mode in ((helper, helper_data, 0o755), (unit, unit_data, 0o644)):
        if path.exists() and path.read_bytes() == data:
            continue
        descriptor, temporary = tempfile.mkstemp(prefix='.saildroid-', dir=path.parent)
        try:
            with os.fdopen(descriptor, 'wb') as output:
                os.fchmod(output.fileno(), mode)
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, path)
            fsync_directory(path.parent)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    subprocess.run(['systemctl', 'daemon-reload'], check=True)
    subprocess.run(['systemctl', 'enable', 'saildroid-binder.service'], check=True)


def mount_type(path):
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        fields = line.split()
        if fields[4] == str(path):
            return fields[fields.index('-') + 1]
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install-service', action='store_true')
    arguments = parser.parse_args()
    if os.geteuid() != 0:
        raise RuntimeError('Root is required')
    account = pwd.getpwnam('defaultuser')
    root_directory(RUNTIME, 0o700)
    with open(RUNTIME / 'setup.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        prepare_directories(account)
        if existing_external_device(account):
            return
        filesystem_type = mount_type(FILESYSTEM)
        if filesystem_type is None:
            root_directory(FILESYSTEM, 0o700)
            subprocess.run(['/bin/mount', '-t', 'binder', '-o', 'max=16', 'binder', str(FILESYSTEM)], check=True)
        elif filesystem_type != 'binder':
            raise RuntimeError('Unexpected filesystem at ' + str(FILESYSTEM))
        if not SOURCE.exists():
            control = os.open(FILESYSTEM / 'binder-control', os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
            try:
                request = bytearray(struct.pack('256sII', b'binder', 0, 0))
                fcntl.ioctl(control, BINDER_CTL_ADD, request, True)
            finally:
                os.close(control)
        source_info = SOURCE.lstat()
        if not stat.S_ISCHR(source_info.st_mode):
            raise RuntimeError('The private Binder source is not a character device')
        os.chown(SOURCE, account.pw_uid, account.pw_gid)
        os.chmod(SOURCE, 0o600)
        descriptor = os.open(SOURCE, os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW)
        try:
            version = bytearray(struct.pack('i', 0))
            fcntl.ioctl(descriptor, BINDER_VERSION, version, True)
        finally:
            os.close(descriptor)
        protocol = struct.unpack('i', version)[0]
        if protocol != 8:
            raise RuntimeError('Incompatible Binder protocol: ' + str(protocol))
        target_type = mount_type(TARGET)
        if target_type is None:
            if TARGET.exists() or TARGET.is_symlink():
                info = TARGET.lstat()
                if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_gid != 0 or info.st_size != 0 or stat.S_IMODE(info.st_mode) != 0o600:
                    raise RuntimeError('Unexpected existing Binder target')
            else:
                descriptor = os.open(TARGET, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                os.close(descriptor)
            subprocess.run(['/bin/mount', '--bind', str(SOURCE), str(TARGET)], check=True)
        elif target_type != 'binder':
            raise RuntimeError('Unexpected Binder target mount')
        source_info, target_info = SOURCE.stat(), TARGET.lstat()
        if not stat.S_ISCHR(target_info.st_mode) or (source_info.st_dev, source_info.st_ino) != (target_info.st_dev, target_info.st_ino):
            raise RuntimeError('Binder target is not the private source device')
        if METADATA.exists() or METADATA.is_symlink():
            info = METADATA.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o644:
                raise RuntimeError('Unexpected Binder provisioning metadata')
        metadata = {
            'schema': SCHEMA,
            'backend': 'binderfs',
            'device': str(TARGET),
            'source': str(SOURCE),
            'uid': account.pw_uid,
            'gid': account.pw_gid,
            'major': os.major(target_info.st_rdev),
            'minor': os.minor(target_info.st_rdev),
            'protocol': protocol,
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        }
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=DIRECTORY, prefix='.provision-', delete=False) as output:
                temporary = Path(output.name)
                json.dump(metadata, output, indent=2)
                output.write('\n')
                os.fchmod(output.fileno(), 0o644)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, METADATA)
            temporary = None
            fsync_directory(DIRECTORY)
        finally:
            if temporary is not None:
                temporary.unlink()
        print('SAILDROID_BINDER_READY ' + json.dumps(metadata, sort_keys=True))
        if arguments.install_service:
            install_service(account)


if __name__ == '__main__':
    main()
