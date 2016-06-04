# Copyright 2014: Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

""" Rally command: verify """

import csv
import json
import os

import six
import yaml

from rally import api
from rally.cli import cliutils
from rally.cli import envutils
from rally.common import fileutils
from rally.common.i18n import _
from rally.common import utils
from rally import consts
from rally import exceptions
from rally.verification.tempest import diff
from rally.verification.tempest import json2html


AVAILABLE_SETS = list(consts.TempestTestsSets) + list(consts.TempestTestsAPI)


class VerifyCommands(object):
    """Verify an OpenStack cloud via Tempest.

    Set of commands that allow you to run Tempest tests.
    """

    @cliutils.args("--deployment", dest="deployment", type=str,
                   metavar="<uuid>", required=False,
                   help="UUID or name of a deployment.")
    @cliutils.args("--set", metavar="<set_name>", dest="set_name", type=str,
                   required=False,
                   help="Name of a Tempest test set. "
                        "Available sets are %s" % ", ".join(AVAILABLE_SETS))
    @cliutils.args("--regex", dest="regex", type=str, required=False,
                   help="Test name regular expression")
    @cliutils.args("--tests-file", metavar="<path>", dest="tests_file",
                   type=str, required=False,
                   help="Path to a file with a list of Tempest tests")
    @cliutils.args("--tempest-config", dest="tempest_config", type=str,
                   required=False, metavar="<path>",
                   help="User-specified Tempest config file location")
    @cliutils.args("--xfails-file", dest="xfails_file", type=str,
                   required=False, metavar="<path>",
                   help="Path to a YAML file with a list of Tempest "
                        "tests that are expected to fail")
    @cliutils.args("--no-use", action="store_false", dest="do_use",
                   help="Don't set the task as default for future operations")
    @cliutils.args("--system-wide", dest="system_wide",
                   help="Don't create a virtual env when installing Tempest; "
                        "use the local env instead of the Tempest virtual env "
                        "when running the tests. Note that all Tempest "
                        "requirements have to be already installed in "
                        "the local env!",
                   required=False, action="store_true")
    @cliutils.args("--concurrency", metavar="N", dest="concur", type=int,
                   required=False,
                   help="How many processes to use to run Tempest tests. "
                        "The default value (0) auto-detects your CPU count")
    @cliutils.args("--failing", dest="failing", required=False,
                   help="Re-run the tests that failed in the last execution",
                   action="store_true")
    @envutils.with_default_deployment(cli_arg_name="deployment")
    def start(self, deployment=None, set_name="", regex=None,
              tests_file=None, tempest_config=None, xfails_file=None,
              do_use=True, system_wide=False, concur=0, failing=False):
        """Start verification (run Tempest tests).

        :param deployment: UUID or name of a deployment
        :param set_name: Name of a Tempest test set
        :param regex: Regular expression of test
        :param tests_file: Path to a file with a list of Tempest tests
        :param tempest_config: User specified Tempest config file location
        :param xfails_file: Path to a file in YAML format with a list of
                            Tempest tests that are expected to fail
        :param do_use: Use new task as default for future operations
        :param system_wide: Whether or not to create a virtual env when
                            installing Tempest; whether or not to use
                            the local env instead of the Tempest virtual
                            env when running the tests
        :param concur: How many processes to use to run Tempest tests.
                       The default value (0) auto-detects CPU count
        :param failing: Re-run tests that failed during the last execution
        """

        msg = _("Arguments '%s' and '%s' are not compatible. "
                "You can use only one of the mentioned arguments.")
        if regex and set_name:
            print(msg % ("regex", "set"))
            return 1
        if tests_file and set_name:
            print(msg % ("tests_file", "set"))
            return 1
        if tests_file and regex:
            print(msg % ("tests_file", "regex"))
            return 1

        if not (regex or set_name or tests_file or failing):
            set_name = "full"

        if set_name and set_name not in AVAILABLE_SETS:
            print(_("Tempest test set '%s' not found "
                    "in available test sets. Available sets are %s.")
                  % (set_name, ", ".join(AVAILABLE_SETS)))
            return 1

        if tests_file and not os.path.exists(tests_file):
            print(_("File '%s' not found.") % tests_file)
            return 1

        if failing and set_name:
            print(msg % ("failing", "set"))
            return 1

        if failing and tests_file:
            print(msg % ("failing", "tests_file"))
            return 1

        expected_failures = None
        if xfails_file:
            if os.path.exists(xfails_file):
                with open(os.path.abspath(xfails_file), "rb") as f:
                    expected_failures = yaml.load(f)
            else:
                print(_("File '%s' not found.") % xfails_file)
                return 1

        verification = api.Verification.verify(
            deployment, set_name=set_name, regex=regex, tests_file=tests_file,
            tempest_config=tempest_config, expected_failures=expected_failures,
            system_wide=system_wide, concur=concur, failing=failing)

        if do_use:
            self.use(verification["uuid"])

    @cliutils.args("--deployment", dest="deployment", type=str,
                   metavar="<uuid>", required=False,
                   help="UUID or name of a deployment.")
    @cliutils.args("--set", metavar="<set_name>", dest="set_name", type=str,
                   required=False,
                   help="Name of a Tempest test set. "
                        "Available sets are %s" % ", ".join(AVAILABLE_SETS))
    @cliutils.args("--file", dest="log_file", type=str,
                   required=True, metavar="<path>",
                   help="User specified Tempest log file location. "
                        "Note, Tempest log file needs to be in subunit format")
    @cliutils.args("--no-use", action="store_false", dest="do_use",
                   required=False,
                   help="Don't set new task as default for future operations")
    @cliutils.alias("import")
    @envutils.with_default_deployment(cli_arg_name="deployment")
    def import_results(self, deployment=None, set_name="", log_file=None,
                       do_use=True):
        """Import Tempest tests results into the Rally database.

        :param deployment: UUID or name of a deployment
        :param set_name: Name of a Tempest test set
        :param do_use: Use new task as default for future operations
        :param log_file: User specified Tempest log file in subunit format
        """
        deployment, verification = api.Verification.import_results(deployment,
                                                                   set_name,
                                                                   log_file)
        if do_use:
            self.use(verification["uuid"])

    def list(self):
        """List verification runs."""

        fields = ["UUID", "Deployment UUID", "Set name", "Tests", "Failures",
                  "Created at", "Duration", "Status"]
        verifications = api.Verification.list()

        for el in verifications:
            el["duration"] = el["updated_at"] - el["created_at"]

        if verifications:
            cliutils.print_list(verifications, fields,
                                sortby_index=fields.index("Created at"))
        else:
            print(_("No verification was started yet. "
                    "To start verification use:\nrally verify start"))

    @cliutils.args("--uuid", type=str, dest="verification",
                   help="UUID of a verification.")
    @cliutils.args("--html", action="store_true", dest="output_html",
                   help="Display results in HTML format.")
    @cliutils.args("--json", action="store_true", dest="output_json",
                   help="Display results in JSON format.")
    @cliutils.args("--output-file", type=str, required=False,
                   dest="output_file", metavar="<path>",
                   help="Path to a file to save results to.")
    @envutils.with_default_verification_id
    @cliutils.suppress_warnings
    def results(self, verification=None, output_file=None,
                output_html=None, output_json=None):
        """Display results of a verification.

        :param verification: UUID of a verification
        :param output_file: Path to a file to save results
        :param output_html: Display results in HTML format
        :param output_json: Display results in JSON format (Default)
        """
        try:
            results = api.Verification.get(verification).get_results()
        except exceptions.NotFoundException as e:
            print(six.text_type(e))
            return 1

        result = ""
        if output_json + output_html > 1:
            print(_("Please specify only one "
                    "output format: --json or --html."))
        elif output_html:
            result = json2html.generate_report(results)
        else:
            result = json.dumps(results, sort_keys=True, indent=4)

        if output_file:
            output_file = os.path.expanduser(output_file)
            with open(output_file, "wb") as f:
                f.write(result)
        else:
            print(result)

    @cliutils.args("--uuid", dest="verification", type=str,
                   required=False,
                   help="UUID of a verification")
    @cliutils.args("--sort-by", metavar="<query>", dest="sort_by", type=str,
                   required=False, choices=("name", "duration"),
                   help="Sort results by 'name' or 'duration'")
    @cliutils.args("--detailed", dest="detailed", action="store_true",
                   required=False,
                   help="Display detailed errors of failed tests")
    @envutils.with_default_verification_id
    def show(self, verification=None, sort_by="name", detailed=False):
        """Display results table of a verification.

        :param verification: UUID of a verification
        :param sort_by: Sort results by 'name' or 'duration'
        :param detailed: Display detailed errors of failed tests
        """
        try:
            verification = api.Verification.get(verification)
            tests = verification.get_results()
        except exceptions.NotFoundException as e:
            print(six.text_type(e))
            return 1

        print(_("Total results of verification:\n"))
        total_fields = ["UUID", "Deployment UUID", "Set name", "Tests",
                        "Failures", "Created at", "Status"]
        cliutils.print_list([verification], fields=total_fields)

        print(_("\nTests:\n"))
        fields = ["name", "time", "status"]

        results = tests["test_cases"]
        values = [utils.Struct(**results[test_name]) for test_name in results]
        sortby_index = ("name", "duration").index(sort_by)
        cliutils.print_list(values, fields, sortby_index=sortby_index)

        if detailed:
            for test in six.itervalues(tests["test_cases"]):
                if test["status"] == "fail":
                    header = cliutils.make_header(
                        "FAIL: %(name)s\n"
                        "Time: %(time)s" % {"name": test["name"],
                                            "time": test["time"]})
                    formatted_test = "%(header)s%(log)s\n" % {
                        "header": header,
                        "log": test["traceback"]}
                    print(formatted_test)

    @cliutils.args("--uuid", dest="verification", type=str,
                   required=False, help="UUID of a verification.")
    @cliutils.args("--sort-by", dest="sort_by", choices=("name", "duration"),
                   required=False, help="Sort results by 'name' or 'duration'")
    @envutils.with_default_verification_id
    def detailed(self, verification=None, sort_by="name"):
        """Display results table of a verification with detailed errors.

        :param verification: UUID of a verification
        :param sort_by: Sort results by 'name' or 'duration'
        """
        self.show(verification, sort_by, True)

    @cliutils.args("--uuid-1", type=str, required=True, dest="verification1",
                   help="UUID of the first verification")
    @cliutils.args("--uuid-2", type=str, required=True, dest="verification2",
                   help="UUID of the second verification")
    @cliutils.args("--csv", action="store_true", dest="output_csv",
                   help="Display results in CSV format")
    @cliutils.args("--html", action="store_true", dest="output_html",
                   help="Display results in HTML format")
    @cliutils.args("--json", action="store_true", dest="output_json",
                   help="Display results in JSON format")
    @cliutils.args("--output-file", type=str, required=False,
                   dest="output_file", help="Path to a file to save results")
    @cliutils.args("--threshold", type=int, required=False,
                   dest="threshold", default=0,
                   help="If specified, timing differences must exceed this "
                   "percentage threshold to be included in output")
    def compare(self, verification1=None, verification2=None,
                output_file=None, output_csv=None, output_html=None,
                output_json=None, threshold=0):
        """Compare two verification results.

        :param verification1: UUID of the first verification
        :param verification2: UUID of the second verification
        :param output_file: Path to a file to save results
        :param output_csv: Display results in CSV format
        :param output_html: Display results in HTML format
        :param output_json: Display results in JSON format (Default)
        :param threshold: Timing difference threshold percentage
        """
        try:
            res_1 = api.Verification.get(
                verification1).get_results()["test_cases"]
            res_2 = api.Verification.get(
                verification2).get_results()["test_cases"]
            _diff = diff.Diff(res_1, res_2, threshold)
        except exceptions.NotFoundException as e:
            print(six.text_type(e))
            return 1

        result = ""
        if output_json + output_html + output_csv > 1:
            print(_("Please specify only one output "
                    "format: --json, --html or --csv."))
            return 1
        elif output_html:
            result = _diff.to_html()
        elif output_csv:
            result = _diff.to_csv()
        else:
            result = _diff.to_json()

        if output_file:
            with open(output_file, "wb") as f:
                if output_csv:
                    writer = csv.writer(f, dialect="excel")
                    writer.writerows(result)
                else:
                    f.write(result)
        else:
            print(result)

    @cliutils.args("--uuid", type=str, dest="verification",
                   required=False, help="UUID of a verification")
    def use(self, verification):
        """Set active verification.

        :param verification: UUID of a verification
        """
        print(_("Verification UUID: %s") % verification)
        api.Verification.get(verification)
        fileutils.update_globals_file("RALLY_VERIFICATION", verification)

    @cliutils.args("--deployment", dest="deployment", type=str,
                   metavar="<uuid>", required=False,
                   help="UUID or name of a deployment.")
    @cliutils.args("--tempest-config", dest="tempest_config", type=str,
                   required=False, metavar="<path>",
                   help="User-specified Tempest config file location")
    @cliutils.args("--override", dest="override",
                   help="Override existing Tempest config file",
                   required=False, action="store_true")
    @envutils.with_default_deployment(cli_arg_name="deployment")
    def genconfig(self, deployment=None, tempest_config=None, override=False):
        """Generate Tempest configuration file.

        :param deployment: UUID or name of a deployment
        :param tempest_config: User-specified Tempest config file location
        :param override: Whether or not to override existing Tempest
                         config file
        """
        api.Verification.configure_tempest(deployment, tempest_config,
                                           override)

    @cliutils.args("--deployment", dest="deployment", type=str,
                   metavar="<uuid>", required=False,
                   help="UUID or name of a deployment.")
    @cliutils.args("--source", type=str, dest="source", required=False,
                   help="Path/URL to repo to clone Tempest from")
    @cliutils.args("--system-wide", dest="system_wide",
                   help="Don't create a virtual env for Tempest. Note "
                        "that all Tempest requirements have to be already "
                        "installed in the local env!",
                   required=False, action="store_true")
    @envutils.with_default_deployment(cli_arg_name="deployment")
    def install(self, deployment=None, source=None, system_wide=False):
        """Install Tempest.

        :param deployment: UUID or name of a deployment
        :param source: Path/URL to repo to clone Tempest from
        :param system_wide: Whether or not to create a Tempest virtual env
        """
        api.Verification.install_tempest(deployment, source, system_wide)

    @cliutils.args("--deployment", dest="deployment", type=str,
                   metavar="<uuid>", required=False,
                   help="UUID or name of a deployment.")
    @envutils.with_default_deployment(cli_arg_name="deployment")
    def uninstall(self, deployment=None):
        """Remove the deployment's local Tempest installation.

        :param deployment: UUID or name of a deployment
        """
        api.Verification.uninstall_tempest(deployment)

    @cliutils.args("--deployment", dest="deployment", type=str,
                   metavar="<uuid>", required=False,
                   help="UUID or name of a deployment.")
    @cliutils.deprecated_args("--tempest-config", dest="tempest_config",
                              type=str, required=False, metavar="<path>",
                              release="0.3.2",
                              help="User-specified Tempest config file "
                                   "location. Note that in the future this "
                                   "argument will be removed! Use `rally "
                                   "verify genconfig` instead")
    @cliutils.args("--source", type=str, dest="source", required=False,
                   help="Path/URL to repo to clone Tempest from")
    @cliutils.args("--system-wide", dest="system_wide",
                   help="Don't create a virtual env for Tempest. Note "
                        "that all Tempest requirements have to be already "
                        "installed in the local env!",
                   required=False, action="store_true")
    @envutils.with_default_deployment(cli_arg_name="deployment")
    def reinstall(self, deployment=None,
                  tempest_config=None, source=None, system_wide=False):
        """Uninstall Tempest and install again.

        :param deployment: UUID or name of a deployment
        :param tempest_config: User specified Tempest config file location
        :param source: Path/URL to repo to clone Tempest from
        :param system_wide: Whether or not to create a Tempest virtual env
        """
        api.Verification.reinstall_tempest(deployment, tempest_config,
                                           source, system_wide)

    @cliutils.args("--deployment", dest="deployment", type=str, required=False,
                   metavar="<uuid>", help="UUID or name of a deployment")
    @cliutils.args("--pattern", dest="pattern", type=str,
                   required=False, metavar="<pattern>",
                   help="Test name pattern which can be used to match")
    @envutils.with_default_deployment(cli_arg_name="deployment")
    def discover(self, deployment=None, pattern=""):
        """Show a list of discovered tests.

        :param deployment: UUID or name of a deployment
        :param pattern: Test name pattern which can be used to match
        """
        discovered_tests = api.Verification.discover_tests(deployment, pattern)
        p_str = (_(" matching pattern '%s'") % pattern) if pattern else ""
        if discovered_tests:
            print(_("Discovered tests%s:\n") % p_str)
            for test in discovered_tests:
                print(test)
        else:
            print(_("No tests%s discovered.") % p_str)

    @cliutils.args("--deployment", dest="deployment", type=str,
                   metavar="<uuid>", required=False,
                   help="UUID or name of a deployment.")
    @envutils.with_default_deployment(cli_arg_name="deployment")
    def showconfig(self, deployment=None):
        """Show configuration file of Tempest.

        :param deployment: UUID or name of a deployment
        """
        conf_info = api.Verification.show_config_info(deployment)
        print(_("Tempest config file: %s") % conf_info["conf_path"])
        print("\n" + conf_info["conf_data"])
