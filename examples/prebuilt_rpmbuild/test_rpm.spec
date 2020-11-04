Name: example
Version: 0
Release: 1
Summary: Example .spec file
License: Apache License, v2.0

# Do not try to use magic to determine file types
%define __spec_install_post %{nil}
# Do not die becuse we give it more input files than are in the files section
%define _unpackaged_files_terminate_build 0

%description
This is a package description.

%build

%install
cp WORKSPACE BUILD readme.md test_rpm.spec %{buildroot}/

%files
/WORKSPACE
/BUILD
/readme.md
/test_rpm.spec
