#!/usr/bin/env python3

import argparse
import pathlib
import os
import sys

import libcst as cst
import libcst.codemod as codemod
import libcst.matchers as cstm

REPOSITORY_NAME = None

class PkgFilesStripPrefixTransformer(cstm.MatcherDecoratableTransformer):
    METADATA_DEPENDENCIES = (cst.metadata.PositionProvider,)

    def __init__(self):
        super().__init__()
        self.load_node = None
        self.may_need_to_amend_load = None

    @cstm.call_if_inside(cstm.Call(func = cstm.Name("pkg_files")))
    @cstm.leave(cstm.Arg(keyword = cstm.Name("strip_prefix")))
    def rename_strip_prefix_to_local_strip_prefix(self,
                                                  original_node: cst.Arg,
                                                  updated_node: cst.Arg) -> cst.Arg:
        return updated_node.with_changes(keyword = cst.Name("local_strip_prefix"))


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
            cstm.Arg(keyword=cstm.Name('local_strip_prefix'))
        ))],
    ))
    @cstm.leave(cstm.Arg(keyword = cstm.Name("srcs")))
    def strip_prefix_account_for_new_default(self,
                                             original_node: cst.Arg,
                                             updated_node: cst.Arg) -> cst.Arg:
        new_node = updated_node.with_changes(
            keyword = cst.Name("local_strip_prefix"),
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
    # evaluated at runtime (so we can get the real value of REPOSITORY_NAME)
    @cstm.leave(
        cstm.Call(
            func=cstm.Name("load"),
            args=[
                cstm.OneOf(
                    cstm.Arg(value=cstm.SimpleString('"//pkg:mappings.bzl"'.format(REPOSITORY_NAME))),
                    #cstm.Arg(value=cstm.SimpleString('"{}//:mappings.bzl"'.format(REPOSITORY_NAME))),
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

        ## Get the args in the original call.  Needs to be made a list because
        ## we'll be changing it later.
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
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--in-place', action='store_true', default=False)
    parser.add_argument('-d', '--diff', action='store_true', default=False)
    parser.add_argument('-n', '--rules_pkg_repo_name', action='store', default='rules_pkg')
    parser.add_argument("paths", nargs='+', type=pathlib.Path, action='store')

    args = parser.parse_args(argv)

    # We don't need to have many of these when matching on the `load` labels,
    # else we would have to do something like
    # https://stackoverflow.com/q/11731136, which is a bit complex
    global REPOSITORY_NAME
    REPOSITORY_NAME = '@' + args.rules_pkg_repo_name if args.rules_pkg_repo_name != '' else ''
    
    cwd = pathlib.Path(os.environ["BUILD_WORKING_DIRECTORY"])

    for p in args.paths:
        real_p = p
        if not p.is_absolute():
            real_p = cwd / p
        if p.is_dir():
            # We're trying to modify a file in here -- it's called "BUILD.bazel"
            p /= "BUILD"
            real_p /= "BUILD"


        text = real_p.open().read()
        source_tree = cst.parse_module(text)
        wrapper = cst.metadata.MetadataWrapper(source_tree)
        transformer = PkgFilesStripPrefixTransformer()

        new_code = wrapper.visit(transformer)
        if args.in_place:
            if real_p == p:
                print(f'Working on {p}')
            else:
                print(f'Working on {p} (AKA {real_p})')
            code = new_code.code
            with real_p.open('w') as fh:
                fh.write(code)
        elif args.diff:
            print(codemod.diff_code(text, new_code.code, context=5, filename = str(p)))
        else:
            print(new_code.code)

if __name__ == '__main__':
    exit(main(sys.argv[1:]))
