load("@rules_pkg//:genpkg.bzl", "make_strip_prefix", "pkgfilegroup")
load("test.bzl", "test_referencing_remote_file")

package(default_visibility = ["//visibility:public"])

exports_files(
    glob(["**"]),
    visibility = ["//visibility:public"],
)

sh_binary(
    name = "script",
    srcs = ["dir/extproj.sh"],
    visibility = ["//visibility:public"]
)

pkgfilegroup(
    name = "extproj_script_pfg",
    prefix = "usr/bin",
    srcs = ["dir/extproj.sh"],
    strip_prefix = make_strip_prefix(from_pkg = "")
)

test_referencing_remote_file(
    name = "pfg_local_file_in_extrepo"
)
