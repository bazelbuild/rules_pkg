# **Using the `update_deb_packages` helper program**

As you might have noticed, it is a lot of work to get the exact path and SHA256 hash of a `.deb` package.
All this information is already available online at the mirrors you defined in your WORKSPACE file: As soon as you know the exact distribution, package name and version, you should be able to just generate this data on the fly.

`update_deb_packages` is exactly such a helper program.
It uses the `buildifier` and `buildozer` tools from [https://github.com/bazelbuild/buildtools](https://github.com/bazelbuild/buildtools), which need to be available on your $PATH.

Version pinning (`foo=1.2.3-4` instead of just `foo` as package name) is supported, to have more fine grained control of which package ends up in which container.
It is the user's responsibility to ensure that all versions are available at the mirror.
In case you always want the latest version (e.g. for canary style builds), `foo=latest` is also supported.

## Add and update packages referred in BUILD files to the WORKSPACE file

`buildozer` is able to parse all BUILD files in a repository for `docker_build` rules.
Using this capability, `update_deb_packages` will look through all these rules in the whole repository, check if their `debs` section exists and add all packages that didn't yet occur in the respective `deb_packages` rule.
After this, it'll automatically run the update routine and update all `deb_packages` rules to their configured version on the mirror.

After running the command, the WORKSPACE file will be changed, it is highly recommended to keep this file unter version control to have a good overview on which versions and files have changed.

This tool is intended as an external independent helper script and not to actually run during your bazel builds (it wouldn't really be possible to change the workspace during builds anyways).

## run with `bazel run`

Similar to the `gazelle` tool which helps with managing golang bazel rules, it is possible (and recommended) to run this helper program by running `bazel run update_deb_packages`.

## Ignoring rules

In case you want or need the tool to ignore some `deb_packages` rules in the WORKSPACE file, add a `"manual_update"` tag to the rule in the `tags` default attribute. It will silently drop all rules that have this tag and just ignore whatever they contain.
