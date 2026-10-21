"""Browser audit for the v0.8.1 light-surface contrast fix.
Requires Playwright + Chromium; only local in-memory content, never opens PayPal.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'MEETINGSPLIT_PREVIEW_v0.8.1.html').read_text(encoding='utf-8')
SCREENS = ('home','import','settings','process','results')
LIGHT = {
    'home':['.step-card small','.step-number','.step-link','.home-section-heading>span'],
    'import':['.folder-text','.field-label','.drop-zone small','.outline-cta'],
    'settings':['.field-label','.screen-intro p:not(.eyebrow)','.settings-footer>span','.checkbox-row small'],
    'process':['.state-label','.run-card #job-status','.run-note'],
    'results':['.result-eyebrow','.results-layout>p','.results-layout h2 em','.results-layout #results-new'],
}

def luminance(values):
    r,g,b=[v/255 for v in values]
    a=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in (r,g,b)]
    return .2126*a[0]+.7152*a[1]+.0722*a[2]

def contrast(a,b):
    x,y=sorted((luminance(a),luminance(b)))
    return (y+.05)/(x+.05)

def rgb(css):
    return tuple(int(k.strip()) for k in css[4:-1].split(',')[:3])

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1366,'height':768})
        errors=[]
        page.on('pageerror',lambda exc: errors.append(str(exc)))
        page.set_content(HTML,wait_until='domcontentloaded')
        tested=0
        for locale in ('en','es'):
            page.locator(f'[data-locale="{locale}"]').click()
            assert page.locator('html').get_attribute('lang') == locale
            for screen in SCREENS:
                page.locator(f'.nav-item[data-go="{screen}"]').click()
                assert page.locator('.screen.active-screen').count() == 1
                assert page.evaluate('document.documentElement.scrollHeight <= innerHeight + 1')
                assert page.locator('#developer-signature').is_visible()
                for selector in LIGHT[screen]:
                    obj=page.locator(f'#view-{screen} {selector}').first
                    assert obj.count(),f'Missing {screen} {selector}'
                    fg = rgb(obj.evaluate('(el)=>getComputedStyle(el).color'))
                    score = contrast(fg,(255,255,255))
                    assert score >= 4.5,(screen,selector,score,fg)
                    tested+=1
        assert not errors, errors
        print(f'PASS: {len(SCREENS)*2} screens inspected; {tested} light text checks >=4.5:1; 2 locales, 0 page JS errors')
        browser.close()
if __name__=='__main__':main()
