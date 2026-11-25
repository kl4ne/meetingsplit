import json
from qa.check_release_gate import blockers, main, MANDATORY


def test_empty_requirements_cannot_authorize_release():
    assert blockers({'release_allowed': True, 'required': {}})


def test_every_mandatory_key_must_be_present():
    gates = dict.fromkeys(MANDATORY, True)
    assert not blockers({'release_allowed': True, 'required': gates})
    for key in MANDATORY:
        incomplete = dict(gates)
        del incomplete[key]
        assert blockers({'release_allowed': True, 'required': incomplete})


def test_explicit_boolean_approval_and_extra_requirements():
    gates = dict.fromkeys(MANDATORY, True)
    assert blockers({'release_allowed': 1, 'required': gates})
    gates['extra_review'] = 1
    assert blockers({'release_allowed': True, 'required': gates})
    assert blockers({'release_allowed': True, 'required': None})


def test_duplicate_or_malformed_json_fails_closed(tmp_path):
    path = tmp_path / 'gate.json'
    path.write_text('{"release_allowed":false,"release_allowed":true,"required":{}}')
    assert main(path) == 2
    path.write_text('{')
    assert main(path) == 2
    assert main(tmp_path / 'missing.json') == 2


def test_current_repository_gate_stays_blocked():
    assert main() == 2
