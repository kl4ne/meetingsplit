"""Fail before distribution if unused GPL-only Qt modules entered the package."""
from pathlib import Path
import sys

root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('dist/MeetingSplit')
if not (root/'MeetingSplit.exe').is_file() or not (root/'_internal'/'PySide6'/'Qt6Core.dll').is_file():
    raise SystemExit('Package audit requires an existing frozen Windows application.')
blocked=('qt6charts','qt6graphs','qt6quick3d','qt6virtualkeyboard','qt6quicktimeline',
         'qt6httpserver','qt6mqtt','qt6coap','qt6grpc','qt6lottie')
bad=[p.name for p in root.rglob('*.dll') if p.name.casefold().startswith(blocked)]
if bad:
    print('Unused Qt modules require exclusion/license assessment: '+', '.join(sorted(set(bad))))
    raise SystemExit(2)
print('Package contains no blocked unused Qt modules. Full native license review remains required.')

# Refuse publishing an accidentally GPL-enabled media stack. This is an
# evidence gate, not a declaration of complete third-party compliance.
import re
from native_inventory import classify_ffmpeg
forbidden=re.compile(r'(?:^|[-_])(?:lib)?(?:x264|x265|xvid)(?:[-_.]|$)',re.I)
problem=[str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.suffix.lower() in ('.dll','.pyd','.exe') and forbidden.search(p.name)]
if problem:
    raise SystemExit('GPL codecs detected in frozen package: '+', '.join(problem))
build_log=root/'_internal'/'legal'/'ffmpeg-build.txt'
report=classify_ffmpeg(build_log.read_text(encoding='utf-8') if build_log.is_file() else None)
if not report['configuration_found'] or any(flag in report['flags'] for flag in ('--enable-gpl','--enable-nonfree','--enable-libx264','--enable-libx265','--enable-libxvid')):
    raise SystemExit('FFmpeg configuration is not confirmed LGPL-only: '+str(report))
print('No GPL/native codec indicators found. LGPL obligations and human review remain open.')
