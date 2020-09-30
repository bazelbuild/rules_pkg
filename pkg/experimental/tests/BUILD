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

load(":pkg_filegroup_test.bzl", "pkg_filegroup_analysis_tests", "pkg_filegroup_unit_tests")
load("@rules_pkg//experimental:pkg_filegroup.bzl", "pkg_filegroup", "pkg_mkdirs", "pkg_mklinks")
load("@rules_python//python:defs.bzl", "py_test")

licenses(["notice"])

pkg_filegroup_analysis_tests()

pkg_filegroup_unit_tests()
