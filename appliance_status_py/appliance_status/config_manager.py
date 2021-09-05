"""
Responsible for configuration.

Retrieving configuration
Validating new configuration
Updating configuration
"""
import json
import string
from copy import deepcopy
from typing import Dict, Union, List
import attr


class _Normalizers:
    """Normalize values, also fail with ValueError if not normalizable."""

    def port(self, value):
        """
        Convert the value to a number, validate that the port is legal.

        Legal ports are between 1 and 65535.
        """
        try:
            value = int(value)
        except OverflowError:
            raise ValueError()
        if value < 1:
            raise ValueError("Invalid Port Value, too small")
        if value > 65535:
            raise ValueError("Invalid port value, too large")
        return value

    def azAZ(self, value):
        """
        Convert a value to a string containing only the letters a-z and A-Z.

        Max allowed size 1000 chars.
        """
        value = str(value)
        if len(value) > 1000:
            raise ValueError("Too large")
        for key in value:
            if key not in string.ascii_letters:
                raise ValueError("Charactor not ascii letter")
        return value


@attr.s
class ConfigOnDisk:
    """
    Represent the configuration on disk.

    Initiated with a full path to the configuration.
    The `config` attribute represents the file contents as json.
    When the file does not exist or has invalid json, return a minimum valid
    object.
    """

    config_file: str = attr.ib(validator=attr.validators.matches_re(r"^/.*"))

    @property
    def config(self):
        """JSON represention of the contents of the config file."""
        try:
            return json.load(open(self.config_file))
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            return {"schema": [], "version": -1}

    @config.setter
    def config(self, value):
        json.dump(value, open(self.config_file, "w"))


@attr.s(frozen=True)
class ConfigManager:
    """Configmanager implements the responsability of the module."""

    config_on_disk: ConfigOnDisk = attr.ib()
    form_schema: Dict[str, Union[str, int, List[Dict[str, str]]]] = attr.ib()
    normalizers = _Normalizers()

    @classmethod
    def makeOne(cls, config_file, form_schema):
        """
        Create a Config Manager.

        `config_on_disk` must be an absolute path to the configuration.
        If it doesn't exist, it will be created, on demand.
        The directory must exit.
        `schema` must be the schema definition as json. The syntax is describeb
        in the documentation
        """
        config_on_disk = ConfigOnDisk(config_file)
        return cls(config_on_disk, form_schema)

    def getSchemaWithConfig(self):
        """Return the schema, together with already stored values, if they exist."""
        extended_schema = deepcopy(self.form_schema)
        try:
            written_config = self.config_on_disk.config
            written_values = {}
            for written_schema_field in written_config["schema"]:
                written_values[written_schema_field["key"]] = written_schema_field[
                    "value"
                ]

            if written_config["version"] == self.form_schema["version"]:
                for schema_field in extended_schema["schema"]:
                    schema_field["value"] = written_values[schema_field["key"]]
        except KeyError:
            pass
        return extended_schema

    def updateConfig(self, form):
        """Update the configuration. Form must be a flask.request.form instance."""
        new_data = []
        written_fields = set()
        for schema_field in self.form_schema["schema"]:
            written_fields.add(schema_field["key"])
            new_data.append(
                {
                    "key": schema_field["key"],
                    "value": getattr(self.normalizers, schema_field["type_normalizer"])(
                        form[schema_field["key"]]
                    ),
                }
            )
        if set(form.keys()) - set(written_fields):
            raise ValueError("Form contained unknown fields")
        self.config_on_disk.config = {
            "version": self.form_schema["version"],
            "schema": new_data,
        }
