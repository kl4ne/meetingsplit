"""EN default / bilingual UI / persistent credit / language state acceptance."""
from pathlib import Path
import os, shutil
import pytest
from playwright.sync_api import sync_playwright

HTML=Path(__file__).resolve().parents[1]/'MEETINGSPLIT_PREVIEW_v0.8.4.html'
BROWSER=os.environ.get('CHROMIUM_BINARY') or shutil.which('chromium') or shutil.which('google-chrome')
pytestmark=pytest.mark.skipif(not BROWSER,reason='Chromium required for UI tests')

def test_ui_defaults_en_and_credit_all_views():
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=BROWSER,headless=True,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1366,'height':768})
        errors=[]
        page.on('pageerror',lambda err:errors.append(str(err)))
        page.set_content(HTML.read_text(encoding='utf-8'),wait_until='load')
        assert page.locator('html').get_attribute('lang')=='en'
        assert page.locator('#home-title').inner_text().startswith('Every word matters.')
        assert page.locator('#lang-en').get_attribute('aria-pressed')=='true'
        assert page.locator('#developer-signature').is_visible()
        assert page.locator('#developer-signature').inner_text()=='Designed & Developed by Roberto S. Macfie'
        assert page.locator('#developer-name').inner_text()=='Roberto S. Macfie'
        assert page.locator('#developer-name').evaluate('(e)=>e.closest("a")') is None
        for screen in ('home','import','settings','process','results'):
            page.locator('.nav-item[data-go="'+screen+'"]').click()
            assert page.locator('#developer-signature').is_visible()
            assert page.locator('#ui-language-control').is_visible()
            assert page.locator('.active-screen').count()==1
            assert page.evaluate('document.documentElement.scrollHeight <= innerHeight + 1')
        assert errors==[]
        browser.close()

def test_switches_to_spanish_without_modifying_meeting_preferences():
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=BROWSER,headless=True,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1366,'height':768})
        page.set_content(HTML.read_text(encoding='utf-8'),wait_until='load')
        page.locator('.nav-item[data-go="settings"]').click()
        page.locator('#minutes').select_option('5')
        page.locator('#input-language').select_option('auto')
        page.locator('#report-language').select_option('both')
        page.locator('#lang-es').click()
        assert page.locator('html').get_attribute('lang')=='es'
        assert page.locator('#settings-title').inner_text().startswith('Configura')
        assert page.locator('#lang-es').get_attribute('aria-pressed')=='true'
        assert page.locator('#minutes').input_value()=='5'
        assert page.locator('#input-language').input_value()=='auto'
        assert page.locator('#report-language').input_value()=='both'
        page.locator('#lang-en').click()
        assert page.locator('html').get_attribute('lang')=='en'
        assert page.locator('#settings-title').inner_text().startswith('Configure')
        assert page.locator('#minutes').input_value()=='5'
        browser.close()

def test_native_qsettings_has_language_persistence_and_no_forced_remote_audio():
    root=HTML.parent
    code=(root/'desktop/main.py').read_text(encoding='utf-8')
    assert "value('ui/language','en')" in code
    assert "setValue('ui/language', language)" in code
    assert 'BlockNetwork' in code
    assert 'openDeveloperCard' not in code
