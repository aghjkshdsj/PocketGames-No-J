"""Runtime selection crosses branches without falling back to another revision."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = (str(Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Git/bin/bash.exe')
        if os.name == 'nt' else shutil.which('bash'))
SHA = '334019ea45d3c4c1cec39ea45f1bd10fa5b71a11'
MOCK = r'''
gh() {
    printf '%s\n' "$@" >> "$MOCK_CALLS"
    case "$MOCK_RESULT" in
        found) printf '39042203068\n' ;;
        missing) return 0 ;;
        error) echo 'API unavailable' >&2; return 42 ;;
    esac
}
export -f gh
bash "$1" "$2"
'''


class RuntimeLookupTests(unittest.TestCase):
    def lookup(self, result, revision=SHA):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / 'calls.txt'
            env = dict(os.environ, GITHUB_REPOSITORY='aghjkshdsj/PocketGames-No-J',
                       GITHUB_SHA='a' * 40, GITHUB_REF_NAME='feature/quit-game-keep-app-open',
                       RUNTIME_SOURCE_SHA=revision, MOCK_RESULT=result, MOCK_CALLS=log.as_posix())
            run = subprocess.run([BASH, '-c', MOCK, '--',
                                  (ROOT / 'tools/latest-run.sh').as_posix(), 'wine-unix.yml'],
                                 env=env, capture_output=True, text=True)
            return run, log.read_text().splitlines() if log.exists() else []

    def test_exact_revision_on_another_branch(self):
        run, args = self.lookup('found')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), '39042203068')
        self.assertNotIn('--branch', args)
        self.assertEqual(args[args.index('--commit') + 1], SHA)
        self.assertEqual(args[args.index('--status') + 1], 'success')
        self.assertEqual(args[args.index('--jq') + 1],
                         f'.[] | select(.headSha == "{SHA}") | .databaseId')
        self.assertEqual(args.count('list'), 1)

    def test_missing_revision_does_not_fall_back(self):
        run, args = self.lookup('missing')
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(run.stdout, '')
        self.assertIn('no successful run for exact runtime revision', run.stderr)
        self.assertEqual(args.count('list'), 1)

    def test_api_failure_is_not_silently_ignored(self):
        run, args = self.lookup('error')
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(run.stdout, '')
        self.assertIn('API unavailable', run.stderr)
        self.assertEqual(args.count('list'), 1)

    def test_short_or_invalid_revision_never_queries(self):
        for revision in ('334019e', 'main', 'g' * 40):
            with self.subTest(revision=revision):
                run, args = self.lookup('found', revision)
                self.assertNotEqual(run.returncode, 0)
                self.assertIn('runtime revision must be a full commit SHA', run.stderr)
                self.assertEqual(args, [])


if __name__ == '__main__':
    unittest.main()
