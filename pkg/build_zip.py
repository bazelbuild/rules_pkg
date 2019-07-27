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

from datetime import datetime
from helpers import SplitNameValuePairAtSeparator
from optparse import OptionParser
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ZIP_EPOCH = 315532800

def get_options_parser():
  parser = OptionParser()

  parser.add_option(
    '-o',
    '--output',
    type = 'string',
    dest = 'output',
    help = 'the output zip file path',
  )

  parser.add_option(
    '-f',
    '--file',
    type = 'string',
    action = 'append',
    dest = 'files',
    help = 'a file to add to the zip, in the form of {src_path}={dst_path}',
  )

  parser.add_option(
    '-d',
    '--directory',
    type = 'string',
    dest = 'directory',
    default = '/',
    help = 'an absolute path to use as a prefix for all files in the zip',
  )

  parser.add_option(
    '-t',
    '--timestamp',
    type = 'int',
    dest = 'timestamp',
    default = ZIP_EPOCH,
    help = 'the unix time to use for files added into the zip. values prior to Jan 1, 1980 are ignored.'
  )

  return parser

def remove_leading_slash(path):
  if path[0] == '/':
    return path[1:]
  return path

def remove_trailing_slash(path):
  if path.endswith('/'):
    return path[:-1]
  return path

def combine_paths(package_dir, dst_path):
  dst_path = remove_leading_slash(dst_path)

  dst_path = package_dir + '/' + dst_path

  # remove leading /'s: the zip format spec says paths should never have a
  # leading slash, but Python will happily do this. The built-in zip tool
  # in Windows will complain that such a zip file is invalid.
  dst_path = remove_leading_slash(dst_path)

  return dst_path

def main(options):
  package_dir = remove_trailing_slash(options.directory)
  ts = datetime.utcfromtimestamp(max(ZIP_EPOCH, options.timestamp))
  ts = (ts.year, ts.month, ts.day, ts.hour, ts.minute, ts.second)

  with ZipFile(options.output, 'w') as zip:
    for f in options.files or []:
      (src_path, dst_path) = SplitNameValuePairAtSeparator(f, '=')

      dst_path = combine_paths(package_dir, dst_path)

      entry_info = ZipInfo(
        filename = dst_path,
        date_time = ts,
      )

      entry_info.compress_type = ZIP_DEFLATED

      # the zipfile library doesn't support adding a file by path with write()
      # and specifying a ZipInfo at the same time.
      with open(src_path, 'rb') as src:
        data = src.read()
        zip.writestr(entry_info, data)

if __name__ == '__main__':
  parser = get_options_parser()
  (options, unused_args) = parser.parse_args()
  main(options)
