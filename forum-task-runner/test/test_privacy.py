import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/'scripts/privacy-check.py'
spec=importlib.util.spec_from_file_location('privacy',SCRIPT);privacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(privacy)

class PrivacyTests(unittest.TestCase):
    def test_private_paths_and_credentials(self):
        for path in ['.data/accounts/sjmc/tasks.sqlite','sites/foo/vault.key','sites/foo/.env.local','exports/data.json','sites/foo/storage-state.json']:
            self.assertIsNotNone(privacy.reason('forum-task-runner/'+path,b''))
        token=b'http://127.0.0.1:8924/#'+b'a'*64
        self.assertIsNotNone(privacy.reason('forum-task-runner/docs/leak.md',token))
        self.assertIsNone(privacy.reason('forum-task-runner/sites/sjmc/task.template.json',b'{"schedule":{"enabled":false}}'))

    def test_staged_snapshot_and_history(self):
        with tempfile.TemporaryDirectory() as d:
            def git(*args):return subprocess.run(['git',*args],cwd=d,check=True,capture_output=True)
            def check(mode):return subprocess.run(['python3',str(SCRIPT),mode],cwd=d,capture_output=True).returncode
            git('init');git('config','user.email','test@example.invalid');git('config','user.name','Test')
            p=Path(d)/'forum-task-runner/docs/note.md';p.parent.mkdir(parents=True)
            p.write_text('http://127.0.0.1:8924/#'+'b'*64);git('add','.')
            p.write_text('clean working copy')
            self.assertEqual(check('--staged'),1) # Must inspect the index, not working copy.
            git('commit','-m','synthetic fixture')
            git('add','.');git('commit','-m','remove synthetic token')
            self.assertEqual(check('--head'),0)
            self.assertEqual(check('--history'),1) # Removal from HEAD cannot hide old leaks.

if __name__=='__main__':unittest.main()
