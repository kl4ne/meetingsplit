"""Process-local WebEngine paint settings for the Windows desktop UI."""
import os
import sys


def configure_web_rendering():
    if sys.platform=='win32':
        flags=os.environ.get('QTWEBENGINE_CHROMIUM_FLAGS','')
        if '--disable-gpu' not in flags.split():
            os.environ['QTWEBENGINE_CHROMIUM_FLAGS']=(flags+' --disable-gpu').strip()
