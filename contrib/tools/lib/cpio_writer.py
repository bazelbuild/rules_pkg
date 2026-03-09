"""CPIO archive writer.

Writes CPIO archives in the SVR4 'newc' format (ASCII with no CRC).
This format uses magic "070701" and is widely supported.

Usage:
    with open("output.cpio", "wb") as f:
        writer = CpioWriter(f)
        writer.add_file("path/to/file.txt", content, mode=0o100644)
        writer.add_directory("path/to/dir", mode=0o40755)
        writer.add_symlink("path/to/link", target="target/path")
        writer.finish()
"""

import os
import stat


class CpioWriter:
    """Write CPIO archives in SVR4 newc format."""

    MAGIC = b"070701"

    def __init__(self, stream):
        """Initialize writer with output stream.

        Args:
            stream: Binary file-like object to write to.
        """
        self.stream = stream
        self._inode = 1  # Auto-increment inode counter

    def _pad_to_4(self, size):
        """Return padding needed to reach 4-byte boundary."""
        return (4 - (size % 4)) % 4

    def _write_header(self, path, mode, uid=0, gid=0, nlink=1, mtime=0,
                      filesize=0, devmajor=0, devminor=0, rdevmajor=0,
                      rdevminor=0):
        """Write a CPIO header entry.

        Header format (110 bytes of hex ASCII):
        - 6 bytes: magic "070701"
        - 8 bytes: inode
        - 8 bytes: mode
        - 8 bytes: uid
        - 8 bytes: gid
        - 8 bytes: nlink
        - 8 bytes: mtime
        - 8 bytes: filesize
        - 8 bytes: devmajor
        - 8 bytes: devminor
        - 8 bytes: rdevmajor
        - 8 bytes: rdevminor
        - 8 bytes: namesize (including null terminator)
        - 8 bytes: checksum (0 for 070701)
        """
        path_bytes = path.encode("utf-8") + b"\x00"
        namesize = len(path_bytes)

        header = (
            f"070701"
            f"{self._inode:08X}"
            f"{mode:08X}"
            f"{uid:08X}"
            f"{gid:08X}"
            f"{nlink:08X}"
            f"{mtime:08X}"
            f"{filesize:08X}"
            f"{devmajor:08X}"
            f"{devminor:08X}"
            f"{rdevmajor:08X}"
            f"{rdevminor:08X}"
            f"{namesize:08X}"
            f"{0:08X}"  # checksum
        )
        self.stream.write(header.encode("ascii"))
        self._inode += 1

        # Write path with null terminator
        self.stream.write(path_bytes)

        # Pad to 4-byte boundary (header is 110 bytes, so total is 110 + namesize)
        header_plus_name = 110 + namesize
        padding = self._pad_to_4(header_plus_name)
        if padding:
            self.stream.write(b"\x00" * padding)

        return filesize

    def add_file(self, path, content, mode=0o100644, uid=0, gid=0, mtime=0):
        """Add a regular file to the archive.

        Args:
            path: Path within the archive.
            content: File content as bytes.
            mode: File mode (default 0o100644 = regular file, rw-r--r--).
            uid: Owner user ID.
            gid: Owner group ID.
            mtime: Modification time (Unix timestamp).
        """
        if isinstance(content, str):
            content = content.encode("utf-8")

        # Ensure mode includes regular file type
        if not (mode & 0o170000):
            mode |= stat.S_IFREG

        filesize = len(content)
        self._write_header(
            path=path,
            mode=mode,
            uid=uid,
            gid=gid,
            filesize=filesize,
            mtime=mtime,
        )

        # Write content
        self.stream.write(content)

        # Pad to 4-byte boundary
        padding = self._pad_to_4(filesize)
        if padding:
            self.stream.write(b"\x00" * padding)

    def add_directory(self, path, mode=0o40755, uid=0, gid=0, mtime=0):
        """Add a directory to the archive.

        Args:
            path: Directory path within the archive.
            mode: Directory mode (default 0o40755 = directory, rwxr-xr-x).
            uid: Owner user ID.
            gid: Owner group ID.
            mtime: Modification time.
        """
        # Ensure mode includes directory type
        if not (mode & 0o170000):
            mode |= stat.S_IFDIR

        self._write_header(
            path=path,
            mode=mode,
            uid=uid,
            gid=gid,
            nlink=2,  # Directories typically have nlink >= 2
            mtime=mtime,
        )

    def add_symlink(self, path, target, mode=0o120777, uid=0, gid=0, mtime=0):
        """Add a symbolic link to the archive.

        Args:
            path: Symlink path within the archive.
            target: Target path the symlink points to.
            mode: Symlink mode (default 0o120777 = symlink, rwxrwxrwx).
            uid: Owner user ID.
            gid: Owner group ID.
            mtime: Modification time.
        """
        target_bytes = target.encode("utf-8")

        # Ensure mode includes symlink type
        if not (mode & 0o170000):
            mode |= stat.S_IFLNK

        self._write_header(
            path=path,
            mode=mode,
            uid=uid,
            gid=gid,
            filesize=len(target_bytes),
            mtime=mtime,
        )

        # Write symlink target as file content
        self.stream.write(target_bytes)

        # Pad to 4-byte boundary
        padding = self._pad_to_4(len(target_bytes))
        if padding:
            self.stream.write(b"\x00" * padding)

    def finish(self):
        """Write the TRAILER record to finalize the archive."""
        # TRAILER!!! is a special entry marking end of archive
        path = "TRAILER!!!"
        self._write_header(
            path=path,
            mode=0,
            nlink=1,
        )
