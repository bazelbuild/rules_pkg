<!-- Generated with Stardoc: http://skydoc.bazel.build -->

<a name="#pkg_deb_impl"></a>

## pkg_deb_impl

<pre>
pkg_deb_impl(<a href="#pkg_deb_impl-name">name</a>, <a href="#pkg_deb_impl-architecture">architecture</a>, <a href="#pkg_deb_impl-architecture_file">architecture_file</a>, <a href="#pkg_deb_impl-breaks">breaks</a>, <a href="#pkg_deb_impl-built_using">built_using</a>, <a href="#pkg_deb_impl-built_using_file">built_using_file</a>,
             <a href="#pkg_deb_impl-conffiles">conffiles</a>, <a href="#pkg_deb_impl-conffiles_file">conffiles_file</a>, <a href="#pkg_deb_impl-config">config</a>, <a href="#pkg_deb_impl-conflicts">conflicts</a>, <a href="#pkg_deb_impl-data">data</a>, <a href="#pkg_deb_impl-depends">depends</a>, <a href="#pkg_deb_impl-depends_file">depends_file</a>, <a href="#pkg_deb_impl-description">description</a>,
             <a href="#pkg_deb_impl-description_file">description_file</a>, <a href="#pkg_deb_impl-distribution">distribution</a>, <a href="#pkg_deb_impl-enhances">enhances</a>, <a href="#pkg_deb_impl-homepage">homepage</a>, <a href="#pkg_deb_impl-maintainer">maintainer</a>, <a href="#pkg_deb_impl-make_deb">make_deb</a>, <a href="#pkg_deb_impl-out">out</a>, <a href="#pkg_deb_impl-package">package</a>,
             <a href="#pkg_deb_impl-package_file_name">package_file_name</a>, <a href="#pkg_deb_impl-package_variables">package_variables</a>, <a href="#pkg_deb_impl-postinst">postinst</a>, <a href="#pkg_deb_impl-postrm">postrm</a>, <a href="#pkg_deb_impl-predepends">predepends</a>, <a href="#pkg_deb_impl-preinst">preinst</a>, <a href="#pkg_deb_impl-prerm">prerm</a>,
             <a href="#pkg_deb_impl-priority">priority</a>, <a href="#pkg_deb_impl-provides">provides</a>, <a href="#pkg_deb_impl-recommends">recommends</a>, <a href="#pkg_deb_impl-replaces">replaces</a>, <a href="#pkg_deb_impl-section">section</a>, <a href="#pkg_deb_impl-suggests">suggests</a>, <a href="#pkg_deb_impl-templates">templates</a>, <a href="#pkg_deb_impl-triggers">triggers</a>,
             <a href="#pkg_deb_impl-urgency">urgency</a>, <a href="#pkg_deb_impl-version">version</a>, <a href="#pkg_deb_impl-version_file">version_file</a>)
</pre>



**ATTRIBUTES**


| Name  | Description | Type | Mandatory | Default |
| :-------------: | :-------------: | :-------------: | :-------------: | :-------------: |
| name |  A unique name for this target.   | <a href="https://bazel.build/docs/build-ref.html#name">Name</a> | required |  |
| architecture |  Package architecture. Must not be used with architecture_file.   | String | optional | "all" |
| architecture_file |  File that contains the package architecture.             Must not be used with architecture.   | <a href="https://bazel.build/docs/build-ref.html#labels">Label</a> | optional | None |
| breaks |  See http://www.debian.org/doc/debian-policy/ch-relationships.html#s-binarydeps.   | List of strings | optional | [] |
| built_using |  -   | String | optional | "" |
| built_using_file |  -   | <a href="https://bazel.build/docs/build-ref.html#labels">Label</a> | optional | None |
| conffiles |  XXX   | List of strings | optional | [] |
| conffiles_file |  XXX   | <a href="https://bazel.build/docs/build-ref.html#labels">Label</a> | optional | None |
| config |  config file used for debconf integration.             See https://www.debian.org/doc/debian-policy/ch-binary.html#prompting-in-maintainer-scripts.   | <a href="https://bazel.build/docs/build-ref.html#labels">Label</a> | optional | None |
| conflicts |  See http://www.debian.org/doc/debian-policy/ch-relationships.html#s-binarydeps.   | List of strings | optional | [] |
| data |  A tar file that contains the data for the debian package.   | <a href="https://bazel.build/docs/build-ref.html#labels">Label</a> | required |  |
| depends |  See http://www.debian.org/doc/debian-policy/ch-relationships.html#s-binarydeps.   | List of strings | optional | [] |
| depends_file |  File that contains a list of package dependencies. Must not be used with <code>depends</code>.             See http://www.debian.org/doc/debian-policy/ch-relationships.html#s-binarydeps.   | <a href="https://bazel.build/docs/build-ref.html#labels">Label</a> | optional | None |
| description |  The package description. Must not be used with <code>description_file</code>.   | String | optional | "" |
| description_file |  The package description. Must not be used with <code>description</code>.   | <a href="https://bazel.build/docs/build-ref.html#labels">Label</a> | optional | None |
| distribution |  XXX   | String | optional | "unstable" |
| enhances |  See http://www.debian.org/doc/debian-policy/ch-relationships.html#s-binarydeps.   | List of strings | optional | [] |
| homepage |  The homepage of the project.   | String | optional | "" |
| maintainer |  The maintainer of the package.   | String | required |  |
| make_deb |  -   | <a href="https://bazel.build/docs/build-ref.html#labels">Label</a> | optional | //private:make_deb |
| out |  -   | <a href="https://bazel.build/docs/build-ref.html#labels">Label</a> | required |  |
| package |  The name of the package   | String | required |  |
| package_file_name |  See Common Attributes   | String | optional | "" |
| package_variables |  See Common Attributes   | <a href="https://bazel.build/docs/build-ref.html#labels">Label</a> | optional | None |
| postinst |  XXX   | <a href="https://bazel.build/docs/build-ref.html#labels">Label</a> | optional | None |
| postrm |  XXX   | <a href="https://bazel.build/docs/build-ref.html#labels">Label</a> | optional | None |
| predepends |  See http://www.debian.org/doc/debian-policy/ch-relationships.html#s-binarydeps.   | List of strings | optional | [] |
| preinst |  XXX   | <a href="https://bazel.build/docs/build-ref.html#labels">Label</a> | optional | None |
| prerm |  XXX   | <a href="https://bazel.build/docs/build-ref.html#labels">Label</a> | optional | None |
| priority |  -   | String | optional | "" |
| provides |  See http://www.debian.org/doc/debian-policy/ch-relationships.html#s-binarydeps.   | List of strings | optional | [] |
| recommends |  See http://www.debian.org/doc/debian-policy/ch-relationships.html#s-binarydeps.   | List of strings | optional | [] |
| replaces |  See http://www.debian.org/doc/debian-policy/ch-relationships.html#s-binarydeps.   | List of strings | optional | [] |
| section |  -   | String | optional | "" |
| suggests |  See http://www.debian.org/doc/debian-policy/ch-relationships.html#s-binarydeps.   | List of strings | optional | [] |
| templates |  XXX   | <a href="https://bazel.build/docs/build-ref.html#labels">Label</a> | optional | None |
| triggers |  XXX   | <a href="https://bazel.build/docs/build-ref.html#labels">Label</a> | optional | None |
| urgency |  XXX   | String | optional | "medium" |
| version |  Package version. Must not be used with <code>version_file</code>.   | String | optional | "" |
| version_file |  File that contains the package version.             Must not be used with <code>version</code>.   | <a href="https://bazel.build/docs/build-ref.html#labels">Label</a> | optional | None |


<a name="#pkg_deb"></a>

## pkg_deb

<pre>
pkg_deb(<a href="#pkg_deb-name">name</a>, <a href="#pkg_deb-archive_name">archive_name</a>, <a href="#pkg_deb-kwargs">kwargs</a>)
</pre>

Creates a deb file. See pkg_deb_impl.

**PARAMETERS**


| Name  | Description | Default Value |
| :-------------: | :-------------: | :-------------: |
| name |  <p align="center"> - </p>   |  none |
| archive_name |  <p align="center"> - </p>   |  <code>None</code> |
| kwargs |  <p align="center"> - </p>   |  none |


