"""saved_tree - read & write an image manifest to disk."""

import json

from tools.lib.tree_reader import FileInfo, TreeReader


def write_tree(output_file: str, items) -> None:
    # Write JSON
    with open(output_file, 'w') as f:
        json.dump(items, f, indent=2)

def dict_to_fileinfo(d: dict) -> FileInfo:
    """Convert dict (from JSON) back to FileInfo.

    Defaults uid and gid to 0 if not present (optimization).
    """
    return FileInfo(
        path=d["path"].removeprefix('./'),
        size=d.get("size", 0),
        mode=int(d["mode"], 8),  # Convert octal string to int
        uid=d.get("uid", 0),     # Default to 0 if omitted
        gid=d.get("gid", 0),     # Default to 0 if omitted
        is_dir=d.get("is_dir", False),
        is_symlink=d.get("is_symlink", False),
        symlink_target=d.get("target")
    )


class SavedTreeReader(TreeReader):
    """Reader for saved JSON metadata files."""

    def __init__(self, json_path: str):
        self.items = []
        self.index = 0
        self._load_json(json_path)

    def _load_json(self, json_path: str):
        """Load items from JSON file."""
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError("JSON must be an array of items")

            for item in data:
                self.items.append(dict_to_fileinfo(item))
        except Exception as e:
            raise ValueError(f"Error reading JSON file {json_path}: {e}")

        self.items.sort(key=lambda x: x.path)

    def next(self) -> FileInfo:
        if self.index < len(self.items):
            item = self.items[self.index]
            self.index += 1
            return item
        return None

    def is_done(self) -> bool:
        return self.index >= len(self.items)
