# Automatically update deb_package rules in the WORKSPACE file
Similar to the `gazelle` tool which helps with managing golang bazel rules, it is possible to run this helper program by running `bazel run update_deb_packages`.

Add the following to the `BUILD` or `BUILD.bazel` file in the root directory of your repository:

```bzl
load("@rules_pkg//deb_packages/tools/update_deb_packages:update_deb_packages.bzl", "update_deb_packages")

update_deb_packages(
    name = "update_deb_packages",
    pgp_keys = ["@rule_name_of_http_file_rule_of_pgp_key//file"],
)
```

The `pgp_keys` list must contain all `http_file` rules that are used in the `pgp_key` portion of the `deb_packages` rules in your `WORKSPACE` file.
Referring to them is necessary, since otherwise these files wouldn't actually be downloaded by Bazel before executing the tool.

This repository also contains the `gazelle` boilerplate in the root `BUILD` file, since the `update_deb_packages` tool is written in go and gazelle helps with automatically generating `BUILD` files for the tool's dependencies.

Then you can run `bazel run update_deb_packages` and it will automatically add missing packages and update hashes and paths of the new and existing ones in your `WORKSPACE` file.

## Dependencies

`update_deb_packages` uses the `buildifier` and `buildozer` tools from [https://github.com/bazelbuild/buildtools](https://github.com/bazelbuild/buildtools) need to be available on your $PATH.

## Pinning versions of deb files

Version pinning (`foo=1.2.3-4` instead of just `foo` as package name) is supported, to have more fine grained control of which package ends up in which container.
It is the user's responsibility to ensure that all versions are available at the mirror.
In case you always want to have access to the latest version (e.g. for canary style builds), `foo=latest` is also supported.

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

## Behind the scenes

This rule works very similar to the [gazelle](https://github.com/bazelbuild/rules_go/blob/master/go/private/tools/gazelle.bzl) rules ([stable link](https://github.com/bazelbuild/rules_go/blob/ee1fef7ec1379fcf36c002fd3ac0d00d940b147e/go/private/tools/gazelle.bzl)) to execute the `gazelle` tool using `bazel run`.

To escape the sandboxing and have direct access to the actual `WORKSPACE` and `BUILD` files, the small shell script resolves the softlink that Bazel creates into the build environment and operates at the root of the actual repository.

This still creates some challenges, as it is also necessary to have access to the PGP keys, which are back in the sandbox.
Moving them to the repository would be an option, but then it would need some reliable cleanup.

Instead, the tool itself uses the fact that the `bazel-<workspacename>` folder is also linked into the repository for convenience and looks for the key in there instead of the sandbox it came from.

As Bazel's sandboxing gets more sophisticated, it might be necessary to reevaluate this approach.
For now it works.
