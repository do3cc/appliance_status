"""Responsible for extracting all required information about networks."""
import json
import re
import subprocess


def _prefix_to_netmask(prefix):
    if prefix < 0:
        raise ValueError("Only positive values are supported")
    tuples = []
    mask = hex((2 ** 32 - 1) ^ (2 ** (32 - prefix) - 1))
    for i in (2, 4, 6, 8):
        tuples.append(str(int(mask[i : i + 2], base=16)))
    return ".".join(tuples)


# See Systemd
# https://github.com/systemd/systemd/blob/v197/src/udev/udev-builtin-net_id.c#L20
__physical_re = re.compile("^((en|wl|ww)[osxp]|eth)")


def _is_physical_address_name(name):
    return bool(__physical_re.match(name))


def get_network_information(default_if):
    """
    Return a big tuple of information over the network.

    Take the output from ip --json addr and provide more information:
    - Is it the interface to the internet (default route uses this interface)?
      default=true
    - Is it a physical device and not a virtual? is_physical=true
    - For all addresses, provide a netmask.
    """
    cmd_result = None
    try:
        cmd_result = subprocess.Popen(["ip", "--json", "addr"], stdout=subprocess.PIPE)
        stdout, stderr = cmd_result.communicate(timeout=2)
        if cmd_result.returncode != 0:
            raise Exception(
                "Unhandled error while getting network information: "
                "Error Code: {} Error Msg:{}".format(
                    cmd_result.returncode, cmd_result.stderr
                )
            )
        retval = json.loads(stdout)
        for entry in retval:
            entry["default"] = entry["ifname"] == default_if
            entry["is_physical"] = _is_physical_address_name(entry["ifname"])
            for addr_info_entry in entry["addr_info"]:
                # Only show netmasks for v4
                if addr_info_entry["family"] == "inet":
                    addr_info_entry["netmask"] = _prefix_to_netmask(
                        addr_info_entry["prefixlen"]
                    )
        return retval
    except subprocess.TimeoutExpired:
        if cmd_result is not None:
            cmd_result.kill()
        raise Exception("Timeout while trying to get network information")
    except (json.JSONDecodeError, KeyError):
        raise Exception("Unknown output format of ip --json addr command")


__route_regex = re.compile(r"(?<=via )(?P<GW>[\d.]{7,15}).*(?<=dev )(?P<IF>\S+)")


def get_default_route():
    """
    Provide a default route.

    Provide a dict, giving the following information:
    - What is the gateway address? `via`
    - What is the device over which the traffic goes? `dev`
    """
    cmd_result = None
    try:
        cmd_result = subprocess.Popen(
            ["ip", "-4", "route", "show", "default"], stdout=subprocess.PIPE
        )
        stdout, stderr = cmd_result.communicate(timeout=2)
        stdout = stdout.decode("ascii")
        if cmd_result.returncode != 0:
            raise Exception(
                "Unhandled error while getting network information:"
                " Error Code: {} Error Msg:{}".format(
                    cmd_result.returncode, cmd_result.stderr
                )
            )
    except subprocess.TimeoutExpired:
        if cmd_result is not None:
            cmd_result.kill()
        raise Exception("Timeout while trying to get network information")
    match = __route_regex.search(stdout)
    if match is None:
        raise Exception("Unknown output format of ip route command")
    return match.groupdict()
