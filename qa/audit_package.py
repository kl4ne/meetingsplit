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
