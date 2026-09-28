"""Regression tests for evidence failures the static course audit must catch."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from audit_course import audit


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'source.py').write_text('value = 1\n', encoding='utf-8')
        self.html = self.root / 'course.html'
        digest = hashlib.sha256(b'value = 1').hexdigest()
        self.valid = ('<section id="chapter-a" data-chapter="a">'
                      '<a href="#chapter-a">chapter</a><code data-source-path="source.py" '
                      f'data-start="1" data-sha256="{digest}">value = 1</code></section>')

    def check(self, body):
        self.html.write_text(body, encoding='utf-8')
        return audit(self.html, self.root, offline=True)

    def test_exact_source_passes(self):
        report = self.check(self.valid)
        self.assertTrue(report['passed'])
        self.assertEqual(report['source_excerpts'], 1)

    def test_changed_source_fails(self):
        (self.root / 'source.py').write_text('value = 2\n', encoding='utf-8')
        self.assertIn('Source mismatch', ' '.join(self.check(self.valid)['errors']))

    def test_broken_and_duplicate_anchors_fail(self):
        report = self.check(self.valid + '<div id="chapter-a"></div><a href="#missing">bad</a>')
        self.assertFalse(report['passed'])
        self.assertEqual(len(report['errors']), 2)

    def test_offline_resources_fail_but_reference_links_allowed(self):
        self.assertTrue(self.check(self.valid + '<a href="https://example.com/docs">docs</a>')['passed'])
        self.assertFalse(self.check(self.valid + '<style>@import "https://example.com/font.css";</style>')['passed'])
        self.assertFalse(self.check(self.valid + '<script src="app.js"></script>')['passed'])

    def test_missing_evidence_is_explicit(self):
        report = self.check('<p>concepts only</p>')
        self.assertFalse(report['passed'])
        self.assertTrue(any('not performed' in note for note in report['errors']))
        self.assertTrue(audit(self.html, self.root, require_source=False)['passed'])

    def test_source_escape_is_rejected(self):
        report = self.check(self.valid.replace('source.py', '../outside.py'))
        self.assertTrue(any('escapes repository' in note for note in report['errors']))


if __name__ == '__main__':
    unittest.main()
