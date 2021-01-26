# This test simply checks that when we create packages with package_file_name
# that we get the expected file names.
set -e

declare -r DATA_DIR="${TEST_SRCDIR}/rules_pkg/tests"

for pkg in test_naming_some_value.deb test_naming_some_value.tar test_naming_some_value.zip ; do
  ls -l "${DATA_DIR}/$pkg"
done
echo "PASS"
