#!/usr/bin/env bash

set -o pipefail

bazel build  //distro:distro
exit_code="$?"
if [ "${exit_code}" -ne 0 ] ; then
    exit "${exit_code}"
fi

FILTERS=""
if [[ "${TEST_FILTER:-}" ]] ; then
   FILTERS=(--build_tag_filters="${TEST_FILTER}"  --test_tag_filters="${TEST_FILTER}")
fi

bazel test -- //tests/... //examples/... -//tests/rpm/... "${FILTERS[@]}"
exit_code="$?"
case "${exit_code}" in
  "4")
    # Status code indicates that the build succeeded but there were no tests to
    # run. Ignore and exit successfully.
    exit "0"
    ;;

  *)
    exit "${exit_code}"
    ;;
esac
