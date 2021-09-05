"""Test Config manager."""

from appliance_status import config_manager
import pytest
import sys


SCHEMA = dict(
    version=1,
    name="Test",
    schema=[dict(name="demofield", key="demo", type_normalizer="azAZ")],
)


@pytest.mark.parametrize("converter", (int, str))
def test_port_normalizer_good(faker, converter):
    """Validate that a valid port number will be converted to a number."""
    port_number = faker.port_number()

    assert port_number == config_manager._Normalizers().port(converter(port_number))


@pytest.mark.parametrize("data_type", ("binary", "word"))
def test_port_normalizer_bad(faker, data_type):
    """Validate that crazy input creates a Value Error."""
    port_number = getattr(faker, data_type)()

    with pytest.raises(ValueError):
        config_manager._Normalizers().port(port_number)


@pytest.mark.parametrize(
    "port_number",
    (
        0,
        -1,
        sys.maxsize,
        -sys.maxsize,
        sys.maxsize + 1,
        -sys.maxsize - 1,
        float("inf"),
        0.5,
    ),
)
def test_port_normalizer_extreme_values(port_number):
    """Trying extreme values to make sure they also trigger ValueErrors."""
    with pytest.raises(ValueError):
        config_manager._Normalizers().port(port_number)


def test_azAZgood(faker):
    """Try a valid word."""
    word = faker.word()

    assert word == config_manager._Normalizers().azAZ(word)


@pytest.mark.parametrize(
    "value",
    (
        lambda f: f.file_name(),
        lambda f: f.unix_device(),
        lambda f: f.password(),
        lambda f: f.sentence(),
        lambda f: f.credit_card_number(),
        lambda f: f.word() * 1000,
    ),
)
def test_azAZBad(faker, value):
    """
    We deliberately are extremely strict in what we accept.

    Not even a path shall work. This test verifies it.
    """
    word = value(faker)

    with pytest.raises(ValueError):
        assert False is config_manager._Normalizers().azAZ(word), word


def test_azAZEdgeCases():
    """Test what happens with an empty value."""
    word = ""

    assert word == config_manager._Normalizers().azAZ(word)


def test_ConfigOnDiskReadGood(tmp_path):
    """See what happens, when file is not empty and good."""
    config_path = tmp_path / "config.json"
    config_path.write_text("{}")
    cd = config_manager.ConfigOnDisk(str(config_path))

    assert dict() == cd.config


@pytest.mark.parametrize(
    "contents",
    (
        "",
        None,
        "not json",
        r"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*",
    ),
)
def test_ConfigOnDiskReadEmptyOrInvalid(contents, tmp_path):
    """Verify that reading an empty or non existing file return a scaffold xml."""
    config_path = tmp_path / "config.json"
    if contents is not None:
        config_path.write_text(contents)
    cd = config_manager.ConfigOnDisk(str(config_path))

    assert {"schema": [], "version": -1} == cd.config


def test_ConfigManagerMakeOne(tmp_path):
    """For the sake of completeness, we run makeOne."""
    config_path = tmp_path / "config.json"
    config = config_manager.ConfigManager.makeOne(str(config_path), SCHEMA)

    assert SCHEMA == config.getSchemaWithConfig()


@pytest.mark.parametrize(
    "invalid_data",
    (
        dict(),
        dict(
            name="Test",
            schema=[dict(name="demofield", key="demo", type_normalizer="azAZ")],
        ),
        dict(
            version=1,
            schema=[dict(name="demofield", key="demo", type_normalizer="azAZ")],
        ),
        dict(
            version=1,
            name="Test",
        ),
        dict(
            version=1,
            name="Test",
            schema=[],
        ),
        dict(
            version=1,
            name="Test",
            schema=[dict(key="demo", type_normalizer="azAZ")],
        ),
        dict(
            version=1,
            name="Test",
            schema=[dict(name="demofield", type_normalizer="azAZ")],
        ),
        dict(
            version=1,
            name="Test",
            schema=[dict(name="demofield", key="demo")],
        ),
    ),
)
def test_ConfigManagerBadConfig(mocker, invalid_data):
    """Verify that we get an empty config file if the existing schema is invalid."""
    cfg_on_disk = mocker.Mock()
    cfg_on_disk.config = invalid_data
    config = config_manager.ConfigManager(cfg_on_disk, SCHEMA)

    assert SCHEMA == config.getSchemaWithConfig()


def test_ConfigManagerGoodConfig(mocker, faker):
    """Verify that we get the actual config if all is good."""
    cfg_on_disk = mocker.Mock()
    cfg_on_disk.config = dict(
        name="Test",
        version=1,
        schema=[
            dict(
                name="demofield",
                key="demo",
                value=faker.name(),
                type_normalizer="azAZ",
            )
        ],
    )

    config = config_manager.ConfigManager(cfg_on_disk, SCHEMA)

    assert cfg_on_disk.config == config.getSchemaWithConfig()


def test_ConfigManagerVersionMismatch(mocker, faker):
    """Verify that we get an empty config file if version does not match."""
    cfg_on_disk = mocker.Mock()
    cfg_on_disk.config = dict(
        name="Test",
        version=2,
        schema=[
            dict(
                name="demofield",
                key="demo",
                value=faker.name(),
                type_normalizer="azAZ",
            )
        ],
    )

    config = config_manager.ConfigManager(cfg_on_disk, SCHEMA)

    assert SCHEMA == config.getSchemaWithConfig()


def test_ConfigManagerNameInConfigIsIgnored(mocker, faker):
    """
    We provide the name of the schema in the written configuration file for convenience.

    Should it be changed, we ignore that.
    """
    cfg_on_disk = mocker.Mock()
    cfg_on_disk.config = dict(
        name=faker.name(),
        version=1,
        schema=[
            dict(
                name="demofield",
                key="demo",
                type_normalizer="azAZ",
            )
        ],
    )

    config = config_manager.ConfigManager(cfg_on_disk, SCHEMA)

    assert SCHEMA["name"] == config.getSchemaWithConfig()["name"]


def test_ConfigManagerUpdateConfigGood(mocker, faker):
    """Verify that valid configurations get written to disk."""
    cfg_on_disk = mocker.Mock()
    form = dict(demo=faker.word())
    config = config_manager.ConfigManager(cfg_on_disk, SCHEMA)

    config.updateConfig(form)

    assert form["demo"] == cfg_on_disk.config["schema"][0]["value"]


@pytest.mark.parametrize(
    "bad_data",
    (
        {"Demo": "x"},
        {"something else": ""},
        {},
        {"demo": "x", "invalid": "y"},
        {"demo": "a b"},  # No space allowed
    ),
)
def test_ConfigManagerUpdateConfigBad(mocker, bad_data):
    """Verify that invalid configurations do nto get written to disk."""
    cfg_on_disk = mocker.Mock()
    form = bad_data
    config = config_manager.ConfigManager(cfg_on_disk, SCHEMA)

    with pytest.raises((KeyError, ValueError)):
        config.updateConfig(form)
