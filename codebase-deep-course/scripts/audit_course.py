"""Audit course HTML anchors, exact source excerpts and offline resource hints.

Standard library only. Does not validate prose, CSS layout or JS behavior.
"""
import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from extract_source import source_bytes


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.resources, self.snippets = [], [], [], []
        self.capture = None
        self.chapters = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if 'data-chapter' in attrs:
            self.chapters += 1
        if tag == 'a' and attrs.get('href'):
            self.links.append(attrs['href'])
        if tag == 'code' and 'data-source-path' in attrs:
            self.capture = {'attrs': attrs, 'parts': []}
        if tag in {'script', 'img', 'iframe', 'source', 'video', 'audio', 'embed', 'input'}:
            if attrs.get('src'):
                self.resources.append(attrs['src'])
        if tag == 'link' and set(attrs.get('rel', '').lower().split()) & {
                'stylesheet', 'preload', 'modulepreload', 'icon'}:
            if attrs.get('href'):
                self.resources.append(attrs['href'])
        if tag == 'object' and attrs.get('data'):
            self.resources.append(attrs['data'])
        if tag in {'image', 'use'}:
            ref = attrs.get('href') or attrs.get('xlink:href')
            if ref:
                self.resources.append(ref)
        # Flag srcset as a whole; data URLs contain commas, so naive splitting is unsafe.
        if attrs.get('srcset'):
            self.resources.append('srcset:' + attrs['srcset'])

    def handle_data(self, data):
        if self.capture is not None:
            self.capture['parts'].append(data)

    def handle_endtag(self, tag):
        if tag == 'code' and self.capture is not None:
            self.snippets.append(self.capture)
            self.capture = None


def audit(html_path, repo, offline=False, require_source=True, require_revision=False):
    html_path, repo = Path(html_path).resolve(), Path(repo).resolve()
    raw = html_path.read_text(encoding='utf-8')
    page = Page()
    page.feed(raw)
    errors, warnings = [], []
    seen = set()
    for identifier in page.ids:
        if identifier in seen:
            errors.append(f'Duplicate id: {identifier}')
        seen.add(identifier)
    for href in page.links:
        url = urlsplit(href)
        if url.scheme or url.netloc:
            continue
        target = (html_path.parent / unquote(url.path)).resolve() if url.path else html_path
        if not target.exists():
            errors.append(f'Missing local link: {href}')
        elif target == html_path and url.fragment and unquote(url.fragment) not in seen:
            errors.append(f'Missing anchor: {href}')
    for item in page.snippets:
        attrs = item['attrs']
        name = attrs['data-source-path']
        try:
            target = (repo / name).resolve()
            if not target.is_relative_to(repo):
                raise ValueError('source path escapes repository')
            start = int(attrs['data-start'])
            if start < 1:
                raise ValueError('data-start must be one-based')
            excerpt = ''.join(item['parts']).replace('\r\n', '\n').replace('\r', '\n')
            revision = attrs.get('data-revision')
            mode = attrs.get('data-source-mode')
            if require_revision and mode not in {'commit', 'worktree'}:
                raise ValueError('explicit commit/worktree provenance is required')
            if mode == 'commit' and (not revision or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', revision)):
                raise ValueError('commit excerpts require a full immutable revision')
            if mode == 'worktree' and revision:
                raise ValueError('worktree excerpts cannot claim a commit revision')
            raw_source, _ = source_bytes(repo, name, revision)
            source = raw_source.decode('utf-8', errors='strict').splitlines()
            if require_revision and not attrs.get('data-file-sha256'):
                raise ValueError('full source file hash is required')
            if attrs.get('data-file-sha256') and hashlib.sha256(raw_source).hexdigest() != attrs['data-file-sha256']:
                errors.append(f'File hash mismatch: {name}')
            count = excerpt.count('\n') + 1
            actual = '\n'.join(source[start-1:start-1+count])
            if actual != excerpt:
                errors.append(f'Source mismatch: {name}:{start}')
            if hashlib.sha256(excerpt.encode('utf-8')).hexdigest() != attrs['data-sha256']:
                errors.append(f'Hash mismatch: {name}:{start}')
        except (OSError, ValueError, KeyError, UnicodeError) as exc:
            errors.append(f'Invalid source record {name}: {exc}')
    if not page.snippets:
        (errors if require_source else warnings).append('No source excerpts found; source verification was not performed.')
    legacy = sum(not s['attrs'].get('data-source-mode') for s in page.snippets)
    if legacy:
        warnings.append(f'{legacy} legacy excerpts checked against worktree only; commit provenance was not verified.')
    if not page.chapters:
        warnings.append('No data-chapter attributes; chapter count is unavailable.')
    css = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', raw, re.S | re.I))
    css += '\n' + '\n'.join(re.findall(r'\bstyle=[\"\'](.*?)[\"\']', raw, re.S | re.I))
    page.resources.extend(re.findall(r'url\(\s*[\"\']?([^\"\')\s]+)', css, re.I))
    page.resources.extend(re.findall(r'@import\s+[\"\']([^\"\']+)', css, re.I))
    resources = sorted(set(r for r in page.resources if not r.startswith(('data:', '#'))))
    if offline and resources:
        errors.append('Non-embedded resource references: ' + ', '.join(r[:180] for r in resources))
    warnings.append('Static audit only: manually verify teaching quality, source semantics, browser behavior and dynamic network requests.')
    return {'passed': not errors, 'html': str(html_path),
            'html_sha256': hashlib.sha256(html_path.read_bytes()).hexdigest(),
            'chapters': page.chapters, 'source_excerpts': len(page.snippets),
            'require_source': require_source, 'require_revision': require_revision,
            'errors': errors, 'warnings': warnings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('html', type=Path)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--allow-no-source', action='store_true', help='Only for explicitly conceptual, non-source courses')
    parser.add_argument('--require-revision', action='store_true', help='Require versioned provenance and full file hashes')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        report = audit(args.html, args.repo, args.offline, not args.allow_no_source, args.require_revision)
    except (OSError, ValueError, UnicodeError) as exc:
        report = {'passed': False, 'errors': [str(exc)]}
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + '\n', encoding='utf-8')
    print(rendered)
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
