#!/usr/bin/env python3
"""
Deduplicate near-identical frames from YOLO training/val datasets.
Uses perceptual hashing (dHash) to find near-duplicates.
Moves duplicates to a backup folder instead of deleting.

Requirements: pip install Pillow

Usage:
    python dedup_frames.py D:\\dataset\\train\\images --dry-run
    python dedup_frames.py D:\\dataset\\train\\images --threshold 8
    python dedup_frames.py /path/to/dataset/val/images --threshold 6 --dry-run
"""

import argparse
import shutil
from pathlib import Path
from collections import defaultdict

try:
    from PIL import Image
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    exit(1)


def dhash(image_path, hash_size=16):
    """Compute difference hash for an image. Larger hash_size = more sensitive."""
    try:
        img = Image.open(image_path).convert("L").resize(
            (hash_size + 1, hash_size), Image.LANCZOS
        )
        pixels = list(img.getdata())
        diff = []
        for row in range(hash_size):
            for col in range(hash_size):
                left = pixels[row * (hash_size + 1) + col]
                right = pixels[row * (hash_size + 1) + col + 1]
                diff.append(1 if left > right else 0)
        return int("".join(str(b) for b in diff), 2)
    except Exception as e:
        print(f"  WARNING: Could not hash {image_path}: {e}")
        return None


def hamming_distance(h1, h2):
    """Count differing bits between two hashes."""
    return bin(h1 ^ h2).count("1")


def find_duplicates(image_dir, threshold=8):
    """
    Find near-duplicate images using dHash.
    threshold: max hamming distance to consider duplicate
      0  = exact match only
      6  = strict (very similar)
      8  = moderate (recommended starting point)
      12 = loose (catches more, may flag legit variations)
    """
    img_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}
    images = sorted([
        f for f in Path(image_dir).rglob("*")
        if f.suffix.lower() in img_extensions
    ])

    print(f"\n  Found {len(images)} images in {image_dir}")
    print(f"  Computing perceptual hashes...")

    hashes = []
    for i, img_path in enumerate(images):
        h = dhash(img_path)
        if h is not None:
            hashes.append((img_path, h))
        if (i + 1) % 100 == 0:
            print(f"    Hashed {i + 1}/{len(images)}...")

    print(f"  Hashed {len(hashes)} images successfully")
    print(f"  Comparing pairs (threshold={threshold})...")

    is_duplicate = set()
    duplicate_groups = defaultdict(list)

    for i in range(len(hashes)):
        if hashes[i][0] in is_duplicate:
            continue
        for j in range(i + 1, len(hashes)):
            if hashes[j][0] in is_duplicate:
                continue
            dist = hamming_distance(hashes[i][1], hashes[j][1])
            if dist <= threshold:
                is_duplicate.add(hashes[j][0])
                duplicate_groups[hashes[i][0]].append((hashes[j][0], dist))

    return duplicate_groups, len(images)


def move_duplicates(duplicate_groups, backup_dir, dry_run=False):
    """Move duplicate images (and their YOLO label files) to backup directory."""
    total_moved = 0
    class_counts = defaultdict(int)
    moved_files = []

    for kept, dupes in duplicate_groups.items():
        for dupe_path, dist in dupes:
            # Track by parent folder name
            class_name = dupe_path.parent.name
            class_counts[class_name] += 1

            # Find corresponding YOLO label file
            # Standard structure: .../images/xxx.jpg -> .../labels/xxx.txt
            label_path = None
            if "images" in dupe_path.parts:
                parts = list(dupe_path.parts)
                img_idx = len(parts) - 1 - parts[::-1].index("images")
                label_parts = parts[:img_idx] + ["labels"] + parts[img_idx + 1:]
                label_path = Path(*label_parts).with_suffix(".txt")

            if dry_run:
                label_exists = label_path and label_path.exists()
                print(f"  [DRY RUN] Remove: {dupe_path.name} "
                      f"(dist={dist}, keep={kept.name})"
                      f"{' +label' if label_exists else ''}")
                moved_files.append(str(dupe_path))
                total_moved += 1
                continue

            # Create backup subdirectory preserving folder structure
            rel = dupe_path.relative_to(dupe_path.parents[1]) if len(dupe_path.parts) > 2 else Path(dupe_path.name)
            backup_img = Path(backup_dir) / "images" / rel
            backup_img.parent.mkdir(parents=True, exist_ok=True)

            shutil.move(str(dupe_path), str(backup_img))
            moved_files.append(str(dupe_path))
            total_moved += 1

            # Move label if exists
            if label_path and label_path.exists():
                backup_lbl = Path(backup_dir) / "labels" / label_path.with_suffix(".txt").name
                backup_lbl.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(label_path), str(backup_lbl))

    return total_moved, class_counts, moved_files


def main():
    parser = argparse.ArgumentParser(
        description="Remove near-duplicate frames from YOLO dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview duplicates (no files moved)
  python dedup_frames.py D:\\dataset\\train\\images --dry-run

  # Remove duplicates with default threshold
  python dedup_frames.py D:\\dataset\\train\\images

  # Stricter matching (fewer removals)
  python dedup_frames.py D:\\dataset\\train\\images --threshold 6

  # Looser matching (more removals)
  python dedup_frames.py D:\\dataset\\train\\images --threshold 12

Threshold guide:
  0  = exact pixel match only
  6  = strict  (very similar frames)
  8  = moderate (recommended starting point)
  12 = loose   (catches more, may flag legit variations)
"""
    )
    parser.add_argument("dataset_path",
                        help="Path to images folder (e.g., D:/dataset/train/images)")
    parser.add_argument("--threshold", type=int, default=8,
                        help="Hamming distance threshold (default: 8)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview only — don't move any files")
    parser.add_argument("--backup-dir", default=None,
                        help="Backup location (default: <path>_duplicates)")
    args = parser.parse_args()

    dataset_path = Path(args.dataset_path)
    if not dataset_path.exists():
        print(f"ERROR: Path does not exist: {dataset_path}")
        return

    backup_dir = args.backup_dir or str(dataset_path) + "_duplicates"

    print("=" * 60)
    print("  YOLO Dataset Deduplication Tool")
    print("=" * 60)
    print(f"  Path:      {dataset_path}")
    print(f"  Threshold: {args.threshold}")
    print(f"  Backup to: {backup_dir}")
    print(f"  Mode:      {'DRY RUN (preview)' if args.dry_run else 'LIVE (will move files)'}")
    print("=" * 60)

    duplicate_groups, total_images = find_duplicates(dataset_path, args.threshold)
    total_dupes = sum(len(v) for v in duplicate_groups.values())

    if total_dupes == 0:
        print(f"\n{'=' * 60}")
        print(f"  ✅ No near-duplicates found! Dataset looks clean.")
        print(f"  Total images scanned: {total_images}")
        print(f"{'=' * 60}")
        return

    print(f"\n  Found {total_dupes} duplicates in {len(duplicate_groups)} groups")

    total_moved, class_counts, moved_files = move_duplicates(
        duplicate_groups, backup_dir, args.dry_run
    )

    # Summary report
    print(f"\n{'=' * 60}")
    print("  SUMMARY")
    print(f"{'=' * 60}")
    action = "Would remove" if args.dry_run else "Removed"
    remaining = total_images - total_moved
    print(f"  Total images scanned:  {total_images}")
    print(f"  {action}:              {total_moved}")
    print(f"  Remaining after dedup: {remaining}")
    print(f"  Reduction:             {total_moved / total_images * 100:.1f}%")

    if class_counts:
        print(f"\n  Duplicates by folder:")
        for cls, count in sorted(class_counts.items(), key=lambda x: -x[1]):
            print(f"    {cls}: {count} removed")

    if args.dry_run:
        print(f"\n  👆 This was a DRY RUN — no files were moved.")
        print(f"  Run again without --dry-run to actually move files.")
    elif total_moved > 0:
        print(f"\n  Files backed up to: {backup_dir}")
        print(f"  Review backup and delete when satisfied.")


if __name__ == "__main__":
    main()
