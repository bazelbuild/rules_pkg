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
"""A simple cross-platform helper to create a debian package."""

import argparse
import gzip
import hashlib
from io import BytesIO
import os
import os.path
import sys
import tarfile
import textwrap
import time


# list of debian fields : (name, mandatory, wrap[, default])
# see http://www.debian.org/doc/debian-policy/ch-controlfields.html
from helpers import GetFlagValue

DEBIAN_FIELDS = [
    ('Package', True, False),
    ('Version', True, False),
    ('Section', False, False, 'contrib/devel'),
    ('Priority', False, False, 'optional'),
    ('Architecture', False, False, 'all'),
    ('Depends', False, True, []),
    ('Recommends', False, True, []),
    ('Replaces', False, True, []),
    ('Suggests', False, True, []),
    ('Enhances', False, True, []),
    ('Conflicts', False, True, []),
    ('Breaks', False, True, []),
    ('Pre-Depends', False, True, []),
    ('Installed-Size', False, False),
    ('Maintainer', True, False),
    ('Description', True, True),
    ('Homepage', False, False),
    ('Built-Using', False, False, None),
    ('Distribution', False, False, 'unstable'),
    ('Urgency', False, False, 'medium'),
]

# size of chunks for copying package content to final .deb file
# This is a wild guess, but I am not convinced of the value of doing much work
# to tune it.
_COPY_CHUNK_SIZE = 1024 * 32


def AddControlFlags(parser):
  """Creates a flag for each of the control file fields."""
  for field in DEBIAN_FIELDS:
    flag_name = '--' + field[0].replace('-', '_').lower()
    msg = 'The value for the %s content header entry.' % field[0]
    required = field[1]
    if len(field) > 3:
      default = field[3]
      if isinstance(field[3], list):
        parser.add_argument(flag_name, action='append', default=default,
                            required=required, help=msg)
      else:
        parser.add_argument(flag_name, default=default, required=required,
                            help=msg)
    else:
      parser.add_argument(flag_name, required=required, help=msg)


def ConvertToFileLike(content, content_len, converter):
  if content_len < 0:
    content_len = len(content)
  content = converter(content)
  return content_len, content


def AddArFileEntry(fileobj, filename,
                   content='', content_len=-1, timestamp=0,
                   owner_id=0, group_id=0, mode=0o644):
  """Add a AR file entry to fileobj."""
  # If we got the content as a string, turn it into a file like thing.
  if isinstance(content, (str, bytes)):
    content_len, content = ConvertToFileLike(content, content_len, BytesIO)
  inputs = [
      (filename + '/').ljust(16),  # filename (SysV)
      str(timestamp).ljust(12),  # timestamp
      str(owner_id).ljust(6),  # owner id
      str(group_id).ljust(6),  # group id
      str(oct(mode)).replace('0o', '0').ljust(8),  # mode
      str(content_len).ljust(10),  # size
      '\x60\x0a',  # end of file entry
  ]
  for i in inputs:
    fileobj.write(i.encode('ascii'))
  size = 0
  while True:
    data = content.read(_COPY_CHUNK_SIZE)
    if not data:
      break
    size += len(data)
    fileobj.write(data)
  if size % 2 != 0:
    fileobj.write(b'\n')  # 2-byte alignment padding


def MakeDebianControlField(name, value, wrap=False):
  """Add a field to a debian control file."""
  result = name + ': '
  if isinstance(value, bytes):
    value = value.decode('utf-8')
  if isinstance(value, list):
    value = u', '.join(value)
  if wrap:
    result += u' '.join(value.split('\n'))
    result = textwrap.fill(result,
                           break_on_hyphens=False,
                           break_long_words=False)
  else:
    result += value
  return result.replace(u'\n', u'\n ') + u'\n'


def CreateDebControl(extrafiles=None, **kwargs):
  """Create the control.tar.gz file."""
  # create the control file
  controlfile = u''
  for values in DEBIAN_FIELDS:
    fieldname = values[0]
    key = fieldname[0].lower() + fieldname[1:].replace('-', '')
    if values[1] or (key in kwargs and kwargs[key]):
      controlfile += MakeDebianControlField(fieldname, kwargs[key], values[2])
  # Create the control.tar file
  tar = BytesIO()
  with gzip.GzipFile('control.tar.gz', mode='w', fileobj=tar, mtime=0) as gz:
    with tarfile.open('control.tar.gz', mode='w', fileobj=gz) as f:
      tarinfo = tarfile.TarInfo('control')
      control_file_data = controlfile.encode('utf-8')
      tarinfo.size = len(control_file_data)
      f.addfile(tarinfo, fileobj=BytesIO(control_file_data))
      if extrafiles:
        for name, (data, mode) in extrafiles.items():
          tarinfo = tarfile.TarInfo(name)
          tarinfo.size = len(data)
          tarinfo.mode = mode
          f.addfile(tarinfo, fileobj=BytesIO(data.encode('utf-8')))
  control = tar.getvalue()
  tar.close()
  return control


def CreateDeb(output,
              data,
              preinst=None,
              postinst=None,
              prerm=None,
              postrm=None,
              config=None,
              templates=None,
              conffiles=None,
              **kwargs):
  """Create a full debian package."""
  extrafiles = {}
  if preinst:
    extrafiles['preinst'] = (preinst, 0o755)
  if postinst:
    extrafiles['postinst'] = (postinst, 0o755)
  if prerm:
    extrafiles['prerm'] = (prerm, 0o755)
  if postrm:
    extrafiles['postrm'] = (postrm, 0o755)
  if config:
    extrafiles['config'] = (config, 0o644)
  if templates:
    extrafiles['templates'] = (templates, 0o644)
  if conffiles:
    extrafiles['conffiles'] = ('\n'.join(conffiles) + '\n', 0o644)
  control = CreateDebControl(extrafiles=extrafiles, **kwargs)

  # Write the final AR archive (the deb package)
  with open(output, 'wb') as f:
    f.write(b'!<arch>\n')  # Magic AR header
    AddArFileEntry(f, 'debian-binary', b'2.0\n')
    AddArFileEntry(f, 'control.tar.gz', control)
    # Tries to preserve the extension name
    ext = os.path.basename(data).split('.')[-2:]
    if len(ext) < 2:
      ext = 'tar'
    elif ext[1] == 'tgz':
      ext = 'tar.gz'
    elif ext[1] == 'tar.bzip2':
      ext = 'tar.bz2'
    else:
      ext = '.'.join(ext)
      if ext not in ['tar.bz2', 'tar.gz', 'tar.xz', 'tar.lzma']:
        ext = 'tar'
    data_size = os.stat(data).st_size
    with open(data, 'rb') as datafile:
      AddArFileEntry(f, 'data.' + ext, datafile, content_len=data_size)


def GetChecksumsFromFile(filename, hash_fns=None):
  """Computes MD5 and/or other checksums of a file.

  Args:
    filename: Name of the file.
    hash_fns: Mapping of hash functions.
              Default is {'md5': hashlib.md5}

  Returns:
    Mapping of hash names to hexdigest strings.
    { <hashname>: <hexdigest>, ... }
  """
  hash_fns = hash_fns or {'md5': hashlib.md5}
  checksums = {k: fn() for (k, fn) in hash_fns.items()}

  with open(filename, 'rb') as file_handle:
    while True:
      buf = file_handle.read(1048576)  # 1 MiB
      if not buf:
        break
      for hashfn in checksums.values():
        hashfn.update(buf)

  return {k: fn.hexdigest() for (k, fn) in checksums.items()}


def CreateChanges(output,
                  deb_file,
                  architecture,
                  short_description,
                  maintainer,
                  package,
                  version,
                  section,
                  priority,
                  distribution,
                  urgency,
                  timestamp=0):
  """Create the changes file."""
  checksums = GetChecksumsFromFile(deb_file, {'md5': hashlib.md5,
                                              'sha1': hashlib.sha1,
                                              'sha256': hashlib.sha256})
  debsize = str(os.path.getsize(deb_file))
  deb_basename = os.path.basename(deb_file)

  changesdata = u''.join([
      MakeDebianControlField('Format', '1.8'),
      MakeDebianControlField('Date', time.ctime(timestamp)),
      MakeDebianControlField('Source', package),
      MakeDebianControlField('Binary', package),
      MakeDebianControlField('Architecture', architecture),
      MakeDebianControlField('Version', version),
      MakeDebianControlField('Distribution', distribution),
      MakeDebianControlField('Urgency', urgency),
      MakeDebianControlField('Maintainer', maintainer),
      MakeDebianControlField('Changed-By', maintainer),
      MakeDebianControlField('Description',
                             '\n%s - %s' % (package, short_description)),
      MakeDebianControlField('Changes',
                             ('\n%s (%s) %s; urgency=%s'
                              '\nChanges are tracked in revision control.') %
                             (package, version, distribution, urgency)),
      MakeDebianControlField(
          'Files', '\n' + ' '.join(
              [checksums['md5'], debsize, section, priority, deb_basename])),
      MakeDebianControlField(
          'Checksums-Sha1',
          '\n' + ' '.join([checksums['sha1'], debsize, deb_basename])),
      MakeDebianControlField(
          'Checksums-Sha256',
          '\n' + ' '.join([checksums['sha256'], debsize, deb_basename]))
  ])
  with open(output, 'wb') as changes_fh:
    changes_fh.write(changesdata.encode('utf-8'))


def GetFlagValues(flagvalues):
  if flagvalues:
    return [GetFlagValue(f, False) for f in flagvalues]
  else:
    return None


def main():
  parser = argparse.ArgumentParser(
      description='Helper for building deb packages')

  parser.add_argument('--output', required=True,
                      help='The output file, mandatory')
  parser.add_argument('--changes', required=True,
                      help='The changes output file, mandatory.')
  parser.add_argument('--data', required=True, 
                      help='Path to the data tarball, mandatory')
  parser.add_argument(
      '--preinst',
      help='The preinst script (prefix with @ to provide a path).')
  parser.add_argument(
      '--postinst',
      help='The postinst script (prefix with @ to provide a path).')
  parser.add_argument(
      '--prerm',
      help='The prerm script (prefix with @ to provide a path).')
  parser.add_argument(
      '--postrm',
      help='The postrm script (prefix with @ to provide a path).')
  parser.add_argument(
      '--config',
      help='The config script (prefix with @ to provide a path).')
  parser.add_argument(
      '--templates',
      help='The templates file (prefix with @ to provide a path).')
  # see
  # https://www.debian.org/doc/manuals/debian-faq/ch-pkg_basics.en.html#s-conffile
  parser.add_argument(
      '--conffile', action='append',
      help='List of conffiles (prefix item with @ to provide a path)')
  AddControlFlags(parser)
  options = parser.parse_args()

  CreateDeb(
      options.output,
      options.data,
      preinst=GetFlagValue(options.preinst, False),
      postinst=GetFlagValue(options.postinst, False),
      prerm=GetFlagValue(options.prerm, False),
      postrm=GetFlagValue(options.postrm, False),
      config=GetFlagValue(options.config, False),
      templates=GetFlagValue(options.templates, False),
      conffiles=GetFlagValues(options.conffile),
      package=options.package,
      version=GetFlagValue(options.version),
      description=GetFlagValue(options.description),
      maintainer=GetFlagValue(options.maintainer),
      section=options.section,
      architecture=options.architecture,
      depends=GetFlagValues(options.depends),
      suggests=options.suggests,
      enhances=options.enhances,
      preDepends=options.pre_depends,
      recommends=options.recommends,
      replaces=options.replaces,
      homepage=GetFlagValue(options.homepage),
      builtUsing=GetFlagValue(options.built_using),
      priority=options.priority,
      conflicts=options.conflicts,
      breaks=options.breaks,
      installedSize=GetFlagValue(options.installed_size))
  CreateChanges(
      output=options.changes,
      deb_file=options.output,
      architecture=options.architecture,
      short_description=GetFlagValue(options.description).split('\n')[0],
      maintainer=GetFlagValue(options.maintainer), package=options.package,
      version=GetFlagValue(options.version), section=options.section,
      priority=options.priority, distribution=options.distribution,
      urgency=options.urgency)

if __name__ == '__main__':
  main()
