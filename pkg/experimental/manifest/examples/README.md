# Why the examples?

We are not sure how to consturct the manifests at this time to a few reasons.
What comes to mind is:

- `buildifier` -- There is currently no way to tell it [to not
  reformat](https://github.com/bazelbuild/buildtools/issues/890) some regions of
  code, a la `//clang format off/on`.  The main result of this is that all
  whitespace within each of the manifest rows (tuples) is collapsed when
  buildifier is used in any "fixing" mode.

- Readability: column formatting, file formats?  Starlark is a great starting
  point here.

- Maintainability: implementations that don't take direct advantage of
  BUILD-loadable Starlark files appear to require much more code than otherwise.

There may be something we are not aware of, or alternative ideas that we
overlooked. Feedback is greatly appreciated.

# Options explored

1. `dest-first.bzl` where the manifest is a list of
   `(destination, action, attributes, source)` tuples.  This is what is currently implemented.

2. `action-first.bzl` where the manifest is a list of
   `(action, destination, attributes, source)` tuples.

   This is the same as the above, except first two columns are swapped.

3. `action-first-string.bzl` where the manifest is defined as a space-delimited
    string, ordered like in `action-first.bzl`.

Notes on these:

- 1) and 2) require no custom parsing other than the `attributes` column, which
  is a simple delimited string.

- 1) and 2) are subject to `buildifier`, 3) is not.

- 1), however is implemented in the code, because it is highly important that
  the destinations are aligned regardless of overall formatting.

- 3) gives us the most control, but requires writing out a parser.  Depending on
  the complexity of the file format, this could be impractical to maintain.

Overall, if we could teach `buildifier` not to reformat a region, our preferred
option is 2), since it has simple code and is easy to read.

# Options not explored

- Moving the transformation from manifest to `pkg_filegroup` list to a
  repository rule.
  
  Not explored due to perceived inconvenience and scalability concerns in large
  monorepos.
  
- Moving the transformation to some other external utility.
  
  Not explored due to potential implementation costs.  Also prevents direct
  reuse of the `pkg_filegroup` rule.
  
  The main concern with this one is that Bazel is not aware of the contents of
  the manifest, and will have to be provided additional information that need
  not be provided when the manifest is available in Starlark.
