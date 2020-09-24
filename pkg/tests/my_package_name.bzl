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

load("//:providers.bzl", "PackageNamingInfo")
load("//:package_naming.bzl", "default_package_naming")

def _my_package_naming_impl(ctx):
  values = default_package_naming(ctx)
  values['cpu'] = 'arm48'
  values['opt'] = 'debug'
  return PackageNamingInfo(values = values)

my_package_naming = rule(
    implementation = _my_package_naming_impl,
)

