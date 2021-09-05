"""
Flask application config.

Responsible for configuring the web application and routing
"""

import json
import os

import structlog
from flask import Flask, abort, render_template, request
from appliance_status import network
from appliance_status.config_manager import ConfigManager
from appliance_status.test_manager import ATestManager
from appliance_status.leases_manager import LeasesManager

app = Flask(__name__)
app.config.from_file(os.path.abspath("./app_config.json"), load=json.load)

config_manager = ConfigManager.makeOne(
    os.path.abspath(app.config["CONFIG_FILE_OUT"]),
    json.load(open(os.path.abspath(app.config["SCHEMA"]))),
)
test_manager = ATestManager(json.load(open(os.path.abspath(app.config["TESTS"]))))
leases_manager = LeasesManager(os.path.abspath(app.config["LEASES"]))


@app.route("/")
def status():
    """Show status information, test results and the form to edit configuration."""
    log = structlog.get_logger()
    default_route = network.getDefaultRoute()
    network_info = network.getNetworkInformation(default_if=default_route["IF"])
    network_tests = test_manager.performNetworkTests(log)
    form_schema = config_manager.getSchemaWithConfig()
    return render_template(
        "status.j2",
        network_info=network_info,
        default_route=default_route,
        network_tests=network_tests,
        form_schema=form_schema,
    )


@app.route("/leases")
def leases():
    """
    Intended for showing information about dhcp leases.

    Since this application is inteded to be run within docker, what gets
    shown depends fully on the directories mounted into the docker container!
    """
    leases = leases_manager.getLeases()

    return render_template("leases.j2", leases=leases)


@app.route("/update", methods=["POST"])
def update():
    """Perform the actual update of the configuration file."""
    log = structlog.get_logger()
    try:
        config_manager.updateConfig(request.form)
    except ValueError:
        log.exception("Value Error while saving configuration")
        abort(
            400,
            "The provided data is invalid",
        )
    except KeyError:
        log.exception("Value Error while saving configuration")
        abort(
            400,
            "You need to provide a value for all keys",
        )
    return "", 204
