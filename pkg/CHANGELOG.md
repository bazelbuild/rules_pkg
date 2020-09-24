# Release 0.2.6

**New Features**

-   Author: aiuto <aiuto@google.com>
    Date:   Mon Apr 27 15:47:20 2020 -0400
    Add support to generate stardoc. (#164)
    This is done in a manner so there is no new runtime dependency on bazel-skylib. The bzl_library needed as input to stardoc is only created within the distro directory, which is not part of the released package.
-   commit eea3f696ca3187897ddc3eb07d9955384809a84c

-   Merge: 0761c40 b4c4a91
    Author: Daniel Sullivan <danielalexandersullivan@gmail.com>
    Date:   Fri Apr 24 11:02:10 2020 -0400
    Merge pull request #162 from aiuto/lic
    remove useless BUILD file.  update readme
-   commit b4c4a91dc36a53bb5e9e1fc42c91f351d782a7ed

-   Author: Tony Aiuto <aiuto@google.com>
    Date:   Thu Apr 23 23:53:56 2020 -0400
    remove useless BUILD file.  update readme
-   commit 0761c40f7f1d265ebd814a11eaa03e327271ae5c

-   Author: Daniel Sullivan <danielalexandersullivan@gmail.com>
    Date:   Mon Apr 20 21:15:27 2020 -0400
    Preserve mtimes from input tar files in TarFileWriter output tars (#155)
    * Preserve mtimes from input tar files in TarFileWriter output tars
    * Provide option for overriding input tar mtimes in TarFileWriter
    * Correctly set test fixture paths in archive test
-   commit 787f41777355ff2c0669e1a5a8771380d8752fa3

-   Author: Matt Mikitka <2027417+mmikitka@users.noreply.github.com>
    Date:   Fri Apr 17 12:31:15 2020 -0400
    Changed the buildroot from BUILD to BUILDROOT (#108)
    * Changed the buildroot from BUILD to BUILDROOT
    * Install files in the RPM spec before the %files section
-   commit ce53425bc5449268ade670346bc39d8c52b1f822

-   Author: Andrew Psaltis <apsaltis@vmware.com>
    Date:   Wed Apr 15 18:22:22 2020 -0400
    Add prototype pkgfilegroup-based RPM builder (#129)
    This change provides a prototype `pkgfilegroup`-based RPM builder in the form of
    the `gen_rpm` rule.  See #128 for more details on `pkgfilegroup`.
    The RPM generator was derived from `make_rpm.py` in `pkg/` and supports a number
    of features over and above what's available in `pkg_rpm`.  As written, it, given
    a template like the one provided, you can construct many full-fledged RPM
    packages entirely within Bazel.  In most cases, the templates will only need to
    be customized with advanced logic and other macros that are not settable via
    bazel itself; `gen_rpm` will write much of the preamble, `%description` text,
    `%install` scriptlets, and `%files` based on rule-provided inputs.
    Documentation outside of the source files is not yet available.  This was
    empirically tested on RPM packages internal to VMware with positive results;
    actual tests of the rules are not yet ready.
    This, naturally, is incomplete, and is missing capabilities such as:
    - Configurable compression
    - Configurable Provides/Requires
    - SRPM emission
    - Reproducibility
    - Configurable stripping
    - Configurable construction of "debug" packages
    Co-authored-by: mzeren-vmw <mzeren@vmware.com>
    Co-authored-by: klash <klash@vmware.com>
    Co-authored-by: mzeren-vmw <mzeren@vmware.com>
    Co-authored-by: klash <klash@vmware.com>
-   commit 79eafadca7b4fdb675b1cfa40b2ac20f23139271

-   Author: Matthias Frei <matthias.frei@inf.ethz.ch>
    Date:   Tue Apr 7 03:27:05 2020 +0200
    make_deb: fix length computation for extrafiles (#144)
    * make_deb: fix length computation for extrafiles
    Analogous to the handling of the main control file.
    * Add test for genrule-preinst with non-ascii chars
    * Fix tests

# Release 0.2.5

**New Features**

commit 48001d12e7037b04dc5b28fadfb1e10a8447e2fc
    Author: aiuto <aiuto@google.com>
    Date:   Thu Mar 12 15:14:32 2020 -0400

    Depend on rules_python (#140)
    
    * load rules python
    
    * add workspace deps
    
    * add missing loads

commit 2b375a08bfe36d2c35885a6f4e5b12d7898c9426
    Author: Ryan Beasley <39353016+beasleyr-vmw@users.noreply.github.com>
    Date:   Wed Mar 11 14:49:21 2020 -0400

    Update test data in response to #121 (#137)
    
    PR #121 changed pkg_deb's behavior but didn't update test data to match.
    
    Reported in PR #132.
    
    Testing Done:
    - `bazelisk test ...`

commit e5919f43791b2d4c5ab9e68786087cf889b9987e
    Author: Andrew Psaltis <ampsaltis@gmail.com>
    Date:   Fri Feb 28 01:22:37 2020 -0500

    Add pkgfilegroup for package-independent destination mappings (#128)
    
    * Add pkgfilegroup for package-independent destination mappings
    
    This adds an experimental rule, `pkgfilegroup`, along with associated Providers,
    that gives rule developers and users a consistent mechanism for using the output
    of bazel targets in packaging rules.
    
    Inspired by #36.
    
    Other capabilities that are provided by this that were not mentioned in #36 are:
    
    - Creation of empty directories (`pkg_mkdirs`)
    - Exclusion of files from a `pkgfilegroup` (`excludes`)
    - Renames of files in a `pkgfilegroup` (`renames`)
    
    * Add analysis tests for pkgfilegroup and friends
    
    This provides some analysis tests for various features of `pkgfilegroup` and
    `pkg_mkdirs`.  See #128.
    
    You can run them by invoking `bazel test experimental/...` from the `pkg`
    directory
    
    This implementation of pkgfilegroup was inspired by #36.

commit 7a991dea418ab17c7e86f0a7b5e7d4a87ef4304b
    Author: Ryan Beasley <39353016+beasleyr-vmw@users.noreply.github.com>
    Date:   Fri Feb 28 01:02:24 2020 -0500

    Improve handling of sources from external repositories (#132)
    
    Avoid use of [`File.short_path`][1] when mapping filenames, because when
    creating archives from files imported from external repositories we'll create
    archive members with leading `./../` prefixes.  Instead, we'll stick to stripping
    to leading `File.root.path` (if present) from `File.path`, resulting in archive
    members like `external/repo/package/file.txt`.
    
    [1]: https://docs.bazel.build/versions/master/skylark/lib/File.html#short_path
    
    Resolves #131.

commit 532f2857e712c5fcb71c662d680108685b242251
    Author: zoidbergwill <zoidbergwill@gmail.com>
    Date:   Fri Feb 28 06:56:05 2020 +0100

    Update pkg.bzl (#125)

commit 5877fa85b8598b5bb2186d3addca2408b1e61c5e
    Author: Matt Mikitka <2027417+mmikitka@users.noreply.github.com>
    Date:   Fri Feb 28 05:49:40 2020 +0000

    Rpm source date epoch (#113)
    
    * Added --source_date_epoch
    * Support source_date_epoch_file since stamp variables are not accessible
    * Fixed _make_rpm label
    * Revert default make_rpm label
    * Default source_date_epoch to None and remove os.environ

commit acc1ca9095e60bb9acd9858bc1812bfd805136df
    Author: Trevor Hickey <TrevorJamesHickey@gmail.com>
    Date:   Mon Feb 24 09:53:55 2020 -0500

    update WORKSPACE example (#124)

commit 2f5c9815a7bde4f18acfde268bd63fedd107d87c
    Author: andreas-0815-qwertz <57450822+andreas-0815-qwertz@users.noreply.github.com>
    Date:   Wed Dec 4 22:32:01 2019 +0100

    Add "./" prefix to files in control.tar (#121)
    
    This improves compatibility to Debian packages created using dpkg.
    
    https://github.com/bazelbuild/rules_pkg/issues/116

commit 2f09779667f0d6644c2ca5914d6113a82666ec63
    Author: Benjamin Peterson <benjamin@python.org>
    Date:   Fri Nov 15 10:09:45 2019 -0800

    pkg_deb: Support Breaks and Replaces. (#117)
    
    https://www.debian.org/doc/debian-policy/ch-relationships.html#overwriting-files-and-replacing-packages-replaces

commit 9192d3b3a0f6ccfdecdc66f08f0b2664fa0afc0f
   Author: Tony Aiuto <aiuto@google.com>
   Date:   Fri Oct 4 16:33:47 2019 -0400

    Fix repo names with '-' in them.
    
    We can not use the form "@repo-name" in Bazel, so the common solution is
    to transform that to "@repo_name". We auto-correct the repo names to the
    required form when printing the WORKSPACE stanza.
