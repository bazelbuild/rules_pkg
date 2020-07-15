# Patch Acceptance Process

1. PRs that change or add behavior are not accepted without being tied to an
   issue.  Most fixes, even if you think they are obvious, require an issue
   too. Almost every change breaks someone who has depended on the behavior,
   even broken behavior.
1. Significant changes need a design document. Please create an issue describing
   the proposed change, and post a link to it to rules-pkg-discuss@googlegroups.com.
   Wait for discussion to come to agreement before proceeding.
1. Prepare a git commit that implements the feature. Don't forget to add tests.
1. Ensure you've signed a [Contributor License
   Agreement](https://cla.developers.google.com).
1. Send us a pull request on
   [GitHub](https://github.com/bazelbuild/rules_pkg/pulls). If you're new to GitHub,
   read [about pull
   requests](https://help.github.com/articles/about-pull-requests/). Note that
   we restrict permissions to create branches on the main repository, so
   you will need to push your commit to [your own fork of the
   repository](https://help.github.com/articles/working-with-forks/).
1. Wait for a repository owner to assign you a reviewer. We strive to do that
   within 4 business days, but it may take longer. If your review gets lost
   you can escalate by sending a mail to
   [bazel-dev@googlegroups.com](mailto:bazel-dev@googlegroups.com).
1. Work with the reviewer to complete a code review. For each change, create a
   new commit and push it to make changes to your pull request.
1. A maintainer will approve the PR and merge it.

For further information about working with Bazel and rules in general:
1. Read the [Bazel governance plan](https://www.bazel.build/governance.html).
1. Read the [contributing to Bazel](https://www.bazel.build/contributing.html) guide.
