# Copyright 2021 The Bazel Authors. All rights reserved.
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
"""Internal utilities for rules_pkg."""

load(":providers.bzl", "PackageVariablesInfo")

def setup_output_files(ctx, package_file_name = None):
    """Handle processing of out and package_file_name.

    By default, output is to the "out" attribute. If package_file_name is
    given, we will write to that name instead, and out will be a symlink to it.

    Callers should:
       - write to ouput_file
       - add outputs to their returned DefaultInfo(files) provider
       - return a PackageArtifactInfo provider of the form:
            label: ctx.label.name
            file_name: output_name

    Args:
      ctx: context
      package_file_name: computed value for package_file_name

    Returns:
      ouputs: list(output handles)
      output_file: file handle to write to
      output_name: name of output file
    """
    outputs = [ctx.outputs.out]
    if not package_file_name:
        package_file_name = ctx.attr.package_file_name
    if package_file_name:
        output_name = substitute_package_variables(ctx, package_file_name)
        output_file = ctx.actions.declare_file(output_name)
        outputs.append(output_file)
        ctx.actions.symlink(
            output = ctx.outputs.out,
            target_file = output_file,
        )
    else:
        output_file = ctx.outputs.out
        output_name = ctx.outputs.out.basename
    return outputs, output_file, output_name

def substitute_package_variables(ctx, attribute_value):
    """Substitute package_variables in the attribute with the given name.

    Args:
      ctx: context
      attribute_value: the name of the attribute to perform package_variables substitution for

    Returns:
      expanded_attribute_value: new value of the attribute after package_variables substitution
    """
    if not attribute_value:
        return attribute_value

    if type(attribute_value) != "string":
        fail("attempt to substitute package_variables in the attribute value %s which is not a string" % attribute_value)

    if not ctx.attr.package_variables:
        # Nothing to substitute. Return the attribute value as is.
        if attribute_value.find("{") >= 0:
            fail("package_variables is required when using '{' in attribute value %s" % attribute_value)
        return attribute_value

    package_variables = ctx.attr.package_variables[PackageVariablesInfo]
    return attribute_value.format(**package_variables.values)
