#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail

# Passed as argument when invoking the script.
TAG="${1}"

# Get back to the root
cd ../../

case "${TAG}" in
  [0-9]* )
    # This is the rules_pkg main release.
    VERSION="${TAG:1}"
    PREFIX="rules_pkg-${TAG:1}"
    ARCHIVE="rules_pkg-$TAG.tar.gz"

    bazel build //distro:relnotes
    cat bazel-bin/distro/relnotes.txt
    exit 0
    ;;
  * )
    ;;
esac

# If we fall to here, we are in a sub-module release

# TODO: We could pass the version as a build time flag. I don't want
# to do that yet, because I want to discuss this with other rule
# authors.
# VERSION=$(echo "$TAG" | sed -e 's/^.*-//')
MODULE=$(echo "$TAG" | sed -e 's/-[0-9]*.*$//')

bazel build //distro:${MODULE}_relnotes
cp bazel-bin/distro/${MODULE}*tgz .
cat bazel-bin/distro/${MODULE}_relnotes.txt
