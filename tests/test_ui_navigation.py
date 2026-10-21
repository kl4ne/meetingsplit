"""Chrome UI acceptance. Separate screens, no stacked long home page."""
from pathlib import Path
import os, shutil
import pytest
from playwright.sync_api import sync_playwright

HTML=Path(__file__).resolve().parents[1]/'MEETINGSPLIT_PREVIEW_v0.8.6.html'
BROWSER=os.environ.get('CHROMIUM_BINARY') or shutil.which('chromium') or shutil.which('google-chrome')
pytestmark=pytest.mark.skipif(not BROWSER,reason='Requires Chromium browser for visual QA')

@pytest.mark.parametrize('width,height',[ (1440,900),(1366,768),(1920,1080) ])
def test_individual_screens_and_navigation(width,height):
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=BROWSER,headless=True,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=1)
        errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.set_content(HTML.read_text(encoding="utf-8"),wait_until="load")
        assert page.locator('.screen.active-screen').count()==1
        assert page.locator('#view-home').is_visible()
        assert page.evaluate('document.documentElement.scrollHeight <= innerHeight + 1')
        for name in ('import','settings','process','results','home'):
            page.locator('.nav-item[data-go="'+name+'"]').click()
            assert page.locator('.screen.active-screen').count()==1
            assert page.locator('#view-'+name).is_visible()
            assert all(not page.locator('#view-'+other).is_visible() for other in ('home','import','settings','process','results') if other!=name)
            assert page.locator('.nav-item[aria-current="page"]').get_attribute('data-go')==name
            assert page.evaluate('document.documentElement.scrollHeight <= innerHeight + 1')
        assert errors==[]
        browser.close()

def test_preview_does_not_fake_processing():
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=BROWSER,headless=True,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1366,'height':768})
        page.set_content(HTML.read_text(encoding="utf-8"),wait_until="load")
        page.locator('.nav-item[data-go="process"]').click()
        page.locator('#start-job').click()
        assert 'Preview only' in page.locator('#job-status').inner_text()
        assert page.locator('#progress-fill').evaluate('(el)=>el.style.width')=='0%'
        assert not page.locator('#cancel-job').is_visible()
        browser.close()

def test_ai_profile_switches_duration():
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=BROWSER,headless=True,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1366,'height':768})
        page.set_content(HTML.read_text(encoding="utf-8"),wait_until="load")
        page.locator('.nav-item[data-go="settings"]').click()
        page.locator('#provider').select_option('gemini')
        page.locator('#plan').select_option('free')
        assert page.locator('#minutes').input_value()=='5'
        assert '5 minutes' in page.locator('#provider-hint').inner_text()
        page.locator('#plan').select_option('paid')
        assert page.locator('#minutes').input_value()=='20'
        browser.close()
