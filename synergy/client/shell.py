import os
import os.path
import sys

from argparse import ArgumentParser
from pkg_resources import iter_entry_points
from requests.exceptions import ConnectionError
from requests.exceptions import HTTPError
from requests.exceptions import RequestException
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
        parser.add_argument("--version", action="version", version="v1.1")

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

        parser.add_argument("--os-user-domain-id",
                            metavar="<auth-user-domain-id>",
                            default=os.environ.get("OS_USER_DOMAIN_ID"),
                            help="defaults to env[OS_USER_DOMAIN_ID]")

        parser.add_argument("--os-user-domain-name",
                            metavar="<auth-user-domain-name>",
                            default=os.environ.get("OS_USER_DOMAIN_NAME"),
                            help="defaults to env[OS_USER_DOMAIN_NAME]")

        parser.add_argument("--os-project-name",
                            metavar="<auth-project-name>",
                            default=os.environ.get("OS_PROJECT_NAME"),
                            help="defaults to env[OS_PROJECT_NAME]")

        parser.add_argument("--os-project-id",
                            metavar="<auth-project-id>",
                            default=os.environ.get("OS_PROJECT_ID"),
                            help="defaults to env[OS_PROJECT_ID]")

        parser.add_argument("--os-project-domain-id",
                            metavar="<auth-project-domain-id>",
                            default=os.environ.get("OS_PROJECT_DOMAIN_ID"),
                            help="defaults to env[OS_PROJECT_DOMAIN_ID]")

        parser.add_argument("--os-project-domain-name",
                            metavar="<auth-project-domain-name>",
                            default=os.environ.get("OS_PROJECT_DOMAIN_NAME"),
                            help="defaults to env[OS_PROJECT_DOMAIN_NAME]")

        parser.add_argument("--os-auth-url",
                            metavar="<auth-url>",
                            default=os.environ.get("OS_AUTH_URL"),
                            help="defaults to env[OS_AUTH_URL]")

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
        os_user_domain_id = args.os_user_domain_id
        os_user_domain_name = args.os_user_domain_name
        os_project_name = args.os_project_name
        os_project_domain_id = args.os_project_domain_id
        os_project_domain_name = args.os_project_domain_name
        os_auth_url = args.os_auth_url
        os_cacert = args.os_cacert
        bypass_url = args.bypass_url
        command_name = args.command_name
        token = None

        if not os_username:
            raise ValueError("'os-username' not defined!")

        if not os_password:
            raise ValueError("'os-password' not defined!")

        if not os_project_name:
            raise ValueError("'os-project-name' not defined!")

        if not os_auth_url:
            raise ValueError("'os-auth-url' not defined!")

        if not os_user_domain_name:
            os_user_domain_name = "default"

        if not os_project_domain_name:
            os_project_domain_name = "default"

        client = keystone_v3.KeystoneClient(
            auth_url=os_auth_url,
            username=os_username,
            password=os_password,
            ca_cert=os_cacert,
            user_domain_id=os_user_domain_id,
            user_domain_name=os_user_domain_name,
            project_name=os_project_name,
            project_domain_id=os_project_domain_id,
            project_domain_name=os_project_domain_name)

        token = client.authenticate()

        if bypass_url:
            synergy_url = bypass_url
        else:
            synergy_endpoint = client.getEndpoint("synergy")
            synergy_url = synergy_endpoint["url"]

        if command_name not in commands:
            print("Command %r not found!" % command_name)

        commands[command_name].setToken(token)
        commands[command_name].execute(synergy_url, args)
    except KeyboardInterrupt:
        print("Shutting down synergyclient")
        sys.exit(1)
    except ConnectionError as ex:
        print("Failed to establish a new connection to %s" % synergy_url)
        sys.exit(1)
    except HTTPError as ex:
        if ex.response._content:
            print("%s" % ex.response._content)
        else:
            print("%s" % ex.message)
        sys.exit(1)
    except RequestException as ex:
        print("%s" % ex.response._content)
        sys.exit(1)
    except Exception as ex:
        print(ex)
        sys.exit(1)


if __name__ == "__main__":
    main()
