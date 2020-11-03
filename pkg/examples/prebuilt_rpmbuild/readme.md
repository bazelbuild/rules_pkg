# Using a prebuilt rpmbuild instead of the system one.

## To use

```
cp /usr/bin/rpmbuild local/rpmbuild_binary
bazel build :test-rpm
rpm2cpio bazel-bin/test-rpm.rpm | cpio -ivt
```
