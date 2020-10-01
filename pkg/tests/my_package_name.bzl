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

"""Sample rule to show package naming."""

load("//:providers.bzl", "PackageVariablesInfo")
load("//:package_variables.bzl", "add_ctx_variables")

def _my_package_naming_impl(ctx):
    values = {}
    # Add variables which are always present
    add_ctx_variables(ctx, values)
    # then add in my own custom values
    values['label'] = ctx.attr.label
    values['special_build'] = ctx.attr.special_build
    return PackageVariablesInfo(values = values)

my_package_naming = rule(
    implementation = _my_package_naming_impl,
    attrs = {
        "label": attr.string(doc = "A label that matters to me."),
        "special_build": attr.string(
            doc = "Another label for the sake of the sample."
        ),
    }
)
