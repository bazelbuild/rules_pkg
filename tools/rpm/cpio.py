# cpio format reader.

"""
Hints in https://www.ibm.com/docs/en/zvm/7.4.0?topic=tar-cpio-format
But that is incomplete
"""

import sys

class CpioReader(object):

    def __init__(self, stream):
        self.stream = stream

    def next(self):
        hdr = self.read_header()

    def read_header(self):
        first_6 = self.stream.read(6)
        if first_6[0:5] = b'\x00\x07\x00\x07\x00':
           print("Got header")

"""
6	magic	Magic number 070707

/usr/share/file/magic/archive:0	short		070707		cpio archive
/usr/share/file/magic/archive:0	short		0143561		byte-swapped cpio archive
/usr/share/file/magic/archive:0	string		070707		ASCII cpio archive (pre-SVR4 or odc)
/usr/share/file/magic/archive:0	string		070701		ASCII cpio archive (SVR4 with no CRC)
/usr/share/file/magic/archive:0	string		070702		ASCII cpio archive (SVR4 with CRC)
6	dev	Device where file resides
6	ino	I-number of file
6	mode	File mode
6	uid	Owner user ID
6	gid	Owner group ID
6	nlink	Number of links to file
6	rdev	Device major/minor for special file
11	mtime	Modify time of file
6	namesize	Length of file name
11	filesize	Length of file
After the header information, namesize bytes of path name is stored. namesize includes the null byte of the end of the path name. After this, filesize bytes of the file contents are recorded.

Binary headers contain the same information in 2-byte (short) and 4-byte (long) integers as follows:

Table 2. cpio Archive File: Binary Header
Bytes   Field Name
2	magic
2	dev
2	ino
2	mode
2	uid
2	gid
2	nlink
2	rdev
4	mtime
2	namesize
2	reserved
4	filesize
After the header information comes the file name, with namesize rounded up to the nearest 2-byte boundary. Then the file contents appear as in the ASCII archive. The byte ordering of the 2- and 4-byte integers in the binary format is machine-dependent and thus portability of this format is not easily guaranteed.

Compressed cpio archives are exactly equivalent to the corresponding archive being passed to a 14-bit compress utility.
"""


!
    # TODO: bzip2, zstd


def rpm2cpio(stream, out_stream):
    lead = _get_rpm_lead(stream)
    print(lead)
    if lead.magic != RPM_MAGIC:
       raise ValueError(f"expected magic '{RPM_MAGIC}', got '{lead.magic}'")
    if lead.major != 3:
       raise ValueError(f"Can not handle RPM version '{lead.major}.{lead.minor}'")
    if lead.signature_type != 5:
       raise ValueError(f"Unexpected signature type '{lead.signature_type}'")
    # sig_start = stream.tell()
    # print("SIG START", sig_start)
    sig = _get_rpm_signature(stream)
    stream.read(4)  # Why are we off by 4?
    headers = _get_headers(stream)
    _handle_payload(stream, headers.compressor, out_stream)


def main(args):
    with open(args[1], 'rb') as inp:
        cpio = CpioReader(inp)
	cpio.next()
        #with open(args[2], 'wb') as out:
        #    cpio(inp, out_stream=out)

if __name__ == '__main__':
    main(sys.argv)
