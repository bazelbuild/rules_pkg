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
#
# -*- coding: utf-8 -*-
"""Testing for archive."""

import codecs
from io import BytesIO
import os
import sys
import tarfile
import tempfile
import types
import unittest
from unittest import mock

from pkg.private.deb import make_deb

class MakeControlFieldTest(unittest.TestCase):
  """Tests for MakeControlField.

  https://www.debian.org/doc/debian-policy/ch-controlfields.html#syntax-of-control-files
  """

  def test_simple(self):
    self.assertEqual(
        'Package: fizzbuzz\n',
        make_deb.MakeDebianControlField('Package', 'fizzbuzz'))

  def test_simple_strip(self):
    self.assertEqual(
        'Package: fizzbuzz\n',
        make_deb.MakeDebianControlField('Package', ' fizzbuzz'))
    self.assertEqual(
        'Package: fizzbuzz\n',
        make_deb.MakeDebianControlField('Package', ' fizzbuzz '))

  def test_simple_no_newline(self):
    with self.assertRaises(ValueError):
      make_deb.MakeDebianControlField('Package', ' fizz\nbuzz ')


  def test_multiline(self):
    self.assertEqual(
        'Description: fizzbuzz\n',
        make_deb.MakeDebianControlField(
            'Description', 'fizzbuzz', multiline=make_deb.Multiline.YES))
    self.assertEqual(
        'Description: fizz\n buzz\n',
        make_deb.MakeDebianControlField(
            'Description', 'fizz\n buzz\n', multiline=make_deb.Multiline.YES))
    self.assertEqual(
        'Description:\n fizz\n buzz\n',
        make_deb.MakeDebianControlField(
            'Description', ' fizz\n buzz\n', multiline=make_deb.Multiline.YES_ADD_NEWLINE))

  def test_multiline_add_required_space(self):
    self.assertEqual(
        'Description: fizz\n buzz\n',
        make_deb.MakeDebianControlField(
            'Description', 'fizz\nbuzz', multiline=make_deb.Multiline.YES))
    self.assertEqual(
        'Description:\n fizz\n buzz\n',
        make_deb.MakeDebianControlField(
            'Description', 'fizz\nbuzz\n', multiline=make_deb.Multiline.YES_ADD_NEWLINE))

  def test_multiline_add_trailing_newline(self):
    self.assertEqual(
        'Description: fizz\n buzz\n baz\n',
        make_deb.MakeDebianControlField(
            'Description', 'fizz\n buzz\n baz', multiline=make_deb.Multiline.YES))


def _write_tar_gz(path, contents):
  """Write a tar.gz at path with the given {name: bytes} contents."""
  with tarfile.open(path, mode='w:gz') as tar:
    for name, data in contents.items():
      info = tarfile.TarInfo(name)
      info.size = len(data)
      tar.addfile(info, fileobj=BytesIO(data))


def _uncompressed_tar_bytes(contents):
  """Return the bytes of an uncompressed tar with the given {name: bytes}."""
  buf = BytesIO()
  with tarfile.open(fileobj=buf, mode='w') as tar:
    for name, data in contents.items():
      info = tarfile.TarInfo(name)
      info.size = len(data)
      tar.addfile(info, fileobj=BytesIO(data))
  return buf.getvalue()


_FAKE_ZSTD_MAGIC = b'FAKEZSTD:'


def _fake_zstd_open(filename, mode='rb'):
  """Stand-in for compression.zstd.open (stdlib only from Python 3.14).

  Lets ComputeInstalledSizeKib's zstd fallback path be exercised on older
  Pythons without a real zstd dependency: "compression" here is just a
  magic-byte prefix, stripped back off on open().
  """
  with open(filename, 'rb') as f:
    data = f.read()
  assert data.startswith(_FAKE_ZSTD_MAGIC)
  return BytesIO(data[len(_FAKE_ZSTD_MAGIC):])


def _block_compression_zstd_module():
  """A sys.modules patch dict that makes `from compression import zstd` fail."""
  return {'compression': None, 'compression.zstd': None}


def _fake_compression_zstd_module():
  """A sys.modules patch dict providing a fake compression.zstd module."""
  fake_zstd = types.ModuleType('compression.zstd')
  fake_zstd.open = _fake_zstd_open
  fake_compression = types.ModuleType('compression')
  fake_compression.zstd = fake_zstd
  return {'compression': fake_compression, 'compression.zstd': fake_zstd}


class ComputeInstalledSizeKibTest(unittest.TestCase):
  """Tests for ComputeInstalledSizeKib."""

  def setUp(self):
    super(ComputeInstalledSizeKibTest, self).setUp()
    self.tmpdir = tempfile.TemporaryDirectory()

  def tearDown(self):
    self.tmpdir.cleanup()
    super(ComputeInstalledSizeKibTest, self).tearDown()

  def _tar_path(self, name='data.tar.gz'):
    return os.path.join(self.tmpdir.name, name)

  def test_sums_member_sizes_and_rounds_up(self):
    path = self._tar_path()
    # 1000 + 100 = 1100 bytes -> ceil(1100 / 1024) = 2 KiB.
    _write_tar_gz(path, {'a': b'x' * 1000, 'b': b'y' * 100})
    self.assertEqual(make_deb.ComputeInstalledSizeKib(path), '2')

  def test_exact_multiple_of_1024_is_not_rounded_up(self):
    path = self._tar_path()
    _write_tar_gz(path, {'a': b'x' * 1024})
    self.assertEqual(make_deb.ComputeInstalledSizeKib(path), '1')

  def test_empty_tar_returns_zero(self):
    path = self._tar_path()
    _write_tar_gz(path, {})
    self.assertEqual(make_deb.ComputeInstalledSizeKib(path), '0')

  def test_unreadable_file_returns_none(self):
    path = self._tar_path('data.tar.zst')
    with open(path, 'wb') as f:
      f.write(b'not actually a tar')
    with mock.patch.dict(sys.modules, _block_compression_zstd_module()):
      self.assertIsNone(make_deb.ComputeInstalledSizeKib(path))

  def test_zstd_without_module_returns_none(self):
    # On a Python without compression.zstd (stdlib only from 3.14), a real
    # zstd-compressed tar can't be read, same as any other unreadable input.
    path = self._tar_path('data.tar.zst')
    with open(path, 'wb') as f:
      f.write(_FAKE_ZSTD_MAGIC + _uncompressed_tar_bytes({'a': b'x' * 1024}))
    with mock.patch.dict(sys.modules, _block_compression_zstd_module()):
      self.assertIsNone(make_deb.ComputeInstalledSizeKib(path))

  def test_zstd_with_module_is_decompressed(self):
    path = self._tar_path('data.tar.zst')
    with open(path, 'wb') as f:
      f.write(_FAKE_ZSTD_MAGIC + _uncompressed_tar_bytes({'a': b'x' * 1024}))
    with mock.patch.dict(sys.modules, _fake_compression_zstd_module()):
      self.assertEqual(make_deb.ComputeInstalledSizeKib(path), '1')


if __name__ == '__main__':
  unittest.main()
