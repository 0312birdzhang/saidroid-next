from pathlib import Path
import copy,os,shutil,subprocess,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import temporary_directory_preparer as target

def preparer():
    return dict(**{'class':'com.android.tradefed.targetprep.RunCommandTargetPreparer'},options=[
        dict(name='run-command',value='mkdir -p /data/local/tmp/ctslibcore/java.io.tmpdir'),
        dict(name='run-command',value='mkdir -p /data/local/tmp/ctslibcore/user.home'),
        dict(name='teardown-command',value='rm -rf /data/local/tmp/ctslibcore')])

class OriginalDirectorySpec(unittest.TestCase):
    def test_original_directories_are_retained(self):
        spec=target.directory_spec([preparer()]);self.assertEqual(spec['children'],['java.io.tmpdir','user.home'])
    def test_extra_shell_operation_is_rejected(self):
        p=preparer();p['options'][0]['value']+='; touch /outside'
        with self.assertRaises(ValueError):target.directory_spec([p])
    def test_missing_cleanup_is_rejected(self):
        p=preparer();p['options'].pop()
        with self.assertRaises(ValueError):target.directory_spec([p])
    def test_duplicate_preparers_are_rejected(self):
        with self.assertRaises(ValueError):target.directory_spec([preparer(),preparer()])
    def test_other_fixture_is_not_reinterpreted(self):
        self.assertIsNone(target.directory_spec([dict(**{'class':'other.RunCommandTargetPreparer'},options=preparer()['options'])]))

@unittest.skipUnless(sys.platform.startswith('linux')and os.geteuid()==0,'Linux root preparer filesystem contract')
class RealFilesystemContract(unittest.TestCase):
    def setUp(self):
        self.container=Path(tempfile.mkdtemp(prefix='saidroid-libcore-preparer-',dir='/run'));self.container.chmod(0o755)
        self.data=self.container/'data';self.data.mkdir(mode=0o755);self.data.chmod(0o755);self.original=target._CTS_DATA;target._CTS_DATA=self.data
        self.spec=target.directory_spec([preparer()]);self.state={};self.root=self.data/'local/tmp/ctslibcore'
        self.outside=self.container/'outside';self.outside.mkdir();(self.outside/'sentinel').write_text('Must survive fixture cleanup')
    def tearDown(self):
        target._CTS_DATA=self.original;shutil.rmtree(self.container)
    def prepare(self):target.prepare_directories(self.spec,self.state,65534,65534)
    def parents(self):
        self.root.parent.mkdir(parents=True)
        (self.data/'local').chmod(0o755);self.root.parent.chmod(0o755)
    def test_real_unprivileged_files_and_cleanup(self):
        self.prepare();file=self.root/'java.io.tmpdir/actual.txt'
        subprocess.run(['/usr/bin/python3','-c','from pathlib import Path;Path('+repr(str(file))+').write_text("actual unprivileged IO")'],user=65534,group=65534,extra_groups=[],check=True)
        self.assertEqual(file.read_text(),'actual unprivileged IO');self.assertEqual(file.stat().st_uid,65534)
        target.cleanup_directories(self.state);self.assertFalse(self.root.exists());self.assertEqual(list(self.data.iterdir()),[]);self.assertTrue(self.state['cleaned'])
    def test_existing_fixture_is_preserved(self):
        self.parents();self.root.mkdir();(self.root/'existing.txt').write_text('existing')
        with self.assertRaises(FileExistsError):self.prepare()
        target.cleanup_directories(self.state);self.assertEqual((self.root/'existing.txt').read_text(),'existing')
    def test_symlink_root_is_not_followed(self):
        self.parents();self.root.symlink_to(self.outside,target_is_directory=True)
        with self.assertRaises(FileExistsError):self.prepare()
        target.cleanup_directories(self.state);self.assertTrue((self.outside/'sentinel').is_file())
    def test_symlink_parent_is_rejected(self):
        (self.data/'local').symlink_to(self.outside,target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError,'real directory'):self.prepare()
        target.cleanup_directories(self.state);self.assertEqual(sorted(p.name for p in self.outside.iterdir()),['sentinel'])
    def test_writable_parent_is_rejected(self):
        p=self.data/'local';p.mkdir();p.chmod(0o777)
        with self.assertRaisesRegex(RuntimeError,'Untrusted'):self.prepare()
        target.cleanup_directories(self.state);self.assertTrue(p.is_dir())
    def test_replaced_top_inode_prevents_cleanup(self):
        self.prepare();self.root.rename(self.root.with_name('original'));self.root.symlink_to(self.outside,target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError,'real directory'):target.cleanup_directories(self.state)
        self.assertTrue((self.outside/'sentinel').is_file())
    def test_nested_symlink_does_not_delete_target(self):
        self.prepare();(self.root/'java.io.tmpdir/link').symlink_to(self.outside,target_is_directory=True)
        target.cleanup_directories(self.state);self.assertTrue((self.outside/'sentinel').is_file())
    def test_new_unrelated_parent_contents_are_retained(self):
        self.prepare();other=self.root.parent/'unrelated';other.write_text('preserve')
        with self.assertRaisesRegex(RuntimeError,'unrelated contents'):target.cleanup_directories(self.state)
        self.assertEqual(other.read_text(),'preserve')
    def test_modified_spec_is_rejected_without_writes(self):
        spec=copy.deepcopy(self.spec);spec['root']='/different';state={}
        with self.assertRaises(ValueError):target.prepare_directories(spec,state,65534,65534)
        self.assertEqual(state,{});self.assertEqual(list(self.data.iterdir()),[])
    def test_nontraversable_parent_is_rejected_without_chmod(self):
        self.data.chmod(0o700)
        with self.assertRaisesRegex(PermissionError,'cannot traverse'):self.prepare()
        self.assertEqual(self.state,{});self.assertEqual(self.data.stat().st_mode&0o777,0o700)
    def test_owner_handoff_follows_all_privileged_child_operations(self):
        real_chown=os.chown;observed=[]
        def chown(path,uid,gid):
            path=Path(path)
            if path.name in ['java.io.tmpdir','user.home']:
                self.assertEqual(self.root.stat().st_uid,0,'Parent ownership handed off before privileged child chown')
                attack=subprocess.run(['/usr/bin/python3','-c','import os;os.rename('+repr(str(path))+','+repr(str(path)+'.moved')+')'],user=65534,group=65534,extra_groups=[],capture_output=True,text=True)
                self.assertNotEqual(attack.returncode,0);self.assertIn('PermissionError',attack.stderr);observed.append(path.name)
            real_chown(path,uid,gid)
        with patch.object(target.os,'chown',chown):self.prepare()
        self.assertEqual(observed,['java.io.tmpdir','user.home']);self.assertEqual(self.root.stat().st_uid,65534)
        target.cleanup_directories(self.state)

if __name__=='__main__':unittest.main()
