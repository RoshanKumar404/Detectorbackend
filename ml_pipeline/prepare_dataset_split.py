import argparse
import hashlib
import os
import shutil
from pathlib import Path

from PIL import Image, ImageFile
from sklearn.model_selection import train_test_split


ImageFile.LOAD_TRUNCATED_IMAGES = True
CLASS_ALIASES = {
    "Not-WaterLogged": {"Not-WaterLogged", "not-waterlogged", "photos", "dry_road", "dry"},
    "waterlogged": {"Waterlogged", "waterlogged", "low_waterlogging", "high_waterlogging"},
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def canonical_class(folder_name):
    for class_name, aliases in CLASS_ALIASES.items():
        if folder_name in aliases:
            return class_name
    return None


def file_hash(path):
    digest = hashlib.sha1()
    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_readable_image(path):
    try:
        with Image.open(path) as image:
            image.convert("RGB").resize((224, 224))
        return True
    except (OSError, ValueError) as error:
        print(f"Skipping unreadable image: {path} ({error})")
        return False


def collect_images(source_dirs):
    images_by_class = {class_name: [] for class_name in CLASS_ALIASES}
    seen_hashes = set()

    for source_dir in source_dirs:
        source_path = Path(source_dir)
        if not source_path.exists():
            continue

        for class_dir in [path for path in source_path.iterdir() if path.is_dir()]:
            class_name = canonical_class(class_dir.name)
            if not class_name:
                continue

            for image_path in class_dir.iterdir():
                if not image_path.is_file() or image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                    continue

                if not is_readable_image(image_path):
                    continue

                digest = file_hash(image_path)
                if digest in seen_hashes:
                    continue

                seen_hashes.add(digest)
                images_by_class[class_name].append(image_path)

    return images_by_class


def copy_split(images_by_class, output_dir, test_size):
    output_path = Path(output_dir)
    if output_path.exists():
        shutil.rmtree(output_path)

    for class_name, images in images_by_class.items():
        if len(images) < 2:
            raise ValueError(f"Need at least 2 images for class '{class_name}', found {len(images)}")

        train_images, val_images = train_test_split(
            images,
            test_size=test_size,
            random_state=42,
            shuffle=True,
        )

        for split_name, split_images in {"train": train_images, "val": val_images}.items():
            class_output_dir = output_path / split_name / class_name
            class_output_dir.mkdir(parents=True, exist_ok=True)

            for index, image_path in enumerate(split_images, start=1):
                output_file = class_output_dir / f"{class_name}_{index:05d}{image_path.suffix.lower()}"
                shutil.copy2(image_path, output_file)

        print(f"{class_name}: {len(train_images)} train, {len(val_images)} validation")


def main():
    parser = argparse.ArgumentParser(description="Create a clean train/validation split with stable class names.")
    parser.add_argument("--source", action="append", required=True, help="Source dataset folder. Can be used more than once.")
    parser.add_argument("--output", default="dataset_retrain", help="Output folder for the generated split.")
    parser.add_argument("--test-size", type=float, default=0.2, help="Validation fraction.")
    args = parser.parse_args()

    images_by_class = collect_images(args.source)
    copy_split(images_by_class, args.output, args.test_size)
    print(f"Prepared split at {args.output}")


if __name__ == "__main__":
    main()
