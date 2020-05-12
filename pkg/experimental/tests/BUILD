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
load("@rules_pkg//experimental:pkg_filegroup.bzl", "pkg_filegroup", "pkg_mkdirs")
load("@rules_pkg//experimental:rpm.bzl", "pkg_rpm")
load("@rules_python//python:defs.bzl", "py_test")

pkg_filegroup_analysis_tests()

pkg_filegroup_unit_tests()

filegroup(
    name = "ars",
    srcs = glob(["testdata/*.ar"]),
)

pkg_filegroup(
    name = "ars_pfg",
    prefix = "/test",
    srcs = [
        ":ars",
    ],
    attrs = {"unix": ["0755", "root", "root"]},
)

pkg_mkdirs(
    name = "var_log_foo",
    dirs = ["/var/log/foo"],
    attrs = {"unix": ["0755", "root", "root"]},
)

pkg_rpm(
    name = "test_rpm",
    data = [":ars_pfg", "var_log_foo"],
    version = "1.1.1",
    release = "2222",
    license = "Apache 2.0",
    architecture = "noarch",
    summary = "pkg_rpm test rpm summary",
    description = """pkg_rpm test rpm description""",
    pre_scriptlet = """echo pre""",
    post_scriptlet = """echo post""",
    preun_scriptlet = """echo preun""",
    postun_scriptlet = """echo postun""",
    testonly = True,
    spec_template = "template-test.spec.in",
)

# Emit a CSV file providing a manifest providing the expected RPM contents
genrule(
    name = "test_rpm_manifest",
    srcs = [":ars"],
    outs = ["manifest.txt"],
    # Keep the header (the first line echo'd below) in sync with
    # rpm_queryformat_fieldnames in pkg_rpm_basic_test.py
    cmd = """
    echo 'path,digest,user,group,mode,fflags,symlink' > $@
    for f in $(locations :ars); do
        # Destination path
        (
            echo -n /test/$$(basename $$f),
            # Hash
            md5sum $$f | cut -d' ' -f1 | tr '\\n' ,
            # User,Group,Mode,Fflags (fflags not provided)
            echo -n 'root,root,100755,'
            # Symlink destination (not provided)
            echo ,
        ) >> $@

    done
    # Directory (has no hash)
    (
        echo -n /var/log/foo,
        # No hash (beginning), fflags (end), or symlink destination (end)
        echo -n ,root,root,40755,,
    ) >> $@
    """,
)

# One cannot simply pass the output of pkg_rpm as runfiles content.
# This seems to be the easiest way around this problem.
sh_library(
    name = "pkg_rpm_basic_test_data",
    data = [":test_rpm", ":test_rpm_manifest"],
    testonly = True,
)

py_test(
    name = "pkg_rpm_basic_test",
    srcs = ["pkg_rpm_basic_test.py"],
    deps = ["@rules_python//python/runfiles"],
    data = [":pkg_rpm_basic_test_data"],
)
