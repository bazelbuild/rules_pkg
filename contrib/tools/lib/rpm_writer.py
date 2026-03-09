# Copyright 2026 The Bazel Authors. All rights reserved.
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
"""RPM file writer.

Creates RPM packages without requiring rpmbuild or Linux-specific tools.
The generated RPMs are unsigned but otherwise valid.

This writes RPM format version 3 files using the SVR4 newc CPIO format
for the payload.
"""

import bz2
import gzip
import hashlib
import io
import lzma
import os
import stat
import struct
import time

from contrib.tools.lib.cpio_writer import CpioWriter


# RPM Lead constants
RPM_MAGIC = b"\xed\xab\xee\xdb"
RPM_MAJOR = 3
RPM_MINOR = 0
RPM_TYPE_BINARY = 0
RPM_TYPE_SOURCE = 1

# RPM Header magic
RPM_HEADER_MAGIC = b"\x8e\xad\xe8"
RPM_HEADER_VERSION = 1

# Header tag types
HEADER_NULL = 0
HEADER_CHAR = 1
HEADER_INT8 = 2
HEADER_INT16 = 3
HEADER_INT32 = 4
HEADER_INT64 = 5
HEADER_STRING = 6
HEADER_BIN = 7
HEADER_STRING_ARRAY = 8
HEADER_I18NSTRING = 9

# Signature tags
SIGTAG_SIZE = 1000          # Size of header + payload
SIGTAG_MD5 = 1004           # MD5 of header + payload
SIGTAG_PAYLOADSIZE = 1007   # Uncompressed payload size

# Header tags - required for a minimal RPM
RPMTAG_NAME = 1000
RPMTAG_VERSION = 1001
RPMTAG_RELEASE = 1002
RPMTAG_SUMMARY = 1004
RPMTAG_DESCRIPTION = 1005
RPMTAG_BUILDTIME = 1006
RPMTAG_BUILDHOST = 1007
RPMTAG_SIZE = 1009
RPMTAG_LICENSE = 1014
RPMTAG_GROUP = 1016
RPMTAG_OS = 1021
RPMTAG_ARCH = 1022
RPMTAG_FILESIZES = 1028
RPMTAG_FILEMODES = 1030
RPMTAG_FILERDEVS = 1033
RPMTAG_FILEMTIMES = 1034
RPMTAG_FILEMD5S = 1035      # Or FILEDIGESTS
RPMTAG_FILELINKTOS = 1036
RPMTAG_FILEFLAGS = 1037
RPMTAG_FILEUSERNAME = 1039
RPMTAG_FILEGROUPNAME = 1040
RPMTAG_SOURCERPM = 1044
RPMTAG_FILEVERIFYFLAGS = 1045
RPMTAG_PROVIDENAME = 1047
RPMTAG_REQUIREFLAGS = 1048
RPMTAG_REQUIRENAME = 1049
RPMTAG_REQUIREVERSION = 1050
RPMTAG_RPMVERSION = 1064
RPMTAG_DIRINDEXES = 1116
RPMTAG_BASENAMES = 1117
RPMTAG_DIRNAMES = 1118
RPMTAG_OPTFLAGS = 1122
RPMTAG_PAYLOADFORMAT = 1124
RPMTAG_PAYLOADCOMPRESSOR = 1125
RPMTAG_PAYLOADFLAGS = 1126
RPMTAG_PLATFORM = 1132
RPMTAG_FILEDEVICES = 1095
RPMTAG_FILEINODES = 1096
RPMTAG_FILELANGS = 1097

# File flags
RPMFILE_CONFIG = (1 << 0)
RPMFILE_DOC = (1 << 1)
RPMFILE_DONOTUSE = (1 << 2)
RPMFILE_MISSINGOK = (1 << 3)
RPMFILE_NOREPLACE = (1 << 4)
RPMFILE_SPECFILE = (1 << 5)
RPMFILE_GHOST = (1 << 6)
RPMFILE_LICENSE = (1 << 7)
RPMFILE_README = (1 << 8)


class RpmHeaderBuilder:
    """Builds RPM header sections."""

    def __init__(self):
        self.entries = []  # List of (tag, type, data)

    def add_int32(self, tag, values):
        """Add INT32 tag with one or more values."""
        if isinstance(values, int):
            values = [values]
        self.entries.append((tag, HEADER_INT32, values))

    def add_int16(self, tag, values):
        """Add INT16 tag with one or more values."""
        if isinstance(values, int):
            values = [values]
        self.entries.append((tag, HEADER_INT16, values))

    def add_string(self, tag, value):
        """Add STRING tag."""
        self.entries.append((tag, HEADER_STRING, value))

    def add_string_array(self, tag, values):
        """Add STRING_ARRAY tag."""
        self.entries.append((tag, HEADER_STRING_ARRAY, values))

    def add_bin(self, tag, data):
        """Add BIN tag."""
        self.entries.append((tag, HEADER_BIN, data))

    def add_i18n_string(self, tag, value):
        """Add I18NSTRING tag."""
        self.entries.append((tag, HEADER_I18NSTRING, value))

    def build(self):
        """Build the header bytes.

        Returns:
            bytes: Complete header section including magic and index.
        """
        # Sort entries by tag number
        self.entries.sort(key=lambda x: x[0])

        # Build the data store and index entries
        data_store = io.BytesIO()
        index_entries = []

        for tag, dtype, data in self.entries:
            # Align data store based on type
            if dtype == HEADER_INT16:
                while data_store.tell() % 2:
                    data_store.write(b'\x00')
            elif dtype in (HEADER_INT32, HEADER_INT64):
                while data_store.tell() % 4:
                    data_store.write(b'\x00')

            offset = data_store.tell()

            if dtype == HEADER_INT16:
                count = len(data)
                for v in data:
                    data_store.write(struct.pack(">H", v))
            elif dtype == HEADER_INT32:
                count = len(data)
                for v in data:
                    data_store.write(struct.pack(">I", v))
            elif dtype == HEADER_STRING:
                count = 1
                data_store.write(data.encode('utf-8') + b'\x00')
            elif dtype == HEADER_STRING_ARRAY:
                count = len(data)
                for s in data:
                    data_store.write(s.encode('utf-8') + b'\x00')
            elif dtype == HEADER_I18NSTRING:
                count = 1
                data_store.write(data.encode('utf-8') + b'\x00')
            elif dtype == HEADER_BIN:
                count = len(data)
                data_store.write(data)
            else:
                raise ValueError(f"Unsupported header type: {dtype}")

            index_entries.append((tag, dtype, offset, count))

        # Build header
        header = io.BytesIO()

        # Magic (3 bytes) + version (1 byte) + reserved (4 bytes)
        header.write(RPM_HEADER_MAGIC)
        header.write(struct.pack(">B", RPM_HEADER_VERSION))
        header.write(b'\x00' * 4)

        # Number of entries and data store size
        header.write(struct.pack(">I", len(index_entries)))
        header.write(struct.pack(">I", data_store.tell()))

        # Index entries
        for tag, dtype, offset, count in index_entries:
            header.write(struct.pack(">I", tag))
            header.write(struct.pack(">I", dtype))
            header.write(struct.pack(">I", offset))
            header.write(struct.pack(">I", count))

        # Data store
        header.write(data_store.getvalue())

        return header.getvalue()


class RpmWriter:
    """Write RPM packages."""

    def __init__(self,
                 name,
                 version,
                 release="1",
                 arch="noarch",
                 os_name="linux",
                 summary=None,
                 description=None,
                 license_text="Unknown",
                 group="Unspecified",
                 compression="gzip"):
        """Initialize RPM writer.

        Args:
            name: Package name.
            version: Package version.
            release: Package release (default "1").
            arch: Target architecture (default "noarch").
            os_name: Target OS (default "linux").
            summary: Package summary (defaults to name).
            description: Package description (defaults to summary).
            license_text: License string (default "Unknown").
            group: Package group (default "Unspecified").
            compression: Payload compression: "gzip", "xz", "bzip2", or "none".
        """
        self.name = name
        self.version = version
        self.release = release
        self.arch = arch
        self.os_name = os_name
        self.summary = summary or name
        self.description = description or self.summary
        self.license = license_text
        self.group = group
        self.compression = compression

        self.files = []  # List of (path, content, mode, uid, gid, is_dir, is_symlink, target)

    def add_file(self, path, content, mode=0o100644, uid=0, gid=0,
                 user="root", group="root"):
        """Add a regular file to the package.

        Args:
            path: Absolute path where file will be installed.
            content: File content as bytes or string.
            mode: File mode (default 0o100644).
            uid: Owner UID (default 0).
            gid: Owner GID (default 0).
            user: Owner username (default "root").
            group: Owner group name (default "root").
        """
        if isinstance(content, str):
            content = content.encode('utf-8')
        if not (mode & 0o170000):
            mode |= stat.S_IFREG
        self.files.append({
            'path': path,
            'content': content,
            'mode': mode,
            'uid': uid,
            'gid': gid,
            'user': user,
            'group': group,
            'is_dir': False,
            'is_symlink': False,
            'target': None,
        })

    def add_directory(self, path, mode=0o40755, uid=0, gid=0,
                      user="root", group="root"):
        """Add a directory to the package.

        Args:
            path: Absolute path of the directory.
            mode: Directory mode (default 0o40755).
            uid: Owner UID.
            gid: Owner GID.
            user: Owner username.
            group: Owner group name.
        """
        if not (mode & 0o170000):
            mode |= stat.S_IFDIR
        self.files.append({
            'path': path,
            'content': b'',
            'mode': mode,
            'uid': uid,
            'gid': gid,
            'user': user,
            'group': group,
            'is_dir': True,
            'is_symlink': False,
            'target': None,
        })

    def add_symlink(self, path, target, mode=0o120777, uid=0, gid=0,
                    user="root", group="root"):
        """Add a symbolic link to the package.

        Args:
            path: Absolute path of the symlink.
            target: Target path the symlink points to.
            mode: Symlink mode (default 0o120777).
            uid: Owner UID.
            gid: Owner GID.
            user: Owner username.
            group: Owner group name.
        """
        if not (mode & 0o170000):
            mode |= stat.S_IFLNK
        self.files.append({
            'path': path,
            'content': b'',
            'mode': mode,
            'uid': uid,
            'gid': gid,
            'user': user,
            'group': group,
            'is_dir': False,
            'is_symlink': True,
            'target': target,
        })

    def _build_lead(self):
        """Build the 96-byte RPM lead."""
        lead = io.BytesIO()

        # Magic (4 bytes)
        lead.write(RPM_MAGIC)

        # Major/minor version (2 bytes)
        lead.write(struct.pack(">B", RPM_MAJOR))
        lead.write(struct.pack(">B", RPM_MINOR))

        # Type: 0=binary, 1=source (2 bytes)
        lead.write(struct.pack(">H", RPM_TYPE_BINARY))

        # Arch number (2 bytes) - use 0 for noarch
        arch_num = 0
        if self.arch == "x86_64":
            arch_num = 1
        elif self.arch == "i386" or self.arch == "i686":
            arch_num = 1
        lead.write(struct.pack(">H", arch_num))

        # Name (66 bytes, null-padded)
        name_bytes = f"{self.name}-{self.version}-{self.release}".encode('utf-8')[:65]
        lead.write(name_bytes + b'\x00' * (66 - len(name_bytes)))

        # OS number (2 bytes) - 1 = Linux
        lead.write(struct.pack(">H", 1))

        # Signature type (2 bytes) - 5 = header-style
        lead.write(struct.pack(">H", 5))

        # Reserved (16 bytes)
        lead.write(b'\x00' * 16)

        assert lead.tell() == 96
        return lead.getvalue()

    def _build_signature(self, header_bytes, payload_bytes):
        """Build the signature header section."""
        sig = RpmHeaderBuilder()

        # Combined size of header + payload
        combined = header_bytes + payload_bytes
        sig.add_int32(SIGTAG_SIZE, len(combined))

        # MD5 of header + payload
        md5_hash = hashlib.md5(combined).digest()
        sig.add_bin(SIGTAG_MD5, md5_hash)

        # Uncompressed payload size
        # For now, just use the compressed size
        sig.add_int32(SIGTAG_PAYLOADSIZE, len(payload_bytes))

        sig_bytes = sig.build()

        # Signature must be padded to 8-byte boundary
        padding = (8 - (len(sig_bytes) % 8)) % 8

        return sig_bytes + (b'\x00' * padding)

    def _build_header(self):
        """Build the main header section."""
        hdr = RpmHeaderBuilder()

        # Required package info
        hdr.add_string(RPMTAG_NAME, self.name)
        hdr.add_string(RPMTAG_VERSION, self.version)
        hdr.add_string(RPMTAG_RELEASE, self.release)
        hdr.add_i18n_string(RPMTAG_SUMMARY, self.summary)
        hdr.add_i18n_string(RPMTAG_DESCRIPTION, self.description)
        hdr.add_int32(RPMTAG_BUILDTIME, int(time.time()))
        hdr.add_string(RPMTAG_BUILDHOST, "localhost")
        hdr.add_string(RPMTAG_LICENSE, self.license)
        hdr.add_i18n_string(RPMTAG_GROUP, self.group)
        hdr.add_string(RPMTAG_OS, self.os_name)
        hdr.add_string(RPMTAG_ARCH, self.arch)
        hdr.add_string(RPMTAG_SOURCERPM, f"{self.name}-{self.version}-{self.release}.src.rpm")
        hdr.add_string(RPMTAG_RPMVERSION, "4.0")

        # Payload info
        hdr.add_string(RPMTAG_PAYLOADFORMAT, "cpio")
        hdr.add_string(RPMTAG_PAYLOADCOMPRESSOR, self.compression if self.compression != "none" else "gzip")
        hdr.add_string(RPMTAG_PAYLOADFLAGS, "9")

        # File info - split paths into dirnames + basenames + dirindexes
        if self.files:
            dirs = {}  # dir -> index
            dir_list = []
            basenames = []
            dirindexes = []
            sizes = []
            modes = []
            rdevs = []
            mtimes = []
            md5s = []
            linktos = []
            flags = []
            users = []
            groups = []
            devices = []
            inodes = []
            langs = []
            verifyflags = []

            for i, f in enumerate(self.files):
                path = f['path'].lstrip('/')
                dirname = os.path.dirname(path)
                if dirname:
                    dirname = '/' + dirname + '/'
                else:
                    dirname = '/'
                basename = os.path.basename(path)

                if dirname not in dirs:
                    dirs[dirname] = len(dir_list)
                    dir_list.append(dirname)

                basenames.append(basename)
                dirindexes.append(dirs[dirname])
                sizes.append(len(f['content']))
                modes.append(f['mode'])
                rdevs.append(0)
                mtimes.append(int(time.time()))

                if f['is_symlink']:
                    md5s.append("")
                    linktos.append(f['target'])
                elif f['is_dir']:
                    md5s.append("")
                    linktos.append("")
                else:
                    md5s.append(hashlib.md5(f['content']).hexdigest())
                    linktos.append("")

                flags.append(0)
                users.append(f['user'])
                groups.append(f['group'])
                devices.append(1)
                inodes.append(i + 1)
                langs.append("")
                verifyflags.append(0xFFFFFFFF)  # Verify all

            hdr.add_string_array(RPMTAG_DIRNAMES, dir_list)
            hdr.add_string_array(RPMTAG_BASENAMES, basenames)
            hdr.add_int32(RPMTAG_DIRINDEXES, dirindexes)
            hdr.add_int32(RPMTAG_FILESIZES, sizes)
            hdr.add_int16(RPMTAG_FILEMODES, modes)
            hdr.add_int16(RPMTAG_FILERDEVS, rdevs)
            hdr.add_int32(RPMTAG_FILEMTIMES, mtimes)
            hdr.add_string_array(RPMTAG_FILEMD5S, md5s)
            hdr.add_string_array(RPMTAG_FILELINKTOS, linktos)
            hdr.add_int32(RPMTAG_FILEFLAGS, flags)
            hdr.add_string_array(RPMTAG_FILEUSERNAME, users)
            hdr.add_string_array(RPMTAG_FILEGROUPNAME, groups)
            hdr.add_int32(RPMTAG_FILEDEVICES, devices)
            hdr.add_int32(RPMTAG_FILEINODES, inodes)
            hdr.add_string_array(RPMTAG_FILELANGS, langs)
            hdr.add_int32(RPMTAG_FILEVERIFYFLAGS, verifyflags)

            # Total installed size
            total_size = sum(sizes)
            hdr.add_int32(RPMTAG_SIZE, total_size)

        return hdr.build()

    def _build_cpio_payload(self):
        """Build the CPIO payload from files."""
        cpio_buf = io.BytesIO()
        writer = CpioWriter(cpio_buf)

        for f in self.files:
            path = f['path'].lstrip('/')
            if f['is_symlink']:
                writer.add_symlink(path, f['target'], mode=f['mode'],
                                   uid=f['uid'], gid=f['gid'])
            elif f['is_dir']:
                writer.add_directory(path, mode=f['mode'],
                                     uid=f['uid'], gid=f['gid'])
            else:
                writer.add_file(path, f['content'], mode=f['mode'],
                                uid=f['uid'], gid=f['gid'])

        writer.finish()
        return cpio_buf.getvalue()

    def _compress_payload(self, data):
        """Compress the CPIO payload."""
        if self.compression == "none":
            return data
        elif self.compression == "gzip":
            return gzip.compress(data, compresslevel=9)
        elif self.compression == "xz":
            return lzma.compress(data, preset=9)
        elif self.compression == "bzip2":
            return bz2.compress(data, compresslevel=9)
        else:
            raise ValueError(f"Unknown compression: {self.compression}")

    def write(self, output_path):
        """Write the RPM to a file.

        Args:
            output_path: Path to write the RPM file.
        """
        # Build components
        cpio_data = self._build_cpio_payload()
        payload = self._compress_payload(cpio_data)
        header = self._build_header()
        signature = self._build_signature(header, payload)
        lead = self._build_lead()

        # Write RPM
        with open(output_path, 'wb') as f:
            f.write(lead)
            f.write(signature)
            f.write(header)
            f.write(payload)

    def write_to_stream(self, stream):
        """Write the RPM to a stream.

        Args:
            stream: Binary file-like object to write to.
        """
        # Build components
        cpio_data = self._build_cpio_payload()
        payload = self._compress_payload(cpio_data)
        header = self._build_header()
        signature = self._build_signature(header, payload)
        lead = self._build_lead()

        # Write RPM
        stream.write(lead)
        stream.write(signature)
        stream.write(header)
        stream.write(payload)
