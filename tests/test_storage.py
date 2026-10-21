from desktop.storage import classify_storage, configure_data_root


def test_internal_disks_are_allowed():
    assert classify_storage(3,'NVMe')[0]
    assert classify_storage(3,'SATA')[0]
    assert classify_storage(3,'',is_system_drive=True)[0]


def test_usb_rejected_even_when_reported_fixed():
    assert not classify_storage(3,'USB')[0]
    assert not classify_storage(2,'USB')[0]
    assert not classify_storage(4,'NVMe')[0]  # network


def test_unknown_non_system_disk_rejected():
    assert not classify_storage(3,'Unknown')[0]
    assert not classify_storage(3,'')[0]


def test_selected_directory_creates_local_meetingsplit_folder(tmp_path):
    output=configure_data_root(tmp_path)
    assert output == tmp_path/'MeetingSplit'
    assert output.is_dir()
    assert configure_data_root(output)==output
