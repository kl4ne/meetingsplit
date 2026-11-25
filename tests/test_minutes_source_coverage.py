import pytest

from engine import summarize
from engine.minutes_evidence import explicit_source_items, source_blocks
from qa.minutes_long_acceptance import fixture, score


def test_independent_source_pass_recovers_omitted_approval(monkeypatch):
    monkeypatch.setattr(summarize, 'ollama_chat', lambda *args, **kwargs: '{"items":[]}')
    evidence = {}
    report = summarize.summarize_local(
        '[00:06:00] The board approved the privacy checklist for the internal review.',
        'both', 'both', 'qwen3:4b', evidence_sink=evidence.update)
    assert [(i['category'], i['sources'][0]['timestamp']) for i in evidence['items']] == [('decision', '00:06:00')]
    assert not evidence['coverage_gaps']
    assert 'privacy checklist' in report


def test_long_bilingual_fixture_recovers_evidence_across_windows(monkeypatch):
    transcript, expected = fixture()
    blocks = list(source_blocks(transcript))
    for start, _, _, _, _, end in expected:
        if end:
            assert any(first[-1]['timestamp']==start and second[0]['timestamp']==end
                       for first, second in zip(blocks, blocks[1:]))
    monkeypatch.setattr(summarize, 'ollama_chat', lambda *args, **kwargs: '{"items":[]}')
    evidence = {}
    summarize.summarize_local(transcript, 'both', 'both', 'qwen3:4b', evidence_sink=evidence.update)
    result = score(transcript, expected, evidence['items'])
    assert result['passed'], result


@pytest.mark.parametrize('sequence', [
    ['The board proposed extending hours.', 'This proposal is not approved.'],
    ['The board proposed extending hours.', 'If the budget is approved, this proposal is approved.'],
    ['The board proposed extending hours.', 'There was a break.', 'This proposal is approved.'],
    ['The board proposed extending hours.', 'Reportedly this proposal was approved.'],
])
def test_no_approval_inferred_from_unlinked_or_uncertain_evidence(sequence):
    transcript = '\n'.join(f'[00:00:{i:02d}] {line}' for i,line in enumerate(sequence))
    items = explicit_source_items([r for block in source_blocks(transcript) for r in block], 'en')
    assert any(item['category']=='proposal' for item in items)
    assert all(item['category']!='decision' for item in items)


def test_model_record_with_unrelated_extra_citation_does_not_duplicate_agreement(monkeypatch):
    transcript = ('[00:00:01] The discussion continued.\n'
                  '[00:00:04] The board approved the retention pilot.')
    response = ('{"items":[{"category":"decision","owner":null,"due":null,'
                '"text_en":"Retention pilot approval","sources":['
                '{"id":1,"quote":"The discussion continued."},'
                '{"id":2,"quote":"The board approved the retention pilot."}]}]}')
    monkeypatch.setattr(summarize, 'ollama_chat', lambda *args, **kwargs: response)
    result = {}
    summarize.summarize_local(transcript, 'minutes', 'en', 'qwen3:4b', evidence_sink=result.update)
    assert [(item['category'], [ref['source_id'] for ref in item['sources']])
            for item in result['items']] == [('decision', [2])]
