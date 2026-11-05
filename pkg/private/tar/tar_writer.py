# Copyright 2022 The Bazel Authors. All rights reserved.
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
"""Tar writing helper."""

import gzip
import io
import os
import posixpath
import shutil
import subprocess
import tarfile
import tempfile

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

_DEBUG_VERBOSITY = 0

TARFILE_MEMBER_TYPE_TO_STR = {
    b"0": "REGTYPE",
    b"\0": "AREGTYPE",
    b"1": "LNKTYPE",
    b"2": "SYMTYPE",
    b"3": "CHRTYPE",
    b"4": "BLKTYPE",
    b"5": "DIRTYPE",
    b"6": "FIFOTYPE",
    b"7": "CONTTYPE",
}


class TarFileWriter(object):
  """A wrapper to write tar files."""

  class Error(Exception):
    pass

  def __init__(self,
               name,
               compression='',
               compressor='',
               create_parents=False,
               allow_dups_from_deps=True,
               default_mtime=None,
               preserve_tar_mtimes=True,
               compression_level=-1,
               bsdtar=None):
    """TarFileWriter wraps tarfile.open().

    Args:
      name: the tar file name.
      compression: compression type: bzip2, bz2, gz, tgz, xz, lzma.
      compressor: custom command to do the compression.
      default_mtime: default mtime to use for elements in the archive.
          May be an integer or the value 'portable' to use the date
          2000-01-01, which is compatible with non *nix OSes'.
      preserve_tar_mtimes: if true, keep file mtimes from input tar file.
      bsdtar: path to a bsdtar binary writing the archive instead of tarfile.
    """
    self.preserve_mtime = preserve_tar_mtimes
    if default_mtime is None:
      self.default_mtime = 0
    elif default_mtime == 'portable':
      self.default_mtime = PORTABLE_MTIME
    else:
      self.default_mtime = int(default_mtime)
    self.name = name
    self.existing_members = {}
    self.create_parents = create_parents
    self.allow_dups_from_deps = allow_dups_from_deps

    if bsdtar:
      self.fileobj = None
      self.compressor_proc = None
      self.tar = _BsdtarArchive(name, bsdtar, compression, (compressor or '').strip(),
                                compression_level)
      return

    self.fileobj = None
    self.compressor_cmd = (compressor or '').strip()
    extra_tar_args = {}
    if self.compressor_cmd:
      # Some custom command has been specified: no need for further
      # configuration, we're just going to use it.
      pass
    # Support xz compression through xz... until we can use Py3
    elif compression in ['xz', 'lzma']:
      compression_level = min(compression_level, 9) if compression_level >= 0 else 6
      if HAS_LZMA:
        mode = 'w:xz'
        extra_tar_args['preset'] = compression_level
      else:
        self.compressor_cmd = 'xz -F {} -{} -'.format(compression, compression_level)
    elif compression in ['bzip2', 'bz2']:
      mode = 'w:bz2'
    else:
      mode = 'w:'
      if compression in ['tgz', 'gz']:
        compression_level = min(compression_level, 9) if compression_level >= 0 else 6
        # The Tarfile class doesn't allow us to specify gzip's mtime attribute.
        # Instead, we manually reimplement gzopen from tarfile.py and set mtime.
        self.fileobj = gzip.GzipFile(
            filename=name, mode='w', compresslevel=compression_level, mtime=self.default_mtime)
    self.compressor_proc = None
    if self.compressor_cmd:
      mode = 'w|'
      self.compressor_proc = subprocess.Popen(self.compressor_cmd.split(),
                                              stdin=subprocess.PIPE,
                                              stdout=open(name, 'wb'))
      self.fileobj = self.compressor_proc.stdin

    self.tar = tarfile.open(name=name, mode=mode, fileobj=self.fileobj,
                            format=tarfile.GNU_FORMAT, **extra_tar_args)

  def __enter__(self):
    return self

  def __exit__(self, t, v, traceback):
    self.close()

  def _existing_member_type(self, path):
    """Retrieve an existing tar file member's type if we have added it previously,
    return None otherwise."""
    # Things we should not add.
    # If we some day need to allow '.' or '/' as an explicit member of the archive,
    # we can adjust that here based on the setting of root_directory.
    if path == '/' or path == './':
      return tarfile.DIRTYPE

    normalized_path = path.rstrip("/")
    return self.existing_members.get(normalized_path, None)

  def _addfile(self, info, fileobj=None):
    """Add a file in the tar file if there is no conflict."""
    if info.type == tarfile.DIRTYPE:
      # Enforce the ending / for directories.
      if not info.name.endswith('/'):
        info.name += '/'
    existing_member_type = self._existing_member_type(info.name)
    if not self.allow_dups_from_deps and existing_member_type is not None:
      # Directories with different contents should get merged without warnings.
      # If they have overlapping content, the warning will be on their duplicate *files* instead
      if info.type != tarfile.DIRTYPE:
        print('Duplicate file in archive: %s, '
              'picking first occurrence' % info.name)
      # Directories that shadow
      elif existing_member_type != tarfile.DIRTYPE and existing_member_type != tarfile.SYMTYPE:
        print('Directory shadows a member of type %s in archive: %s, '
              'picking first occurrence' % (TARFILE_MEMBER_TYPE_TO_STR.get(
                  existing_member_type, "UNKNOWN"), info.name))

      return

    self.tar.addfile(info, fileobj)
    # Strip the trailing slash from the path so that we can detect when, for example, we are
    # trying to overwrite a symbolic link with a directory.
    self.existing_members[info.name.rstrip("/")] = info.type

  def add_directory_path(self,
                         path,
                         uid=0,
                         gid=0,
                         uname='',
                         gname='',
                         mtime=None,
                         mode=0o755):
    """Add a directory to the current tar.

    Args:
      path: the ('/' delimited) path of the file to add.
      uid: owner user identifier.
      gid: owner group identifier.
      uname: owner user names.
      gname: owner group names.
      mtime: modification time to put in the archive.
      mode: unix permission mode of the file, default: 0755.
    """
    assert path[-1] == '/'
    if not path:
      return
    if _DEBUG_VERBOSITY > 1:
      print('DEBUG: adding directory', path)
    tarinfo = tarfile.TarInfo(path)
    tarinfo.type = tarfile.DIRTYPE
    tarinfo.mtime = mtime
    tarinfo.mode = mode
    tarinfo.uid = uid
    tarinfo.gid = gid
    tarinfo.uname = uname
    tarinfo.gname = gname
    self._addfile(tarinfo)

  def conditionally_add_parents(self, path, uid=0, gid=0, uname='', gname='', mtime=0, mode=0o755):
    dirs = path.split('/')
    parent_path = ''
    for next_level in dirs[0:-1]:
      parent_path = parent_path + next_level + '/'

      if self.create_parents and self._existing_member_type(
          parent_path) is None:
        self.add_directory_path(
          parent_path,
          uid=uid,
          gid=gid,
          uname=uname,
          gname=gname,
          mtime=mtime,
          mode=0o755)

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
    if not self.allow_dups_from_deps and self._existing_member_type(
        name) is not None:
      return

    if mtime is None:
      mtime = self.default_mtime

    # Make directories up the file
    self.conditionally_add_parents(name, mtime=mtime, mode=0o755, uid=uid, gid=gid, uname=uname, gname=gname)

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

  def add_tar(self,
              tar,
              rootuid=None,
              rootgid=None,
              numeric=False,
              name_filter=None,
              prefix=None):
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
      prefix: prefix to add to all file paths.

    Raises:
      TarFileWriter.Error: if an error happens when uncompressing the tar file.
    """
    if prefix:
      prefix = prefix.strip('/') + '/'
    if _DEBUG_VERBOSITY > 1:
      print('==========================  prefix is', prefix)
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

        in_name = tarinfo.name
        if prefix:
          in_name = os.path.normpath(prefix + in_name).replace(os.path.sep, '/')
        tarinfo.name = in_name
        self.conditionally_add_parents(
            path=tarinfo.name,
            mtime=tarinfo.mtime,
            mode=0o755,
            uid=tarinfo.uid,
            gid=tarinfo.gid,
            uname=tarinfo.uname,
            gname=tarinfo.gname)

        if prefix is not None:
          # Relocate internal hardlinks as well to avoid breaking them.
          link = tarinfo.linkname
          if link.startswith('.') and tarinfo.type == tarfile.LNKTYPE:
            tarinfo.linkname = '.' + prefix + link.lstrip('.')

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


# Bytes written as is in mtree(5) names and values, all others being octal-escaped.
_MTREE_SAFE_BYTES = frozenset(
    b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+,-./:@_~')

_MTREE_TYPES = {
    tarfile.REGTYPE: 'file',
    tarfile.AREGTYPE: 'file',
    tarfile.CONTTYPE: 'file',
    tarfile.LNKTYPE: 'file',  # mtree(5) has no hard links: the target content is copied
    tarfile.DIRTYPE: 'dir',
    tarfile.SYMTYPE: 'link',
    tarfile.CHRTYPE: 'char',
    tarfile.BLKTYPE: 'block',
    tarfile.FIFOTYPE: 'fifo',
}

# bsdtar filter and its option module for each supported compression.
_BSDTAR_FILTERS = {
    'gz': ('--gzip', 'gzip'),
    'tgz': ('--gzip', 'gzip'),
    'bz2': ('--bzip2', 'bzip2'),
    'bzip2': ('--bzip2', 'bzip2'),
    'xz': ('--xz', 'xz'),
    'lzma': ('--lzma', 'lzma'),
}


def _mtree_escape(text):
  return ''.join(chr(b) if b in _MTREE_SAFE_BYTES else '\\%03o' % b
                 for b in text.encode('utf-8'))


def _member_path(name):
  return posixpath.normpath(name[2:] if name.startswith('./') else name).strip('/')


class _BsdtarArchive(object):
  """Stands in for tarfile.TarFile, describing members in mtree(5) specs bsdtar archives."""

  def __init__(self, name, bsdtar, compression, compressor, compression_level):
    self.name = name
    self.bsdtar = bsdtar
    self.compression = compression
    self.compressor = compressor
    self.compression_level = compression_level
    self.spool = tempfile.TemporaryDirectory()
    # bsdtar merges mtree entries sharing a name, so duplicates start a new spec.
    self.specs = [[]]
    self.spec_names = set()
    self.contents = {}  # member path -> content path, to materialize hard links

  def _content_path(self, tarinfo, fileobj):
    if tarinfo.type == tarfile.LNKTYPE:
      target = _member_path(tarinfo.linkname)
      if target not in self.contents:
        raise TarFileWriter.Error('Hard link %s targets unknown member %s' % (
            tarinfo.name, tarinfo.linkname))
      return self.contents[target]
    # bsdtar reads files opened by TarFileWriter.add_file in place.
    if isinstance(getattr(fileobj, 'raw', None), io.FileIO) and isinstance(fileobj.name, str):
      return os.path.abspath(fileobj.name)
    if fileobj is None:
      return None
    # Spool content only available as a stream, such as members of merged tar files.
    with tempfile.NamedTemporaryFile(dir=self.spool.name, delete=False) as spooled:
      shutil.copyfileobj(fileobj, spooled)
    return spooled.name

  def addfile(self, tarinfo, fileobj=None):
    kind = _MTREE_TYPES.get(tarinfo.type)
    if kind is None:
      raise TarFileWriter.Error('Unsupported member type %r for %s' % (
          tarinfo.type, tarinfo.name))
    member = _member_path(tarinfo.name)
    # A trailing slash keeps bsdtar from descending into directories as relative mtree entries do.
    name = tarinfo.name.rstrip('/') + ('/' if kind == 'dir' else '')
    keywords = [
        'type=' + kind,
        'mode=%04o' % (tarinfo.mode & 0o7777),
        'uid=%d' % tarinfo.uid,
        'gid=%d' % tarinfo.gid,
        'time=%d.%09d' % divmod(round(tarinfo.mtime * 1e9), 10**9),
    ]
    if tarinfo.uname:
      keywords.append('uname=' + _mtree_escape(tarinfo.uname))
    if tarinfo.gname:
      keywords.append('gname=' + _mtree_escape(tarinfo.gname))
    if kind == 'link':
      keywords.append('link=' + _mtree_escape(tarinfo.linkname))
    elif kind in ('char', 'block'):
      keywords.append('device=native,%d,%d' % (tarinfo.devmajor, tarinfo.devminor))
    elif kind == 'file':
      content = self._content_path(tarinfo, fileobj)
      if content is None:
        keywords.append('size=0')
      else:
        keywords.append('contents=' + _mtree_escape(content))
        self.contents[member] = content
    if member in self.spec_names:
      self.specs.append([])
      self.spec_names.clear()
    self.spec_names.add(member)
    self.specs[-1].append(' '.join([_mtree_escape(name)] + keywords))

  def _compression_args(self):
    if self.compression not in _BSDTAR_FILTERS:
      return []
    flag, module = _BSDTAR_FILTERS[self.compression]
    options = ['gzip:!timestamp'] if module == 'gzip' else []
    # Like the tarfile writer, only gzip and xz honor the compression level, defaulting to 6.
    if module != 'bzip2' and self.compression_level >= 0:
      options.append('%s:compression-level=%d' % (module, min(self.compression_level, 9)))
    return [flag] + (['--options', ','.join(options)] if options else [])

  def close(self):
    try:
      cmd = [self.bsdtar, '--create', '--format=gnutar', '--file']
      cmd += ['-'] if self.compressor else [self.name] + self._compression_args()
      for i, lines in enumerate(self.specs):
        spec = os.path.join(self.spool.name, 'spec%d.mtree' % i)
        with open(spec, 'w', encoding='utf-8') as f:
          f.write('\n'.join(['#mtree'] + lines) + '\n')
        cmd.append('@' + spec)
      if not self.compressor:
        subprocess.run(cmd, check=True)
        return
      with open(self.name, 'wb') as out:
        archiver = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        compressor = subprocess.Popen(self.compressor.split(), stdin=archiver.stdout, stdout=out)
        archiver.stdout.close()
        if compressor.wait() != 0:
          raise TarFileWriter.Error('Custom compression command "%s" failed' % self.compressor)
        if archiver.wait() != 0:
          raise subprocess.CalledProcessError(archiver.returncode, cmd)
    finally:
      self.spool.cleanup()
