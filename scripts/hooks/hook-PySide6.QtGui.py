"""Keep normal Windows input; exclude the unused GPL virtual-keyboard plugin."""
from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
binaries=[entry for entry in binaries if 'qtvirtualkeyboardplugin' not in entry[0].lower()]
