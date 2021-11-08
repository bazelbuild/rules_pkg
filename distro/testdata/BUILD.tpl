load("@not_named_rules_pkg//pkg:pkg.bzl", "pkg_tar")

pkg_tar(
    name = "dummy_tar",
    srcs = [
      ":BUILD",
    ],
    extension = "tar.gz",
    owner = "0.0",
    package_dir = ".",
    tags = [
        "manual",
    ],
)
