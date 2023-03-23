#!/usr/bin/env bash

run_test() {
    echo -n "Inspecting $1..."
    if [[ "$(tar tvf $1 | wc -l)" != 1 ]]; then
        echo "FAIL"
        tar tvf $1
    else
        echo "PASS"
    fi
}

run_test $1
run_test $2