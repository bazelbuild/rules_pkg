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

"""Utility methods to populate PackageVariablesInfo instances."""

load("@bazel_tools//tools/cpp:toolchain_utils.bzl", "find_cpp_toolchain")

def add_cpp_variables(ctx, values):
    cc_toolchain = find_cpp_toolchain(ctx)
    # TODO(aiuto): Expand this to include target OS. Maybe also compilation
    # mode, ABI and libc version, since they are sometimes used in package file
    # names.
    values['cpu'] = cc_toolchain.cpu
    return values
