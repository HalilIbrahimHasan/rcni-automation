from pathlib import Path
import shutil
import gzip
import zipfile
import tarfile
from datetime import datetime


def find_rcni_root() -> Path:
    current = Path(__file__).resolve()

    for parent in [current.parent, *current.parents]:
        zipped = parent / "extraction" / "zipped"
        unzipped = parent / "extraction" / "unzipped"

        if zipped.exists() and unzipped.exists():
            return parent

    raise FileNotFoundError(
        "RCNI root bulunamadı. Beklenen structure: RCNI/extraction/zipped ve RCNI/extraction/unzipped"
    )


def unique_path(target: Path) -> Path:
    if not target.exists():
        return target

    counter = 1
    while True:
        duplicate = target.with_name(
            f"{target.stem}__duplicate_{counter}{target.suffix}"
        )
        if not duplicate.exists():
            return duplicate
        counter += 1


def log(log_file: Path, message: str):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    print(line)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def is_archive(file_path: Path) -> bool:
    name = file_path.name.lower()
    return (
        name.endswith(".zip")
        or name.endswith(".gz")
        or name.endswith(".tar")
        or name.endswith(".tar.gz")
        or name.endswith(".tgz")
        or name.endswith(".tar.bz2")
        or name.endswith(".tar.xz")
    )


def copy_flat(file_path: Path, output_folder: Path, log_file: Path):
    destination = unique_path(output_folder / file_path.name)
    shutil.copy2(file_path, destination)
    log(log_file, f"COPIED: {file_path.name} -> {destination.name}")


def extract_zip_flat(file_path: Path, output_folder: Path, log_file: Path):
    with zipfile.ZipFile(file_path, "r") as zip_ref:
        for member in zip_ref.infolist():
            if member.is_dir():
                continue

            file_name = Path(member.filename).name
            if not file_name:
                continue

            destination = unique_path(output_folder / file_name)

            with zip_ref.open(member) as source:
                with open(destination, "wb") as target:
                    shutil.copyfileobj(source, target)

            log(log_file, f"ZIP EXTRACTED: {file_path.name} -> {destination.name}")


def extract_tar_flat(file_path: Path, output_folder: Path, log_file: Path):
    with tarfile.open(file_path, "r:*") as tar_ref:
        for member in tar_ref.getmembers():
            if not member.isfile():
                continue

            file_name = Path(member.name).name
            if not file_name:
                continue

            destination = unique_path(output_folder / file_name)
            source = tar_ref.extractfile(member)

            if source is None:
                log(log_file, f"TAR MEMBER SKIPPED: {member.name}")
                continue

            with source:
                with open(destination, "wb") as target:
                    shutil.copyfileobj(source, target)

            log(log_file, f"TAR EXTRACTED: {file_path.name} -> {destination.name}")


def extract_gz_flat(file_path: Path, output_folder: Path, log_file: Path):
    destination = unique_path(output_folder / file_path.stem)

    with gzip.open(file_path, "rb") as gz_file:
        with open(destination, "wb") as out_file:
            shutil.copyfileobj(gz_file, out_file)

    log(log_file, f"GZ EXTRACTED: {file_path.name} -> {destination.name}")


def remove_archive_if_inside_unzipped(file_path: Path, unzipped_folder: Path, log_file: Path):
    try:
        if file_path.parent.resolve() == unzipped_folder.resolve() and file_path.exists():
            file_path.unlink()
            log(log_file, f"REMOVED ARCHIVE FROM UNZIPPED: {file_path.name}")
    except Exception as e:
        log(log_file, f"ERROR REMOVING ARCHIVE: {file_path} | {type(e).__name__}: {e}")


def extract_one(file_path: Path, unzipped_folder: Path, log_file: Path):
    name = file_path.name.lower()

    try:
        if name.endswith(".zip"):
            extract_zip_flat(file_path, unzipped_folder, log_file)
            remove_archive_if_inside_unzipped(file_path, unzipped_folder, log_file)

        elif tarfile.is_tarfile(file_path):
            extract_tar_flat(file_path, unzipped_folder, log_file)
            remove_archive_if_inside_unzipped(file_path, unzipped_folder, log_file)

        elif name.endswith(".gz"):
            extract_gz_flat(file_path, unzipped_folder, log_file)
            remove_archive_if_inside_unzipped(file_path, unzipped_folder, log_file)

        else:
            copy_flat(file_path, unzipped_folder, log_file)

    except Exception as e:
        log(log_file, f"ERROR: {file_path} | {type(e).__name__}: {e}")


def remove_folders_from_unzipped(unzipped_folder: Path, log_file: Path):
    folders = sorted(
        [p for p in unzipped_folder.rglob("*") if p.is_dir()],
        reverse=True
    )

    for folder in folders:
        try:
            shutil.rmtree(folder)
            log(log_file, f"REMOVED FOLDER FROM UNZIPPED: {folder}")
        except Exception as e:
            log(log_file, f"ERROR REMOVING FOLDER: {folder} | {type(e).__name__}: {e}")


def remove_remaining_archives(unzipped_folder: Path, log_file: Path):
    for file_path in list(unzipped_folder.rglob("*")):
        if file_path.is_file() and is_archive(file_path):
            try:
                file_path.unlink()
                log(log_file, f"REMOVED LEFTOVER ARCHIVE: {file_path.name}")
            except Exception as e:
                log(log_file, f"ERROR REMOVING LEFTOVER ARCHIVE: {file_path} | {type(e).__name__}: {e}")


def extract_all_files():
    rcni_root = find_rcni_root()

    zipped_folder = rcni_root / "extraction" / "zipped"
    unzipped_folder = rcni_root / "extraction" / "unzipped"
    logs_folder = rcni_root / "extraction" / "logs"

    unzipped_folder.mkdir(parents=True, exist_ok=True)
    logs_folder.mkdir(parents=True, exist_ok=True)

    log_file = logs_folder / f"extraction_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    log(log_file, "STARTED")
    log(log_file, f"READING FROM: {zipped_folder}")
    log(log_file, f"WRITING TO FLAT FOLDER: {unzipped_folder}")

    processed = set()

    while True:
        source_files = [
            p for p in zipped_folder.rglob("*")
            if p.is_file() and p.resolve() not in processed
        ]

        nested_archives = [
            p for p in unzipped_folder.rglob("*")
            if p.is_file()
            and p.resolve() not in processed
            and is_archive(p)
        ]

        files_to_process = source_files + nested_archives

        if not files_to_process:
            break

        for file_path in files_to_process:
            processed.add(file_path.resolve())
            extract_one(file_path, unzipped_folder, log_file)

    remove_remaining_archives(unzipped_folder, log_file)
    remove_folders_from_unzipped(unzipped_folder, log_file)

    total_source_files = len([p for p in zipped_folder.rglob("*") if p.is_file()])
    total_output_files = len([p for p in unzipped_folder.rglob("*") if p.is_file()])

    log(log_file, f"TOTAL SOURCE FILES: {total_source_files}")
    log(log_file, f"TOTAL OUTPUT FILES: {total_output_files}")
    log(log_file, "COMPLETED")


def test_extract_all_files():
    extract_all_files()


if __name__ == "__main__":
    extract_all_files()
