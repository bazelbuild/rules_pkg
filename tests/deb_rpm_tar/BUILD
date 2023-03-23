load("//pkg:deb.bzl", "pkg_deb")
load("//pkg:tar.bzl", "pkg_tar")
load("//pkg:rpm.bzl", "pkg_rpm")
load("//pkg:mappings.bzl", "pkg_files")

genrule(
    name = "gen_foo",
    outs = ["usr/bin/foo"],
    cmd = "touch $@",
)

pkg_tar(
    name = "deb_input",
    srcs = [":gen_foo"],
)

pkg_deb(
    name = "test_deb",
    data = ":deb_input",
    description = "Some package",
    maintainer = "john.doe@example.com",
    package = "debpackage",
    package_file_name = "debpackage-0.0.0.deb",
    version = "0.0.0",
)

pkg_tar(
    name = "deb_tar",
    srcs = [":test_deb"],
)

pkg_files(
    name = "rpm_input",
    srcs = [":gen_foo"],
)

pkg_rpm(
    name = "test_rpm",
    srcs = [":rpm_input"],
    description = "Description",
    license = "Apache 2.0",
    package_file_name = "rpmpackage-0.0.0-1.rpm",
    release = "1",
    summary = "Summary",
    version = "0.0.0",
)

pkg_tar(
    name = "rpm_tar",
    srcs = [":test_rpm"],
)

sh_test(
    name = "deb_rpm_tar_test",
    size = "small",
    srcs = ["test.sh"],
    args = [
        "$(location :deb_tar)",
        "$(location :rpm_tar)",
    ],
    data = [
        ":deb_tar",
        ":rpm_tar",
    ],
)
