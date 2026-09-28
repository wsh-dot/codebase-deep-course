"""Deterministically extract a unique source range from a commit or worktree."""
import argparse
import hashlib
import html
import json
import subprocess
from pathlib import Path, PurePosixPath


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(repo, *args):
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True)
    if result.returncode:
        raise ValueError(result.stderr.decode('utf-8', errors='replace').strip())
    return result.stdout


def source_bytes(repo, path, revision=None):
    repo = Path(repo).resolve()
    relative = PurePosixPath(path)
    if not path or '\\' in path or ':' in path or relative.is_absolute() or '..' in relative.parts:
        raise ValueError('source path must be repository-relative POSIX path')
    target = (repo / path).resolve()
    if not target.is_relative_to(repo):
        raise ValueError('source path escapes repository')
    if revision is not None:
        commit = git(repo, 'rev-parse', '--verify', '--end-of-options', revision + '^{commit}').decode().strip()
        data = git(repo, 'cat-file', 'blob', commit + ':' + relative.as_posix())
        return data, commit
    return target.read_bytes(), None


def extract(repo, path, marker, *, line_count=None, end_marker=None, revision='HEAD', worktree=False):
    if not marker or (line_count is None) == (end_marker is None):
        raise ValueError('provide a nonempty start marker and exactly one range: lines or end marker')
    raw, commit = source_bytes(repo, path, None if worktree else revision)
    lines = raw.decode('utf-8', errors='strict').splitlines()
    matches = [i for i, line in enumerate(lines) if marker in line]
    if len(matches) != 1:
        raise ValueError(f'start marker must match exactly once; found {len(matches)}')
    start = matches[0]
    if line_count is not None:
        if line_count < 1 or start + line_count > len(lines):
            raise ValueError('line count must be positive and stay within the file')
        end = start + line_count
    else:
        ends = [i for i, line in enumerate(lines) if end_marker and end_marker in line]
        if len(ends) != 1 or ends[0] < start:
            raise ValueError('end marker must match exactly once at or after start')
        end = ends[0] + 1
    text = '\n'.join(lines[start:end])
    record = {'path': path, 'mode': 'worktree' if worktree else 'commit',
              'revision': commit, 'start': start + 1, 'end': end, 'line_count': end-start,
              'sha256': digest(text.encode('utf-8')), 'file_sha256': digest(raw), 'text': text}
    if worktree:
        try:
            baseline, base = source_bytes(repo, path, 'HEAD')
            record.update(base_revision=base, differs_from_base=baseline != raw)
        except ValueError:
            # Untracked file or non-Git source: do not invent a baseline commit.
            record.update(base_revision=None, differs_from_base=None)
    attrs = {'data-source-path': path, 'data-start': record['start'],
             'data-sha256': record['sha256'], 'data-source-mode': record['mode'],
             'data-file-sha256': record['file_sha256']}
    if commit:
        attrs['data-revision'] = commit
    if record.get('base_revision'):
        attrs['data-base-revision'] = record['base_revision']
    attribute_text = ' '.join(f'{k}="{html.escape(str(v), quote=True)}"' for k, v in attrs.items())
    record['html'] = '<pre><code ' + attribute_text + '>' + html.escape(text) + '</code></pre>'
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--path', required=True)
    parser.add_argument('--start-marker', required=True)
    ranges = parser.add_mutually_exclusive_group(required=True)
    ranges.add_argument('--lines', type=int)
    ranges.add_argument('--end-marker')
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--revision', default='HEAD')
    source.add_argument('--worktree', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--html-output', type=Path)
    args = parser.parse_args()
    try:
        record = extract(args.repo, args.path, args.start_marker, line_count=args.lines,
                         end_marker=args.end_marker, revision=args.revision, worktree=args.worktree)
        for path in [args.output, args.html_output]:
            if path:
                path.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        if args.html_output:
            args.html_output.write_text(record['html'], encoding='utf-8')
        print(json.dumps({'passed': True, 'path': record['path'], 'revision': record['revision'],
                          'mode': record['mode'], 'start': record['start'], 'end': record['end']}))
    except (OSError, ValueError, UnicodeError) as exc:
        print(json.dumps({'passed': False, 'error': str(exc)}, ensure_ascii=False))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
