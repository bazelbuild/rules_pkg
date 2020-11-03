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
"""toolchain to provide an rpmbuild binary."""

RpmbuildInfo = provider(
    doc = """Platform inde artifact.""",
    fields = {
        "label": "The path to a target I will build",
        "path": "The path to a pre-built rpmbuild",
    },
)

def _rpmbuild_toolchain_impl(ctx):
    toolchain_info = platform_common.ToolchainInfo(
        rpmbuild = RpmbuildInfo(
            label = ctx.attr.label,
            path = ctx.attr.path,
        ),
    )
    return [toolchain_info]

rpmbuild_toolchain = rule(
    implementation = _rpmbuild_toolchain_impl,
    attrs = {
        "label": attr.label(
            cfg = "exec",
            executable = True,
            allow_files = True,
        ),
        "path": attr.string(),
    },
)

# Expose the presence of an rpmbuild in the resolved toolchain as a flag.
def _is_rpmbuild_available_impl(ctx):
    toolchain = ctx.toolchains["//toolchains:rpmbuild_toolchain_type"].rpmbuild
    if toolchain.label or toolchain.path:
        value = "1"
    else:
        value = "0"
    return [config_common.FeatureFlagInfo(value = value)]

is_rpmbuild_available = rule(
    implementation = _is_rpmbuild_available_impl,
    attrs = {},
    toolchains = ["//toolchains:rpmbuild_toolchain_type"],
)
