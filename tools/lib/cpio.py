"""cpio file reader.

This is a minimal tool to read a cpio stream. It could be turned into a
partial cpio equivalent tool.

Usage:
    cpio = CpioReader(sys.stdin.buffer)
    while True:
        # returns CpioReader.Info
        info = cpio.next()
        if not header:
            break
        # do something with info
or
    cpio = CpioReader(sys.stdin.buffer)
    while True:
        info, content = cpio.next(return_content=True)
        if not header:
            break
        with open(info.path, "wb") as out:
            out.write(content)

Decent docs at
https://github.com/libyal/dtformats/blob/main/documentation/Copy%20in%20and%20out%20(CPIO)%20archive%20format.asciidoc
"""

from tools.lib.tree_reader import FileInfo

DEBUG = 0


class CpioReader(object):
    # TODO: Support compressed archives.  These are exactly equivalent to
    # the corresponding archive being passed to a 14-bit compress utility.

    def __init__(self, stream):
        self.stream = stream

    def next(self, return_content=False):
        header, content_size = self.read_header_and_content_size()
        if not header:
            return None
        if DEBUG > 1:
            print(f"{header} => to_read:{content_size}")
        # Consume the content of the file.
        # TODO: if we are not looking for content, seek over it.
        if content_size > 0:
            file_data = self.stream.read(content_size)
        if return_content:
            # content_size is padded, so return only the correct amount.
            return header, file_data[: header.size]
        else:
            return header

    def read_ascii_int(self, size, base=10):
        try:
            return int(self.stream.read(size).decode("ASCII"), base=base)
        except Exception as e:
            print(e)
            return -1

    def read_header_and_content_size(self):
        first_6 = self.stream.read(6)
        if DEBUG > 1:
            print("Got header", first_6)
        if first_6 == b"070707":
            return self.read_odc_ascii_header(magic=first_6)
        if first_6 == b"070701" or first_6 == b"070702":
            return self.read_newc_ascii_header(magic=first_6)
        else:
            print(f"Wonky header {first_6}")
            # print("128 after:", str(self.stream.peek(128)))
            return self.read_newc_ascii_header(magic=first_6)

    def read_odc_ascii_header(self, magic):
        # """
        # 6	magic	Magic number 070707
        # /usr/share/file/magic/archive:0	short		070707		cpio archive
        # /usr/share/file/magic/archive:0	short		0143561		byte-swapped cpio archive
        # /usr/share/file/magic/archive:0	string		070707		ASCII cpio archive (pre-SVR4 or odc)
        # /usr/share/file/magic/archive:0	string		070701		ASCII cpio archive (SVR4 with no CRC)
        # /usr/share/file/magic/archive:0	string		070702		ASCII cpio archive (SVR4 with CRC)
        # 6	dev	Device where file resides
        # 6	ino	I-number of file
        # 6	mode	File mode
        # 6	uid	Owner user ID
        # 6	gid	Owner group ID
        # 6	nlink	Number of links to file
        # 6	rdev	Device major/minor for special file
        # 11	mtime	Modify time of file
        # 6	namesize	Length of file name
        # 11	filesize	Length of file
        # After the header information, namesize bytes of path name is stored. namesize includes the null
        # byte of the end of the path name. After this, filesize bytes of the file contents are recorded.

        assert magic[0:5] == b"07070"
        magic = int(magic.decode("ASCII"))
        dev = self.read_ascii_int(size=6)
        inode = self.read_ascii_int(size=6)
        mode = self.read_ascii_int(size=6)
        _uid = self.read_ascii_int(size=6)
        _gid = self.read_ascii_int(size=6)
        _nlinks = self.read_ascii_int(size=6)
        _rdev = self.read_ascii_int(size=6)
        if DEBUG > 1:
            print(f"magic: {magic}, dev/node: {dev}/{inode} mode: {mode:o}")
        name_size = self.read_ascii_int(size=6)
        file_size = self.read_ascii_int(size=6)
        # TODO: Make an info.
        return 0, file_size

    def read_newc_ascii_header(self, magic):
        # Size	Description
        # 6         magic: "070701" or "070702"
        # 8         inode index.  1-n and then 0 at TRAILER.
        # 8         mode (permissions and type)
        # 8         numeric user
        # 8         numeric group
        # 8         n_links
        # 8         modification time
        # 8         file_size: file size
        # 8         device major number
        # 8         device minor number
        # 8         block or character special device major number
        # 8         block or character special device minor number
        # 8         path_len: Size of path string, including terminationg NUL.
        # 8         Checksum Contains a Sum32 if magic is "070702", or 0 otherwise
        # path_len  path string (with null)
        # .         4 byte alignment padding. set to 0
        # file_size File data
        # .         4 byte alignment padding. set to 0

        assert magic[0:5] == b"07070"
        magic = magic.decode("ASCII")
        inode = self.read_ascii_int(size=8, base=16)
        mode = self.read_ascii_int(size=8, base=16)
        uid = self.read_ascii_int(size=8, base=16)
        gid = self.read_ascii_int(size=8, base=16)
        _nlinks = self.read_ascii_int(size=8, base=16)
        mod_time = self.read_ascii_int(size=8, base=16)
        file_size = self.read_ascii_int(size=8, base=16)
        _dev_major = self.read_ascii_int(size=8, base=16)
        _dev_minor = self.read_ascii_int(size=8, base=16)
        _blk_major = self.read_ascii_int(size=8, base=16)
        _blk_minor = self.read_ascii_int(size=8, base=16)
        path_len = self.read_ascii_int(size=8, base=16)
        _checksum = self.read_ascii_int(size=8, base=16)

        # Determine file type from mode (bits 12-14 contain file type)
        file_type = mode & 0o170000
        is_dir = (file_type == 0o040000)  # S_IFDIR
        is_symlink = (file_type == 0o120000)  # S_IFLNK

        at = self.stream.tell()
        path_block_len = 4 * ((at + path_len + 3) // 4) - at
        raw_path = self.stream.read(path_block_len)
        try:
            path = raw_path[: (path_len - 1)].decode("utf-8").removeprefix('./')
        except Exception:
            path = str(raw_path[: (path_len - 1)])
        if DEBUG > 1:
            print(
                f"magic: {magic}, inode: {inode}, mode: {mode:o}, size: {file_size}, {path}"
            )
            if DEBUG > 2:
                print(f"   path_len: {path_len}, block_len: {path_block_len}")
        if path == "TRAILER!!!":
            return None, -1

        # Now we are positioned at the end of the header, right before content.
        # All archive entries are 4 byte padded, so we might have to read a
        # little more than file_size.
        data_size = 4 * ((file_size + 3) // 4)

        # symlink targets are stored as the file data.
        symlink_target = None
        if is_symlink and file_size > 0:
            file_content = self.stream.read(data_size)
            symlink_target = file_content[: file_size].decode(
                'utf-8', errors='replace')
            data_size = -1  # signal that we have read the content.

        info = FileInfo(
            path=path,
            size=0 if (is_dir or is_symlink) else file_size,
            uid=uid,
            gid=gid,
            mode=mode,
            is_dir=is_dir,
            is_symlink=is_symlink,
            symlink_target=symlink_target,

            # TODO: Consider dropping these, they are unneed.
            inode=inode,
            data_size=data_size,

            # TODO
            # mod_time=mod_time,
        )
        return info, data_size

    def read_binary_header(self, magic):
        # Binary headers contain the same information in 2-byte (short) and 4-byte (long) integers as follows:
        #
        # Bytes   Field Name
        # 2	magic
        # 2	dev
        # 2	ino
        # 2	mode
        # 2	uid
        # 2	gid
        # 2	nlink
        # 2	rdev
        # 4	mtime
        # 2	namesize
        # 2	reserved
        # 4	filesize
        # After the header information comes the file name, with namesize rounded up to the nearest
        # 2-byte boundary. Then the file contents appear as in the ASCII archive. The byte ordering
        # of the 2 and 4-byte integers in the binary format is machine-dependent and thus
        # portability of this format is not easily guaranteed.
        print("Binary CPIO is not supported.")
