import os
import tarfile

def assertTarFileContent(test_class, tar, content):
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
      test_class.assertLess(i, len(content), error_msg)
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
        test_class.assertEqual(value, v, error_msg)
      i += 1
    if i < len(content):
      test_class.fail("Missing file %s in archive %s" % (content[i], tar))
