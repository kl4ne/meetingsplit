"""MeetingSplit 0.8.6: user-requested two-step readability increase."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_typography_increased_on_all_pages_and_controls():
    stylesheet = (ROOT / 'ui/styles.css').read_text(encoding='utf-8')
    page = (ROOT / 'ui/index.html').read_text(encoding='utf-8')
    # All explicit sizes must stay legible: no 8-11 px text on desktop.
    sizes = [float(n) for n in re.findall(r'font-size\s*:\s*(\d+(?:\.\d+)?)px', stylesheet)]
    assert len(sizes) >= 80
    assert min(sizes) >= 11
    assert 'font-size:16px' in stylesheet  # prev 12px body/controls
    assert 'font-size:15px' in stylesheet  # prev 11px secondary text
    assert 'font-size:14px' in stylesheet  # prev 10px captions
    assert 'v0.8.6' in page
    assert '#start-job' in stylesheet  # progress button still styled
    assert '#developer-name' in stylesheet
    for name in ('home', 'import', 'settings', 'process', 'results'):
        assert f'id="view-{name}"' in page


def test_preview_contains_same_styles_and_is_standalone():
    preview = (ROOT / 'MEETINGSPLIT_PREVIEW_v0.8.6.html').read_text(encoding='utf-8')
    css = (ROOT / 'ui/styles.css').read_text(encoding='utf-8')
    assert f'<style>{css}</style>' in preview
    assert 'Support Development' in preview
    assert 'https://rmcard.pages.dev' not in preview
