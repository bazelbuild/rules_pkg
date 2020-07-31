# This package contains extra test data that should not be contained mixed with
# the regular test data.

package(default_visibility = ["//tests:__pkg__"])

genrule(
    name = "generate_files",
    outs = [
        "a",
        "b/c",
        "d/e/f"
    ],
    cmd = "for i in $(OUTS); do echo 1 >$$i; done",
)
