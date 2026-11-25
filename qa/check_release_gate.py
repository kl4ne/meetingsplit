"""Fail closed if any mandatory release gate is missing or unapproved."""
import json
from pathlib import Path

MANDATORY = frozenset({
    'asus_gpu_real_speech',
    'frozen_app_gpu_and_ollama_on_asus',
    'long_synthetic_workload',
    'cpu_split_transcription_regression',
    'ollama_real_generation_and_failure_paths',
    'installer_clean_upgrade_cancel_uninstall',
    'five_screens_en_es_large_typography',
    'third_party_license_and_security_review',
    'resume_and_isolated_worker_acceptance',
    'installed_component_integrity_and_resume',
})


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate release gate key: ' + key)
        result[key] = value
    return result


def blockers(gate):
    if not isinstance(gate, dict):
        return ['Invalid release gate']
    required = gate.get('required')
    if not isinstance(required, dict):
        return ['Invalid or missing required gate dictionary']
    problems = []
    if gate.get('release_allowed') is not True:
        problems.append('Explicit release authorization missing')
    problems.extend('Missing mandatory gate: ' + key for key in sorted(MANDATORY - required.keys()))
    problems.extend('Not approved: ' + key for key, ok in sorted(required.items()) if ok is not True)
    return problems


def main(path=None):
    path = Path(path) if path is not None else Path(__file__).parent / 'release_gate.json'
    try:
        gate = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique_keys)
        problems = blockers(gate)
    except (OSError, ValueError, TypeError) as exc:
        problems = ['Cannot validate release gate: ' + str(exc)]
    if problems:
        print('RELEASE BLOCKED:\n' + '\n'.join(problems))
        return 2
    # Flags alone are not independent evidence of qualified approval.
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
