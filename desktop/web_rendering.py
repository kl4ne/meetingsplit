"""Process-local WebEngine paint settings for the Windows desktop UI."""
import os
import sys


def configure_web_rendering():
    if sys.platform=='win32':
        flags=os.environ.get('QTWEBENGINE_CHROMIUM_FLAGS','')
        for flag in ('--disable-gpu','--disable-gpu-compositing'):
            if flag not in flags.split():
                flags=(flags+' '+flag).strip()
        os.environ['QTWEBENGINE_CHROMIUM_FLAGS']=flags
