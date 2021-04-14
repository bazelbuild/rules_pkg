'''Fake compressor that just prepends garbage bytes.'''

import sys

GARBAGE = b'garbage'

sys.stdout.buffer.write(GARBAGE)
sys.stdout.buffer.write(sys.stdin.buffer.read())
