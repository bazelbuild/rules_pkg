# Using system rpmbuild with bzlmod and stamp = 1

## Summary

Target declarations may use the `stamp` attribute to control the time
stamping of files in an archive. The behavior follows the pattern of
the cc_binary rule:

https://docs.bazel.build/versions/main/be/c-cpp.html#cc_binary

Read the BUILD file for more details.

## To Demonstrate

```
bazel build test-rpm-stamped
# look for the build timestamp in the Release field:
rpm -qip bazel-bin/test-rpm-stamped-1.noarch.rpm
```
