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
"""Testing for archive."""

import os
import tarfile
import unittest

from bazel_tools.tools.python.runfiles import runfiles
from pkg.private import archive
from tests.tar import compressor


class SimpleArFileTest(unittest.TestCase):
  """Testing for SimpleArFile class."""

  def setUp(self):
    super(SimpleArFileTest, self).setUp()
    self.data_files = runfiles.Create()

  def assertArFileContent(self, arfile, content):
    """Assert that arfile contains exactly the entry described by `content`.

    Args:
      arfile: the path to the AR file to test.
      content: an array describing the expected content of the AR file.
          Each entry in that list should be a dictionary where each field
          is a field to test in the corresponding SimpleArFileEntry. For
          testing the presence of a file "x", then the entry could simply
          be `{"filename": "x"}`, the missing field will be ignored.
    """
    print("READING: %s" % arfile)
    with archive.SimpleArFile(arfile) as f:
      current = f.next()
      i = 0
      while current:
        error_msg = "Extraneous file at end of archive %s: %s" % (
            arfile,
            current.filename
            )
        self.assertLess(i, len(content), error_msg)
        for k, v in content[i].items():
          value = getattr(current, k)
          error_msg = " ".join([
              "Value `%s` for key `%s` of file" % (value, k),
              "%s in archive %s does" % (current.filename, arfile),
              "not match expected value `%s`" % v
              ])
          self.assertEqual(value, v, error_msg)
        current = f.next()
        i += 1
      if i < len(content):
        self.fail("Missing file %s in archive %s" % (content[i], arfile))

  def testEmptyArFile(self):
    self.assertArFileContent(
        self.data_files.Rlocation("rules_pkg/tests/testdata/empty.ar"),
        [])

  def assertSimpleFileContent(self, names):
    datafile = self.data_files.Rlocation(
        "rules_pkg/tests/testdata/" + "_".join(names) + ".ar")
    # pylint: disable=g-complex-comprehension
    content = [{"filename": n,
                "size": len(n.encode("utf-8")),
                "data": n.encode("utf-8")}
               for n in names]
    self.assertArFileContent(datafile, content)

  def testAFile(self):
    self.assertSimpleFileContent(["a"])

  def testBFile(self):
    self.assertSimpleFileContent(["b"])

  def testABFile(self):
    self.assertSimpleFileContent(["ab"])

  def testA_BFile(self):
    self.assertSimpleFileContent(["a", "b"])

  def testA_ABFile(self):
    self.assertSimpleFileContent(["a", "ab"])

  def testA_B_ABFile(self):
    self.assertSimpleFileContent(["a", "b", "ab"])


class TarFileWriterTest(unittest.TestCase):
  """Testing for TarFileWriter class."""

  def assertTarFileContent(self, tar, content):
    """Assert that tarfile contains exactly the entry described by `content`.

    Args:
        tar: the path to the TAR file to test.
        content: an array describing the expected content of the TAR file.
            Each entry in that list should be a dictionary where each field
            is a field to test in the corresponding TarInfo. For
            testing the presence of a file "x", then the entry could simply
            be `{"name": "x"}`, the missing field will be ignored. To match
            the content of a file entry, use the key "data".
    """
    got_names = []
    with tarfile.open(tar, "r:*") as f:
      for current in f:
        got_names.append(getattr(current, "name"))

    with tarfile.open(tar, "r:*") as f:
      i = 0
      for current in f:
        error_msg = "Extraneous file at end of archive %s: %s" % (
            tar,
            current.name
            )
        self.assertLess(i, len(content), error_msg)
        for k, v in content[i].items():
          if k == "data":
            value = f.extractfile(current).read()
          elif k == "name" and os.name == "nt":
            value = getattr(current, k).replace("\\", "/")
          else:
            value = getattr(current, k)
          error_msg = " ".join([
              "Value `%s` for key `%s` of file" % (value, k),
              "%s in archive %s does" % (current.name, tar),
              "not match expected value `%s`" % v
              ])
          error_msg += str(got_names)
          self.assertEqual(value, v, error_msg)
        i += 1
      if i < len(content):
        self.fail("Missing file %s in archive %s" % (content[i], tar))

  def setUp(self):
    super(TarFileWriterTest, self).setUp()
    self.tempfile = os.path.join(os.environ["TEST_TMPDIR"], "test.tar")
    self.data_files = runfiles.Create()

  def tearDown(self):
    super(TarFileWriterTest, self).tearDown()
    if os.path.exists(self.tempfile):
      os.remove(self.tempfile)

  def testEmptyTarFile(self):
    with archive.TarFileWriter(self.tempfile):
      pass
    self.assertTarFileContent(self.tempfile, [])

  def assertSimpleFileContent(self, names):
    with archive.TarFileWriter(self.tempfile) as f:
      for n in names:
        f.add_file(n, content=n)
    # pylint: disable=g-complex-comprehension
    content = ([{"name": "."}] +
               [{"name": n,
                 "size": len(n.encode("utf-8")),
                 "data": n.encode("utf-8")}
                for n in names])
    self.assertTarFileContent(self.tempfile, content)

  def testAddFile(self):
    self.assertSimpleFileContent(["./a"])
    self.assertSimpleFileContent(["./b"])
    self.assertSimpleFileContent(["./ab"])
    self.assertSimpleFileContent(["./a", "./b"])
    self.assertSimpleFileContent(["./a", "./ab"])
    self.assertSimpleFileContent(["./a", "./b", "./ab"])

  def testDottedFiles(self):
    with archive.TarFileWriter(self.tempfile) as f:
      f.add_file("a")
      f.add_file("/b")
      f.add_file("./c")
      f.add_file("./.d")
      f.add_file("..e")
      f.add_file(".f")
    content = [
        {"name": "."}, {"name": "./a"}, {"name": "/b"}, {"name": "./c"},
        {"name": "./.d"}, {"name": "./..e"}, {"name": "./.f"}
    ]
    self.assertTarFileContent(self.tempfile, content)

  def testAddDir(self):
    # For some strange reason, ending slash is stripped by the test
    content = [
        {"name": ".", "mode": 0o755},
        {"name": "./a", "mode": 0o755},
        {"name": "./a/b", "data": b"ab", "mode": 0o644},
        {"name": "./a/c", "mode": 0o755},
        {"name": "./a/c/d", "data": b"acd", "mode": 0o644},
        ]
    tempdir = os.path.join(os.environ["TEST_TMPDIR"], "test_dir")
    # Iterate over the `content` array to create the directory
    # structure it describes.
    for c in content:
      if "data" in c:
        # Create files is happening locally, so use native path sep.
        path_parts = c["name"][2:].split('/')
        p = os.path.join(tempdir, *path_parts)
        os.makedirs(os.path.dirname(p))
        with open(p, "wb") as f:
          f.write(c["data"])
    with archive.TarFileWriter(self.tempfile) as f:
      f.add_dir("./", tempdir, mode=0o644)
    self.assertTarFileContent(self.tempfile, content)

  def testMergeTar(self):
    content = [
        {"name": "./a", "data": b"a"},
        {"name": "./ab", "data": b"ab"},
        ]
    for ext in [("." + comp if comp else "") for comp in archive.COMPRESSIONS]:
      with archive.TarFileWriter(self.tempfile) as f:
        datafile = self.data_files.Rlocation(
            "rules_pkg/tests/testdata/tar_test.tar" + ext)
        f.add_tar(datafile, name_filter=lambda n: n != "./b")
      self.assertTarFileContent(self.tempfile, content)

  def testMergeTarRelocated(self):
    content = [
        {"name": ".", "mode": 0o755},
        {"name": "./foo", "mode": 0o755},
        {"name": "./foo/a", "data": b"a"},
        {"name": "./foo/ab", "data": b"ab"},
        ]
    with archive.TarFileWriter(self.tempfile) as f:
      datafile = self.data_files.Rlocation(
          "rules_pkg/tests/testdata/tar_test.tar")
      f.add_tar(datafile, name_filter=lambda n: n != "./b", root="/foo")
    self.assertTarFileContent(self.tempfile, content)

  def testDefaultMtimeNotProvided(self):
    with archive.TarFileWriter(self.tempfile) as f:
      self.assertEqual(f.default_mtime, 0)

  def testDefaultMtimeProvided(self):
    with archive.TarFileWriter(self.tempfile, default_mtime=1234) as f:
      self.assertEqual(f.default_mtime, 1234)

  def testPortableMtime(self):
    with archive.TarFileWriter(self.tempfile, default_mtime="portable") as f:
      self.assertEqual(f.default_mtime, 946684800)

  def testPreserveTarMtimesTrueByDefault(self):
    with archive.TarFileWriter(self.tempfile) as f:
      input_tar_path = self.data_files.Rlocation(
          "rules_pkg/tests/testdata/tar_test.tar")
      f.add_tar(input_tar_path)
      input_tar = tarfile.open(input_tar_path, "r")
      for file_name in f.members:
        input_file = input_tar.getmember(file_name)
        output_file = f.tar.getmember(file_name)
        self.assertEqual(input_file.mtime, output_file.mtime)

  def testPreserveTarMtimesFalse(self):
    with archive.TarFileWriter(self.tempfile, preserve_tar_mtimes=False) as f:
      input_tar_path = self.data_files.Rlocation(
          "rules_pkg/tests/testdata/tar_test.tar")
      f.add_tar(input_tar_path)
      for output_file in f.tar:
        self.assertEqual(output_file.mtime, 0)

  def testAddingDirectoriesForFile(self):
    with archive.TarFileWriter(self.tempfile) as f:
      f.add_file("d/f")
    content = [
        {"name": ".",
         "mode": 0o755},
        {"name": "./d",
         "mode": 0o755},
        {"name": "./d/f"},
    ]
    self.assertTarFileContent(self.tempfile, content)

  def testAddingDirectoriesForFileSeparately(self):
    d_dir = os.path.join(os.environ["TEST_TMPDIR"], "d_dir")
    os.makedirs(d_dir)
    with open(os.path.join(d_dir, "dir_file"), "w"):
      pass
    a_dir = os.path.join(os.environ["TEST_TMPDIR"], "a_dir")
    os.makedirs(a_dir)
    with open(os.path.join(a_dir, "dir_file"), "w"):
      pass

    with archive.TarFileWriter(self.tempfile) as f:
      f.add_dir("d", d_dir)
      f.add_file("d/f")

      f.add_dir("a", a_dir)
      f.add_file("a/b/f")
    content = [
        {"name": ".",
         "mode": 0o755},
        {"name": "./d",
         "mode": 0o755},
        {"name": "./d/dir_file"},
        {"name": "./d/f"},
        {"name": "./a",
         "mode": 0o755},
        {"name": "./a/dir_file"},
        {"name": "./a/b",
         "mode": 0o755},
        {"name": "./a/b/f"},
    ]
    self.assertTarFileContent(self.tempfile, content)

  def testAddingDirectoriesForFileManually(self):
    with archive.TarFileWriter(self.tempfile) as f:
      f.add_file("d", tarfile.DIRTYPE)
      f.add_file("d/f")

      f.add_file("a", tarfile.DIRTYPE)
      f.add_file("a/b", tarfile.DIRTYPE)
      f.add_file("a/b", tarfile.DIRTYPE)
      f.add_file("a/b/", tarfile.DIRTYPE)
      f.add_file("a/b/c/f")

      f.add_file("x/y/f")
      f.add_file("x", tarfile.DIRTYPE)
    content = [
        {"name": ".",
         "mode": 0o755},
        {"name": "./d",
         "mode": 0o755},
        {"name": "./d/f"},
        {"name": "./a",
         "mode": 0o755},
        {"name": "./a/b",
         "mode": 0o755},
        {"name": "./a/b/c",
         "mode": 0o755},
        {"name": "./a/b/c/f"},
        {"name": "./x",
         "mode": 0o755},
        {"name": "./x/y",
         "mode": 0o755},
        {"name": "./x/y/f"},
    ]
    self.assertTarFileContent(self.tempfile, content)

  def testChangingRootDirectory(self):
    with archive.TarFileWriter(self.tempfile, root_directory="root") as f:
      f.add_file("d", tarfile.DIRTYPE)
      f.add_file("d/f")

      f.add_file("a", tarfile.DIRTYPE)
      f.add_file("a/b", tarfile.DIRTYPE)
      f.add_file("a/b", tarfile.DIRTYPE)
      f.add_file("a/b/", tarfile.DIRTYPE)
      f.add_file("a/b/c/f")

      f.add_file("x/y/f")
      f.add_file("x", tarfile.DIRTYPE)
    content = [
        {"name": "root",
         "mode": 0o755},
        {"name": "root/d",
         "mode": 0o755},
        {"name": "root/d/f"},
        {"name": "root/a",
         "mode": 0o755},
        {"name": "root/a/b",
         "mode": 0o755},
        {"name": "root/a/b/c",
         "mode": 0o755},
        {"name": "root/a/b/c/f"},
        {"name": "root/x",
         "mode": 0o755},
        {"name": "root/x/y",
         "mode": 0o755},
        {"name": "root/x/y/f"},
    ]
    self.assertTarFileContent(self.tempfile, content)

  def testPackageDirFileAttribute(self):
    """Tests package_dir and package_dir_file attributes of pkg_tar.

    Verifies that passing package_dir (string) and package_dir_file(label) to
    pkg_tar yields identical results.
    """
    package_dir = self.data_files.Rlocation(
        "rules_pkg/tests/tar/test_tar_package_dir.tar")
    package_dir_file = self.data_files.Rlocation(
        "rules_pkg/tests/tar/test_tar_package_dir_file.tar")

    expected_content = [
        {"name": "."},
        {"name": "./package"},
        {"name": "./package/nsswitch.conf"},
    ]

    self.assertTarFileContent(package_dir, expected_content)
    self.assertTarFileContent(package_dir_file, expected_content)

  def testCustomCompression(self):
    original = self.data_files.Rlocation(
        "rules_pkg/tests/testdata/tar_test.tar")
    compressed = self.data_files.Rlocation(
        "rules_pkg/tests/tar/test_tar_compression.tar")
    expected_content = [
        {"name": "./" + x, "data": x.encode("utf-8")} for x in ["a", "b", "ab"]
    ]
    with open(compressed, "rb") as f_in, open(self.tempfile, "wb") as f_out:
      # "Decompress" by skipping garbage bytes
      f_in.seek(len(compressor.GARBAGE))
      f_out.write(f_in.read())

    self.assertTarFileContent(original, expected_content)
    self.assertTarFileContent(self.tempfile, expected_content)

if __name__ == "__main__":
  unittest.main()
