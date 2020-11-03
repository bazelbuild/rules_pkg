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
    rctx.file(
        "BUILD",
        content = """# This content is generated
load("@rules_pkg//toolchains:rpmbuild.bzl", "rpmbuild_toolchain")

rpmbuild_toolchain(
    name = "rpmbuild",
    path = "%s",
    is_present = True,
)

toolchain(
    name = "rpmbuild_toolchain",
    toolchain = ":rpmbuild",
    toolchain_type = "@rules_pkg//toolchains:rpmbuild_toolchain_type",
)
""" % path,
        executable=False)

def _write_register_toolchains(rctx, path):
    register_func = """# This content is generated

def register_rpmbuild_toolchains():
"""
    if path:
       register_func += """    native.register_toolchains("@%s//:rpmbuild_toolchain")\n""" % rctx.name
    register_func += """    native.register_toolchains("@rules_pkg//toolchains:rpmbuild_missing_toolchain")\n"""
    rctx.file(
        "register_toolchains.bzl",
        content = register_func,
        executable=False)


def _autoconf_rpmbuild_impl(rctx):
    if not rctx.attr.installed_rpmbuild_path:
       rpmbuild_path = rctx.which("rpmbuild")
    else:
       rpmbuild_path = rctx.attr.installed_rpmbuild_path
    print("rpmbuild.path='%s'" % rpmbuild_path)
    _write_build(rctx=rctx, path=rpmbuild_path)
    _write_register_toolchains(rctx=rctx, path=rpmbuild_path)
    # I would like to register the toolchain here, but you can only call
    # register_toolchains from the WORKSPACE file.

autoconf_rpmbuild = repository_rule(
    implementation=_autoconf_rpmbuild_impl,
    local=True,
    attrs={
        "installed_rpmbuild_path": attr.string(default=""),
    }
)


def XXXXegister_autoconf(repo_name):
   native.register_toolchains("@%s//:rpmbuild_toolchain" % repo_name)
