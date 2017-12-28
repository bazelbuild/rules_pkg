# Copyright 2017 mgIT GmbH All rights reserved.
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

_script_content = """
BASE=$(pwd)
WORKSPACE=$(dirname $(readlink WORKSPACE))
cd "$WORKSPACE"
$BASE/{update_deb_packages} {args} $@
"""

def _update_deb_packages_script_impl(ctx):
  args = ctx.attr.args
  script_content = _script_content.format(update_deb_packages=ctx.file._update_deb_packages.short_path, args=" ".join(args))
  script_file = ctx.new_file(ctx.label.name+".bash")
  ctx.file_action(output=script_file, executable=True, content=script_content)
  return struct(
    files = depset([script_file]),
    runfiles = ctx.runfiles([ctx.file._update_deb_packages])
  )

_update_deb_packages_script = rule(
    _update_deb_packages_script_impl,
    attrs = {
        "args": attr.string_list(),
        "pgp_keys": attr.label_list(),
        "_update_deb_packages": attr.label(
            default = Label("@rules_pkg//tools/update_deb_packages/src:update_deb_packages"),
            allow_single_file = True,
            executable = True,
            cfg = "host",
        ),
    },
)

def update_deb_packages(name, pgp_keys, **kwargs):
  script_name = name+"_script"
  _update_deb_packages_script(
      name = script_name,
      tags = ["manual"],
      **kwargs
  )
  native.sh_binary(
      name = name,
      srcs = [script_name],
      data = ["//:WORKSPACE"] + pgp_keys,
      tags = ["manual"],
  )
