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
"""Archive manipulation library for the Docker rules."""

# pylint: disable=g-import-not-at-top
import gzip
import io
import os
import subprocess
import tarfile

try:
  import lzma  # pylint: disable=g-import-not-at-top, unused-import
  HAS_LZMA = True
except ImportError:
  HAS_LZMA = False

# This is slightly a lie. We do support xz fallback through the xz tool, but
# that is fragile. Users should stick to the expectations provided here.
COMPRESSIONS = ('', 'gz', 'bz2', 'xz') if HAS_LZMA else ('', 'gz', 'bz2')


# Use a deterministic mtime that doesn't confuse other programs.
# See: https://github.com/bazelbuild/bazel/issues/1299
PORTABLE_MTIME = 946684800  # 2000-01-01 00:00:00.000 UTC


class SimpleArFile(object):
  """A simple AR file reader.

  This enable to read AR file (System V variant) as described
  in https://en.wikipedia.org/wiki/Ar_(Unix).

  The standard usage of this class is:

  with SimpleArFile(filename) as ar:
    nextFile = ar.next()
    while nextFile:
      print(nextFile.filename)
      nextFile = ar.next()

  Upon error, this class will raise a ArError exception.
  """

  # TODO(dmarting): We should use a standard library instead but python 2.7
  #   does not have AR reading library.

  class ArError(Exception):
    pass

  class SimpleArFileEntry(object):
    """Represent one entry in a AR archive.

    Attributes:
      filename: the filename of the entry, as described in the archive.
      timestamp: the timestamp of the file entry.
      owner_id: numeric id of the user and group owning the file.
      group_id: numeric id of the user and group owning the file.
      mode: unix permission mode of the file
      size: size of the file
      data: the content of the file.
    """

    def __init__(self, f):
      self.filename = f.read(16).decode('utf-8').strip()
      if self.filename.endswith('/'):  # SysV variant
        self.filename = self.filename[:-1]
      self.timestamp = int(f.read(12).strip())
      self.owner_id = int(f.read(6).strip())
      self.group_id = int(f.read(6).strip())
      self.mode = int(f.read(8).strip(), 8)
      self.size = int(f.read(10).strip())
      pad = f.read(2)
      if pad != b'\x60\x0a':
        raise SimpleArFile.ArError('Invalid AR file header')
      self.data = f.read(self.size)

  MAGIC_STRING = b'!<arch>\n'

  def __init__(self, filename):
    self.filename = filename

  def __enter__(self):
    self.f = open(self.filename, 'rb')
    if self.f.read(len(self.MAGIC_STRING)) != self.MAGIC_STRING:
      raise self.ArError('Not a ar file: ' + self.filename)
    return self

  def __exit__(self, t, v, traceback):
    self.f.close()

  def next(self):
    """Read the next file. Returns None when reaching the end of file."""
    # AR sections are two bit aligned using new lines.
    if self.f.tell() % 2 != 0:
      self.f.read(1)
    # An AR sections is at least 60 bytes. Some file might contains garbage
    # bytes at the end of the archive, ignore them.
    if self.f.tell() > os.fstat(self.f.fileno()).st_size - 60:
      return None
    return self.SimpleArFileEntry(self.f)


class TarFileWriter(object):
  """A wrapper to write tar files."""

  class Error(Exception):
    pass

  def __init__(self,
               name,
               compression='',
               compressor='',
               root_directory='',
               default_mtime=None,
               preserve_tar_mtimes=True):
    """TarFileWriter wraps tarfile.open().

    Args:
      name: the tar file name.
      compression: compression type: bzip2, bz2, gz, tgz, xz, lzma.
      compressor: custom command to do the compression.
      root_directory: virtual root to prepend to elements in the archive.
      default_mtime: default mtime to use for elements in the archive.
          May be an integer or the value 'portable' to use the date
          2000-01-01, which is compatible with non *nix OSes'.
      preserve_tar_mtimes: if true, keep file mtimes from input tar file.
    """
    self.preserve_mtime = preserve_tar_mtimes
    if default_mtime is None:
      self.default_mtime = 0
    elif default_mtime == 'portable':
      self.default_mtime = PORTABLE_MTIME
    else:
      self.default_mtime = int(default_mtime)

    self.fileobj = None
    self.compressor_cmd = (compressor or '').strip()
    if self.compressor_cmd:
      # Some custom command has been specified: no need for further
      # configuration, we're just going to use it.
      pass
    # Support xz compression through xz... until we can use Py3
    elif compression in ['xz', 'lzma']:
      if HAS_LZMA:
        mode = 'w:xz'
      else:
        self.compressor_cmd = 'xz -F {} -'.format(compression)
    elif compression in ['bzip2', 'bz2']:
      mode = 'w:bz2'
    else:
      mode = 'w:'
      if compression in ['tgz', 'gz']:
        # The Tarfile class doesn't allow us to specify gzip's mtime attribute.
        # Instead, we manually reimplement gzopen from tarfile.py and set mtime.
        self.fileobj = gzip.GzipFile(
            filename=name, mode='w', compresslevel=9, mtime=self.default_mtime)
    self.compressor_proc = None
    if self.compressor_cmd:
      mode = 'w|'
      self.compressor_proc = subprocess.Popen(self.compressor_cmd.split(),
                                              stdin=subprocess.PIPE,
                                              stdout=open(name, 'wb'))
      self.fileobj = self.compressor_proc.stdin
    self.name = name
    # tarfile uses / instead of os.path.sep
    self.root_directory = root_directory.replace(os.path.sep, '/').rstrip('/')
    if self.root_directory:
      self.root_directory = self.root_directory + '/'

    self.tar = tarfile.open(name=name, mode=mode, fileobj=self.fileobj)
    self.members = set()
    # The directories we have created so far
    self.directories = set()

  def __enter__(self):
    return self

  def __exit__(self, t, v, traceback):
    self.close()


  def add_root(self, path: str) -> str:
    """Add the root prefix to a path.

    If the path begins with / or the prefix itself, do nothing.

    Args:
      path: a file path
    Returns:
      modified path.
    """
    path = path.replace(os.path.sep, '/').rstrip('/')
    if not self.root_directory or path.startswith('/'):
      return path
    if (path + '/').startswith(self.root_directory):
      return path
    return self.root_directory + path

  def _addfile(self, info, fileobj=None):
    """Add a file in the tar file if there is no conflict."""
    if not info.name.endswith('/') and info.type == tarfile.DIRTYPE:
      # Enforce the ending / for directories so we correctly deduplicate.
      info.name += '/'
    if info.name not in self.members:
      self.tar.addfile(info, fileobj)
      self.members.add(info.name)
    elif info.type != tarfile.DIRTYPE:
      print('Duplicate file in archive: %s, '
            'picking first occurrence' % info.name)

  def add_file(self,
               name,
               kind=tarfile.REGTYPE,
               content=None,
               link=None,
               file_content=None,
               uid=0,
               gid=0,
               uname='',
               gname='',
               mtime=None,
               mode=None):
    """Add a file to the current tar.

    Args:
      name: the ('/' delimited) path of the file to add.
      kind: the type of the file to add, see tarfile.*TYPE.
      content: the content to put in the file.
      link: if the file is a link, the destination of the link.
      file_content: file to read the content from. Provide either this
          one or `content` to specifies a content for the file.
      uid: owner user identifier.
      gid: owner group identifier.
      uname: owner user names.
      gname: owner group names.
      mtime: modification time to put in the archive.
      mode: unix permission mode of the file, default 0644 (0755).
    """
    if not name:
      return
    if name == '.':
      return
    name = self.add_root(name)
    # Do not add a directory that is already in the tar file.
    if kind == tarfile.DIRTYPE and name in self.directories:
      return

    if mtime is None:
      mtime = self.default_mtime

    # Make directories up the file
    parent_dirs = name.rsplit('/', 1)
    if len(parent_dirs) > 1:
      self.add_file(parent_dirs[0],
                    kind=tarfile.DIRTYPE,
                    uid=uid,
                    gid=gid,
                    uname=uname,
                    gname=gname,
                    mtime=mtime,
                    mode=0o755)

    tarinfo = tarfile.TarInfo(name)
    tarinfo.mtime = mtime
    tarinfo.uid = uid
    tarinfo.gid = gid
    tarinfo.uname = uname
    tarinfo.gname = gname
    tarinfo.type = kind
    if mode is None:
      tarinfo.mode = 0o644 if kind == tarfile.REGTYPE else 0o755
    else:
      tarinfo.mode = mode
    if link:
      tarinfo.linkname = link
    if content:
      content_bytes = content.encode('utf-8')
      tarinfo.size = len(content_bytes)
      self._addfile(tarinfo, io.BytesIO(content_bytes))
    elif file_content:
      with open(file_content, 'rb') as f:
        tarinfo.size = os.fstat(f.fileno()).st_size
        self._addfile(tarinfo, f)
    else:
      self._addfile(tarinfo)
    if kind == tarfile.DIRTYPE:
      assert name[-1] != '/'
      self.directories.add(name)

  def add_tar(self,
              tar,
              rootuid=None,
              rootgid=None,
              numeric=False,
              name_filter=None,
              root=None):
    """Merge a tar content into the current tar, stripping timestamp.

    Args:
      tar: the name of tar to extract and put content into the current tar.
      rootuid: user id that we will pretend is root (replaced by uid 0).
      rootgid: group id that we will pretend is root (replaced by gid 0).
      numeric: set to true to strip out name of owners (and just use the
          numeric values).
      name_filter: filter out file by names. If not none, this method will be
          called for each file to add, given the name and should return true if
          the file is to be added to the final tar and false otherwise.
      root: place all non-absolute content under given root directory, if not
          None.

    Raises:
      TarFileWriter.Error: if an error happens when uncompressing the tar file.
    """
    if root and root[0] not in ['/', '.']:
      # Root prefix should start with a '/', adds it if missing
      root = '/' + root
    intar = tarfile.open(name=tar, mode='r:*')
    for tarinfo in intar:
      if name_filter is None or name_filter(tarinfo.name):
        if not self.preserve_mtime:
          tarinfo.mtime = self.default_mtime
        if rootuid is not None and tarinfo.uid == rootuid:
          tarinfo.uid = 0
          tarinfo.uname = 'root'
        if rootgid is not None and tarinfo.gid == rootgid:
          tarinfo.gid = 0
          tarinfo.gname = 'root'
        if numeric:
          tarinfo.uname = ''
          tarinfo.gname = ''

        name = self.add_root(tarinfo.name)
        if root is not None:
          if name.startswith('.'):
            name = '.' + root + name.lstrip('.')
            # Add root dir with same permissions if missing. Note that
            # add_file deduplicates directories and is safe to call here.
            self.add_file('.' + root,
                          tarfile.DIRTYPE,
                          uid=tarinfo.uid,
                          gid=tarinfo.gid,
                          uname=tarinfo.uname,
                          gname=tarinfo.gname,
                          mtime=tarinfo.mtime,
                          mode=0o755)
          # Relocate internal hardlinks as well to avoid breaking them.
          link = tarinfo.linkname
          if link.startswith('.') and tarinfo.type == tarfile.LNKTYPE:
            tarinfo.linkname = '.' + root + link.lstrip('.')
        tarinfo.name = name

        # Remove path pax header to ensure that the proposed name is going
        # to be used. Without this, files with long names will not be
        # properly written to its new path.
        if 'path' in tarinfo.pax_headers:
          del tarinfo.pax_headers['path']

        if tarinfo.isfile():
          # use extractfile(tarinfo) instead of tarinfo.name to preserve
          # seek position in intar
          self._addfile(tarinfo, intar.extractfile(tarinfo))
        else:
          self._addfile(tarinfo)
    intar.close()

  def close(self):
    """Close the output tar file.

    This class should not be used anymore after calling that method.

    Raises:
      TarFileWriter.Error: if an error happens when compressing the output file.
    """
    self.tar.close()
    # Close the file object if necessary.
    if self.fileobj:
      self.fileobj.close()
    if self.compressor_proc and self.compressor_proc.wait() != 0:
      raise self.Error('Custom compression command '
                       '"{}" failed'.format(self.compressor_cmd))
