import os
import json
from pathlib import Path
import sys  # Import sys for stderr


def log_message(message):
    """Ensure messages are immediately flushed to stderr"""
    print(message, file=sys.stderr)
    sys.stderr.flush()


def chunked_file_listing(root_path, chunk_size=1000, output_dir="file_chunks"):
    Path(output_dir).mkdir(
        parents=True, exist_ok=True
    )  # Ensure output_dir is created with parents
    chunk_count = 0
    file_count = 0
    current_chunk = []

    log_message(f"Starting to walk directory: {root_path}")
    for root, _, files in os.walk(root_path):
        for file in files:
            try:
                file_path = os.path.join(root, file)
                # Make sure to generate paths relative to the *root_path* for portability
                rel_path = os.path.relpath(file_path, root_path)
                current_chunk.append(rel_path)
                file_count += 1

                if len(current_chunk) >= chunk_size:
                    output_filename = f"chunk_{chunk_count:05d}.json"
                    output_path = os.path.join(output_dir, output_filename)
                    with open(output_path, "w") as f:
                        json.dump(current_chunk, f)
                    log_message(
                        f"Saved chunk: {output_filename} with {len(current_chunk)} "
                        f"files in {output_dir}"
                    )
                    current_chunk = []
                    chunk_count += 1
            except Exception as e:
                log_message(
                    f"Error processing file "
                    f"{file_path if 'file_path' in locals() else file}: {str(e)}"
                )

    # Save remaining files in the last chunk
    if current_chunk:
        output_filename = f"chunk_{chunk_count:05d}.json"
        output_path = os.path.join(output_dir, output_filename)
        with open(output_path, "w") as f:
            json.dump(current_chunk, f)
        log_message(
            f"Saved final chunk: {output_filename} with {len(current_chunk)} "
            f"files in {output_dir}"
        )
        chunk_count += 1  # To correctly reflect the number of chunks created.

    log_message(
        f"Finished walking. Total files found: {file_count}. "
        f"Total chunks created: {chunk_count}."
    )
    return file_count, chunk_count


if __name__ == "__main__":
    # This script will be located at backend/generate_file_chunks.py
    # The source directory to scan is backend/gaia_genesis_new/
    # The output chunks should go into backend/file_chunks/
    source_dir_for_script = "backend/gaia_genesis_new"
    output_directory_for_script = "backend/file_chunks"

    files_found, chunks_made = chunked_file_listing(
        source_dir_for_script,
        chunk_size=500,
        output_dir=output_directory_for_script,
    )

    log_message(
        f"Script execution summary: Created {chunks_made} chunks for {files_found} "
        f"files in '{output_directory_for_script}'."
    )
