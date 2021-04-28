# vim: ts=2:sw=2:

# Copyright 2017-2020 The Bazel Authors. All rights reserved.
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
"""A simple cross-platform helper to create an RPM package."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import contextlib
import fileinput
import os
import re
import shutil
import subprocess
import sys
import tempfile
from string import Template

from helpers import GetFlagValue

# Setup to safely create a temporary directory and clean it up when done.
@contextlib.contextmanager
def Cd(newdir, cleanup=lambda: True):
  """Change the current working directory.

  This will run the provided cleanup function when the context exits and the
  previous working directory is restored.

  Args:
    newdir: The directory to change to. This must already exist.
    cleanup: An optional cleanup function to be executed when the context exits.

  Yields:
    Nothing.
  """

  prevdir = os.getcwd()
  os.chdir(os.path.expanduser(newdir))
  try:
    yield
  finally:
    os.chdir(prevdir)
    cleanup()


@contextlib.contextmanager
def Tempdir():
  """Create a new temporary directory and change to it.

  The temporary directory will be removed when the context exits.

  Yields:
    The full path of the temporary directory.
  """

  dirpath = tempfile.mkdtemp()

  def Cleanup():
    shutil.rmtree(dirpath)

  with Cd(dirpath, Cleanup):
    yield dirpath


WROTE_FILE_RE = re.compile(r'Wrote: (?P<rpm_path>.+)', re.MULTILINE)


def FindOutputFile(log):
  """Find the written file from the log information."""

  m = WROTE_FILE_RE.search(log)
  if m:
    return m.group('rpm_path')
  return None

def SlurpFile(input_path):
  with open(input_path, 'r') as input:
    return input.read()

def CopyAndRewrite(input_file, output_file, replacements=None):
  """Copies the given file and optionally rewrites with replacements.

  Args:
    input_file: The file to copy.
    output_file: The file to write to.
    replacements: A dictionary of replacements.
      Keys are prefixes scan for, values are the replacements to write after
      the prefix.
  """
  with open(input_file, 'r') as input:
    text = input.read()

  with open(output_file, 'w') as output:
    template = Template(text)
    out_text =  template.safe_substitute(replacements)
    output.write(out_text)

def IsExe(fpath):
  return os.path.isfile(fpath) and os.access(fpath, os.X_OK)


def Which(program):
  """Search for the given program in the PATH.

  Args:
    program: The program to search for.

  Returns:
    The full path to the program.
  """

  for path in os.environ['PATH'].split(os.pathsep):
    filename = os.path.join(path, program)
    if IsExe(filename):
      return filename

  return None


class NoRpmbuildFoundError(Exception):
  pass


class InvalidRpmbuildError(Exception):
  pass


def FindRpmbuild(rpmbuild_path):
  if rpmbuild_path:
    if not IsExe(rpmbuild_path):
      raise InvalidRpmbuildError('{} is not executable'.format(rpmbuild_path))
    return rpmbuild_path
  path = Which('rpmbuild')
  if path:
    return path
  raise NoRpmbuildFoundError()


class RpmBuilder(object):
  """A helper class to manage building the RPM file."""

  SOURCE_DIR = 'SOURCES'
  BUILD_DIR = 'BUILD'
  BUILDROOT_DIR = 'BUILDROOT'
  TEMP_DIR = 'TMP'
  RPMS_DIR = 'RPMS'
  DIRS = [SOURCE_DIR, BUILD_DIR, BUILDROOT_DIR, RPMS_DIR, TEMP_DIR]

  def __init__(self, name, version, release, arch, rpmbuild_path,
               pre_scriptlet_path,
               post_scriptlet_path,
               preun_scriptlet_path,
               postun_scriptlet_path,
               debug=False):
    self.name = name
    self.version = GetFlagValue(version)
    self.release = GetFlagValue(release)
    self.pre_scriptlet = SlurpFile(pre_scriptlet_path) if pre_scriptlet_path is not None else ''
    self.post_scriptlet = SlurpFile(post_scriptlet_path) if post_scriptlet_path is not None else ''
    self.preun_scriptlet = SlurpFile(preun_scriptlet_path) if preun_scriptlet_path is not None else ''
    self.postun_scriptlet = SlurpFile(postun_scriptlet_path) if postun_scriptlet_path is not None else ''
    # TODO(nacl): delete this or properly integrate it into the call to
    # rpmbuild(8).
    self.arch = arch
    self.files = []
    self.rpmbuild_path = FindRpmbuild(rpmbuild_path)
    self.rpm_path = None
    self.debug = debug

  def AddFiles(self, paths, root=''):
    """Add a set of files to the current RPM.

    If an item in paths is a directory, its files are recursively added.

    Args:
      paths: The files to add.
      root: The root of the filesystem to search for files. Defaults to ''.
    """
    for path in paths:
      full_path = os.path.join(root, path)
      if os.path.isdir(full_path):
        self.AddFiles(os.listdir(full_path), full_path)
      else:
        self.files.append(full_path)

  def SetupWorkdir(self,
                   spec_file,
                   preamble_file,
                   description_file,
                   install_script_file,
                   file_list_file,
                   original_dir):
    """Create the needed structure in the workdir."""

    # Create directory structure.
    for name in RpmBuilder.DIRS:
      if not os.path.exists(name):
        os.makedirs(name, 0o777)

    # Copy the files.
    for f in self.files:
      dst_dir = os.path.join(RpmBuilder.BUILD_DIR, os.path.dirname(f))
      if not os.path.exists(dst_dir):
        os.makedirs(dst_dir, 0o777)
      shutil.copy(os.path.join(original_dir, f), dst_dir)

    # Copy the spec file, updating with the correct version.
    spec_origin = os.path.join(original_dir, spec_file)
    self.spec_file = os.path.basename(spec_file)
    replacements = {}
    replacements['PRE_SCRIPTLET'] = "%pre\n" + self.pre_scriptlet
    replacements['POST_SCRIPTLET'] = "%post\n" + self.post_scriptlet
    replacements['PREUN_SCRIPTLET'] = "%preun\n" + self.preun_scriptlet
    replacements['POSTUN_SCRIPTLET'] = "%postun\n" + self.postun_scriptlet
    CopyAndRewrite(spec_origin, self.spec_file, replacements)

    # Copy in the various other files needed to build the RPM
    self.preamble_file = os.path.basename(preamble_file)
    replacements = {}
    if self.version:
      replacements['VERSION_FROM_FILE'] = self.version
    if self.release:
      replacements['RELEASE_FROM_FILE'] = self.release
    CopyAndRewrite(os.path.join(original_dir, preamble_file), self.preamble_file, replacements)

    shutil.copy(os.path.join(original_dir, description_file), os.getcwd())
    self.description_file = os.path.basename(description_file)

    shutil.copy(os.path.join(original_dir, install_script_file), os.getcwd())
    self.install_script_file = os.path.basename(install_script_file)

    shutil.copy(os.path.join(original_dir, file_list_file), RpmBuilder.BUILD_DIR)
    self.file_list_file = os.path.join(RpmBuilder.BUILD_DIR, os.path.basename(file_list_file))

  def CallRpmBuild(self, dirname):
    """Call rpmbuild with the correct arguments."""

    buildroot = os.path.join(dirname, RpmBuilder.BUILDROOT_DIR)
    # For reference, E121 is a hanging indent flake8 issue.  It really wants
    # four space indents, but properly fixing that will require re-indenting the
    # entire file.

    # Further, the use of disabling yapf and friends is to allow argument names
    # to be associated with their values neatly.
    args = [
      self.rpmbuild_path,  # noqa: E121
    ]
    if self.debug:
      args.append('-vv')
    args += [
      '--define', '_topdir %s' % dirname,  # noqa: E121
      '--define', '_tmppath %s/TMP' % dirname,
      '--define', 'build_rpm_install %s' % self.install_script_file,
      '--define', 'build_rpm_options %s' % self.preamble_file,
      '--define', 'build_rpm_description %s' % self.description_file,
      # %files -f is taken relative to the package root
      '--define', 'build_rpm_files %s' % os.path.basename(self.file_list_file),
      '--bb',
      '--buildroot=%s' % buildroot,
    ]  # yapf: disable
    args.append(self.spec_file)

    if self.debug:
      print('Running rpmbuild as: {}'.format(' '.join(args)))

    p = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env={'LANG': 'C'})
    output = p.communicate()[0].decode()

    if p.returncode == 0:
      # Find the created file.
      self.rpm_path = FindOutputFile(output)

    if p.returncode != 0 or not self.rpm_path:
      print('Error calling rpmbuild:')
      print(output)
    elif self.debug:
      print(output)

    # Return the status.
    return p.returncode

  def SaveResult(self, out_file):
    """Save the result RPM out of the temporary working directory."""

    if self.rpm_path:
      shutil.copy(self.rpm_path, out_file)
      if self.debug:
        print('Saved RPM file to %s' % out_file)
    else:
      print('No RPM file created.')

  def Build(self, spec_file,
            preamble_file, description_file,
            install_script_file, file_list_file, out_file):
    """Build the RPM described by the spec_file."""

    if self.debug:
      print('Building RPM for %s at %s' % (self.name, out_file))

    original_dir = os.getcwd()
    spec_file = os.path.join(original_dir, spec_file)
    out_file = os.path.join(original_dir, out_file)
    with Tempdir() as dirname:
      self.SetupWorkdir(spec_file,
                        preamble_file,
                        description_file,
                        install_script_file,
                        file_list_file,
                        original_dir)
      status = self.CallRpmBuild(dirname)
      self.SaveResult(out_file)

    return status


def main(argv):
  parser = argparse.ArgumentParser(
      description='Helper for building rpm packages',
      fromfile_prefix_chars='@')

  parser.add_argument('--name',
                      help='The name of the software being packaged.')
  parser.add_argument('--version',
                      help='The version of the software being packaged.')
  parser.add_argument('--release',
                      help='The release of the software being packaged.')
  # TODO(nacl): This currently doesn't do anything here (or in
  # RpmBuilder); we should allow this to be configured in a way that allows for
  # the RPM spec file to be reusable.
  parser.add_argument(
      '--arch',
      help='The CPU architecture of the software being packaged.')
  parser.add_argument('--spec_file', required=True,
                      help='The file containing the RPM specification.')
  parser.add_argument('--out_file', required=True,
                      help='The destination to save the resulting RPM file to.')
  parser.add_argument('--rpmbuild', help='Path to rpmbuild executable.')
  parser.add_argument('--debug', action='store_true', default=False,
                      help='Print debug messages.')
  parser.add_argument('--install_script', required=True,
                      help='Installer script')
  parser.add_argument('--file_list', required=True,
                      help='File containing a list of files to include with rpm spec %files -f')
  parser.add_argument('--preamble', required=True,
                      help='File containing the RPM Preamble')
  parser.add_argument('--description', required=True,
                      help='File containing the RPM %description text')
  parser.add_argument('--pre_scriptlet',
                      help='File containing the RPM %pre scriptlet, if to be substituted')
  parser.add_argument('--post_scriptlet',
                      help='File containing the RPM %post scriptlet, if to be substituted')
  parser.add_argument('--preun_scriptlet',
                      help='File containing the RPM %preun scriptlet, if to be substituted')
  parser.add_argument('--postun_scriptlet',
                      help='File containing the RPM %postun scriptlet, if to be substituted')
  parser.add_argument('files', nargs='*')

  options = parser.parse_args(argv or ())

  try:
    builder = RpmBuilder(options.name,
                         options.version, options.release,
                         options.arch, options.rpmbuild,
                         # Scriptlet paths
                         options.pre_scriptlet, options.post_scriptlet,
                         options.preun_scriptlet, options.postun_scriptlet,
                         debug=options.debug)
    builder.AddFiles(options.files)
    return builder.Build(options.spec_file,
                         options.preamble, options.description,
                         options.install_script, options.file_list,
                         options.out_file)
  except NoRpmbuildFoundError:
    print('ERROR: rpmbuild is required but is not present in PATH')
    return 1


if __name__ == '__main__':
  main(sys.argv[1:])
