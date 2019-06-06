package(default_visibility = ["//visibility:public"])

# rules_go boilerplate
load("@bazel_gazelle//:def.bzl", "gazelle")

gazelle(
    name = "gazelle",
    prefix = "github.com/bazelbuild/rules_pkg",
)

# update_deb_packages boilerplate
load("@rules_pkg//tools/update_deb_packages:update_deb_packages.bzl", "update_deb_packages")

update_deb_packages(
    name = "update_deb_packages",
    pgp_keys = [
        "@jessie_archive_key//file",
        "@stretch_archive_key//file",
    ],
)
