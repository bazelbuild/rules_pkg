load("@rules_python//python:defs.bzl", "py_binary")
load("@migration_deps//:requirements.bzl", "requirement")
load("@rules_python//python:pip.bzl", "compile_pip_requirements")

py_binary(
    name = "migrate_strip_prefix",
    srcs = [":migrate_strip_prefix.py"],
    deps = [requirement("libcst")],
)

compile_pip_requirements(
    name = "requirements",
    requirements_in = "migration_deps.txt",
    requirements_txt = "migration_deps_lock.txt",
)
