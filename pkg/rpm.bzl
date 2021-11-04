# Copyright 2021 The Bazel Authors. All rights reserved.
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

"""RPM packaging interfaces

This module provides a wrapper macro "pkg_rpm" that allows users to select
between the two variants of `pkg_rpm`:

- `pkg_rpm_pfg`, which arranges contents via the `pkg_filegroup`
  framework defined in `:mappings.bzl`.

- `pkg_rpm_legacy`, which arranges contents via a spec file template.

`pkg_rpm_legacy` is deprecated and will be removed in a future release of
rules_pkg.

The mechanism for choosing between the two is documented in the function itself.

"""

load("//pkg/legacy:rpm.bzl", pkg_rpm_legacy = "pkg_rpm")
load("//pkg:rpm_pfg.bzl", pkg_rpm_pfg = "pkg_rpm")

def pkg_rpm(name, srcs = None, spec_file = None, **kwargs):
    """pkg_rpm wrapper

    This rule selects between the two implementations of pkg_rpm as described in
    the module docstring.  In particular:

    If `srcs` is provided, this macro will choose `pkg_rpm_pfg`.  If
    `spec_file` is provided, it will choose `pkg_rpm_legacy`.

    If neither or both are provided, this will fail.

    Args:
      name: rule name
      srcs: pkg_rpm_pfg `srcs` attribute
      spec_file: pkg_rpm_legacy `spec_file` attribute
      **kwargs: arguments to eihter `pkg_rpm_pfg` or `pkg_rpm_legacy`,
                depending on mode

    """
    if srcs and spec_file:
        fail("Cannot determine which pkg_rpm rule to use.  `srcs` and `spec_file` are mutually exclusive")

    if not srcs and not spec_file:
        fail("Either `srcs` or `spec_file` must be provided.")

    if srcs:
        pkg_rpm_pfg(
            name = name,
            srcs = srcs,
            **kwargs
        )
    elif spec_file:
        pkg_rpm_legacy(
            name = name,
            spec_file = spec_file,
            **kwargs
        )

    else:
        fail("This should be unreachable; kindly file a bug against rules_pkg.")
