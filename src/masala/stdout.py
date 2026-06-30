import io
import sys


class CaptureStdout:
    """Context manager that captures stdout while still writing to the original stream."""

    def __init__(self):
        """Create a new stdout capture context."""
        self._buffer = io.StringIO()
        self._original_stdout = None

    def __enter__(self):
        self._original_stdout = sys.stdout
        self._tee = _TeeStream(self._original_stdout, self._buffer)
        sys.stdout = self._tee
        return self

    def __exit__(self, *args):
        sys.stdout = self._original_stdout
        self._tee = None

    def text(self) -> str:
        """Return the captured stdout text."""
        return self._buffer.getvalue().strip()


class _TeeStream(io.RawIOBase):
    """Internal stream that writes to both a target and a buffer."""

    def __init__(self, target, buffer):
        self._target = target
        self._buffer = buffer

    def write(self, s):
        self._target.write(s)
        self._target.flush()
        self._buffer.write(s)
        return len(s)
