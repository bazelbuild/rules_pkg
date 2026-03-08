import gzip
import lzma
import sys
import tarfile

PORTABLE_MTIME = 946684800  # 2000-01-01 00:00:00.000 UTC


class TarReader:
    """Testing for pkg_tar rule."""

    def __init__(self, stream, compress=None):
        if compress == "gz":
            self.stream = gzip.GzipFile(fileobj=stream, mode="r")
        elif compress == "xz":
            self.stream = lzma.LZMAFile(filename=stream, mode="r")
        else:
            self.stream = stream
        self.tarfile = tarfile.TarFile(fileobj=self.stream, mode="r")

    def next(self, return_content=False):
        info = self.tarfile.next()
        return info


def main(args):
    with open(args[1], "rb") as inp:
        reader = TarReader(inp, compress="xz")
        size = 0
        while True:
            info = reader.next()
            if not info:
                break
            size += info.size
    print(f"Total size: {size}, {size / 1000000} MiB")


if __name__ == "__main__":
    main(sys.argv)

"""
          elif k == 'data':
            value = f.extractfile(info).read()
          elif k == 'isdir':
            value = info.isdir()
          else:
            value = getattr(info, k)
          if k == 'mode':
            p_value = '0o%o' % value
            p_v = '0o%o' % v
          else:
            p_value = str(value)
            p_v = str(v)
          error_msg = ' '.join([
              'Value `%s` for key `%s` of file' % (p_value, k),
              '%s in archive %s does' % (info.name, file_path),
              'not match expected value `%s`' % p_v
              ])
          self.assertEqual(value, v, error_msg)
          if value != v:
            print(error_msg)
        i += 1
      if i < len(content):
        self.fail('Missing file %s in archive %s of [%s]' % (
            content[i], file_path, ',\n    '.join(got)))
"""
