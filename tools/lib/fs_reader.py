#!/usr/bin/env python3

import os

from tools.lib.tree_reader import FileInfo, TreeReader


class FileSystemReader(TreeReader):
    """Reader for filesystem directories."""

    def __init__(self, folder_path: str):
        folder_path = os.path.abspath(folder_path)
        if not os.path.isdir(folder_path):
            raise ValueError(f"Path is not a directory: {folder_path}")

        self.root = folder_path
        self._gen = self._scan_directory()
        self.done = False

    def _scan_directory(self):
        """Walk directory tree, yielding FileInfo for each entry."""
        for dirpath, dirnames, filenames in os.walk(self.root, followlinks=False):
            # Yield directories
            for dirname in sorted(dirnames):
                full_path = os.path.join(dirpath, dirname)
                rel_path = os.path.relpath(full_path, self.root)
                stat_info = os.lstat(full_path)
                is_symlink = os.path.islink(full_path)

                yield FileInfo(
                    path=rel_path,
                    size=0,
                    mode=stat_info.st_mode,
                    uid=stat_info.st_uid,
                    gid=stat_info.st_gid,
                    is_dir=not is_symlink,
                    is_symlink=is_symlink,
                    symlink_target=os.readlink(full_path) if is_symlink else None
                )

            # Yield files
            for filename in sorted(filenames):
                full_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(full_path, self.root)
                stat_info = os.lstat(full_path)
                is_symlink = os.path.islink(full_path)

                yield FileInfo(
                    path=rel_path,
                    size=0 if is_symlink else stat_info.st_size,
                    mode=stat_info.st_mode,
                    uid=stat_info.st_uid,
                    gid=stat_info.st_gid,
                    is_dir=False,
                    is_symlink=is_symlink,
                    symlink_target=os.readlink(full_path) if is_symlink else ""
                )

    def next(self) -> FileInfo:
        """Return the next FileInfo, or None if no more items."""
        if self.done:
            return None
        try:
            return next(self._gen)
        except StopIteration:
            self.done = True
            return None

    def is_done(self) -> bool:
        """Return True if all items have been read."""
        return self.done
