"""Keep the existing 0.8.6 standalone UI preview in sync without a version bump."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    text=(ROOT/'ui/index.html').read_text(encoding='utf-8')
    text=text.replace('<link rel="stylesheet" href="styles.css">',
                      '<style>'+(ROOT/'ui/styles.css').read_text(encoding='utf-8')+'</style>')
    for script in ('locales.js','app.js'):
        text=text.replace(f'<script src="{script}"></script>',
                          '<script>'+(ROOT/'ui'/script).read_text(encoding='utf-8')+'</script>')
    text=text.replace('<script src="qrc:///qtwebchannel/qwebchannel.js"></script>','')
    (ROOT/'MEETINGSPLIT_PREVIEW_v0.8.6.html').write_text(text,encoding='utf-8')


if __name__=='__main__': main()
