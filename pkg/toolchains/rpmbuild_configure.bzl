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
"""Repository rule to autoconfigure a toolchain using the system rpmbuild."""

def _write_build(rctx, path):
    if not path:
        path = ""
    rctx.template(
        "BUILD",
        Label("//toolchains:BUILD.tpl"),
        substitutions = {
            "{GENERATOR}": "@rules_pkg//toolchains/rpmbuild_configure.bzl%find_system_rpmbuild",
            "{RPMBUILD_PATH}": str(path),
        },
        executable = False,
    )

def _find_system_rpmbuild_impl(rctx):
    rpmbuild_path = rctx.which("rpmbuild")
    if rctx.attr.verbose:
        if rpmbuild_path:
            print("Found rpmbuild at '%s'" % rpmbuild_path)  # buildifier: disable=print
        else:
          print("No system rpmbuild found.")  # buildifier: disable=print
    _write_build(rctx = rctx, path = rpmbuild_path)

_find_system_rpmbuild = repository_rule(
    implementation = _find_system_rpmbuild_impl,
    doc = """Create a repository that defines an rpmbuild toolchain based on the system rpmbuild.""",
    local = True,
    environ = ["PATH"],
    attrs = {
        "verbose": attr.bool(
            doc = "If true, print status messages.",
        ),
    },
)

def find_system_rpmbuild(name, verbose=False):
    _find_system_rpmbuild(name=name, verbose=verbose)
    native.register_toolchains(
        "@%s//:rpmbuild_auto_toolchain" % name,
        "@rules_pkg//toolchains:rpmbuild_missing_toolchain")
