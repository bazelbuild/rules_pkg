#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail

# Passed as argument when invoking the script.
TAG="${1}"

case "${TAG}" in
  [0-9]* )
    # This is the rules_pkg main release.
    VERSION="${TAG:1}"
    PREFIX="rules_pkg-${TAG:1}"
    ARCHIVE="rules_pkg-$TAG.tar.gz"

    cd ../../
    bazel build distro:relnotes
    cat bazel-bin/distro/relnotes.txt
    exit 0
    ;;
  * )
    ;;
esac

# otherwise, it is the providers, or some future sub module
VERSION=$(echo "$TAG" | sed -e 's/^.*-//')
MODULE=$(echo "$TAG" | sed -e 's/-[0-9]*.*$//')
PREFIX="${TAG}"
ARCHIVE="${TAG}.tgz"

(cd $MODULE ; git archive --format=tgz head . ) > $ARCHIVE
SHA=$(shasum -a 256 $ARCHIVE | awk '{print $1}')

cat << EOF

\`\`\`starlark
bazel_dep(name = "${MODULE}", version = "${VERSION}")
\`\`\`

or

\`\`\`starlark
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
http_archive(
    name = "${MODULE}",
    sha256 = "${SHA}",
    url = "https://github.com/bazelbuild/rules-pkg/releases/download/${TAG}/${ARCHIVE}",
)
\`\`\`
EOF
exit 0
