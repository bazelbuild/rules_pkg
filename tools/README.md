# package inspection and analysis tools

This is toolkit for building need specific tools.  It consists of:

- A collection of readers for various kinds of packages.
- Some reference implementation tools to show how the readers work.

Much of the code here is AI generated.  The ar, deb, rpm and cpio readers
were hand crafted by a human.

## Tools

### rpm2cpio - portable rpm2cpio utility
- runs anywhere with python 3.12 or higher
- extracts and steams out the cpio archive
- can also dump rpm headers

### cpio-ls - read a cpio archive stream and list the files
- this is just a demonstration of how you could write `cpio -i`

### tree_size_compare
- compare 2 archives and look for differences in sizes of files.
