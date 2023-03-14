# Status Page

This project allows a person to debug basic issues of a a software appliance and basic configuration of the same appliance.

The web application will show you the following information:

- Network interfaces
- Default route (Make sure your container is running with host mode network).
- If predefined network tests pass.
- A configuration file with a configurable schema.

The web application will allow you to edit the following information:

- The configuration file.

The idea is to deploy this application as a docker container, and to configure it by linking a few configuration files.

## Configuration

### Network tests

Link a provided test file to `/usr/src/app/tests.json`. It must contain a list of tests like that:

```json
[
  {
    "TestType": "HTTPTest",
    "args": ["https://example.com"]
  }
]
```

It supports the following test types:

| Test type | Description                                                                                       | arguments                     |
| --------- | ------------------------------------------------------------------------------------------------- | ----------------------------- |
| MQTT Test | Tries to connect to an encrypted MQTT server will pass if it connects                             | IP, PORT                      |
| TCP Test  | Tries to connect to a tcp port and sends input data. checks the answer against a a provided regex | HOST, PORT, INPUT_DATA, REGEX |
| SSL Test  | Tries to connect, passes if the ssl version is TLSv1.2 or TLSv1.3                                 | HOST, PORT                    |
| HTTP Test | tries to connect, validates that status code is either 200 or 401                                 | URL                           |
| NTP Test  | tries to connect, asks for a time in version 3 format, validates the version response             | HOST                          |

Some tests will try to verify the certificate and issue a warning, if the cert cannot be validated. There is currently no option to enforce a valid cert.

### config file

Link a provided schema file to `/usr/src/app/schema.json`. It must contain a valid schema.
Link a local file to `/usr/src/app/config.json` in the docker container. The application will write new configurations to this file. It will contain schema information and provided values.
Warning, if the config file does not exist, the -v parameter of docker will create a directory with that name!
The value will be under the key _value_.
See the provided _schema.json_ for an example.

Your schema must contain a _version_ and a _name_. The version will be used to validate that existing config parameters can be shown. If the version does not match, existing configuration values are ignored.
The name will be shown in the app.
Each schema field requires _name_, _key_, _type_normalizer_. While name and key is self explanatory, the type normalizer must match a normalizer method provided with the project.

Currently there are only _port_ and _az_az_upper_. Port validates that the port number is valid, azAZ validates that the values are only ascii alphabet letters.
Yes, the normalizer validates and normalizes.

### Leases

It can be very beneficial for complex problems to see the dhcp configuration one got. systemd exposes this in a undocumented format.
If you mount this directory readonly, a special page will show these leases.

## Limitations

### Error handling

Errors will be caught, but currently the application does not provide information about what failed.

## Example

Get the `config.json` and the `tests.json` from this repository and put them into a directory. create an empty `config.json`.
If you won't create an empty config.json, Docker will create a directory and
the application will fail!
Finally execute on a linux system:

```shell
docker run -it --rm \
 -v ${PWD}/schema.json:/usr/src/app/schema.json:ro \
 -v ${PWD}/tests.json:/usr/src/app/tests.json:ro \
 -v ${PWD}/config.json:/usr/src/app/config.json \
 -v /run/systemd/netif/leases/:/usr/src/app/leases:ro \
 --network="host" \
 appliance_status
```

If you have the package installed locally, you can all execute `make run`

