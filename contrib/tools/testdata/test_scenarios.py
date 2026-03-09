#!/usr/bin/env python3

"""
Test framework for tree_size_compare.

Creates expected and got trees with known differences, then:
1. Runs baseline comparison
2. Tests each parameter to show expected output variations
3. Tests saving in different formats and comparing

Run with: python3 test_scenarios.py
"""

import io
import json
import lzma
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path


class TestScenario:
    """A test scenario with expected and got trees."""

    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.temp_dir = None
        self.expected_dir = None
        self.got_dir = None

    def setup(self):
        """Create temporary directories for this scenario."""
        self.temp_dir = tempfile.mkdtemp(prefix=f"tree_test_{self.name}_")
        self.expected_dir = f"{self.temp_dir}/expected"
        self.got_dir = f"{self.temp_dir}/got"
        os.makedirs(self.expected_dir)
        os.makedirs(self.got_dir)
        print(f"\n{'='*70}")
        print(f"Scenario: {self.name}")
        print(f"{'='*70}")
        print(f"Description: {self.description}")
        print(f"Working directory: {self.temp_dir}")

    def cleanup(self):
        """Clean up temporary directories."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def run_command(self, *args):
        """Run tree_size_compare with given arguments."""
        script_path = os.path.join(os.path.dirname(__file__), "tree_size_compare.py")
        cmd = [sys.executable, script_path] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result

    def test_case(self, name, *args):
        """Run a test case and print results."""
        print(f"\n  Test: {name}")
        print(f"  Command: tree_size_compare.py {' '.join(args)}")
        print("  " + "-" * 65)

        result = self.run_command(*args)

        # Print output
        if result.stdout:
            for line in result.stdout.split('\n'):
                if line:
                    print(f"  {line}")
        if result.stderr:
            print("  STDERR:")
            for line in result.stderr.split('\n'):
                if line:
                    print(f"  {line}")

        print(f"  Exit code: {result.returncode}")
        return result

    def save_and_compare(self, format_name, save_path):
        """Save expected tree and compare against got using the save."""
        print(f"\n  Save & Compare: {format_name}")
        print(f"  Saving expected to {format_name}...")

        # Save expected in the specified format
        script_path = os.path.join(os.path.dirname(__file__), "tree_size_compare.py")
        save_cmd = [sys.executable, script_path, "--save", save_path, self.expected_dir]
        result = subprocess.run(save_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"  ERROR: Failed to save: {result.stderr}")
            return

        print(f"  Saved. Now comparing {format_name} with got...")
        result = self.run_command(save_path, self.got_dir)


# ============================================================================
# Utility: Create .deb files for testing
# ============================================================================

def create_deb_file(output_path, files_dict):
    """Create a minimal .deb file with specified files.

    Args:
        output_path: Path where .deb file will be created
        files_dict: Dict of {file_path: content} (content as bytes or str)
    """
    # Create tar with the files
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
        for file_path, content in files_dict.items():
            if isinstance(content, str):
                content = content.encode('utf-8')

            # Handle directories
            if file_path.endswith('/'):
                tarinfo = tarfile.TarInfo(name=file_path)
                tarinfo.type = tarfile.DIRTYPE
                tarinfo.mode = 0o755
                tar.addfile(tarinfo)
            else:
                tarinfo = tarfile.TarInfo(name=file_path)
                tarinfo.size = len(content)
                tarinfo.mode = 0o644
                tar.addfile(tarinfo, io.BytesIO(content))

    tar_data = tar_buffer.getvalue()
    tar_xz = lzma.compress(tar_data)

    # Create ar archive with required entries
    ar_data = b"!<arch>\n"

    # debian-binary entry
    debian_binary_content = b"2.0\n"
    ar_data += _create_ar_entry("debian-binary", debian_binary_content)

    # control.tar.xz entry (minimal empty)
    empty_tar = io.BytesIO()
    with tarfile.open(fileobj=empty_tar, mode='w') as tar:
        pass
    control_tar_xz = lzma.compress(empty_tar.getvalue())
    ar_data += _create_ar_entry("control.tar.xz", control_tar_xz)

    # data.tar.xz entry (actual content)
    ar_data += _create_ar_entry("data.tar.xz", tar_xz)

    # Write .deb file
    with open(output_path, 'wb') as f:
        f.write(ar_data)


def _create_ar_entry(filename, content):
    """Create an ar archive entry (60-byte header + content)."""
    name_field = filename.encode('ascii').ljust(16)[:16]
    mtime_field = str(int(time.time())).ljust(12)[:12].encode('ascii')
    owner_field = b"0       "[:6]
    group_field = b"0       "[:6]
    mode_field = b"100644  "[:6]
    size_field = str(len(content)).ljust(12)[:12].encode('ascii')
    magic_field = b"`\n"

    header = name_field + mtime_field + owner_field + group_field + mode_field + size_field + magic_field

    # Pad content to even boundary
    padded_content = content
    if len(content) % 2 == 1:
        padded_content = content + b"\n"

    return header + padded_content


# ============================================================================
# Scenario 1: Size Changes
# ============================================================================

class SizeChangeScenario(TestScenario):
    """Scenario with files that change size."""

    def __init__(self):
        super().__init__("size_changes", "Files with various size changes")

    def setup(self):
        super().setup()

        # Expected tree
        Path(f"{self.expected_dir}/small.txt").write_text("x" * 100)
        Path(f"{self.expected_dir}/medium.txt").write_text("y" * 1000)
        Path(f"{self.expected_dir}/large.txt").write_text("z" * 10000)

        # Got tree - with size changes
        Path(f"{self.got_dir}/small.txt").write_text("x" * 100)  # Same
        Path(f"{self.got_dir}/medium.txt").write_text("y" * 1500)  # +50% increase
        Path(f"{self.got_dir}/large.txt").write_text("z" * 9000)  # Decreased

    def run(self):
        # Baseline
        self.test_case(
            "Baseline (default: 1% threshold)",
            self.expected_dir, self.got_dir
        )

        # Relax threshold
        self.test_case(
            "Relaxed threshold (10%)",
            self.expected_dir, self.got_dir,
            "--max_allowed_percent_increase", "10"
        )

        # Relax further
        self.test_case(
            "Very relaxed (100%)",
            self.expected_dir, self.got_dir,
            "--max_allowed_percent_increase", "100"
        )

        # Ignore decreases
        self.test_case(
            "Ignore decreases",
            self.expected_dir, self.got_dir,
            "--no-show_decreases",
            "--max_allowed_percent_increase", "10"
        )

        # Absolute threshold
        self.test_case(
            "Absolute increase threshold (200 bytes)",
            self.expected_dir, self.got_dir,
            "--max_allowed_absolute_increase", "200"
        )

        # Minimum file size
        self.test_case(
            "Ignore files < 500 bytes",
            self.expected_dir, self.got_dir,
            "--minimum_compare_size", "500"
        )

        # Save and compare
        self.save_and_compare("JSON", f"{self.temp_dir}/expected.json")
        self.save_and_compare("tar.gz", f"{self.temp_dir}/expected.tar.gz")
        self.save_and_compare("tar.xz", f"{self.temp_dir}/expected.tar.xz")
        self.save_and_compare(".tgz", f"{self.temp_dir}/expected.tgz")


# ============================================================================
# Scenario 2: File Presence
# ============================================================================

class FilePresenceScenario(TestScenario):
    """Scenario with missing and extra files."""

    def __init__(self):
        super().__init__("file_presence", "Files added and removed")

    def setup(self):
        super().setup()

        # Expected tree
        Path(f"{self.expected_dir}/common1.txt").write_text("shared")
        Path(f"{self.expected_dir}/common2.txt").write_text("shared")
        Path(f"{self.expected_dir}/only_expected.txt").write_text("removed")

        os.makedirs(f"{self.expected_dir}/subdir", exist_ok=True)
        Path(f"{self.expected_dir}/subdir/nested.txt").write_text("nested")

        # Got tree
        Path(f"{self.got_dir}/common1.txt").write_text("shared")
        Path(f"{self.got_dir}/common2.txt").write_text("shared")
        Path(f"{self.got_dir}/only_got.txt").write_text("extra")

        os.makedirs(f"{self.got_dir}/subdir", exist_ok=True)
        Path(f"{self.got_dir}/subdir/nested.txt").write_text("nested")
        Path(f"{self.got_dir}/subdir/new_file.txt").write_text("new")

    def run(self):
        # Baseline
        self.test_case(
            "Baseline (show all differences)",
            self.expected_dir, self.got_dir
        )

        # Filter to only show missing files
        self.test_case(
            "Filter: show only 'only_' files",
            self.expected_dir, self.got_dir,
            "--include", "only_"
        )

        # Filter to exclude subdir
        self.test_case(
            "Filter: exclude subdir",
            self.expected_dir, self.got_dir,
            "--exclude", "subdir"
        )

        # Save and compare
        self.save_and_compare("JSON", f"{self.temp_dir}/expected.json")
        self.save_and_compare("tar.gz", f"{self.temp_dir}/expected.tar.gz")


# ============================================================================
# Scenario 3: Metadata Changes
# ============================================================================

class MetadataChangeScenario(TestScenario):
    """Scenario with permission and ownership changes."""

    def __init__(self):
        super().__init__("metadata_changes", "File permissions and ownership changes")

    def setup(self):
        super().setup()

        # Expected tree
        f1 = Path(f"{self.expected_dir}/file1.txt")
        f1.write_text("content")
        os.chmod(f1, 0o644)

        f2 = Path(f"{self.expected_dir}/file2.txt")
        f2.write_text("content")
        os.chmod(f2, 0o755)

        os.makedirs(f"{self.expected_dir}/dir1", exist_ok=True)
        os.chmod(f"{self.expected_dir}/dir1", 0o755)

        # Got tree - same content but different modes
        f1_got = Path(f"{self.got_dir}/file1.txt")
        f1_got.write_text("content")
        os.chmod(f1_got, 0o755)  # Changed

        f2_got = Path(f"{self.got_dir}/file2.txt")
        f2_got.write_text("content")
        os.chmod(f2_got, 0o755)  # Same

        os.makedirs(f"{self.got_dir}/dir1", exist_ok=True)
        os.chmod(f"{self.got_dir}/dir1", 0o711)  # Changed

    def run(self):
        # Baseline
        self.test_case(
            "Baseline (show metadata changes)",
            self.expected_dir, self.got_dir
        )

        # Filter to only files
        self.test_case(
            "Filter: files only (no directories)",
            self.expected_dir, self.got_dir,
            "--exclude", "^dir"
        )

        # Save and compare
        self.save_and_compare("JSON", f"{self.temp_dir}/expected.json")
        self.save_and_compare("tar.gz", f"{self.temp_dir}/expected.tar.gz")


# ============================================================================
# Scenario 4: Symlinks
# ============================================================================

class SymlinkScenario(TestScenario):
    """Scenario with symlink changes."""

    def __init__(self):
        super().__init__("symlinks", "Symlink target changes")

    def setup(self):
        super().setup()

        # Expected tree
        Path(f"{self.expected_dir}/target1.txt").write_text("target")
        Path(f"{self.expected_dir}/target2.txt").write_text("target")
        os.symlink("target1.txt", f"{self.expected_dir}/link1")
        os.symlink("target2.txt", f"{self.expected_dir}/link2")

        # Got tree - link1 target changed
        Path(f"{self.got_dir}/target1.txt").write_text("target")
        Path(f"{self.got_dir}/target2.txt").write_text("target")
        os.symlink("target2.txt", f"{self.got_dir}/link1")  # Changed target
        os.symlink("target2.txt", f"{self.got_dir}/link2")  # Same

    def run(self):
        # Baseline
        self.test_case(
            "Baseline (show symlink changes)",
            self.expected_dir, self.got_dir
        )

        # Filter to symlinks only
        self.test_case(
            "Filter: symlinks only",
            self.expected_dir, self.got_dir,
            "--include", "^link"
        )

        # Save and compare
        self.save_and_compare("JSON", f"{self.temp_dir}/expected.json")
        self.save_and_compare("tar.gz", f"{self.temp_dir}/expected.tar.gz")


# ============================================================================
# Scenario 5: Complex Real-World
# ============================================================================

class ComplexScenario(TestScenario):
    """Complex scenario with mixed changes."""

    def __init__(self):
        super().__init__("complex", "Mixed changes: sizes, metadata, files, symlinks")

    def setup(self):
        super().setup()

        # Create a more realistic structure
        for dirname in ["bin", "lib", "config"]:
            os.makedirs(f"{self.expected_dir}/{dirname}", exist_ok=True)
            os.makedirs(f"{self.got_dir}/{dirname}", exist_ok=True)

        # Binary files (size changes)
        Path(f"{self.expected_dir}/bin/app").write_text("x" * 5000)
        Path(f"{self.got_dir}/bin/app").write_text("x" * 6000)  # 20% larger

        # Libraries (permissions change)
        lib_exp = Path(f"{self.expected_dir}/lib/libfoo.so")
        lib_exp.write_text("library")
        os.chmod(lib_exp, 0o755)

        lib_got = Path(f"{self.got_dir}/lib/libfoo.so")
        lib_got.write_text("library")
        os.chmod(lib_got, 0o644)  # Changed

        # Config files
        Path(f"{self.expected_dir}/config/app.conf").write_text("config")
        Path(f"{self.got_dir}/config/app.conf").write_text("config")
        Path(f"{self.got_dir}/config/new.conf").write_text("new")  # Extra file

        # Symlinks
        os.symlink("../lib/libfoo.so", f"{self.expected_dir}/lib.link")
        os.symlink("../bin/app", f"{self.got_dir}/lib.link")  # Different target

    def run(self):
        # Baseline
        self.test_case(
            "Baseline (all changes)",
            self.expected_dir, self.got_dir
        )

        # Focus on binaries
        self.test_case(
            "Focus: binary files only",
            self.expected_dir, self.got_dir,
            "--include", "bin/"
        )

        # Focus on libraries
        self.test_case(
            "Focus: library files only",
            self.expected_dir, self.got_dir,
            "--include", "lib/.*\\.so"
        )

        # Ignore small size changes
        self.test_case(
            "Relaxed: ignore size changes under 5%",
            self.expected_dir, self.got_dir,
            "--max_allowed_percent_increase", "5"
        )

        # Save and compare
        self.save_and_compare("JSON", f"{self.temp_dir}/expected.json")
        self.save_and_compare("tar.gz", f"{self.temp_dir}/expected.tar.gz")
        self.save_and_compare("tar.xz", f"{self.temp_dir}/expected.tar.xz")


# ============================================================================
# Scenario 6: .deb Package Files
# ============================================================================

class DebPackageScenario(TestScenario):
    """Scenario testing .deb package file format support."""

    def __init__(self):
        super().__init__("deb_packages", ".deb package file format support")

    def setup(self):
        super().setup()

        # Create .deb files instead of directories
        create_deb_file(
            f"{self.temp_dir}/expected.deb",
            {
                "usr/bin/app": b"#!/bin/bash\necho hello",
                "usr/lib/": "",
                "usr/lib/libfoo.so": b"binary library content",
                "usr/share/doc/app.txt": b"Documentation for app",
            }
        )

        create_deb_file(
            f"{self.temp_dir}/got.deb",
            {
                "usr/bin/app": b"#!/bin/bash\necho hello modified",
                "usr/lib/": "",
                "usr/lib/libfoo.so": b"binary library content",
                "usr/share/doc/app.txt": b"Documentation for app",
            }
        )

    def run(self):
        # Baseline: Compare two .deb files
        self.test_case(
            "Compare two .deb packages",
            f"{self.temp_dir}/expected.deb", f"{self.temp_dir}/got.deb"
        )

        # Save .deb to JSON
        print(f"\n  Test: Save .deb to JSON")
        print(f"  Command: tree_size_compare.py --save test.json expected.deb")
        print("  " + "-" * 65)

        script_path = os.path.join(os.path.dirname(__file__), "tree_size_compare.py")
        save_cmd = [
            sys.executable, script_path,
            "--save", f"{self.temp_dir}/deb_to_json.json",
            f"{self.temp_dir}/expected.deb"
        ]
        result = subprocess.run(save_cmd, capture_output=True, text=True)

        if result.stdout:
            for line in result.stdout.split('\n'):
                if line:
                    print(f"  {line}")

        if result.returncode == 0:
            print(f"  Successfully saved .deb as JSON")

            # Compare JSON back to original .deb (roundtrip test)
            print(f"\n  Test: Roundtrip verification (JSON -> .deb)")
            print(f"  Command: tree_size_compare.py deb_to_json.json expected.deb")
            print("  " + "-" * 65)

            result = self.run_command(
                f"{self.temp_dir}/deb_to_json.json",
                f"{self.temp_dir}/expected.deb"
            )

        # Compare .deb to directory (for mixed format support)
        print(f"\n  Test: Compare .deb to directory")
        os.makedirs(f"{self.temp_dir}/expected_dir/usr/bin", exist_ok=True)
        os.makedirs(f"{self.temp_dir}/expected_dir/usr/lib", exist_ok=True)
        os.makedirs(f"{self.temp_dir}/expected_dir/usr/share/doc", exist_ok=True)
        Path(f"{self.temp_dir}/expected_dir/usr/bin/app").write_bytes(b"#!/bin/bash\necho hello")
        Path(f"{self.temp_dir}/expected_dir/usr/lib/libfoo.so").write_bytes(b"binary library content")
        Path(f"{self.temp_dir}/expected_dir/usr/share/doc/app.txt").write_bytes(b"Documentation for app")

        self.test_case(
            "Compare directory to .deb",
            f"{self.temp_dir}/expected_dir",
            f"{self.temp_dir}/expected.deb"
        )


# ============================================================================
# Runner
# ============================================================================

def main():
    """Run all test scenarios."""
    scenarios = [
        SizeChangeScenario(),
        FilePresenceScenario(),
        MetadataChangeScenario(),
        SymlinkScenario(),
        ComplexScenario(),
        DebPackageScenario(),
    ]

    print("\n" + "=" * 70)
    print("Tree Size Compare Test Scenarios")
    print("=" * 70)
    print("\nThis framework demonstrates the tool's behavior by creating")
    print("known differences between expected and got trees, then running")
    print("various comparisons with different options.")
    print("\nEach scenario tests:")
    print("  - Baseline comparison with default settings")
    print("  - Various flags and filters")
    print("  - Consistency across different input formats (dir, JSON, tar)")

    try:
        for scenario in scenarios:
            scenario.setup()
            scenario.run()
            scenario.cleanup()

        print("\n" + "=" * 70)
        print("All scenarios completed successfully!")
        print("=" * 70)
        return 0

    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
