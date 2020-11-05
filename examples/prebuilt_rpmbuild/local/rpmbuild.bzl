# You can not call register toolchains directly from WORKSPACE, so you need
# a wrapper function to do that for you
def register_my_rpmbuild_toolchain():
    native.register_toolchains("//local:local_rpmbuild")
