# Copyright 2020 The Bazel Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This module provides an alternate way to specify package contents using a
simple csv-like description specification.

This allows for a highly succinct descriptions of package contents in many
common cases.

The following cases are known NOT to be supported by this scheme:

- Exclusion of any files from a source target with multiple files.
- Renaming of any files from a source target with multiple files.
- Any sort of prefix stripping or path manipulation.

Normal pkg_filegroup's should be used in the above cases.

"""

load("//experimental:pkg_filegroup.bzl", "pkg_filegroup", "pkg_mkdirs", "pkg_mklinks")

# Example manifest:
#
#[
#    #dest                             action     attributes... source
#    ("/some/destination/directory/",  "copy",    "unix=0755", ":target-or-label"),
#    ("/some/destination/binary-name", "copy",    "unix=0755", ":target-or-label"),
#    ("/dir",                          "mkdir",   "unix=0755", "IGNORED"),
#    ("/dir/child",                    "mkdir",   "unix=0755", "IGNORED"),
#    ("/dir/child/other-child",        "mkdir",   "unix=0755", "IGNORED"),
#    ("target",                        "symlink", "unix=0777", "source"),
#]

_MANIFEST_ROW_SIZE = 4

def _manifest_process_copy(name, destination, attrs, source, **kwargs):
    allowed_attrs = ["section", "unix", "user", "group"]

    section = None
    unix_perms = "-"
    user = "-"
    group = "-"
    for decl in attrs.split(";"):
        (attr, _, value) = decl.partition("=")
        if attr not in allowed_attrs:
            fail("{}: unknown attribute {}".format(name, attr))
        if attr == "section":
            section = value
        elif attr == "unix":
            unix_perms = value
        elif attr == "user":
            user = value
        elif attr == "group":
            group = value

    if destination.endswith("/"):
        prefix = destination
        renames = None
    else:
        prefix = None
        renames = {source: destination}

    pkg_filegroup(
        name = name,
        srcs = [source],
        attrs = {"unix": [unix_perms, user, group]},
        section = section,
        renames = renames,
        prefix = prefix,
        **kwargs
    )

def _manifest_process_mkdir(name, destination, attrs, source, **kwargs):
    allowed_attrs = ["section", "unix", "user", "group"]

    section = None
    unix_perms = "-"
    user = "-"
    group = "-"
    for decl in attrs.split(";"):
        (attr, _, value) = decl.partition("=")
        if attr not in allowed_attrs:
            fail("{}: unknown attribute {}".format(name, attr))
        if attr == "section":
            section = value
        elif attr == "unix":
            unix_perms = value
        elif attr == "user":
            user = value
        elif attr == "group":
            group = value

    pkg_mkdirs(
        name = name,
        dirs = [destination],
        attrs = {"unix": [unix_perms, user, group]},
        section = section,
        **kwargs
    )

def _manifest_process_symlink(name, destination, attrs, source, **kwargs):
    allowed_attrs = ["section", "unix", "user", "group"]

    section = None
    unix_perms = "0777"
    user = "-"
    group = "-"

    if attrs != "-":
        for decl in attrs.split(";"):
            (attr, _, value) = decl.partition("=")
            if attr not in allowed_attrs:
                fail("{}: unknown attribute {}".format(name, attr))
            if attr == "section":
                section = value
            elif attr == "unix":
                unix_perms = value
            elif attr == "user":
                user = value
            elif attr == "group":
                group = value

    pkg_mklinks(
        name = name,
        links = {destination: source},
        attrs = {"unix": [unix_perms, user, group]},
        section = section,
        **kwargs
    )

def pkg_list_manifest(name, manifest, default_attrs = "", **kwargs):
    """
    Process a "manifest" of package specifications into packaging rules.

    The "manifest" format is a list of tuples that looks like this:

    ```
    (destination, action, attributes, source)
    ```

    Each element is a string.

    Where:
    - `destination` refers to the destination path within the package, although
      can have special meaning depending on the action

    - `action` is one of:
      - "copy", for a simple install-to-destination action, corresponding to `pkg_filegroup`
      - "mkdir", for a directory creation action, corresponding to `pkg_mkdirs`
      - "symlink", for a symlink creation action, corresponding to `pkg_mklinks`

    - `attributes` refers to various properties and permissions on the
       destination targets.  They are formatted as a semicolon-separated list of
       key=value pairs, e.g. `foo=bar;baz=qux`.

      Common attributes include:

      - "unix": UNIX-style filesystem permissions as four-digit octal (e.g. "0644")

      - "user": Filesystem owning user, as known to your target platform

      - "group: Filesystem owning group, as known to your target platform

      - "section": Package installation property, see each individual action for
                   details.
    
    - `source` depends on the action

    For `copy` actions:

    - `destination`: the location within the package where files are installed.
      If `destination` ends in "/", the `source` is installed to this path as
      the prefix, otherwise, it is renamed to the destination.

      If `destination` refers to a target with more than one output, only the
      "/" option is allowed.

    - `attributes`: see "Common attributes", above.  "section" corresponds to the
      "section" attribute of `pkg_filegroup`.

    - `source`: to a label that specifies the value to be installed.

    For "mkdir" actions:

    - `destination` refers to the path within the package where the directory is created.

    - `attributes: see "Common attributes", above.  "section" corresponds to the
      "section" attribute of `pkg_mkdirs`.

    - `source` is ignored.

    For "symlink" actions:

    - `destination`: the name of the symbolic link in the target package

    - `attributes: see "Common attributes", above.  "section" corresponds to the
      "section" attribute of `pkg_mklinks`.

    - `source` refers to the "target" of the symbolic link in question.  It may
      exist outside of the defined package.

    Args:
        name: string value used to influence the output rule names

        manifest: list of tuples, with the format described in the introduction of this rule

        default_attrs: A string representing the default attributes for all
          actions in this manifest.  Attributes must be specified as though they
          were in a manifest.

        **kwargs: Any arguments that should be passed to generated rules.

    Returns:
        A list of rules that can be passed to a `pkg_filegroup`-compatible packaging rule.

        The output rules are each named after the rule "name" and the index in
        the manifest, which can be useful for finding where precisely errors can
        occur.
    """

    rules = []

    for idx, desc in enumerate(manifest):
        if len(desc) != _MANIFEST_ROW_SIZE:
            fail("Package description index {} malformed (size {}, must be {})".format(
                idx,
                len(desc),
                _MANIFEST_ROW_SIZE,
            ))

        (destination, action, attrs, source) = desc

        if default_attrs != "":
            attrs = default_attrs + ";" + attrs

        rule_name = "{}_manifest_elem_{}".format(name, idx)
        if action == "copy":
            _manifest_process_copy(rule_name, destination, attrs, source, **kwargs)
        elif action == "mkdir":
            _manifest_process_mkdir(rule_name, destination, attrs, source, **kwargs)
        elif action == "symlink":
            _manifest_process_symlink(rule_name, destination, attrs, source, **kwargs)
        else:
            fail("Package description index {} malformed (unknown action {})".format(
                idx,
                action,
            ))

        rules.append(":{}".format(rule_name))

    # TODO: making this return something like a pkg_filegroup requires some sort
    # of "aggregator" rule.  The original pkg_filegroup framework was not
    # designed this way, and it needs to be rethought to better facilitate this
    # purpose.
    return rules
