"""Verify network module functionality."""
import json
import math
import sys

import pytest

from appliance_status import network


def test_prefixToNetMaskGood():
    """For the sake of completeness."""
    assert "255.128.0.0" == network._prefixToNetmask(9)


@pytest.mark.parametrize(
    "bad_prefix", (0, -1, 0.5, math.inf, "horse", 100, sys.maxsize)
)
def test_prefixToNetMaskBad(bad_prefix):
    """For the sake of completeness."""
    with pytest.raises((ValueError, TypeError)):
        network._prefixToNetmask(bad_prefix)


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
def test_isPhysicalAddress(if_name, is_physical):
    """Verify that various strings return the correct result."""
    assert is_physical == network._isPhysicalAddressName(if_name)


def test_getNetworkInformationGood(mocker):
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

    network_information = network.getNetworkInformation("eth0")

    assert expectation == network_information


def test_getNetworkInformationOutputChanged2(mocker):
    """At one time, the output will change. Validate that the error makes sense."""
    subprocess = mocker.patch("appliance_status.network.subprocess")
    subprocess.TimeoutExpired = type("TimeoutExpired", (BaseException,), {})
    stdout = "Bad string"
    subprocess.Popen().returncode = 0
    subprocess.Popen().communicate.return_value = (stdout, None)

    with pytest.raises(Exception) as exc:
        network.getNetworkInformation("eth0")

    assert ("Unknown output format of ip --json addr command",) == exc.value.args


def test_getNetworkInformationOutputChanged1(mocker):
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
        network.getNetworkInformation("eth0")

    assert ("Unknown output format of ip --json addr command",) == exc.value.args


def test_getNetworkInformationReturnCodeNotNull(mocker):
    """Verify that we fail hard on bad return code of ip command."""
    subprocess = mocker.patch("appliance_status.network.subprocess")
    subprocess.Popen().returncode = 1
    subprocess.Popen().communicate.return_value = (None, None)

    with pytest.raises(Exception):
        network.getNetworkInformation("eth0")


def test_getNetworkInformationFailIfTooSlow(mocker):
    """Verify that we fail hard on bad return code of ip command."""
    subprocess = mocker.patch("appliance_status.network.subprocess")
    subprocess.TimeoutExpired = type("TimeoutExpired", (BaseException,), {})
    subprocess.Popen().communicate.side_effect = subprocess.TimeoutExpired()

    with pytest.raises(Exception):
        network.getNetworkInformation("eth0")

    assert 2 == subprocess.Popen().communicate.call_args.kwargs["timeout"]


def test_getDefaultRouteGood(mocker, faker):
    """Verify that we get a default route that makes sense."""
    subprocess = mocker.patch("appliance_status.network.subprocess")
    subprocess.TimeoutExpired = type("TimeoutExpired", (BaseException,), {})
    gw = faker.ipv4_private()
    stdout = "default via {} dev eth0".format(gw).encode("ascii")
    expectation = {"GW": gw, "IF": "eth0"}
    subprocess.Popen().returncode = 0
    subprocess.Popen().communicate.return_value = (stdout, None)

    route_info = network.getDefaultRoute()

    assert expectation == route_info


def test_getDefaultRouteCantParseAnswer(mocker):
    """At one time, the output will change. Validate that the error makes sense."""
    subprocess = mocker.patch("appliance_status.network.subprocess")
    subprocess.TimeoutExpired = type("TimeoutExpired", (BaseException,), {})
    stdout = b"Oh no, the format changed, but in what way?"
    subprocess.Popen().returncode = 0
    subprocess.Popen().communicate.return_value = (stdout, None)

    with pytest.raises(Exception) as exc:
        network.getDefaultRoute()

    assert ("Unknown output format of ip route command",) == exc.value.args


def test_getDefaultRouteReturnCodeNotNull(mocker):
    """Verify that we fail hard on bad return code of ip command."""
    subprocess = mocker.patch("appliance_status.network.subprocess")
    subprocess.Popen().returncode = 1
    subprocess.Popen().communicate.return_value = (None, None)

    with pytest.raises(Exception):
        network.getDefaultRoute()


def test_getDefaultRouteFailIfTooSlow(mocker):
    """Verify that we fail hard on bad return code of ip command."""
    subprocess = mocker.patch("appliance_status.network.subprocess")
    subprocess.TimeoutExpired = type("TimeoutExpired", (BaseException,), {})
    subprocess.Popen().communicate.side_effect = subprocess.TimeoutExpired()

    with pytest.raises(Exception):
        network.getDefaultRoute()

    assert 2 == subprocess.Popen().communicate.call_args.kwargs["timeout"]
