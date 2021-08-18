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
"""This tool builds zip files from a list of inputs."""

import argparse
import datetime
import json
import zipfile

from private import build_info
from private import helpers
from private import manifest

ZIP_EPOCH = 315532800

# Unix dir bit and Windows dir bit. Magic from zip spec
UNIX_DIR_BIT = 0o40000
MSDOS_DIR_BIT = 0x10

def _create_argument_parser():
  """Creates the command line arg parser."""
  parser = argparse.ArgumentParser(description='create a zip file',
                                   fromfile_prefix_chars='@')
  parser.add_argument('-o', '--output', type=str,
                      help='The output zip file path.')
  parser.add_argument(
      '-d', '--directory', type=str, default='/',
      help='An absolute path to use as a prefix for all files in the zip.')
  parser.add_argument(
      '-t', '--timestamp', type=int, default=ZIP_EPOCH,
      help='The unix time to use for files added into the zip. values prior to'
           ' Jan 1, 1980 are ignored.')
  parser.add_argument('--stamp_from', default='',
                      help='File to find BUILD_STAMP in')
  parser.add_argument(
      '-m', '--mode',
      help='The file system mode to use for files added into the zip.')
  parser.add_argument('--manifest',
                      help='manifest of contents to add to the layer.')
  parser.add_argument(
      'files', type=str, nargs='*',
      help='Files to be added to the zip, in the form of {srcpath}={dstpath}.')
  return parser


def _combine_paths(left, right):
  result = left.rstrip('/') + '/' + right.lstrip('/')

  # important: remove leading /'s: the zip format spec says paths should never
  # have a leading slash, but Python will happily do this. The built-in zip
  # tool in Windows will complain that such a zip file is invalid.
  return result.lstrip('/')


def parse_date(ts):
  ts = datetime.datetime.utcfromtimestamp(ts)
  return (ts.year, ts.month, ts.day, ts.hour, ts.minute, ts.second)

def _add_manifest_entry(options, zip_file, entry, default_mode, ts):
  """Add an entry to the zip file.

  Args:
    options: parsed options
    zip_file: ZipFile to write to
    entry: manifest entry
    default_mode: (int) file mode to use if not specified in the entry.
    ts: (int) time stamp to add to files
  """

  entry_type, dest, src, mode, user, group = entry

  # Use the pkg_tar mode/owner remaping as a fallback
  non_abs_path = dest.strip('/')
  dst_path = _combine_paths(options.directory, non_abs_path)
  if entry_type == manifest.ENTRY_IS_DIR and not dst_path.endswith('/'):
    dst_path += '/'
  entry_info = zipfile.ZipInfo(filename=dst_path, date_time=ts)
  # See http://www.pkware.com/documents/casestudies/APPNOTE.TXT
  # denotes UTF-8 encoded file name.
  entry_info.flag_bits |= 0x800
  if mode:
    f_mode = int(mode, 8)
  else:
    f_mode = default_mode

  # See: https://trac.edgewall.org/attachment/ticket/8919/ZipDownload.patch
  # external_attr is 4 bytes in size. The high order two bytes represent UNIX
  # permission and file type bits, while the low order two contain MS-DOS FAT file
  # attributes.
  entry_info.external_attr = f_mode << 16
  if entry_type == manifest.ENTRY_IS_FILE:
    entry_info.compress_type = zipfile.ZIP_DEFLATED
    with open(src, 'rb') as src:
      zip_file.writestr(entry_info, src.read())
  elif entry_type == manifest.ENTRY_IS_DIR:
    entry_info.compress_type = zipfile.ZIP_STORED
    # Set directory bits
    entry_info.external_attr |= (UNIX_DIR_BIT << 16) | MSDOS_DIR_BIT
    zip_file.writestr(entry_info, '')
  # TODO(#309): All the rest

def main(args):
  unix_ts = max(ZIP_EPOCH, args.timestamp)
  if args.stamp_from:
    unix_ts = build_info.get_timestamp(args.stamp_from)
  ts = parse_date(unix_ts)
  default_mode = None
  if args.mode:
    default_mode = int(args.mode, 8)

  with zipfile.ZipFile(args.output, mode='w') as zip_file:
    if args.manifest:
      with open(args.manifest, 'r') as manifest_fp:
        manifest = json.load(manifest_fp)
        for entry in manifest:
          _add_manifest_entry(args, zip_file, entry, default_mode, ts)


if __name__ == '__main__':
  arg_parser = _create_argument_parser()
  main(arg_parser.parse_args())
