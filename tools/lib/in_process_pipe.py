import threading


class InProcessPipe:
    """A thread-safe bytes pipe connecting a writer thread and a reader thread.

    Mimics Unix pipe semantics:
    - write(data) appends to an internal buffer.
    - read(n) blocks until n bytes are available (or EOF), then returns up to n bytes.
    - read() with no argument blocks until close(), then returns all remaining data.
    - close() signals EOF from the writer side.
    - Returns b"" only at EOF (closed and buffer drained).
    """

    def __init__(self):
        self._buffer = bytearray()
        self._lock = threading.Condition()
        self._closed = False
        self._bytes_read = 0

    def write(self, data: bytes) -> int:
        with self._lock:
            if self._closed:
                raise ValueError("write to closed pipe")
            self._buffer.extend(data)
            self._lock.notify_all()
            return len(data)

    def read(self, n: int = -1) -> bytes:
        with self._lock:
            if n < 0:
                # Read all until EOF, like read() on a pipe with no size.
                while not self._closed:
                    self._lock.wait()
                data = bytes(self._buffer)
                self._bytes_read += len(data)
                self._buffer.clear()
                return data

            # Block until n bytes are available or the pipe is closed.
            while len(self._buffer) < n and not self._closed:
                self._lock.wait()

            if not self._buffer:
                return b""

            data = bytes(self._buffer[:n])
            del self._buffer[:n]
            self._bytes_read += len(data)
            return data

    def flush(self):
        pass

    def tell(self) -> int:
        with self._lock:
            return self._bytes_read

    def close(self):
        with self._lock:
            self._closed = True
            self._lock.notify_all()
