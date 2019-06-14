# Workspace dependencies for rules_pkg/pkg

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

def _maybe(repo, name, **kwargs):
    if not native.existing_rule(name):
        repo(name = name, **kwargs)

# @federation: BEGIN @rules_pkg
def rules_pkg_dependencies():
    # Needed for helper tools
    _maybe(
        http_archive,
        name = "abseil_py",
        urls = [
            "https://github.com/abseil/abseil-py/archive/pypi-v0.7.1.tar.gz",
      ],
      sha256 = "3d0f39e0920379ff1393de04b573bca3484d82a5f8b939e9e83b20b6106c9bbe",
      strip_prefix = "abseil-py-pypi-v0.7.1",
    )

    # Needed by abseil-py. They do not use deps yet.
    _maybe(
        http_archive,
        name = "six_archive",
        urls = [
            "http://mirror.bazel.build/pypi.python.org/packages/source/s/six/six-1.10.0.tar.gz",
            "https://pypi.python.org/packages/source/s/six/six-1.10.0.tar.gz",
        ],
        sha256 = "105f8d68616f8248e24bf0e9372ef04d3cc10104f1980f54d57b2ce73a5ad56a",
        strip_prefix = "six-1.10.0",
        build_file = "@abseil_py//third_party:six.BUILD"
    )


def rules_pkg_register_toolchains():
    pass
# @federation: END @rules_pkg
