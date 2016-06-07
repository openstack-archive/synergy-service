import os
import os.path
import requests
import sys

from argparse import ArgumentParser
from pkg_resources import iter_entry_points
from synergy.client import keystone_v3

__author__ = "Lisa Zangrando"
__email__ = "lisa.zangrando[AT]pd.infn.it"
__copyright__ = """Copyright (c) 2015 INFN - INDIGO-DataCloud
All Rights Reserved

Licensed under the Apache License, Version 2.0;
you may not use this file except in compliance with the
License. You may obtain a copy of the License at:

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
either express or implied.
See the License for the specific language governing
permissions and limitations under the License."""

COMMANDS_ENTRY_POINT = "synergy.commands"  # used to discover Synergy commands


def main():
    try:
        parser = ArgumentParser(prog="synergy",
                                epilog="Command-line interface to the"
                                       " OpenStack Synergy API.")

        # Global arguments
        parser.add_argument("--version", action="version", version="v1.0")

        parser.add_argument("--debug",
                            default=False,
                            action="store_true",
                            help="print debugging output")

        parser.add_argument("--os-username",
                            metavar="<auth-user-name>",
                            default=os.environ.get("OS_USERNAME"),
                            help="defaults to env[OS_USERNAME]")

        parser.add_argument("--os-password",
                            metavar="<auth-password>",
                            default=os.environ.get("OS_PASSWORD"),
                            help="defaults to env[OS_PASSWORD]")

        parser.add_argument("--os-project-name",
                            metavar="<auth-project-name>",
                            default=os.environ.get("OS_PROJECT_NAME"),
                            help="defaults to env[OS_PROJECT_NAME]")

        parser.add_argument("--os-project-id",
                            metavar="<auth-project-id>",
                            default=os.environ.get("OS_PROJECT_ID"),
                            help="defaults to env[OS_PROJECT_ID]")

        parser.add_argument("--os-auth-token",
                            metavar="<auth-token>",
                            default=os.environ.get("OS_AUTH_TOKEN", None),
                            help="defaults to env[OS_AUTH_TOKEN]")

        parser.add_argument('--os-auth-token-cache',
                            default=os.environ.get("OS_AUTH_TOKEN_CACHE",
                                                   False),
                            action='store_true',
                            help="Use the auth token cache. Defaults to False "
                                 "if env[OS_AUTH_TOKEN_CACHE] is not set")

        parser.add_argument("--os-auth-url",
                            metavar="<auth-url>",
                            default=os.environ.get("OS_AUTH_URL"),
                            help="defaults to env[OS_AUTH_URL]")

        parser.add_argument("--os-auth-system",
                            metavar="<auth-system>",
                            default=os.environ.get("OS_AUTH_SYSTEM"),
                            help="defaults to env[OS_AUTH_SYSTEM]")

        parser.add_argument("--bypass-url",
                            metavar="<bypass-url>",
                            dest="bypass_url",
                            help="use this API endpoint instead of the "
                                 "Service Catalog")

        parser.add_argument("--os-cacert",
                            metavar="<ca-certificate>",
                            default=os.environ.get("OS_CACERT", None),
                            help="Specify a CA bundle file to use in verifying"
                                 " a TLS (https) server certificate. Defaults "
                                 "to env[OS_CACERT]")
        """
        parser.add_argument("--insecure",
                            default=os.environ.get("INSECURE", False),
                            action="store_true",
                            help="explicitly allow Synergy's client to perform"
                                 " \"insecure\" SSL (https) requests. The "
                                 "server's certificate will not be verified "
                                 "against any certificate authorities. This "
                                 "option should be used with caution.")
        """

        subparser = parser.add_subparsers(help="commands", dest="command_name")
        commands = {}

        for entry in iter_entry_points(COMMANDS_ENTRY_POINT):
            command_class = entry.load()
            command = command_class()
            commands[entry.name] = command

        for command_name in sorted(commands.keys()):
            commands[command_name].configureParser(subparser)

        args = parser.parse_args(sys.argv[1:])

        os_username = args.os_username
        os_password = args.os_password
        os_project_name = args.os_project_name
        os_auth_token = args.os_auth_token
        os_auth_token_cache = args.os_auth_token_cache
        os_auth_url = args.os_auth_url
        bypass_url = args.bypass_url
        command_name = args.command_name

        if not os_username:
            raise Exception("'os-username' not defined!")

        if not os_password:
            raise Exception("'os-password' not defined!")

        if not os_project_name:
            raise Exception("'os-project-name' not defined!")

        if not os_auth_url:
            raise Exception("'os-auth-url' not defined!")

        client = keystone_v3.KeystoneClient(auth_url=os_auth_url,
                                            username=os_username,
                                            password=os_password,
                                            project_name=os_project_name)

        token = None

        if os_auth_token:
            token = os_auth_token
        elif os_auth_token_cache:
            token = keystone_v3.Token.load(".auth_token")

            if token is None or token.isExpired():
                client.authenticate()
                token = client.getToken()
                token.save(".auth_token")
        else:
            client.authenticate()
            token = client.getToken()

        synergy_url = None
        if bypass_url:
            synergy_url = bypass_url
        else:
            synergy_service = client.getService(name="synergy")

            synergy_endpoint = client.getEndpoint(
                service_id=synergy_service["id"])

            synergy_url = synergy_endpoint["url"]

        if command_name not in commands:
            print("command %r not found!" % command_name)

        commands[command_name].sendRequest(synergy_url, args)
        commands[command_name].log()
    except KeyboardInterrupt as e:
        print("Shutting down synergyclient")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print("HTTPError: %s" % e.response._content)
        sys.exit(1)
    except Exception as e:
        print("ERROR: %s" % e)
        sys.exit(1)


if __name__ == "__main__":
    main()
