import os
import shutil
import sys
import psutil  # Added for memory monitoring
from pathlib import Path


def log_message(message):
    """Ensure messages are immediately flushed"""
    print(message, file=sys.stderr)
    sys.stderr.flush()


def copy_directory(src_root, dest_root):
    """Streaming file copier for huge directories"""
    count = 0
    errors = 0

    # Ensure the root destination directory exists
    Path(dest_root).mkdir(parents=True, exist_ok=True)

    for root, dirs, files in os.walk(src_root):
        # Process directories first
        for dirname in dirs:
            src_dir_path = os.path.join(root, dirname)
            rel_dir_path = os.path.relpath(src_dir_path, src_root)
            dest_dir_path = os.path.join(dest_root, rel_dir_path)
            Path(dest_dir_path).mkdir(parents=True, exist_ok=True)

        # Process files in current directory
        for filename in files:
            try:
                src_path = os.path.join(root, filename)
                rel_path = os.path.relpath(src_path, src_root)
                dest_path = os.path.join(dest_root, rel_path)

                # Create parent directory if needed
                # This is technically redundant if dirs are processed first as above,
                # but provides an extra layer of safety.
                # os.makedirs(os.path.dirname(dest_path), exist_ok=True) # Already handled by Path(dest_dir_path).mkdir

                shutil.copy2(src_path, dest_path)
                count += 1

                if count % 1000 == 0:
                    mem = psutil.virtual_memory()
                    log_message(
                        f"Copied {count} files | "
                        f"Mem: {mem.used / (1024 * 1024):.1f}MB used/"
                        f"{mem.total / (1024 * 1024):.1f}MB total"
                    )

            except Exception as e:
                errors += 1
                log_message(f"ERROR: {src_path} → {dest_path}: {str(e)}")
                # Attempt simple retry
                try:
                    log_message(f"Attempting retry for: {src_path}")
                    shutil.copy2(src_path, dest_path)
                    log_message(f"RETRY SUCCESS: {src_path}")
                    count += 1  # Count as success if retry works
                    errors -= 1  # Decrement error count
                except Exception as e2:
                    log_message(f"RETRY FAILED: {src_path} → {dest_path}: {str(e2)}")

    return count, errors


if __name__ == "__main__":
    if len(sys.argv) != 3:
        log_message("Usage: python streaming_copier.py <source_dir> <dest_dir>")
        sys.exit(1)

    src = sys.argv[1]
    dest = sys.argv[2]

    log_message(f"Starting copy: {src} → {dest}")
    total_files, total_errors = copy_directory(src, dest)
    success_rate = 0.0
    if (
        total_files + total_errors > 0
    ):  # Avoid division by zero if no files processed at all
        # Calculate success rate based on files successfully copied out of total
        # attempts. If a file failed even after retry, it contributes to
        # (total_files + total_errors) but not to total_files.
        # Initial total_files counts only successful copies (including retries).
        # total_errors counts files that failed even after retry.
        # So, total attempts = initial_successful_copies + final_errors
        # No, total_files already includes retried successes.
        # So, total_processed_or_attempted = total_files (successes) +
        # total_errors (final failures)

        # If total_files is 0 and total_errors is > 0, success_rate is 0.
        # If total_files is > 0, then calculate rate.
        if total_files == 0 and total_errors > 0:
            success_rate = 0.0
        elif total_files > 0:  # This implicitly means total_files + total_errors > 0
            success_rate = (total_files / (total_files + total_errors)) * 100
        else:  # total_files == 0 and total_errors == 0 (no files found/processed)
            # Or arguably undefined, but 100% success on 0 files is fine.
            success_rate = 100.0

    log_message(
        f"\nCompleted! {total_files} files copied | {total_errors} errors | "
        f"Success rate: {success_rate:.2f}%"
    )

    if total_errors > 0:
        sys.exit(1)
    else:
        sys.exit(0)
