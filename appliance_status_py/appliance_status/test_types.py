"""Provide all test implementations."""
from abc import abstractmethod
from functools import partial
from time import ctime
from time import sleep
from typing import Protocol
import attr
import ntplib
import paho.mqtt.client as mqtt
import re
import requests
import socket
import ssl
import structlog


@attr.s
class ATestResult:
    """Represent the result of a test."""

    test_type = attr.ib()
    passed = attr.ib()
    address = attr.ib()
    status_code = attr.ib()
    reason = attr.ib()
    description = attr.ib()


@attr.s
class ErrorResult:
    """Represent the result of a test."""

    test_type = attr.ib()
    passed = False
    address = attr.ib()
    status_code = attr.ib()
    reason = attr.ib()
    description = attr.ib()


def _makeTimeoutErrorResult(test_type, address, description):
    return ErrorResult(
        test_type,
        address,
        status_code=0,
        reason="Network timeout",
        description=description,
    )


def _makeGenericErrorResult(test_type, address, description, exc):
    return ErrorResult(
        test_type,
        address=address,
        status_code=500,
        reason=repr(exc),
        description=description,
    )


def _handle_socket_errors(func):
    def inner(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except ssl.SSLCertVerificationError as exc:
            return _makeGenericErrorResult(
                self.test_type, self._address, self.description, exc
            )
        except socket.gaierror as exc:
            return _makeGenericErrorResult(
                self.test_type, self._address, self.description, exc
            )
        except socket.timeout:
            return _makeTimeoutErrorResult(
                self.test_type, self._address, self.description
            )

    return inner


class ATestProtocol(Protocol):
    """Responsible for configuring a test object, and performing tests."""

    test_type: str = "Test"

    @abstractmethod
    def test(self, log: structlog.stdlib.BoundLogger) -> ATestResult:
        """Perform the test and return the result as ATestResult."""
        ...


@attr.s
class MQTTTest(ATestProtocol):
    """
    MQTT Test.

    Checks that it can connect to the MQTT endpoint
    """

    host = attr.ib()
    port = attr.ib()
    description = attr.ib()
    connected = False
    test_type = "MQTT Test"

    @property
    def _address(self):
        return "{}:{}".format(self.host, self.port)

    def _on_connect(self, log, client, userdata, flags, rc):
        log = log.bind(client=client, userdata=userdata, flags=flags, rc=rc)
        log.info("Got connected")
        self.connected = True

    def _on_message(self, log, client, userdata, msg):
        log = log.bind(client=client, userdata=userdata, msg=msg)
        log.info("Got a message")

    @_handle_socket_errors
    def test(self, log):
        """See Test.test."""
        log = log.bind(address=self._address, test_type=self.test_type)
        client = mqtt.Client()
        client.on_connect = partial(self._on_connect, log)
        client.on_message = partial(self._on_message, log)
        client.tls_set()

        log.info("Connecting")
        client.connect(self.host, self.port, 1)
        wait_step = 0.01
        for _i in range(int(1.0 / wait_step)):
            if self.connected:
                break
            sleep(wait_step)
            client.loop(timeout=1)
        client.disconnect()
        log.info("looped through")
        if self.connected:
            return ATestResult(
                test_type=self.test_type,
                address=self._address,
                status_code=200,
                reason="OK",
                passed=True,
                description=self.description,
            )
        else:
            return _makeTimeoutErrorResult(
                self.test_type, self._address, self.description
            )


@attr.s
class TCPTest:
    """
    TCP Test.

    Tries to connect to tcp socket, sends some data and
    validates the result against a provided regex
    """

    host = attr.ib()
    port = attr.ib()
    input_data = attr.ib()
    output_re_str = attr.ib()
    description = attr.ib()
    test_type = "TCP Test"

    @property
    def _address(self):
        return "{}:{}".format(self.host, self.port)

    @_handle_socket_errors
    def test(self, log):
        """See Test.test."""
        output_re = re.compile(self.output_re_str)
        with socket.create_connection((self.host, self.port), timeout=1) as sock:
            sock.sendall(self.input_data.encode("ascii"))
            response = sock.recv(4096)
            passed = bool(output_re.match(response.decode("ascii")))
            log.info("TCP Response: {}".format(response))
            return ATestResult(
                test_type=self.test_type,
                address=self._address,
                status_code=200 if passed else 500,
                reason="OK" if passed else "OUTPUT DOES NOT MATCH: {}".format(response),
                passed=passed,
                description=self.description,
            )


@attr.s
class SSLTest(ATestProtocol):
    """
    SSL Test.

    Tries to connect and checks that the ssl tunnel is version TLSv1.2 and TLSv1.3
    """

    host = attr.ib()
    port = attr.ib()
    description = attr.ib()
    test_type = "SSL Test"

    @property
    def _address(self):
        return "{}:{}".format(self.host, self.port)

    def _test_no_verify(self, log):
        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        with socket.create_connection((self.host, self.port), timeout=1) as sock:
            with context.wrap_socket(sock, server_hostname=self.host) as ssock:
                ssl_version = ssock.version()
                log = log.bind(ssl_version=ssl_version)
                return self._evaluateSslVersionAndReturnResult(
                    ssl_version, verified=False
                )

    @_handle_socket_errors
    def test(self, log):
        """See Test.test."""
        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        try:
            with socket.create_connection((self.host, self.port), timeout=1) as sock:
                with context.wrap_socket(sock, server_hostname=self.host) as ssock:
                    ssl_version = ssock.version()
                    log = log.bind(ssl_version=ssl_version)
                    return self._evaluateSslVersionAndReturnResult(
                        ssl_version, verified=True
                    )
        except ssl.SSLCertVerificationError:
            return self._test_no_verify(log)

    def _evaluateSslVersionAndReturnResult(self, data, verified):
        if data in ["TLSv1.3", "TLSv1.2"]:
            reason = "OK" if verified else "OK but no SSL Verification possible"

            return ATestResult(
                test_type=self.test_type,
                address=self._address,
                status_code=200,
                reason=reason,
                passed=True,
                description=self.description,
            )
        else:
            return ATestResult(
                test_type=self.test_type,
                address=self._address,
                status_code=500,
                reason="We do not trust this SSL Version: {}".format(data),
                passed=False,
                description=self.description,
            )


@attr.s
class HTTPTest(ATestProtocol):
    """
    HTTP Test.

    Tries to connect to the URL and expects either 200 or 401
    """

    url = attr.ib()
    description = attr.ib()
    test_type = "HTTP Test"

    def _test_no_verify(self, log):
        return self._test(log, BROKEN_SSL=True)

    def test(self, log):
        """See Test.test."""
        return self._test(log, BROKEN_SSL=False)

    def _test(self, log, BROKEN_SSL):
        try:
            req = requests.request("HEAD", self.url, timeout=1, verify=not BROKEN_SSL)
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
            return _makeTimeoutErrorResult(self.test_type, self.url, self.description)
        except requests.exceptions.SSLError:
            log.info("Failed to validate cert, no trying without validation")
            return self._test_no_verify(log)
        except requests.exceptions.ConnectionError as exc:
            return _makeGenericErrorResult(
                self.test_type, self.url, self.description, exc
            )
        except Exception:
            log.exception("Something went wrong and will bubble up now")
            raise

        reason = (
            req.reason + " but no SSL Verification possible"
            if BROKEN_SSL
            else req.reason
        )
        return ATestResult(
            test_type=self.test_type,
            address=self.url,
            status_code=req.status_code,
            reason=reason,
            passed=req.status_code in [200, 401],
            description=self.description,
        )


@attr.s
class NTPTest(ATestProtocol):
    """
    NTP Test.

    Trying to get the time and checks the version of the answer
    """

    host = attr.ib()
    description = attr.ib()
    test_type = "NTP Test"

    @property
    def _address(self):
        return "{}:123".format(self.host)

    @_handle_socket_errors
    def test(self, log):
        """See Test.test."""
        client = ntplib.NTPClient()
        try:
            response = client.request(self.host, version=3)
        except ntplib.NTPException as exc:
            return _makeGenericErrorResult(
                self.test_type, self._address, self.description, exc
            )
        return ATestResult(
            test_type=self.test_type,
            address=self._address,
            status_code=200,
            reason=ctime(response.tx_time),
            passed=response.version == 3,
            description=self.description,
        )
