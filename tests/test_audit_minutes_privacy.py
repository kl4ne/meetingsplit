import json
import pytest
from engine.summarize import validate_report_references
from desktop.storage import validate_local_folder, UnsafeStorage


def test_minutes_reference_must_exist_in_source():
    source='[00:00:01] Ana agreed to send the draft.'
    validate_report_references('# Minutes\nAna [00:00:01]',source)
    with pytest.raises(RuntimeError,match='references'):
        validate_report_references('# Minutes\nAna [00:01:01]',source)
    with pytest.raises(RuntimeError,match='references'):
        validate_report_references('# Minutes\nNo evidence',source)


def test_custom_dropbox_sync_folder_rejected(tmp_path,monkeypatch):
    target=tmp_path/'CustomSync'
    target.mkdir()
    appdata=tmp_path/'settings'
    (appdata/'Dropbox').mkdir(parents=True)
    (appdata/'Dropbox'/'info.json').write_text(json.dumps({'personal':{'path':str(target)}}))
    monkeypatch.setenv('APPDATA',str(appdata))
    with pytest.raises(UnsafeStorage,match='nube'):
        validate_local_folder(target)
