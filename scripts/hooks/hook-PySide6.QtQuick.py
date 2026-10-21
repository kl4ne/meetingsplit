"""Qt Quick is a native WebEngine dependency; application QML debugging is unused."""
from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
binaries=[entry for entry in binaries if '/qmltooling/' not in entry[0].replace('\\','/').lower()]
