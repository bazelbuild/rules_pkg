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

load("@bazel_skylib//rules:build_test.bzl", "build_test")
load("@rules_pkg//experimental:pkg_filegroup.bzl", "pkg_filegroup", "pkg_mkdirs", "pkg_mklinks")
load("@rules_pkg//experimental:rpm.bzl", "pkg_rpm")
load("@rules_python//python:defs.bzl", "py_test")

licenses(["notice"])

filegroup(
    name = "ars",
    srcs = glob(["testdata/*.ar"]),
)

############################################################################
# pkg_filegroups for testing
############################################################################

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

############################################################################
# Test RPMs
############################################################################

pkg_rpm(
    name = "test_rpm",
    architecture = "noarch",
    conflicts = ["not-a-test"],
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
    provides = ["test"],
    release = "2222",
    requires = ["test-lib > 1.0"],
    requires_contextual = {"preun": ["bash"]},
    spec_template = "template-test.spec.in",
    summary = "pkg_rpm test rpm summary",
    version = "1.1.1",
)

# Just like the above one, except the compression is changed.
pkg_rpm(
    name = "test_rpm-bzip2",
    architecture = "noarch",
    binary_payload_compression = "w2.bzdio",
    conflicts = ["not-a-test"],
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
    provides = ["test"],
    release = "2222",
    requires = ["test-lib > 1.0"],
    requires_contextual = {"preun": ["bash"]},
    spec_template = "template-test.spec.in",
    summary = "pkg_rpm test rpm summary",
    version = "1.1.1",
)

############################################################################
# Test RPM metadata -- used to verify RPM contents in tests
############################################################################

# Emit a CSV file providing a manifest providing the expected RPM contents
genrule(
    name = "test_rpm_manifest",
    srcs = [":ars"],
    outs = ["manifest.csv"],
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

genrule(
    name = "test_rpm_metadata",
    srcs = [],
    outs = [
        "conflicts.csv",
        "provides.csv",
        "requires.csv",
    ],
    # In the below, we don't use the "," separator for everything, because the
    # query tags used to get the associated dependency types
    # (e.g. %{REQUIREFLAGS:deptype}) itself uses commas.  This makes it so the test
    # doesn't have to rely on knowing the number of fields in each CSV file.
    cmd = """
    (
        echo 'capability:sense'
        echo 'not-a-test:manual'
    ) > $(RULEDIR)/conflicts.csv
    (
        # NOTE: excludes the "self-require" (we did nothing special to make it
        # appear)

        echo 'capability:sense'
        echo 'test:manual'
    ) > $(RULEDIR)/provides.csv
    (
        # NOTE: excludes 'rpmlib' requires that may be version-dependent
        echo 'capability:sense'
        # Common, automatically generated
        echo '/bin/sh:pre,interp'
        echo '/bin/sh:post,interp'
        echo '/bin/sh:preun,interp'
        echo '/bin/sh:postun,interp'
        # Hand-specified, specific dependencies
        echo 'bash:preun'
        # Hand-specified
        echo 'test-lib > 1.0:manual'
    ) > $(RULEDIR)/requires.csv
    """,
)

# One cannot simply pass the output of pkg_rpm as runfiles content (#161).  This
# seems to be the easiest way around this problem.
sh_library(
    name = "pkg_rpm_basic_test_data",
    testonly = True,
    data = [
        ":test_rpm",
        ":test_rpm-bzip2",
        ":test_rpm_manifest",
        ":test_rpm_metadata",
    ],
)

############################################################################
# Actual tests
############################################################################

# RPM content verification tests
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

# Smoke test for defaults
pkg_rpm(
    name = "test_rpm_default_template",
    testonly = True,
    architecture = "noarch",
    data = [
        ":ars_pfg",
        ":test_links",
        ":var_log_foo",
    ],
    description = """pkg_rpm test rpm description""",
    license = "Apache 2.0",
    release = "2222",
    summary = "pkg_rpm test rpm summary",
    version = "1.1.1",
)

build_test(
    name = "pkg_rpm_smoke",
    targets = [":test_rpm_default_template"],
)
