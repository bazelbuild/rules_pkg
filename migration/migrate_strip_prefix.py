#!/usr/bin/env python3

import argparse
import pathlib
import os
import sys

import libcst as cst
import libcst.codemod as codemod
import libcst.matchers as cstm

class PkgFilesStripPrefixTransformer(cstm.MatcherDecoratableTransformer):
    METADATA_DEPENDENCIES = (cst.metadata.PositionProvider,)
    @cstm.call_if_inside(cstm.Call(
        func = cstm.Name("pkg_files")
    ))
    @cstm.leave(cstm.Arg(keyword = cstm.Name("strip_prefix")))
    def rename_strip_prefix_to_local_strip_prefix(self,
                                                  original_node: cst.Arg,
                                                  updated_node: cst.Arg) -> cst.Arg:
        #print(self.metadata)
        # pos = self.get_metadata(cst.metadata.PositionProvider, original_node).start
        # print(dir(self.get_metadata(cst.metadata.PositionProvider, original_node).start))
        # print(f"{updated_node.keyword.value} found at line {pos.line}, column {pos.column}")
        return updated_node.with_changes(keyword = cst.Name("local_strip_prefix"))

    @cstm.call_if_inside(cstm.Call(
        func = cstm.Name("pkg_files")
        args = ~(cstm.Arg(cstm.keyword('strip_prefix')))
    ))
    @cstm.leave(cstm.Call(
        func = cstm.Name("pkg_files")
    ))
    def strip_prefix_account_for_new_default(self,
                                             original_node: cst.Arg,
                                             updated_node: cst.Arg) -> cst.Arg:
        print('empty node')
        return updated_node

    @cstm.call_if_inside(cstm.Call(
        func = cstm.Attribute(value = cstm.Name("strip_prefix"))
    ))
    @cstm.leave(cstm.Attribute(value = cstm.Name("strip_prefix")))
    def rename_strip_prefix_files_only_to_flatten(self,
                                                  original_node: cst.Attribute,
                                                  updated_node: cst.Attribute) -> cst.Attribute:
        return updated_node.with_changes(
            attr = cst.Name('flatten') if updated_node.attr.value == 'files_only' else updated_node.attr
        )

    # @cstm.call_if_inside(cstm.Call(
    #     func = cstm.Name("pkg_files")
    # ))
    # @cstm.leave(cstm.Call(func = cstm.Name("pkg_files")))
    # def yeah_whatever(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
    #     print(updated_node.args)
    #     return updated_node
    
def main(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--in-place', action='store_true', default=False)
    parser.add_argument('-d', '--diff', action='store_true', default=False)
    parser.add_argument("paths", nargs='+', type=pathlib.Path, action='store')

    args = parser.parse_args(argv)

    cwd = pathlib.Path(os.environ["BUILD_WORKING_DIRECTORY"])

    for p in args.paths:
        real_p = p
        if not p.is_absolute():
            real_p = cwd / p
        if p.is_dir():
            # We're trying to modify a file in here -- it's called "BUILD.bazel"
            p /= "BUILD"
            real_p /= "BUILD"

        if real_p == p:
            print(f'Working on {p}')
        else:
            print(f'Working on {p} (AKA {real_p})')

        text = real_p.open().read()
        source_tree = cst.parse_module(text)
        wrapper = cst.metadata.MetadataWrapper(source_tree)
        transformer = PkgFilesStripPrefixTransformer()

        new_code = wrapper.visit(transformer)
        if args.in_place:
            code = new_code.code
            with real_p.open('w') as fh:
                fh.write(code)
        elif args.diff:
            print(codemod.diff_code(text, new_code.code, context=5, filename = str(p)))
        else:
            print(new_code.code)

if __name__ == '__main__':
    exit(main(sys.argv[1:]))
