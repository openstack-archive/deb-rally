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

from __future__ import print_function
import os.path
import re
import sys


def get_template(template_path):
    import mako.lookup

    templates_dir = os.path.join(os.path.dirname(__file__), "templates")

    lookup_dirs = [
        templates_dir,
        os.path.abspath(os.path.join(templates_dir, "..", "..", ".."))
    ]

    lookup = mako.lookup.TemplateLookup(directories=lookup_dirs)

    return lookup.get_template(template_path)


def main(*args):
    if (len(args) < 2 or args[0] != "render"
       or not all(re.match("^[^=]+=[^=]+$", arg) for arg in args[2:])):
        raise ValueError(
            "Usage: \n\t"
            "utils.py render <lookup/path/to/template.mako> "
            "<key-1>=<value-1> <key-2>=<value-2>\n\n\t"
            "Where key-1,value-1 and key-2,value-2 are key pairs of template"
        )

    render_kwargs = dict([arg.split("=") for arg in args[2:]])
    print(get_template(args[1]).render(**render_kwargs))


if __name__ == "__main__":
    main(*sys.argv[1:])
