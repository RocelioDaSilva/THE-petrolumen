#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$HOME/THE-petrolumen" && pwd -P)"
current_dir="$(pwd -P)"
if [[ "$current_dir" != "$repo_root" && "$current_dir" != "$repo_root/"* ]]; then
  printf 'Refusing to run outside %s (current directory: %s)\n' "$repo_root" "$current_dir" >&2
  exit 1
fi

git_root="$(git -C "$repo_root" rev-parse --show-toplevel)"
if [[ "$(cd "$git_root" && pwd -P)" != "$repo_root" ]]; then
  printf 'Refusing to run: %s is not the Git repository root\n' "$repo_root" >&2
  exit 1
fi

cd "$repo_root"

items=("petrolumen_tmp" "c" "oil&gas projects")
backup_dir="$repo_root/../petrolumen_accident_backup"

for name in "${items[@]}"; do
  if [[ ! -d "$name" ]]; then
    printf 'Refusing to run: source directory is missing: %s\n' "$name" >&2
    exit 1
  fi
done

for name in "${items[@]}"; do
  if [[ -e "$backup_dir/$name" || -L "$backup_dir/$name" ]]; then
    printf 'Refusing to run: backup target already exists: %s\n' "$backup_dir/$name" >&2
    exit 1
  fi
done

mkdir -p -- "$backup_dir"

total_bytes=0

for name in "${items[@]}"; do
  before_bytes="$(du -sb -- "$name" | awk '{print $1}')"
  printf '%s: before move: %s bytes\n' "$name" "$before_bytes"
  mv -T -- "$name" "$backup_dir/$name"
  after_bytes="$(du -sb -- "$backup_dir/$name" | awk '{print $1}')"
  printf '%s: after move:  %s bytes\n' "$name" "$after_bytes"
  if [[ "$before_bytes" != "$after_bytes" ]]; then
    printf 'Byte count mismatch after moving %s; inspect the backup before proceeding.\n' "$name" >&2
    exit 1
  fi
  total_bytes=$((total_bytes + before_bytes))
done

printf 'Total bytes moved: %s\n' "$total_bytes"
printf 'Untracked files remaining: '
git ls-files --others --exclude-standard | wc -l
git status --short | wc -l
