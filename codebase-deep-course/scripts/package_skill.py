"""Package a skill only after all recognized text files strictly decode as UTF-8."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

TEXT_SUFFIXES = {'.md', '.py', '.yaml', '.yml', '.json', '.js', '.mjs', '.cjs',
                 '.html', '.css', '.svg', '.txt', '.toml', '.ps1', '.sh', '.csv'}


def package(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.is_relative_to(root):
        raise ValueError('archive must be outside the skill directory')
    payload = []
    for path in sorted(root.rglob('*')):
        if any(part in {'__pycache__', '.git', 'node_modules', '.venv'} for part in path.relative_to(root).parts):
            continue
        if path.is_symlink():
            raise ValueError(f'symlink not packaged: {path}')
        if not path.is_file():
            continue
        data = path.read_bytes()
        if path.suffix.lower() in TEXT_SUFFIXES or not path.suffix:
            try:
                data.decode('utf-8', errors='strict')
            except UnicodeDecodeError as exc:
                raise ValueError(f'non-UTF-8 text: {path.relative_to(root)}') from exc
        payload.append((path.relative_to(root).as_posix(), data))
    if not any(name == 'SKILL.md' for name, _ in payload):
        raise ValueError('SKILL.md missing')
    output.parent.mkdir(parents=True, exist_ok=True)
    pending = output.with_suffix(output.suffix + '.tmp')
    with zipfile.ZipFile(pending, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in payload:
            info = zipfile.ZipInfo(root.name + '/' + name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    with zipfile.ZipFile(pending) as archive:
        if archive.testzip() is not None:
            raise ValueError('archive CRC check failed')
        for name, data in payload:
            if archive.read(root.name + '/' + name) != data:
                raise ValueError('archive roundtrip mismatch: ' + name)
    pending.replace(output)
    return {'passed': True, 'files': len(payload), 'archive': str(output),
            'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
            'utf8_text_files': sum(Path(n).suffix.lower() in TEXT_SUFFIXES or not Path(n).suffix for n, _ in payload)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('skill', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(package(args.skill, args.output), ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        print(json.dumps({'passed': False, 'error': str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
