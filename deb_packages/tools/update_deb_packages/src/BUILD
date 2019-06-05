load("@io_bazel_rules_go//go:def.bzl", "go_binary", "go_library")

go_library(
    name = "go_default_library",
    srcs = [
        "update_deb_packages.go",
    ],
    importpath = "github.com/bazelbuild/rules_pkg/deb_packages/tools/update_deb_packages/src",
    deps = [
        #"@com_github_bazelbuild_buildtools//:go_default_library",
        "@com_github_knqyf263_go_deb_version//:go_default_library",
        "@com_github_stapelberg_godebiancontrol//:go_default_library",
        "@org_golang_x_crypto//openpgp:go_default_library",
    ],
)

go_binary(
    name = "update_deb_packages",
    srcs = ["update_deb_packages.go"],
    importpath = "github.com/bazelbuild/rules_pkg/deb_packages/tools/update_deb_packages/src",
    visibility = ["//visibility:public"],
    deps = [
        ":go_default_library",
        #"@com_github_bazelbuild_buildtools//:go_default_library",
        "@com_github_knqyf263_go_deb_version//:go_default_library",
        "@com_github_stapelberg_godebiancontrol//:go_default_library",
        "@org_golang_x_crypto//openpgp:go_default_library",
    ],
)
