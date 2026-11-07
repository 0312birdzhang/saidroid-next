#!/usr/bin/env python3
"""Exercise Binder provisioning in isolated Linux filesystem fixtures."""
import contextlib
import importlib.util
import io
import json
import os
import stat
import struct
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class BinderSetupTests(unittest.TestCase):
    def setUp(self):
        specification = importlib.util.spec_from_file_location(
            'binder_setup', Path(__file__).with_name('saildroid-binder-setup.py'))
        self.module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(self.module)
        self.temporary = tempfile.TemporaryDirectory(prefix='saildroid-binder-fixture-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.account = types.SimpleNamespace(pw_uid=65534, pw_gid=65534)
        self.module.RUNTIME = self.root / 'run/saildroid-binder'
        self.module.RUNTIME.parent.mkdir()
        self.module.FILESYSTEM = self.module.RUNTIME / 'binderfs'
        self.module.SOURCE = self.module.FILESYSTEM / 'binder'
        self.module.DIRECTORY = self.root / 'home/art/runtime/binder'
        self.module.TARGET = self.module.DIRECTORY / 'binder'
        self.module.METADATA = self.module.DIRECTORY / 'provision.json'
        (self.root / 'home/art').mkdir(parents=True)
        self.mounts = {}
        self.precreated = True
        self.protocol = 8
        self.additions = 0
        original_directory = self.module.root_directory

        def root_directory(path, mode):
            if path == Path('/home/art'):
                path = self.root / 'home/art'
            original_directory(path, mode)

        patches = (
            patch.object(self.module, 'root_directory', root_directory),
            patch.object(self.module, 'mount_type', lambda path: self.mounts.get(path)),
            patch.object(self.module.pwd, 'getpwnam', return_value=self.account),
            patch.object(self.module.subprocess, 'run', self.run_command),
            patch.object(self.module.fcntl, 'ioctl', self.ioctl),
            patch.object(sys, 'argv', ['saildroid-binder-setup']),
        )
        for replacement in patches:
            replacement.start()
            self.addCleanup(replacement.stop)

    def device(self, path):
        os.mknod(path, stat.S_IFCHR | 0o600, os.makedev(1, 3))

    def run_command(self, command, check):
        self.assertTrue(check)
        if command[:3] == ['/bin/mount', '-t', 'binder']:
            self.mounts[self.module.FILESYSTEM] = 'binder'
            (self.module.FILESYSTEM / 'binder-control').touch(mode=0o600)
            if self.precreated:
                self.device(self.module.SOURCE)
        elif command[:2] == ['/bin/mount', '--bind']:
            self.module.TARGET.unlink()
            os.link(self.module.SOURCE, self.module.TARGET)
            self.mounts[self.module.TARGET] = 'binder'
        else:
            self.fail('Unexpected command: ' + str(command))
        return subprocess.CompletedProcess(command, 0)

    def ioctl(self, descriptor, command, request, mutate):
        self.assertTrue(mutate)
        if command == self.module.BINDER_CTL_ADD:
            self.assertFalse(self.precreated)
            self.assertEqual(len(request), 264)
            self.assertEqual(struct.unpack('256sII', request)[0].split(b'\0')[0], b'binder')
            self.device(self.module.SOURCE)
            self.additions += 1
        elif command == self.module.BINDER_VERSION:
            request[:] = struct.pack('i', self.protocol)
        else:
            self.fail('Unexpected ioctl: ' + str(command))
        return 0

    def provision(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.module.main()

    def test_kernel_precreated_node_and_repeated_execution(self):
        self.module.DIRECTORY.mkdir(parents=True)
        for directory in (self.module.DIRECTORY.parent, self.module.DIRECTORY):
            os.chown(directory, self.account.pw_uid, self.account.pw_gid)
            directory.chmod(0o700)
        self.provision()
        before = self.module.TARGET.stat()
        self.provision()
        after = self.module.TARGET.stat()
        self.assertEqual((before.st_dev, before.st_ino), (after.st_dev, after.st_ino))
        self.assertEqual(self.additions, 0)
        self.assertEqual(after.st_uid, self.account.pw_uid)
        self.assertEqual(stat.S_IMODE(after.st_mode), 0o600)
        self.assertEqual(self.module.DIRECTORY.stat().st_uid, 0)
        self.assertEqual(json.loads(self.module.METADATA.read_text())['protocol'], 8)

    def test_kernel_dynamic_node_creation(self):
        self.precreated = False
        self.provision()
        self.assertEqual(self.additions, 1)
        self.assertTrue(stat.S_ISCHR(self.module.TARGET.stat().st_mode))

    def test_directory_preflight_preserves_ownership_on_failure(self):
        self.module.DIRECTORY.mkdir(parents=True)
        for directory in (self.module.DIRECTORY.parent, self.module.DIRECTORY):
            os.chown(directory, self.account.pw_uid, self.account.pw_gid)
            directory.chmod(0o700)
        (self.module.DIRECTORY / 'unexpected').touch()
        with self.assertRaisesRegex(RuntimeError, 'Unexpected runtime directory contents'):
            self.provision()
        for directory in (self.module.DIRECTORY.parent, self.module.DIRECTORY):
            self.assertEqual(directory.stat().st_uid, self.account.pw_uid)
            self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
        self.assertFalse(self.mounts)

    def test_recreate_mount_after_boot(self):
        self.provision()
        self.module.TARGET.unlink()
        self.module.TARGET.touch(mode=0o600)
        self.module.SOURCE.unlink()
        (self.module.FILESYSTEM / 'binder-control').unlink()
        self.module.FILESYSTEM.rmdir()
        self.mounts.clear()
        self.provision()
        self.assertTrue(stat.S_ISCHR(self.module.TARGET.stat().st_mode))

    def test_protocol_mismatch_rejected(self):
        self.protocol = 7
        with self.assertRaisesRegex(RuntimeError, 'Incompatible Binder protocol'):
            self.provision()
        self.assertFalse(self.module.TARGET.exists())

    def test_linked_target_preserved_and_rejected(self):
        self.module.DIRECTORY.mkdir(parents=True)
        self.module.TARGET.symlink_to('/dev/null')
        with self.assertRaisesRegex(RuntimeError, 'Unexpected existing Binder target'):
            self.provision()
        self.assertTrue(self.module.TARGET.is_symlink())

    def test_external_provisioning_preserved(self):
        self.module.DIRECTORY.mkdir(parents=True)
        self.device(self.module.TARGET)
        os.chown(self.module.TARGET, self.account.pw_uid, self.account.pw_gid)
        self.module.METADATA.write_text('{"schema":"external-device"}\n')
        self.module.METADATA.chmod(0o644)
        before = self.module.TARGET.stat()
        metadata = self.module.METADATA.read_bytes()
        self.provision()
        self.assertEqual(self.module.TARGET.stat().st_ctime_ns, before.st_ctime_ns)
        self.assertEqual(self.module.METADATA.read_bytes(), metadata)
        self.assertFalse(self.mounts)


if __name__ == '__main__':
    if sys.platform != 'linux' or os.geteuid() != 0:
        raise SystemExit('Run isolated fixtures as root on the Linux build host')
    if 'sailfishos' in Path('/etc/os-release').read_text().lower():
        raise SystemExit('Fixture runner is forbidden on the device')
    unittest.main()
