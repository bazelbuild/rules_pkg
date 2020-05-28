package(default_visibility = ["//visibility:public"])

# Extracting the ca-certificates deb package
sh_binary(
    name = "extract_certs",
    srcs = ["extract.sh"],
)

# For convenience, rename busybox-x86_64 to busybox.
# TODO: https://github.com/GoogleCloudPlatform/distroless/pull/119
genrule(
    name = "busybox_tar",
    srcs = ["@busybox//file"],
    outs = ["busybox.tar"],
    cmd = "mkdir busybox; cp $(<) busybox/busybox; cd busybox; \
           for cmd in $$(./busybox --list); do \
             ln -s busybox $$cmd; \
           done; \
           cd ..; \
           tar -cf $@ busybox",
)

load("@io_bazel_rules_docker//docker:docker.bzl", "docker_build")
load("@io_bazel_rules_docker//contrib:passwd.bzl", "passwd_file")
load("@bazel_tools//tools/build_defs/pkg:pkg.bzl", "pkg_tar")
load("@runtimes_common//structure_tests:tests.bzl", "structure_test")
load("@io_bazel_rules_go//go:def.bzl", "go_binary")

# Create a default passwd_file rule and put it in a tarball.

passwd_file(
    name = "passwd",
    gid = 0,
    info = "root",
    uid = 0,
    username = "root",
)

pkg_tar(
    name = "passwd_tar",
    srcs = [":passwd"],
    mode = "0644",
    package_dir = "etc",
)

load("//examples/deb_packages/deb_packages_base:cacerts.bzl", "cacerts")
load("@debian_jessie_amd64//debs:deb_packages.bzl", "debian_jessie_amd64")
load("@debian_stretch_amd64//debs:deb_packages.bzl", "debian_stretch_amd64")

cacerts(
    name = "cacerts_jessie",
    deb = debian_jessie_amd64["ca-certificates"],
)

cacerts(
    name = "cacerts_stretch",
    deb = debian_stretch_amd64["ca-certificates"],
)

# Create /tmp, too many things assume it exists.
# tmp.tar has a /tmp with the correct permissions 01777
# A tar is needed because at the moment there is no way to create an empty directory with specific permissions

docker_build(
    name = "base_jessie",
    debs = [
        debian_jessie_amd64["libc6"],
        debian_jessie_amd64["libssl1.0.0"],
        debian_jessie_amd64["openssl"],
        debian_jessie_amd64["netbase"],
        debian_jessie_amd64["tzdata"],
    ],
    env = {"PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"},
    tars = [
        ":passwd_tar",
        ":cacerts_jessie.tar",
        ":tmp.tar",
        # os-release files are not (yet) implemented in deb_packages
        #"@debian_jessie//file:os_release.tar",
    ],
)

docker_build(
    name = "base_stretch",
    debs = [
        debian_stretch_amd64["libc6"],
        debian_stretch_amd64["libssl1.0.2"],
        debian_stretch_amd64["openssl"],
        debian_stretch_amd64["netbase"],
        debian_stretch_amd64["tzdata"],
    ],
    env = {"PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"},
    tars = [
        ":passwd_tar",
        ":cacerts_stretch.tar",
        ":tmp.tar",
        # os-release files are not (yet) implemented in deb_packages
        #"@debian_stretch//file:os_release.tar",
    ],
)

# A debug image with busybox available.
docker_build(
    name = "debug_jessie",
    base = ":base_jessie",
    directory = "/",
    entrypoint = ["/busybox/sh"],
    env = {"PATH": "$PATH:/busybox"},
    tars = [":busybox_tar"],
)

docker_build(
    name = "debug_stretch",
    base = ":base_stretch",
    directory = "/",
    entrypoint = ["/busybox/sh"],
    env = {"PATH": "$PATH:/busybox"},
    tars = [":busybox_tar"],
)

structure_test(
    name = "debug_jessie_test",
    config = "testdata/debug.yaml",
    image = ":debug_jessie",
)

structure_test(
    name = "debug_stretch_test",
    config = "testdata/debug.yaml",
    image = ":debug_stretch",
)

structure_test(
    name = "base_jessie_test",
    config = "testdata/base.yaml",
    image = ":base_jessie",
)

structure_test(
    name = "base_stretch_test",
    config = "testdata/base.yaml",
    image = ":base_stretch",
)

go_binary(
    name = "check_certs",
    srcs = ["testdata/check_certs.go"],
)

docker_build(
    name = "check_certs_jessie_image",
    base = "//examples/deb_packages/deb_packages_base:base_jessie",
    files = [":check_certs"],
    visibility = ["//visibility:private"],
)

docker_build(
    name = "check_certs_stretch_image",
    base = "//examples/deb_packages/deb_packages_base:base_stretch",
    files = [":check_certs"],
    visibility = ["//visibility:private"],
)

structure_test(
    name = "certs_jessie_test",
    config = "testdata/certs.yaml",
    image = ":check_certs_jessie_image",
)

structure_test(
    name = "certs_stretch_test",
    config = "testdata/certs.yaml",
    image = ":check_certs_stretch_image",
)
