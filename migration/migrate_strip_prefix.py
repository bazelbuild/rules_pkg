#!/usr/bin/env python3

# Copyright 2023 The Bazel Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import pathlib
import os
import sys

import libcst as cst
import libcst.codemod as codemod
import libcst.matchers as cstm

class PkgFilesStripPrefixTransformer(codemod.ContextAwareTransformer):
    def __init__(self, context):
        super().__init__(context)
        self.load_node = None
        self.may_need_to_amend_load = None

    @cstm.call_if_inside(cstm.Call(func = cstm.Name("pkg_files")))
    @cstm.leave(cstm.Arg(keyword = cstm.Name("strip_prefix")))
    def rename_strip_prefix_to_srcs_strip_prefix(self,
                                                  original_node: cst.Arg,
                                                  updated_node: cst.Arg) -> cst.Arg:
        return updated_node.with_changes(keyword = cst.Name("srcs_strip_prefix"))


    @cstm.call_if_inside(cstm.Call(func = cstm.Attribute(value = cstm.Name("strip_prefix"))))
    @cstm.leave(cstm.Attribute(value = cstm.Name("strip_prefix")))
    def rename_strip_prefix_files_only_to_flatten(self,
                                                  original_node: cst.Attribute,
                                                  updated_node: cst.Attribute) -> cst.Attribute:
        return updated_node.with_changes(
            attr = cst.Name('flatten') if updated_node.attr.value == 'files_only' else updated_node.attr
        )

    @cstm.call_if_inside(cstm.Call(
        func = cstm.Name("pkg_files"),
        args = [cstm.ZeroOrMore(~cstm.OneOf(
            cstm.Arg(keyword=cstm.Name('strip_prefix')),
            # Be idempotent
            cstm.Arg(keyword=cstm.Name('srcs_strip_prefix'))
        ))],
    ))
    @cstm.leave(cstm.Arg(keyword = cstm.Name("srcs")))
    def strip_prefix_account_for_new_default(self,
                                             original_node: cst.Arg,
                                             updated_node: cst.Arg) -> cst.Arg:
        new_node = updated_node.with_changes(
            keyword = cst.Name("srcs_strip_prefix"),
            value = cst.Call(
                func = cst.Attribute(
                    value = cst.Name("strip_prefix"),
                    attr = cst.Name("flatten"),
                )
            )
        )
        may_need_to_amend_load = True
        return cst.FlattenSentinel([
            updated_node,
            new_node,
        ])

    # FIXME: need to incorporate a hack to allow the decorator's contents to be
    # evaluated at runtime so we can name the rules_pkg repository as a CLI
    # argument.  Perhaps one like https://stackoverflow.com/q/11731136, which is
    # a bit complex.
    @cstm.leave(
        cstm.Call(
            func=cstm.Name("load"),
            args=[
                cstm.OneOf(
                    cstm.Arg(value=cstm.SimpleString('"//:mappings.bzl"')),
                    cstm.Arg(value=cstm.SimpleString('"//pkg:mappings.bzl"')),
                    cstm.Arg(value=cstm.SimpleString('"@rules_pkg//:mappings.bzl"')),
                    cstm.Arg(value=cstm.SimpleString('"@rules_pkg//pkg:mappings.bzl"')),
                ),
                cstm.ZeroOrMore(~cstm.Arg(value=cstm.SimpleString('"strip_prefix"')))
            ],
        )
    )
    def find_eligible_rules_pkg_node(self,
                                     original_node: cst.Call,
                                     updated_node: cst.Call) -> cst.Call:
        self.load_node = updated_node
        return updated_node

    def leave_Module(self,
                     original_node: cst.Module,
                     updated_node: cst.Module) -> cst.Module:
        if self.load_node is None or self.may_need_to_amend_load == False:
            # Nothing to do
            return updated_node

        # This is somewhat convoluted, but it works.  I guess.

        # Get the args in the original call.  Needs to be made a list because
        # we'll be changing it later.
        args = list(self.load_node.args)

        ## Figure out where "strip_prefix" will appear in the arg list.

        # If the args list is already sensibly sorted, keep it that way.
        # Else, we will be applying the entry to the end.

        # libcst nodes are not comparable.  Instead derive our own metric to
        # preserve the sort order.
        def arg_value(a):
            if isinstance(a.value, cst.SimpleString):
                # It's a string.  Get the value without the quotes.
                return a.value.value[1:-1]
            else:
                # It's a `name = "string"` arrangement
                return a.value

        # Do that sorting thing.  The label argument (if properly formatted)
        # should come first regardless.
        args_sorted = sorted(args, key=arg_value)

        # Also of note is that libcst objects are only immediately compared by
        # identity.
        is_sorted = args_sorted == args

        if is_sorted:
            new_args = sorted(args_sorted + [
                cst.Arg(
                    value=cst.SimpleString(value='"strip_prefix"')
                )
            ], key = arg_value)
        else:
            # Just stick `strip_prefix` on the back.  They can sort the list
            # again later if they want
            new_args = args + [
                cst.Arg(
                    value=cst.SimpleString(value='"strip_prefix"')
                )]

        ## Given the existing arg list as a template, create the new one.

        # This is largely to keep track of whitespace.  In libcst arg lists,
        # it's associated with the comma at the end of each entry.
            
        # Set aside the first one and the last one.
        starting_arg = args[0]
        final_arg = args[-1]

        # Do the overlaying.  Everything but the last arg is formatted the same
        # way.
        formatted_new_args = [new_args[0]]
        for a in new_args[1:-1]:
            formatted_new_args.append(
                starting_arg.with_changes(
                    value = a.value,
                    keyword = a.keyword,
                )
            )
        formatted_new_args.append(
            final_arg.with_changes(
                value = new_args[-1].value,
                keyword = new_args[-1].keyword,
            )
        )

        new_load_node = self.load_node.with_changes(
            args = formatted_new_args
        )

        return updated_node.deep_replace(
            old_node = self.load_node,
            new_node = new_load_node
        )

def main(argv):
    if os.name == 'nt':
        exit('This script does not support windows.  If this support is desired, please file an issue against rules_pkg.')

    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--diff', action='store_true', default=False)
    parser.add_argument('-q', '--quiet', action='store_true', default=False)
    parser.add_argument("paths", nargs='+', type=pathlib.Path, action='store')

    # TODO(nacl): this doesn't quite work with the decorators (since they're evaluated
    # at compile-time), but we can work around it if that ends up being an issue.
    #parser.add_argument('-n', '--rules_pkg_repo_name', action='store', default='rules_pkg')

    # TODO(nacl): See comment around `jobs` in
    #`codemod.parallel_exec_transform_with_prettyprint()`
    #parser.add_argument('-j', '--jobs', type=int, action='store', default=1)

    args = parser.parse_args(argv)
    
    cwd = pathlib.Path(os.environ["BUILD_WORKING_DIRECTORY"])

    def real_filepath(p):
        real_p = p
        if not real_p.is_absolute():
            real_p = cwd / real_p
        if real_p.is_dir():
            if (real_p / "BUILD").exists():
                return real_p / "BUILD"
            elif (real_p / "BUILD.bazel").exists():
                return real_p / "BUILD.bazel"
            else:
                exit("Directory {} does not contain any valid BUILD files".format(real_p))
        else:
            return real_p
                
    paths = [str(real_filepath(p)) for p in args.paths]

    # Calculate something close to the repo root to placate libcst (which was
    # designed for python)
    if len(paths) == 1:
        repo_root = os.path.dirname(paths[0])
    else:
        repo_root = os.path.commonprefix(paths)
    
    codemod_ctx = codemod.CodemodContext()
    transformer = PkgFilesStripPrefixTransformer(codemod_ctx)

    # NOTE: this can't be interrupted, because the underlying transform
    # execution catches KeyboardInterrupt and
    # parallel_exec_transform_with_prettyprint thinks of it as a "skip".
    print("")
    print("!!! Interrupt with C-\\ !!!")
    print("")

    # NOTE: doesn't work on Windows
    res = codemod.parallel_exec_transform_with_prettyprint(
        transformer,
        paths,
        # TODO(nacl): We cannot parallelize this due to issues pickling some objects
        # in libcst.  File a bug for this.
        jobs = 1, # defaults to None, which means "use all cores"
        unified_diff = args.diff,
        # Otherwise libcst can't calculate module paths and emits (for us)
        # spurious warnings.
        repo_root = repo_root,
        hide_progress = args.quiet,
    )

    print(res)

if __name__ == '__main__':
    exit(main(sys.argv[1:]))
