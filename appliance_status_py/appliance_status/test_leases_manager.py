"""Verify functionality of leases_manager module."""
from appliance_status import leases_manager


def test_leases_manager_good(tmp_path, faker):
    """Verify that LeasesManager returns file contents."""
    file_contents = [faker.paragraph() for _ in range(5)]
    for file_content in file_contents:
        (tmp_path / faker.file_name()).write_text(file_content)
    leases_mgr = leases_manager.LeasesManager(str(tmp_path))

    assert set(file_contents) == set(leases_mgr.get_leases())


def test_leases_manager_no_sub_directories(tmp_path, faker):
    """Verify that we don't traverse subdirectories."""
    good = faker.paragraph()
    bad = faker.paragraph()
    (tmp_path / faker.file_name()).write_text(good)
    bad_path = tmp_path / faker.word()
    bad_path.mkdir()
    (bad_path / faker.file_name()).write_text(bad)
    leases_mgr = leases_manager.LeasesManager(str(tmp_path))

    assert {good} == set(leases_mgr.get_leases())


def test_leases_manager_empty_dir(tmp_path):
    """Verify that an empty list is returned, if the directory is empty."""
    leases_mgr = leases_manager.LeasesManager(str(tmp_path))

    assert [] == leases_mgr.get_leases()


def test_leases_manager_non_existing_dir(tmp_path, faker):
    """Verify that an empty list is returned, if the directory does not exist."""
    leases_mgr = leases_manager.LeasesManager(str(tmp_path / faker.name()))

    assert [] == leases_mgr.get_leases()
