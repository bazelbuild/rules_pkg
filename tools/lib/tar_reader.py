"""Tar file reader."""

import tarfile

from tools.lib.tree_reader import FileInfo, TreeReader


class TarReader(TreeReader):
    """Reader for tar archives (.tar, .tar.gz, .tar.bz2, .tar.xz, .tgz)."""

    def __init__(self, tar_path: str=None, tar_stream=None):
        """Initialize TarReader with either a file path or file-like object.

        Args:
            tar_path: Path to tar file (mutually exclusive with tar_stream)
            tar_stream: File-like object containing tar data (mutually exclusive with tar_path)
        """
        if tar_path is None and tar_stream is None:
            raise ValueError("Either tar_path or tar_stream must be provided")
        if tar_path is not None and tar_stream is not None:
            raise ValueError("Cannot provide both tar_path and tar_stream")

        if tar_path is not None:
            self._tar = tarfile.open(tar_path, mode='r|*')
        else:
            self._tar = tarfile.open(fileobj=tar_stream, mode='r|*')
        self._iter = iter(self._tar)
        self.done = False

    def next(self) -> FileInfo:
        if self.done:
            return None
        while True:
            try:
                tarinfo = next(self._iter)
            except StopIteration:
                self.done = True
                return None
            if tarinfo.name and tarinfo.name != './':
                break

        path = tarinfo.name.removeprefix('./')
        is_symlink = tarinfo.issym() or tarinfo.islnk()
        is_dir = tarinfo.isdir() and not is_symlink

        return FileInfo(
            path=path,
            size=0 if (is_symlink or is_dir) else tarinfo.size,
            mode=tarinfo.mode,
            uid=tarinfo.uid,
            gid=tarinfo.gid,
            is_dir=is_dir,
            is_symlink=is_symlink,
            symlink_target=tarinfo.linkname if is_symlink else None,
        )

    def is_done(self) -> bool:
        return self.done
