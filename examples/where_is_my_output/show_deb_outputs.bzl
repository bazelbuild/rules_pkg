# Extract the paths to the various outputs of pkg_deb
#
# Usage:
#   bazel cquery //:debian --output=starlark --starlark:file=show_deb_outputs.bzl
#

def format(target):
  provider_map = providers(target)
  return '\n'.join([
      'deb: ' + provider_map["OutputGroupInfo"].deb.to_list()[0].path,
      'changes: ' + provider_map["OutputGroupInfo"].changes.to_list()[0].path,
      ])
