from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NOTICE='© 2026 Roberto S. Macfie. All rights reserved.'
def test_rights_notice_both_interfaces():
    for p in ('ui/index.html','MEETINGSPLIT_PREVIEW_v0.8.5.html'):
        s=(ROOT/p).read_text(encoding='utf-8')
        assert s.count(NOTICE)==1
        assert s.index('id="developer-signature"') < s.index('id="copyright-line"')
        assert 'https://rmcard.pages.dev/' not in s
        assert '<span id="developer-name">Roberto S. Macfie</span>' in s
def test_support_does_not_publish_unverified_donation_links():
    assert (ROOT/'.github/FUNDING.yml').exists()
    assert 'https://www.paypal.com/ncp/payment/XPUK3HVHJW8KE' in (ROOT/'.github/FUNDING.yml').read_text(encoding='utf-8')
    assert (ROOT/'.github/FUNDING.example.yml').exists()
    s=(ROOT/'README.md').read_text(encoding='utf-8')
    assert 'Free to use · Voluntary support' in s
    assert 'No donation is required' in s
