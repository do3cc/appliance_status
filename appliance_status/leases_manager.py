"""Responsible for accessing leases."""
from typing import List
import os
import attr


@attr.s(frozen=True)
class LeasesManager:
    """
    Implement responsibility of the module.

    To instanciate a manager, provide an absolute path to the directory
    that contain lease information
    """

    leases_directory: str = attr.ib(validator=attr.validators.matches_re(r"^/.*"))

    def getLeases(self) -> List[str]:
        """
        Return leases as a list.

        provide an absolute path to the `leases_directory`
        """
        leases = []
        try:
            for filename in os.listdir(self.leases_directory):
                file_with_path = os.path.join(self.leases_directory, filename)
                if os.path.isfile(file_with_path):
                    leases.append(open(file_with_path).read())
        except FileNotFoundError:
            pass
        return leases
