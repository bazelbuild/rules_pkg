# Copyright 2015 The Bazel Authors. All rights reserved.
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
"""This tool build tar files from a list of inputs."""

import argparse
import json
import os
import tarfile
import tempfile

from pkg.private import archive
from pkg.private import helpers
from pkg.private import build_info
from pkg.private import manifest


class TarFile(object):
  """A class to generates a TAR file."""

  class DebError(Exception):
    pass

  def __init__(self, output, directory, compression, compressor, root_directory,
               default_mtime):
    self.directory = directory
    self.output = output
    self.compression = compression
    self.compressor = compressor
    self.root_directory = root_directory
    self.default_mtime = default_mtime

  def __enter__(self):
    self.tarfile = archive.TarFileWriter(
        self.output,
        self.compression,
        self.compressor,
        self.root_directory,
        default_mtime=self.default_mtime)
    return self

  def __exit__(self, t, v, traceback):
    self.tarfile.close()

  def add_file(self, f, destfile, mode=None, ids=None, names=None):
    """Add a file to the tar file.

    Args:
       f: the file to add to the layer
       destfile: the name of the file in the layer
       mode: (int) force to set the specified mode, by default the value from the
         source is taken.
       ids: (uid, gid) for the file to set ownership
       names: (username, groupname) for the file to set ownership. `f` will be
         copied to `self.directory/destfile` in the layer.
    """
    dest = destfile.lstrip('/')  # Remove leading slashes
    if self.directory and self.directory != '/':
      dest = self.directory.lstrip('/') + '/' + dest
    # If mode is unspecified, derive the mode from the file's mode.
    if mode is None:
      mode = 0o755 if os.access(f, os.X_OK) else 0o644
    if ids is None:
      ids = (0, 0)
    if names is None:
      names = ('', '')
    # Note: normpath changes / to \ on windows, but we expect / style paths.
    dest = os.path.normpath(dest).replace(os.path.sep, '/')
    self.tarfile.add_file(
        dest,
        file_content=f,
        mode=mode,
        uid=ids[0],
        gid=ids[1],
        uname=names[0],
        gname=names[1])

  def add_empty_file(self,
                     destfile,
                     mode=None,
                     ids=None,
                     names=None,
                     kind=tarfile.REGTYPE):
    """Add a file to the tar file.

    Args:
       destfile: the name of the file in the layer
       mode: force to set the specified mode, defaults to 644
       ids: (uid, gid) for the file to set ownership
       names: (username, groupname) for the file to set ownership.
       kind: type of the file. tarfile.DIRTYPE for directory.  An empty file
         will be created as `destfile` in the layer.
    """
    dest = destfile.lstrip('/')  # Remove leading slashes
    # If mode is unspecified, assume read only
    if mode is None:
      mode = 0o644
    if ids is None:
      ids = (0, 0)
    if names is None:
      names = ('', '')
    dest = os.path.normpath(dest).replace(os.path.sep, '/')
    self.tarfile.add_file(
        dest,
        content='' if kind == tarfile.REGTYPE else None,
        kind=kind,
        mode=mode,
        uid=ids[0],
        gid=ids[1],
        uname=names[0],
        gname=names[1])

  def add_empty_dir(self, destpath, mode=None, ids=None, names=None):
    """Add a directory to the tar file.

    Args:
       destpath: the name of the directory in the layer
       mode: force to set the specified mode, defaults to 644
       ids: (uid, gid) for the file to set ownership
       names: (username, groupname) for the file to set ownership.  An empty
         file will be created as `destfile` in the layer.
    """
    self.add_empty_file(
        destpath, mode=mode, ids=ids, names=names, kind=tarfile.DIRTYPE)

  def add_empty_root_dir(self, destpath, mode=None, ids=None, names=None):
    """Add a directory to the root of the tar file.

    Args:
       destpath: the name of the directory in the layer
       mode: force to set the specified mode, defaults to 644
       ids: (uid, gid) for the file to set ownership
       names: (username, groupname) for the file to set ownership.  An empty
         directory will be created as `destfile` in the root layer.
    """
    original_root_directory = self.tarfile.root_directory
    self.tarfile.root_directory = destpath
    self.add_empty_dir(destpath, mode=mode, ids=ids, names=names)
    self.tarfile.root_directory = original_root_directory

  def add_tar(self, tar):
    """Merge a tar file into the destination tar file.

    All files presents in that tar will be added to the output file
    under self.directory/path. No user name nor group name will be
    added to the output.

    Args:
      tar: the tar file to add
    """
    root = None
    if self.directory and self.directory != '/':
      root = self.directory
    self.tarfile.add_tar(tar, numeric=True, root=root)

  def add_link(self, symlink, destination, mode=None, ids=None, names=None):
    """Add a symbolic link pointing to `destination`.

    Args:
      symlink: the name of the symbolic link to add.
      destination: where the symbolic link point to.
      mode: (int) force to set the specified posix mode (e.g. 0o755). The
        default is derived from the source
      ids: (uid, gid) for the file to set ownership
      names: (username, groupname) for the file to set ownership.  An empty
        file will be created as `destfile` in the layer.
    """
    symlink = os.path.normpath(symlink).replace(os.path.sep, '/')
    self.tarfile.add_file(
        symlink,
        tarfile.SYMTYPE,
        link=destination,
        mode = mode,
        uid=ids[0],
        gid=ids[1],
        uname=names[0],
        gname=names[1])

  def add_deb(self, deb):
    """Extract a debian package in the output tar.

    All files presents in that debian package will be added to the
    output tar under the same paths. No user name nor group names will
    be added to the output.

    Args:
      deb: the tar file to add

    Raises:
      DebError: if the format of the deb archive is incorrect.
    """
    with archive.SimpleArFile(deb) as arfile:
      current = next(arfile)
      while current and not current.filename.startswith('data.'):
        current = next(arfile)
      if not current:
        raise self.DebError(deb + ' does not contains a data file!')
      tmpfile = tempfile.mkstemp(suffix=os.path.splitext(current.filename)[-1])
      with open(tmpfile[1], 'wb') as f:
        f.write(current.data)
      self.add_tar(tmpfile[1])
      os.remove(tmpfile[1])

  def add_tree(self, tree_top, destpath, mode=None, ids=None, names=None):
    """Add a tree artifact to the tar file.

    Args:
       tree_top: the top of the tree to add
       destpath: the path under which to place the files
       mode: (int) force to set the specified posix mode (e.g. 0o755). The
         default is derived from the source
       ids: (uid, gid) for the file to set ownership
       names: (username, groupname) for the file to set ownership. `f` will be
         copied to `self.directory/destfile` in the layer.
    """
    # We expect /-style paths.
    tree_top = os.path.normpath(tree_top).replace(os.path.sep, '/')

    dest = destpath.strip('/')  # redundant, dests should never have / here
    if self.directory and self.directory != '/':
      dest = self.directory.lstrip('/') + '/' + dest

    # Again, we expect /-style paths.
    dest = os.path.normpath(dest).replace(os.path.sep, '/')
    if ids is None:
      ids = (0, 0)
    if names is None:
      names = ('', '')

    to_write = {}
    for root, dirs, files in os.walk(tree_top):
      # While `tree_top` uses '/' as a path separator, results returned by
      # `os.walk` and `os.path.join` on Windows may not.
      root = os.path.normpath(root).replace(os.path.sep, '/')

      dirs = sorted(dirs)
      rel_path_from_top = root[len(tree_top):].lstrip('/')
      if rel_path_from_top:
        dest_dir = dest + '/' + rel_path_from_top + '/'
      else:
        dest_dir = dest + '/'
      for dir in dirs:
        to_write[dest_dir + dir] = None
      for file in sorted(files):
        to_write[dest_dir + file] = root + '/' + file

    for path in sorted(to_write.keys()):
      content_path = to_write[path]
      # If mode is unspecified, derive the mode from the file's mode.
      if mode is None:
        f_mode = 0o755 if os.access(content_path, os.X_OK) else 0o644
      else:
        f_mode = mode
      if not content_path:
        self.add_empty_file(
            path,
            mode=f_mode,
            ids=ids,
            names=names,
            kind=tarfile.DIRTYPE)
      else:
        self.tarfile.add_file(
            path,
            file_content=content_path,
            mode=f_mode,
            uid=ids[0],
            gid=ids[1],
            uname=names[0],
            gname=names[1])

  def add_manifest_entry(self, entry_list, file_attributes):
    entry = manifest.ManifestEntry(*entry_list)

    # Use the pkg_tar mode/owner remaping as a fallback
    non_abs_path = entry.dest.strip('/')
    if file_attributes:
      attrs = file_attributes(non_abs_path)
    else:
      attrs = {}
    # But any attributes from the manifest have higher precedence
    if entry.mode is not None and entry.mode != '':
      attrs['mode'] = int(entry.mode, 8)
    if entry.user:
      if entry.group:
        attrs['names'] = (entry.user, entry.group)
      else:
        # Use group that legacy tar process would assign
        attrs['names'] = (entry.user, attrs.get('names')[1])
    if entry.entry_type == manifest.ENTRY_IS_LINK:
      self.add_link(entry.dest, entry.src, **attrs)
    elif entry.entry_type == manifest.ENTRY_IS_DIR:
      self.add_empty_dir(entry.dest, **attrs)
    elif entry.entry_type == manifest.ENTRY_IS_TREE:
      self.add_tree(entry.src, entry.dest, **attrs)
    elif entry.entry_type == manifest.ENTRY_IS_EMPTY_FILE:
      self.add_empty_file(entry.dest, **attrs)
    else:
      self.add_file(entry.src, entry.dest, **attrs)


def main():
  parser = argparse.ArgumentParser(
      description='Helper for building tar packages',
      fromfile_prefix_chars='@')
  parser.add_argument('--output', required=True,
                      help='The output file, mandatory.')
  parser.add_argument('--manifest',
                      help='manifest of contents to add to the layer.')
  parser.add_argument('--legacy_manifest',
                      help='DEPRECATED: JSON manifest of contents to add to the layer.')
  parser.add_argument('--mode',
                      help='Force the mode on the added files (in octal).')
  parser.add_argument(
      '--mtime',
      help='Set mtime on tar file entries. May be an integer or the'
           ' value "portable", to get the value 2000-01-01, which is'
           ' is usable with non *nix OSes.')
  parser.add_argument('--empty_root_dir', action='append',
                      help='An empty dir to add to the layer.')
  parser.add_argument('--tar', action='append',
                      help='A tar file to add to the layer')
  parser.add_argument('--deb', action='append',
                      help='A debian package to add to the layer')
  parser.add_argument(
      '--directory',
      help='Directory in which to store the file inside the layer')

  compression = parser.add_mutually_exclusive_group()
  compression.add_argument('--compression',
                           help='Compression (`gz` or `bz2`), default is none.')
  compression.add_argument('--compressor',
                           help='Compressor program and arguments, '
                                'e.g. `pigz -p 4`')

  parser.add_argument(
      '--modes', action='append',
      help='Specific mode to apply to specific file (from the file argument),'
           ' e.g., path/to/file=0455.')
  parser.add_argument(
      '--owners', action='append',
      help='Specify the numeric owners of individual files, '
           'e.g. path/to/file=0.0.')
  parser.add_argument(
      '--owner', default='0.0',
      help='Specify the numeric default owner of all files,'
           ' e.g., 0.0')
  parser.add_argument(
      '--owner_name',
      help='Specify the owner name of all files, e.g. root.root.')
  parser.add_argument(
      '--owner_names', action='append',
      help='Specify the owner names of individual files, e.g. '
           'path/to/file=root.root.')
  parser.add_argument('--root_directory', default='./',
                      help='Default root directory is named "."')
  parser.add_argument('--stamp_from', default='',
                      help='File to find BUILD_STAMP in')
  options = parser.parse_args()

  # Parse modes arguments
  default_mode = None
  if options.mode:
    # Convert from octal
    default_mode = int(options.mode, 8)

  mode_map = {}
  if options.modes:
    for filemode in options.modes:
      (f, mode) = helpers.SplitNameValuePairAtSeparator(filemode, '=')
      if f[0] == '/':
        f = f[1:]
      mode_map[f] = int(mode, 8)

  default_ownername = ('', '')
  if options.owner_name:
    default_ownername = options.owner_name.split('.', 1)
  names_map = {}
  if options.owner_names:
    for file_owner in options.owner_names:
      (f, owner) = helpers.SplitNameValuePairAtSeparator(file_owner, '=')
      (user, group) = owner.split('.', 1)
      if f[0] == '/':
        f = f[1:]
      names_map[f] = (user, group)

  default_ids = options.owner.split('.', 1)
  default_ids = (int(default_ids[0]), int(default_ids[1]))
  ids_map = {}
  if options.owners:
    for file_owner in options.owners:
      (f, owner) = helpers.SplitNameValuePairAtSeparator(file_owner, '=')
      (user, group) = owner.split('.', 1)
      if f[0] == '/':
        f = f[1:]
      ids_map[f] = (int(user), int(group))

  default_mtime = options.mtime
  if options.stamp_from:
    default_mtime = build_info.get_timestamp(options.stamp_from)

  # Add objects to the tar file
  with TarFile(
      options.output, helpers.GetFlagValue(options.directory),
      options.compression, options.compressor, options.root_directory,
      default_mtime=default_mtime) as output:

    def file_attributes(filename):
      if filename.startswith('/'):
        filename = filename[1:]
      return {
          'mode': mode_map.get(filename, default_mode),
          'ids': ids_map.get(filename, default_ids),
          'names': names_map.get(filename, default_ownername),
      }

    # TODO(aiuto): Make sure this is unused and remove the code.
    if options.legacy_manifest:
      with open(options.legacy_manifest, 'r') as manifest_fp:
        manifest = json.load(manifest_fp)
        for f in manifest.get('files', []):
          output.add_file(f['src'], f['dst'], **file_attributes(f['dst']))
        for f in manifest.get('empty_files', []):
          output.add_empty_file(f, **file_attributes(f))
        for d in manifest.get('empty_dirs', []):
          output.add_empty_dir(d, **file_attributes(d))
        for d in manifest.get('empty_root_dirs', []):
          output.add_empty_root_dir(d, **file_attributes(d))
        for f in manifest.get('symlinks', []):
          output.add_link(f['linkname'], f['target'])
        for tar in manifest.get('tars', []):
          output.add_tar(tar)
        for deb in manifest.get('debs', []):
          output.add_deb(deb)

    if options.manifest:
      with open(options.manifest, 'r') as manifest_fp:
        manifest = json.load(manifest_fp)
        for entry in manifest:
          output.add_manifest_entry(entry, file_attributes)

    for f in options.empty_root_dir or []:
      output.add_empty_root_dir(f, **file_attributes(f))
    for tar in options.tar or []:
      output.add_tar(tar)
    for deb in options.deb or []:
      output.add_deb(deb)


if __name__ == '__main__':
  main()
