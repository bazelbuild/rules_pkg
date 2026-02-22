#!/usr/bin/env python3

import argparse
import io
import json
import os
import re
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from tools.lib.tree_reader import FileInfo, TreeReader
from tools.lib.deb_reader import DebReader
from tools.lib.fs_reader import FileSystemReader
from tools.lib.rpm_reader import RpmReader
from tools.lib.tar_reader import TarReader
from tools.lib.saved_tree import SavedTreeReader, write_tree


class InputFactory:
    """Factory for creating appropriate TreeReader based on input path."""

    @staticmethod
    def is_filesystem(path: str) -> bool:
        """Return True if the input path is a filesystem directory."""
        return os.path.isdir(path)

    @staticmethod
    def create(path: str) -> TreeReader:
        """
        Detect input type and create appropriate reader.

        Args:
            path: Path to directory, tar file, JSON file, or RPM file

        Returns:
            TreeReader instance

        Raises:
            ValueError: If input type cannot be determined or is invalid
        """
        if path.endswith('.json'):
            return SavedTreeReader(path)
        elif path.endswith('.deb'):
            return DebReader(path)
        elif path.endswith('.rpm'):
            return RpmReader(path)
        elif path.endswith(('.tar', '.tar.gz', '.tar.bz2', '.tar.xz', '.tgz')):
            return TarReader(path)
        elif os.path.isdir(path):
            return FileSystemReader(path)
        else:
            raise ValueError(f"Cannot determine input type for: {path}")


# ============================================================================
# Utility Functions
# ============================================================================

def format_mode(mode: int) -> str:
    """Format mode as octal string, preserving file type bits (e.g., '100644')."""
    # Remove the '0o' prefix but keep all octal digits including file type bits
    return oct(mode)[2:]


def fileinfo_to_dict(info: FileInfo) -> dict:
    """
    Convert FileInfo to a dict for JSON serialization.

    Only includes relevant fields:
    - Regular files: path, size, mode, uid (if != 0), gid (if != 0)
    - Directories: path, is_dir, mode, uid (if != 0), gid (if != 0)
    - Symlinks: path, is_symlink, target, mode, uid (if != 0), gid (if != 0)

    Optimization: uid and gid are omitted when 0 and default to 0 when reading.
    """
    result = {
        "path": info.path,
        "mode": format_mode(info.mode),
    }

    # Only include uid/gid if non-zero (saves ~25% on typical files)
    if info.uid != 0:
        result["uid"] = info.uid
    if info.gid != 0:
        result["gid"] = info.gid

    if info.is_symlink:
        result["is_symlink"] = True
        result["target"] = info.symlink_target
    elif info.is_dir:
        result["is_dir"] = True
    else:
        result["size"] = info.size

    return result


def should_include_path(path: str, include_patterns: list, exclude_patterns: list) -> bool:
    """
    Check if a path should be included based on include/exclude filters.

    Args:
        path: The file path to check
        include_patterns: List of regex patterns (if non-empty, path must match at least one)
        exclude_patterns: List of regex patterns (path must not match any)

    Returns:
        True if path should be included, False otherwise
    """
    # If include patterns are specified, path must match at least one
    if include_patterns:
        matches_include = any(re.search(pattern, path) for pattern in include_patterns)
        if not matches_include:
            return False

    # Check exclude patterns
    if exclude_patterns:
        matches_exclude = any(re.search(pattern, path) for pattern in exclude_patterns)
        if matches_exclude:
            return False

    return True


def check_size_threshold(expected_size: int, got_size: int, flags: dict) -> tuple:
    """
    Check if size change exceeds thresholds.

    Args:
        expected_size: Size in expected tree
        got_size: Size in got tree
        flags: Dictionary with threshold settings

    Returns:
        Tuple of (passed: bool, message: str)
    """
    max_abs_increase = flags["max_allowed_absolute_increase"]
    max_pct_increase = flags["max_allowed_percent_increase"]
    show_decreases = flags["show_decreases"]
    minimum_compare_size = flags["minimum_compare_size"]

    # Skip check if file is below minimum size
    if expected_size < minimum_compare_size and got_size < minimum_compare_size:
        return True, ""

    size_diff = got_size - expected_size

    # If decreasing and we don't show decreases, pass
    if size_diff < 0 and not show_decreases:
        return True, ""

    # Check absolute increase
    if max_abs_increase > 0 and size_diff > max_abs_increase:
        return False, f"size increased by {size_diff} bytes (max allowed: {max_abs_increase})"

    # Check percent increase
    if expected_size > 0:
        pct_change = (size_diff / expected_size) * 100
        if pct_change > max_pct_increase:
            return False, f"size increased by {pct_change:.2f}% (max allowed: {max_pct_increase}%)"

    return True, ""


# ============================================================================
# Comparison and Reporting
# ============================================================================

def load_tree_from_reader(reader: TreeReader) -> dict:
    """
    Load all items from a reader into a dict.

    Args:
        reader: TreeReader instance

    Returns:
        Dictionary keyed by path with FileInfo values
    """
    result = {}
    while True:
        item = reader.next()
        if item is None:
            break
        result[item.path] = item
    return result


def stream_compare(expected_dict: dict, got_reader: TreeReader, flags: dict) -> dict:
    """
    Compare trees in streaming fashion: expected is pre-loaded, got is streamed.

    Args:
        expected_dict: Pre-loaded expected tree dict
        got_reader: TreeReader for got tree
        flags: Comparison flags

    Returns:
        Dictionary with results
    """
    results = {
        "only_in_expected": [],
        "only_in_got": [],
        "symlink_target_changed": [],
        "metadata_changed": [],
        "size_changed": [],
    }

    include_patterns = flags.get("include_patterns", [])
    exclude_patterns = flags.get("exclude_patterns", [])

    # Track which expected items we've seen
    found_in_got = set()

    # Stream through got and compare
    while True:
        got_item = got_reader.next()
        if got_item is None:
            break

        # Check filtering
        if not should_include_path(got_item.path, include_patterns, exclude_patterns):
            continue

        found_in_got.add(got_item.path)

        if got_item.path not in expected_dict:
            # File in got but not in expected
            file_type = "symlink" if got_item.is_symlink else ("directory" if got_item.is_dir else "file")
            results["only_in_got"].append((got_item.path, file_type))
            continue

        # File in both - compare
        exp_item = expected_dict[got_item.path]

        # Check filtering on expected too
        if not should_include_path(exp_item.path, include_patterns, exclude_patterns):
            continue

        # If both are symlinks, check if target changed
        if exp_item.is_symlink and got_item.is_symlink:
            if exp_item.symlink_target != got_item.symlink_target:
                results["symlink_target_changed"].append((
                    exp_item.path,
                    exp_item.symlink_target,
                    got_item.symlink_target
                ))

        # If symlink status changed
        elif exp_item.is_symlink != got_item.is_symlink:
            results["metadata_changed"].append((
                exp_item.path,
                f"symlink status changed: {exp_item.is_symlink} -> {got_item.is_symlink}"
            ))

        # If both are regular files, check size
        elif not exp_item.is_dir and not exp_item.is_symlink:
            passed, msg = check_size_threshold(exp_item.size, got_item.size, flags)
            if not passed:
                results["size_changed"].append((
                    exp_item.path,
                    exp_item.size,
                    got_item.size,
                    msg
                ))

        # Check metadata for all types (mode, and optionally uid/gid)
        compare_uid_gid = flags.get("compare_uid_gid", True)
        changes = []
        if exp_item.mode != got_item.mode:
            changes.append(f"mode {format_mode(exp_item.mode)} -> {format_mode(got_item.mode)}")
        if compare_uid_gid:
            if exp_item.uid != got_item.uid:
                changes.append(f"uid {exp_item.uid} -> {got_item.uid}")
            if exp_item.gid != got_item.gid:
                changes.append(f"gid {exp_item.gid} -> {got_item.gid}")
        if changes:
            results["metadata_changed"].append((exp_item.path, ", ".join(changes)))

    # Report items in expected but not found in got
    for exp_path, exp_item in sorted(expected_dict.items()):
        if exp_path in found_in_got:
            continue

        if not should_include_path(exp_path, include_patterns, exclude_patterns):
            continue

        file_type = "symlink" if exp_item.is_symlink else ("directory" if exp_item.is_dir else "file")
        results["only_in_expected"].append((exp_path, file_type))

    return results


def print_report(results: dict) -> int:
    """
    Print comparison report and return exit code.

    Args:
        results: Dictionary from compare_trees

    Returns:
        0 if no differences, 1 if differences found
    """
    has_diffs = False

    # Only in expected
    if results["only_in_expected"]:
        has_diffs = True
        print("\nFiles/directories in expected but not in got:")
        for path, file_type in results["only_in_expected"]:
            print(f"  [{file_type}] {path}")

    # Only in got
    if results["only_in_got"]:
        has_diffs = True
        print("\nFiles/directories in got but not in expected:")
        for path, file_type in results["only_in_got"]:
            print(f"  [{file_type}] {path}")

    # Symlink targets changed
    if results["symlink_target_changed"]:
        has_diffs = True
        print("\nSymlinks with changed targets:")
        for path, expected_target, got_target in results["symlink_target_changed"]:
            print(f"  {path}")
            print(f"    expected: -> {expected_target}")
            print(f"    got:      -> {got_target}")

    # Metadata changed
    if results["metadata_changed"]:
        has_diffs = True
        print("\nFiles with changed metadata (mode/uid/gid):")
        for path, changes in results["metadata_changed"]:
            print(f"  {path}: {changes}")

    # Size changed
    if results["size_changed"]:
        has_diffs = True
        print("\nFiles with size changes exceeding threshold:")
        for path, expected_size, got_size, message in results["size_changed"]:
            print(f"  {path}")
            print(f"    expected: {expected_size} bytes")
            print(f"    got:      {got_size} bytes")
            print(f"    {message}")

    if not has_diffs:
        print("\nTrees are identical.")

    return 1 if has_diffs else 0


def save_tree(input_path: str, output_file: str) -> int:
    """
    Read a tree from any input type and save as JSON.

    Args:
        input_path: Path to directory, tar, or JSON
        output_file: Path to output JSON file

    Returns:
        0 on success, 1 on error
    """
    try:
        print(f"Scanning tree: {input_path}")
        reader = InputFactory.create(input_path)
        tree = load_tree_from_reader(reader)
        print(f"Found {len(tree)} items")

        # Convert to list of dicts, sorted by path
        items = [fileinfo_to_dict(info) for info in tree.values()]
        items.sort(key=lambda x: x["path"])

        write_tree(output_file, items)

        print(f"Saved to {output_file}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Compare two directory trees (directories, tars, or JSON) and report differences."
    )
    parser.add_argument(
        "--save",
        type=str,
        metavar="OUTPUT_FILE",
        help="Save tree metadata as JSON. Takes single directory/tar/JSON argument."
    )
    parser.add_argument(
        "--max_allowed_absolute_increase",
        type=int,
        default=0,
        help="Maximum allowed absolute increase in bytes (0 = no check, default: 0)"
    )
    parser.add_argument(
        "--max_allowed_percent_increase",
        type=float,
        default=1,
        help="Maximum allowed percent increase in file size (default: 1)"
    )
    parser.add_argument(
        "--show_decreases",
        type=bool,
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Check size decreases as well (default: True)"
    )
    parser.add_argument(
        "--minimum_compare_size",
        type=int,
        default=500,
        help="Minimum file size in bytes to check for size changes (default: 500)"
    )
    parser.add_argument(
        "--compare_uid_gid",
        default=None,
        action=argparse.BooleanOptionalAction,
        help="Compare uid/gid metadata (default: True unless either input is a filesystem directory)"
    )
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        help="Include only files matching this regex pattern (can be specified multiple times)"
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Exclude files matching this regex pattern (can be specified multiple times)"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Paths (directory, tar, or JSON). 1 for --save, 2 for comparison."
    )

    args = parser.parse_args()

    # Determine mode and validate arguments
    if args.save:
        # Save mode: requires exactly one input
        if len(args.paths) != 1:
            parser.error("--save mode requires exactly one path argument")
        return save_tree(args.paths[0], args.save)
    else:
        # Comparison mode: requires exactly two inputs
        if len(args.paths) != 2:
            parser.error("Comparison mode requires exactly two path arguments (expected got)")

        expected_path, got_path = args.paths

        try:
            # Load expected (fully)
            print(f"Loading expected tree: {expected_path}")
            expected_reader = InputFactory.create(expected_path)
            expected_dict = load_tree_from_reader(expected_reader)
            print(f"Found {len(expected_dict)} items")

            # Create got reader (for streaming)
            print(f"Comparing against: {got_path}")
            got_reader = InputFactory.create(got_path)

            # Determine whether to compare uid/gid
            compare_uid_gid = args.compare_uid_gid
            if compare_uid_gid is None:
                # Default: skip uid/gid comparison if either input is a filesystem
                compare_uid_gid = not (
                    InputFactory.is_filesystem(expected_path)
                    or InputFactory.is_filesystem(got_path))

            # Compare
            flags = {
                "max_allowed_absolute_increase": args.max_allowed_absolute_increase,
                "max_allowed_percent_increase": args.max_allowed_percent_increase,
                "show_decreases": args.show_decreases,
                "minimum_compare_size": args.minimum_compare_size,
                "include_patterns": args.include,
                "exclude_patterns": args.exclude,
                "compare_uid_gid": compare_uid_gid,
            }

            results = stream_compare(expected_dict, got_reader, flags)

            # Report
            exit_code = print_report(results)
            return exit_code

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    sys.exit(main())
