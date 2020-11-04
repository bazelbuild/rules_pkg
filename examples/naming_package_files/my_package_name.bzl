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

"""Example rule to show package naming techniques."""

load("@rules_pkg//:providers.bzl", "PackageVariablesInfo")
load("@rules_pkg//:package_variables.bzl", "add_ctx_variables")

def _my_package_naming_impl(ctx):
    values = {}

    # Add variables which are always present
    add_ctx_variables(ctx, values)

    # then add in my own custom values
    values["product_name"] = ctx.attr.product_name
    values["special_build"] = ctx.attr.special_build
    return PackageVariablesInfo(values = values)

my_package_naming = rule(
    implementation = _my_package_naming_impl,
    attrs = {
        "product_name": attr.string(
            doc = "Placeholder for our final product name.",
        ),
        "special_build": attr.string(
            doc = "Indicates that we have built with a 'special' option.",
        ),
    },
)
