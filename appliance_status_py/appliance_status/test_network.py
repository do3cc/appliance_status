"""Verify network module functionality."""
import json
import math
import sys

import pytest

from appliance_status import network


def test_prefix_to_net_mask_good():
    """For the sake of completeness."""
    assert "255.128.0.0" == network._prefix_to_netmask(9)


@pytest.mark.parametrize(
    "bad_prefix", (0.5, math.inf, "horse", 100, sys.maxsize)
)
def test_prefix_to_net_mask_bad1(bad_prefix):
    """For the sake of completeness."""
    with pytest.raises(TypeError):
        network._prefix_to_netmask(bad_prefix)


@pytest.mark.parametrize(
    "bad_prefix", (0, -1)
)
def test_prefix_to_net_mask_bad2(bad_prefix):
    """For the sake of completeness."""
    with pytest.raises(ValueError):
        network._prefix_to_netmask(bad_prefix)


@pytest.mark.parametrize(
    "if_name,is_physical",
    (
        ("ens1999", True),
        ("eth0", True),
        ("wwx1", True),
        ("wlo77", True),
        ("xeth0", False),
        ("br123255", False),
        ("randomthings", False),
        ("", False),
    ),
)
def test_is_physical_address(if_name, is_physical):
    """Verify that various strings return the correct result."""
    assert is_physical == network._is_physical_address_name(if_name)


def test_get_network_information_good(mocker):
    """At one time, the output will change. Validate that the error makes sense."""
    subprocess = mocker.patch("appliance_status.network.subprocess")
    subprocess.TimeoutExpired = type("TimeoutExpired", (BaseException,), {})
    stdout = json.dumps(
        [
            dict(ifname="eth0", addr_info=[dict(prefixlen=8, family="inet")]),
            dict(ifname="eth0", addr_info=[dict(prefixlen=128, family="inet6")]),
            dict(ifname="br222", addr_info=[dict(prefixlen=32, family="inet")]),
        ]
    )
    expectation = [
        {
            "addr_info": [{"netmask": "255.0.0.0", "prefixlen": 8, "family": "inet"}],
            "default": True,
            "ifname": "eth0",
            "is_physical": True,
        },
        {
            "addr_info": [{"prefixlen": 128, "family": "inet6"}],
            "default": True,
            "ifname": "eth0",
            "is_physical": True,
        },
        {
            "addr_info": [
                {"netmask": "255.255.255.255", "prefixlen": 32, "family": "inet"}
            ],
            "default": False,
            "ifname": "br222",
            "is_physical": False,
        },
    ]
    subprocess.Popen().returncode = 0
    subprocess.Popen().communicate.return_value = (stdout, None)

    network_information = network.get_network_information("eth0")

    assert expectation == network_information


def test_get_network_information_output_changed2(mocker):
    """At one time, the output will change. Validate that the error makes sense."""
    subprocess = mocker.patch("appliance_status.network.subprocess")
    subprocess.TimeoutExpired = type("TimeoutExpired", (BaseException,), {})
    stdout = "Bad string"
    subprocess.Popen().returncode = 0
    subprocess.Popen().communicate.return_value = (stdout, None)

    with pytest.raises(Exception) as exc:
        network.get_network_information("eth0")

    assert ("Unknown output format of ip --json addr command",) == exc.value.args


def test_get_network_information_output_changed1(mocker):
    """At one time, the output will change. Validate that the error makes sense."""
    subprocess = mocker.patch("appliance_status.network.subprocess")
    subprocess.TimeoutExpired = type("TimeoutExpired", (BaseException,), {})
    stdout = json.dumps(
        [
            dict(iname="eth0", addr_info=[dict(prefixlen=8)]),
            dict(iname="br222", addr_info=[dict(prefixlen=32)]),
        ]
    )
    subprocess.Popen().returncode = 0
    subprocess.Popen().communicate.return_value = (stdout, None)

    with pytest.raises(Exception) as exc:
        network.get_network_information("eth0")

    assert ("Unknown output format of ip --json addr command",) == exc.value.args


def test_get_network_information_return_code_not_null(mocker):
    """Verify that we fail hard on bad return code of ip command."""
    subprocess = mocker.patch("appliance_status.network.subprocess")
    subprocess.Popen().returncode = 1
    subprocess.Popen().communicate.return_value = (None, None)

    with pytest.raises(Exception):
        network.get_network_information("eth0")


def test_get_network_information_fail_if_too_slow(mocker):
    """Verify that we fail hard on bad return code of ip command."""
    subprocess = mocker.patch("appliance_status.network.subprocess")
    subprocess.TimeoutExpired = type("TimeoutExpired", (BaseException,), {})
    subprocess.Popen().communicate.side_effect = subprocess.TimeoutExpired()

    with pytest.raises(Exception):
        network.get_network_information("eth0")

    assert 2 == subprocess.Popen().communicate.call_args.kwargs["timeout"]


def test_get_default_route_good(mocker, faker):
    """Verify that we get a default route that makes sense."""
    subprocess = mocker.patch("appliance_status.network.subprocess")
    subprocess.TimeoutExpired = type("TimeoutExpired", (BaseException,), {})
    gw = faker.ipv4_private()
    stdout = "default via {} dev eth0".format(gw).encode("ascii")
    expectation = {"GW": gw, "IF": "eth0"}
    subprocess.Popen().returncode = 0
    subprocess.Popen().communicate.return_value = (stdout, None)

    route_info = network.get_default_route()

    assert expectation == route_info


def test_get_default_route_cant_parse_answer(mocker):
    """At one time, the output will change. Validate that the error makes sense."""
    subprocess = mocker.patch("appliance_status.network.subprocess")
    subprocess.TimeoutExpired = type("TimeoutExpired", (BaseException,), {})
    stdout = b"Oh no, the format changed, but in what way?"
    subprocess.Popen().returncode = 0
    subprocess.Popen().communicate.return_value = (stdout, None)

    with pytest.raises(Exception) as exc:
        network.get_default_route()

    assert ("Unknown output format of ip route command",) == exc.value.args


def test_get_default_route_return_code_not_null(mocker):
    """Verify that we fail hard on bad return code of ip command."""
    subprocess = mocker.patch("appliance_status.network.subprocess")
    subprocess.Popen().returncode = 1
    subprocess.Popen().communicate.return_value = (None, None)

    with pytest.raises(Exception):
        network.get_default_route()


def test_get_default_route_fail_if_too_slow(mocker):
    """Verify that we fail hard on bad return code of ip command."""
    subprocess = mocker.patch("appliance_status.network.subprocess")
    subprocess.TimeoutExpired = type("TimeoutExpired", (BaseException,), {})
    subprocess.Popen().communicate.side_effect = subprocess.TimeoutExpired()

    with pytest.raises(Exception):
        network.get_default_route()

    assert 2 == subprocess.Popen().communicate.call_args.kwargs["timeout"]
