"""Base interface for all readers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class FileInfo:
    """Information about a file or directory."""
    path: str     # relative path
    size: int     # 0 for directories and symlinks
    mode: int     # octal mode
    uid: int = 0  # user id
    gid: int = 0  # group id
    is_dir: bool = False
    is_symlink: bool = False
    symlink_target: str = None
    # only in cpio entries.
    inode: int = 0
    data_size: int = 0


# ============================================================================
# TreeReader Interface and Implementations
# ============================================================================

class TreeReader(ABC):
    """Abstract base class for reading tree metadata from various sources."""

    @abstractmethod
    def next(self) -> FileInfo:
        """
        Return the next FileInfo, or None if no more items.
        """
        pass

    @abstractmethod
    def is_done(self) -> bool:
        """Return True if all items have been read."""
        pass
