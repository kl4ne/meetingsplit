"""MeetingSplit uses QWebEngineWidgets/HTML, with no application QML documents.

Keep QtQml's native dependencies, but do not harvest every installed QML plugin.
The upstream generic hook otherwise adds unused Graphs/Quick3D/VirtualKeyboard
modules (GPL-only components) to this proprietary application's package.
Reassess this hook before introducing an application QML interface.
"""
from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
binaries=[entry for entry in binaries if '/qmltooling/' not in entry[0].replace('\\','/').lower()]
