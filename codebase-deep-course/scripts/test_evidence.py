"""Test the extract -> render -> audit and UTF-8 packaging boundary."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from extract_source import extract
from audit_course import audit
from package_skill import package


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.run_git('init', '-q')
        self.path = self.repo / 'sample.py'
        self.path.write_text('def twice(n):\n    return n * 2\n# END\n', encoding='utf-8')
        self.run_git('add', 'sample.py')
        self.run_git('-c', 'user.name=Skill Test', '-c', 'user.email=skill@example.invalid',
                     '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture')

    def run_git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.STDOUT)

    def test_commit_snapshot_survives_worktree_edits(self):
        record = extract(self.repo, 'sample.py', 'def twice', line_count=2)
        self.assertEqual(len(record['revision']), 40)
        self.assertEqual((record['start'], record['end']), (1, 2))
        self.path.write_text('def twice(n):\n    return n * 9\n', encoding='utf-8')
        page = self.repo / 'snapshot.html'
        page.write_text(record['html'], encoding='utf-8')
        self.assertTrue(audit(page, self.repo, require_revision=True)['passed'])

    def test_worktree_is_not_labeled_as_commit(self):
        self.path.write_text('def twice(n):\n    return n * 3\n', encoding='utf-8')
        record = extract(self.repo, 'sample.py', 'def twice', line_count=2, worktree=True)
        self.assertIsNone(record['revision'])
        self.assertTrue(record['differs_from_base'])
        page = self.repo / 'worktree.html'
        page.write_text(record['html'], encoding='utf-8')
        self.assertTrue(audit(page, self.repo, require_revision=True)['passed'])

    def test_missing_and_ambiguous_markers_fail(self):
        self.path.write_text('start\nstart\n', encoding='utf-8')
        for marker in ['missing', 'start']:
            with self.assertRaises(ValueError):
                extract(self.repo, 'sample.py', marker, line_count=1, worktree=True)

    def test_invalid_ranges_and_paths_fail(self):
        for count in [0, 99]:
            with self.assertRaises(ValueError):
                extract(self.repo, 'sample.py', 'def twice', line_count=count)
        with self.assertRaises(ValueError):
            extract(self.repo, '../sample.py', 'def twice', line_count=1)
        with self.assertRaises(ValueError):
            extract(self.repo, 'sample.py', 'def twice', end_marker='missing')

    def test_inclusive_end_and_untracked_source(self):
        record = extract(self.repo, 'sample.py', 'def twice', end_marker='# END')
        self.assertEqual(record['end'], 3)
        extra = self.repo / 'extra.py'
        extra.write_text('value = 4', encoding='utf-8')
        record = extract(self.repo, 'extra.py', 'value', line_count=1, worktree=True)
        self.assertIsNone(record['base_revision'])

    def test_forged_provenance_and_hash_fail(self):
        record = extract(self.repo, 'sample.py', 'def twice', line_count=2)
        page = self.repo / 'forged.html'
        page.write_text(record['html'].replace(record['revision'], 'HEAD'), encoding='utf-8')
        self.assertFalse(audit(page, self.repo, require_revision=True)['passed'])
        page.write_text(record['html'].replace(record['sha256'], '0'*64), encoding='utf-8')
        self.assertFalse(audit(page, self.repo, require_revision=True)['passed'])

    def test_cli_zero_source_returns_failure(self):
        page = self.repo / 'empty.html'
        page.write_text('<p>no excerpts</p>', encoding='utf-8')
        import sys
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('audit_course.py')),
                                 str(page), '--repo', str(self.repo)], capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b'"passed": false', result.stdout)

    def test_packaging_rejects_gbk_and_is_reproducible(self):
        skill = self.root / 'skill'
        skill.mkdir()
        (skill / 'SKILL.md').write_text('# Test', encoding='utf-8')
        meta = skill / 'metadata.yaml'
        meta.write_bytes('\u4e2d\u6587'.encode('gbk'))
        output = self.root / 'skill.zip'
        with self.assertRaisesRegex(ValueError, 'non-UTF-8'):
            package(skill, output)
        self.assertFalse(output.exists())
        meta.write_text('\u4e2d\u6587', encoding='utf-8')
        first = package(skill, output)
        second = package(skill, output)
        self.assertEqual(first['sha256'], second['sha256'])


if __name__ == '__main__':
    unittest.main()
