"""QA only, no package creation or release authorization."""
import json,platform,ssl,sqlite3,sys
from pathlib import Path
out=Path('work/runtime-compatibility.json')
result={'python':platform.python_version(),'openssl':ssl.OPENSSL_VERSION,'sqlite':sqlite3.sqlite_version,'candidate':'Python 3.14.10 compatibility only','imports':{},'ok':False}
try:
    import ctranslate2,av,PyInstaller
    from faster_whisper.audio import decode_audio
    from PySide6.QtCore import qVersion
    from PySide6.QtWebEngineCore import qWebEngineVersion,qWebEngineChromiumVersion,qWebEngineChromiumSecurityPatchVersion
    result['imports']={'ctranslate2':ctranslate2.__version__,'av':av.__version__,'pyinstaller':PyInstaller.__version__,'qt':qVersion(),'webengine':qWebEngineVersion(),'chromium':qWebEngineChromiumVersion(),'chromium_security_patch':qWebEngineChromiumSecurityPatchVersion()}
    result['ok']=True
finally:
    out.write_text(json.dumps(result,indent=2),encoding='utf-8')
