# Extract the paths to the various outputs of pkg_deb
#
# Usage:
#   bazel cquery //:debian --output=starlark --starlark:file=show_deb_outputs.bzl
#

def format(target):
    provider_map = providers(target)
    output_group_info = provider_map["OutputGroupInfo"]
    # Look at the attributes of the provider. Visit the depsets.
    ret = []
    for attr in dir(output_group_info):
        if attr.startswith("_"):
            continue
        attr_value = getattr(output_group_info, attr)
        if type(attr_value) == "depset":
            for file in attr_value.to_list():
                ret.append("%s: %s" % (attr, file.path))
    return "\n".join(ret)
