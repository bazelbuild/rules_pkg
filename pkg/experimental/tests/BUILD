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
load("@rules_pkg//experimental:rpm.bzl", "pkg_rpm")
load("@rules_python//python:defs.bzl", "py_test")

licenses(["notice"])

pkg_filegroup_analysis_tests()

pkg_filegroup_unit_tests()

filegroup(
    name = "ars",
    srcs = glob(["testdata/*.ar"]),
)

pkg_filegroup(
    name = "ars_pfg",
    srcs = [
        ":ars",
    ],
    attrs = {"unix": [
        "0755",
        "root",
        "root",
    ]},
    prefix = "/test",
)

pkg_mkdirs(
    name = "var_log_foo",
    attrs = {"unix": [
        "0755",
        "root",
        "root",
    ]},
    dirs = ["/var/log/foo"],
)

pkg_mklinks(
    name = "test_links",
    attrs = {"unix": [
        "0777",
        "root",
        "root",
    ]},
    links = {"/usr/bin/link-name": "/usr/bin/link-target"},
)

pkg_rpm(
    name = "test_rpm",
    architecture = "noarch",
    data = [
        ":ars_pfg",
        ":test_links",
        ":var_log_foo",
    ],
    description = """pkg_rpm test rpm description""",
    license = "Apache 2.0",
    post_scriptlet = """echo post""",
    postun_scriptlet = """echo postun""",
    pre_scriptlet = """echo pre""",
    preun_scriptlet = """echo preun""",
    release = "2222",
    spec_template = "template-test.spec.in",
    summary = "pkg_rpm test rpm summary",
    version = "1.1.1",
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
        echo ,root,root,40755,,
    ) >> $@

    # Symlink (has no hash)
    (
        echo -n /usr/bin/link-name,
        # No hash (beginning), or fflags (second-to-last)
        echo ,root,root,120777,,/usr/bin/link-target
    ) >> $@
    """,
)

# One cannot simply pass the output of pkg_rpm as runfiles content (#161).  This
# seems to be the easiest way around this problem.
sh_library(
    name = "pkg_rpm_basic_test_data",
    testonly = True,
    data = [
        ":test_rpm",
        ":test_rpm_manifest",
    ],
)

py_test(
    name = "pkg_rpm_basic_test",
    srcs = ["pkg_rpm_basic_test.py"],
    data = [":pkg_rpm_basic_test_data"],
    python_version = "PY3",
    tags = [
        "no_windows",  # Windows doesn't have rpmbuild(8)
    ],
    deps = ["@rules_python//python/runfiles"],
)
