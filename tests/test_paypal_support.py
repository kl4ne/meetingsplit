"""Direct PayPal NCP hosted checkout: explicit click, no iframe or embedded SDK."""
from pathlib import Path
import os, shutil
import pytest
ROOT=Path(__file__).resolve().parents[1]
PAYPAL='https://www.paypal.com/ncp/payment/XPUK3HVHJW8KE'
PREVIEW=ROOT/'MEETINGSPLIT_PREVIEW_v0.8.5.html'

def test_paypal_link_is_owner_provided_and_no_sdk():
    for file in (ROOT/'ui/index.html',PREVIEW):
        src=file.read_text(encoding='utf8')
        assert src.count('href="'+PAYPAL+'"')==1
        assert 'id="support-development"' in src
        assert 'target="_blank"' in src
        assert 'rel="noopener noreferrer"' in src
        assert 'www.paypal.com/sdk/js' not in src
        assert 'paypal.HostedButtons' not in src
        assert 'rmcard.pages.dev' not in src
    assert not (ROOT/'support').exists()

def test_external_browser_native_and_no_personal_card_link():
    source=(ROOT/'desktop/main.py').read_text(encoding='utf8')
    assert 'def openPayPalSupport(self)' in source
    assert "QUrl('"+PAYPAL+"')" in source
    assert 'QDesktopServices.openUrl(url)' in source
    assert 'openDeveloperCard' not in source
    assert "ROOT/'support'/'paypal_support.html'" not in source
    script=(ROOT/'ui/app.js').read_text(encoding='utf8')
    assert 'bridge.openPayPalSupport()' in script
    assert 'event.preventDefault()' in script
    assert "window.open" not in script
    assert '--add-data "support;support"' not in (ROOT/'scripts/compilar_windows.bat').read_text(encoding='utf8')

BROWSER=os.getenv('CHROMIUM_BINARY') or shutil.which('chromium') or shutil.which('google-chrome')
@pytest.mark.skipif(not BROWSER,reason='Chromium unavailable')
def test_support_bilingual_navigation_and_real_outbound_click():
    sync_playwright = pytest.importorskip('playwright.sync_api').sync_playwright
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=BROWSER,headless=True,args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':1366,'height':768})
        context.route('https://www.paypal.com/**',lambda route:route.fulfill(status=200,content_type='text/html',body='<title>PayPal test interception</title>'))
        page=context.new_page()
        outbound=[]
        page.on('request',lambda req: outbound.append(req.url) if req.url.startswith('http') else None)
        page.set_content(PREVIEW.read_text(encoding='utf8'),wait_until='load')
        support=page.locator('#support-development')
        assert support.is_visible()
        assert 'Support Development' in support.inner_text()
        assert outbound==[]
        page.locator('#lang-es').click()
        assert 'Apoyar el desarrollo' in support.inner_text()
        page.locator('#lang-en').click()
        assert 'Support Development' in support.inner_text()
        for screen in ['home','import','settings','process','results']:
            page.locator('.nav-item[data-go="'+screen+'"]').click()
            assert support.is_visible()
            assert page.locator('.active-screen').count()==1
        with page.expect_popup() as popup_info:
            support.click()
        popup=popup_info.value
        assert popup is not None # a real new tab is created by the click; network checkout is not tested
        assert page.url=='about:blank' # set_content preview stays put
        assert page.locator('#developer-name').evaluate('(el)=>el.closest("a")') is None
        assert not page.locator('#developer-link').count()
        assert 'rmcard.pages.dev' not in PREVIEW.read_text(encoding='utf8')
        browser.close()
