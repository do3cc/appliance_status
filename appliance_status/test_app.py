"""Super basic tests for app config."""
import werkzeug
from appliance_status import app
import pytest


def test_status(mocker):
    """Only validate that things get called."""
    network = mocker.patch("appliance_status.app.network")
    test_manager = mocker.patch("appliance_status.app.test_manager")
    config_manager = mocker.patch("appliance_status.app.config_manager")
    renderer = mocker.patch("appliance_status.app.render_template")
    renderer.return_value = "success"

    template = app.status()

    assert network.getDefaultRoute.called
    assert test_manager.performNetworkTests.called
    assert config_manager.getSchemaWithConfig.called
    assert renderer.called
    assert template == "success"


def test_leases(mocker):
    """Only validate that things get called."""
    renderer = mocker.patch("appliance_status.app.render_template")
    renderer.return_value = "success"
    leases_manager = mocker.patch("appliance_status.app.leases_manager")

    template = app.leases()

    assert leases_manager.getLeases.called
    assert renderer.called
    assert template == "success"


def test_update_good(mocker):
    """Only validate that things get called."""
    config_manager = mocker.patch("appliance_status.app.config_manager")

    with app.app.test_request_context():
        text, code = app.update()

    assert config_manager.updateConfig.calles
    assert "" == text
    assert 204 == code


@pytest.mark.parametrize("exception", [ValueError, KeyError])
def test_update_fails(mocker, exception):
    """
    Validate Exception handling.

    Catch them, return a 400
    """
    config_manager = mocker.patch("appliance_status.app.config_manager")
    config_manager.updateConfig.side_effect = exception()

    with app.app.test_request_context():
        with pytest.raises(werkzeug.exceptions.BadRequest):
            app.update()
