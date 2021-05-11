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
import zipfile

from rules_pkg.private.helpers import SplitNameValuePairAtSeparator

ZIP_EPOCH = 315532800


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

  parser.add_argument(
      '-m', '--mode',
      help='The file system mode to use for files added into the zip.')

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


def main(args):
  unix_ts = max(ZIP_EPOCH, args.timestamp)
  ts = parse_date(unix_ts)
  default_mode = None
  if args.mode:
    default_mode = int(args.mode, 8)

  with zipfile.ZipFile(args.output, 'w') as zip_file:
    for f in args.files or []:
      (src_path, dst_path) = SplitNameValuePairAtSeparator(f, '=')

      dst_path = _combine_paths(args.directory, dst_path)

      entry_info = zipfile.ZipInfo(filename=dst_path, date_time=ts)

      if default_mode:
        entry_info.external_attr = default_mode << 16

      entry_info.compress_type = zipfile.ZIP_DEFLATED

      # the zipfile library doesn't support adding a file by path with write()
      # and specifying a ZipInfo at the same time.
      with open(src_path, 'rb') as src:
        data = src.read()
        zip_file.writestr(entry_info, data)

if __name__ == '__main__':
  arg_parser = _create_argument_parser()
  main(arg_parser.parse_args())
