#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail

# First, check the core providers basically OK.
bazel_cmd=(bazel query :all)
echo "${bazel_cmd[@]}"
( cd providers ; "${bazel_cmd[@]}" )

FILTERS=()
if [[ -n "${TEST_FILTER:-}" ]] ; then
   FILTERS=(--build_tag_filters="${TEST_FILTER}"  --test_tag_filters="${TEST_FILTER}")
fi

TESTS=$(bazel query 'filter(".*_test$", //tests/...)')

bazel_cmd=(bazel test --build_tests_only "${FILTERS[@]}" -- ${TESTS} //examples/... -//tests/rpm/...)

echo "${bazel_cmd[@]}"
"${bazel_cmd[@]}"

if [ -n "${BUILD_DISTRO:-}" ] ; then
    bazel build  //distro:distro
fi
