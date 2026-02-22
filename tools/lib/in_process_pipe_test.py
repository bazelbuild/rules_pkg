import threading
import unittest

from in_process_pipe import InProcessPipe


class InProcessPipeTest(unittest.TestCase):

    def test_basic_write_read(self):
        p = InProcessPipe()
        p.write(b"hello")
        self.assertEqual(p.read(5), b"hello")

    def test_read_less_than_available(self):
        p = InProcessPipe()
        p.write(b"hello world")
        self.assertEqual(p.read(5), b"hello")
        self.assertEqual(p.read(6), b" world")

    def test_read_more_than_available_returns_at_eof(self):
        p = InProcessPipe()
        p.write(b"hi")
        p.close()
        self.assertEqual(p.read(100), b"hi")

    def test_read_all_waits_for_close(self):
        p = InProcessPipe()
        p.write(b"aaa")
        p.write(b"bbb")
        p.close()
        self.assertEqual(p.read(), b"aaabbb")

    def test_eof_returns_empty(self):
        p = InProcessPipe()
        p.close()
        self.assertEqual(p.read(10), b"")
        self.assertEqual(p.read(), b"")

    def test_write_after_close_raises(self):
        p = InProcessPipe()
        p.close()
        with self.assertRaises(ValueError):
            p.write(b"nope")

    def test_threaded_producer_consumer(self):
        p = InProcessPipe()
        chunks = [b"chunk1-", b"chunk2-", b"chunk3"]
        total = sum(len(c) for c in chunks)

        def writer():
            for c in chunks:
                p.write(c)
            p.close()

        t = threading.Thread(target=writer)
        t.start()

        received = bytearray()
        while len(received) < total:
            data = p.read(7)
            if not data:
                break
            received.extend(data)

        t.join()
        self.assertEqual(bytes(received), b"chunk1-chunk2-chunk3")

    def test_threaded_read_all(self):
        p = InProcessPipe()
        expected = b"X" * 10000

        def writer():
            for i in range(0, len(expected), 100):
                p.write(expected[i:i+100])
            p.close()

        t = threading.Thread(target=writer)
        t.start()
        result = p.read()
        t.join()
        self.assertEqual(result, expected)


    def test_read_blocks_until_n_bytes(self):
        p = InProcessPipe()
        result = []

        def reader():
            result.append(p.read(10))

        t = threading.Thread(target=reader)
        t.start()

        # First write is only 4 bytes — reader should still be blocked.
        p.write(b"aaaa")
        t.join(timeout=0.05)
        self.assertTrue(t.is_alive(), "reader returned before n bytes available")

        # Second write brings total to 10 — reader should unblock.
        p.write(b"bbbbbb")
        t.join(timeout=1)
        self.assertFalse(t.is_alive())
        self.assertEqual(result[0], b"aaaabbbbbb")

    def test_tell_tracks_bytes_read(self):
        p = InProcessPipe()
        p.write(b"hello world")
        self.assertEqual(p.tell(), 0)
        p.read(5)
        self.assertEqual(p.tell(), 5)
        p.read(3)
        self.assertEqual(p.tell(), 8)

    def test_tell_with_read_all(self):
        p = InProcessPipe()
        p.write(b"abcdef")
        p.close()
        p.read()
        self.assertEqual(p.tell(), 6)

    def test_flush_is_noop(self):
        p = InProcessPipe()
        p.write(b"data")
        p.flush()
        self.assertEqual(p.read(4), b"data")


if __name__ == "__main__":
    unittest.main()
