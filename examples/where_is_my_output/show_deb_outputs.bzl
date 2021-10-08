# Extract the paths to the various outputs of pkg_deb
#
# Usage:
#   bazel cquery //:debian --output=starlark --starlark:file=show_deb_outputs.bzl
#

def format(target):
  provider_map = providers(target)
  output_group_info = provider_map["OutputGroupInfo"]
  # Extract the depset of files for the .deb output and return the first
  deb_file = output_group_info.deb.to_list()[0]
  # Do the same for the changes file.
  changes_file = output_group_info.deb.to_list()[0]
  # Return a nicely formatted string showing their paths
  return '\n'.join([
      'deb: ' + deb_file.path,
      'changes: ' + changes_file.path,
      ])
