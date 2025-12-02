#!/usr/bin/env bash

set -o pipefail


FILTERS=()
if [[ -n "${TEST_FILTER:-}" ]] ; then
   FILTERS=(--build_tag_filters="${TEST_FILTER}"  --test_tag_filters="${TEST_FILTER}")
fi

echo bazel test "${FILTERS[@]}" -- //tests/... //examples/... -//tests/rpm/...
bazel test "${FILTERS[@]}" -- //tests/... //examples/... -//tests/rpm/... 
exit_code="$?"

if [ "${exit_code}" -ne 0 ] ; then
    exit "${exit_code}"
fi

if [ -n "${BUILD_DISTRO:-}" ] ; then
    bazel build  //distro:distro
    exit_code="$?"
    if [ "${exit_code}" -ne 0 ] ; then
        echo "Could not build //distro:distro"
        exit "${exit_code}"
    fi
fi

exit "${exit_code}"
