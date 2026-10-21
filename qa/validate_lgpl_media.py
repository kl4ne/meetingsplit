"""QA contract for an independently built LGPL-only Windows media stack.

This cannot certify LGPL obligations or copyright notices. Fail before binary
packaging whenever an unexpected proprietary/GPL codec slips into the build.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import subprocess
import sys
import zipfile

BLOCKED = re.compile(r'(?:^|[-_])(?:lib)?(?:x264|x265|xvid(?:core)?|xavs2)(?:[-_.]|$)', re.I)


def reject_native_names(names: list[str]) -> None:
    bad = sorted(name for name in names if Path(name).suffix.lower() in {'.dll','.pyd','.exe'}
                 and BLOCKED.search(Path(name).name))
    if bad:
        raise ValueError('GPL codec library present in LGPL media package: ' + ', '.join(bad))


def validate(binary_dir: Path, wheel_path: Path) -> None:
    for name in ('ffmpeg.exe','ffprobe.exe'):
        if not (binary_dir/name).is_file():
            raise ValueError('Missing LGPL executable: ' + name)
    reject_native_names([p.name for p in binary_dir.iterdir()])
    with zipfile.ZipFile(wheel_path) as wheel:
        reject_native_names(wheel.namelist())
        if not any(x.startswith('av/') and x.endswith('.pyd') for x in wheel.namelist()):
            raise ValueError('Repaired wheel does not contain PyAV binary extensions')
    for binary in ('ffmpeg.exe','ffprobe.exe'):
        output = subprocess.run([str(binary_dir/binary),'-version'], capture_output=True,text=True,
                                check=True,timeout=20).stdout
        configure = next((line for line in output.splitlines() if 'configuration:' in line),None)
        if not configure:
            raise ValueError(f'{binary} lacks build flags')
        forbidden=('--enable-gpl','--enable-nonfree','--enable-libx264','--enable-libx265','--enable-libxvid')
        if any(re.search(r'(?<!\S)'+re.escape(t)+r'(?:\s|$)',configure) for t in forbidden):
            raise ValueError(f'{binary} uses forbidden GPL/nonfree flags')


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--av-wheel',type=Path,required=True)
    args=parser.parse_args()
    validate(args.directory,args.av_wheel)
    print('Media build has no known GPL/native codec red flags. Human LGPL compliance review remains required.')
    return 0

if __name__=='__main__':
    sys.exit(main())