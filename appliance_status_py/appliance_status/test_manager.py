"""Responsible for loading test configurations and for running them."""
import concurrent.futures

from appliance_status import test_types


class ATestManager:
    """Implements all responsibilities of the module."""

    def __init__(self, test_config):
        """
        Create an instance of the TestManager.

        Loads the test definition from the provided `test_file`
        """
        self.tests = []
        for entry in test_config:
            self.tests.append(
                getattr(test_types, entry["TestType"])(
                    *entry["args"], description=entry["description"]
                )
            )

    def perform_network_tests(self, log):
        """Perform network tests and return the results."""
        futures = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            for test in self.tests:
                futures.append((test, executor.submit(test.test, log.bind())))
            results = []
            for test, future in futures:
                log.info("Getting future", future=future, test=test)
                results.append(future.result())
            return results
