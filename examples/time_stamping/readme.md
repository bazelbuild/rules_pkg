# Examples of how time stamping works.

## How it works

Target declarations may use the `stamp` attribute to control
the time stamping of files in an archive. The behavior follows
the pattern of the cc_binary rule:

https://docs.bazel.build/versions/main/be/c-cpp.html#cc_binary

Read the BUILD file for more details.

## Try this

bazel build :* 
for tarball in bazel-bin/*.tar ; do
  echo ==== $tarball
  tar tvf $tarball
done

bazel build :*  --stamp=1
for tarball in bazel-bin/*.tar ; do
  echo ==== $tarball
  tar tvf $tarball
done
