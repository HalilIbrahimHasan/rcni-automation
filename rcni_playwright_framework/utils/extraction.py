from pathlib import Path
import shutil
import gzip
import zipfile
import tarfile
from datetime import datetime


def find_rcni_root() -> Path:
    current = Path(__file__).resolve()

    for parent in [current.parent, *current.parents]:
        if (parent / "extraction" / "zipped").exists():
            return parent

    raise FileNotFoundError("RCNI/extraction/zipped bulunamadı.")


def log(log_file: Path, message: str):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    print(line)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    counter = 1
    while True:
        new_path = path.with_name(f"{path.stem}__duplicate_{counter}{path.suffix}")
        if not new_path.exists():
            return new_path
        counter += 1


def detect_type(file_path: Path) -> str:
    try:
        with open(file_path, "rb") as f:
            header = f.read(8)

        if header.startswith(b"PK"):
            return "zip"

        if header.startswith(b"\x1f\x8b"):
            return "gz"

        if tarfile.is_tarfile(file_path):
            return "tar"

        return "normal"

    except Exception:
        return "unknown"


def clean_folder(folder: Path):
    folder.mkdir(parents=True, exist_ok=True)

    for item in folder.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)


def copy_final_file(file_path: Path, unzipped_folder: Path, log_file: Path):
    destination = unique_path(unzipped_folder / file_path.name)
    shutil.copy2(file_path, destination)
    log(log_file, f"FINAL FILE COPIED: {file_path.name} -> {destination.name}")


def extract_zip_to_temp(file_path: Path, temp_folder: Path, log_file: Path):
    extract_dir = temp_folder / f"{file_path.stem}_zip_extract"
    extract_dir = unique_path(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(file_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)

    log(log_file, f"ZIP EXTRACTED TO TEMP: {file_path.name}")
    return extract_dir


def extract_tar_to_temp(file_path: Path, temp_folder: Path, log_file: Path):
    extract_dir = temp_folder / f"{file_path.stem}_tar_extract"
    extract_dir = unique_path(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)

    with tarfile.open(file_path, "r:*") as tar_ref:
        tar_ref.extractall(extract_dir)

    log(log_file, f"TAR EXTRACTED TO TEMP: {file_path.name}")
    return extract_dir


def extract_gz_to_temp(file_path: Path, temp_folder: Path, log_file: Path):
    output_name = file_path.stem

    if not Path(output_name).suffix:
        output_name = output_name + ".xml"

    output_file = unique_path(temp_folder / output_name)

    with gzip.open(file_path, "rb") as gz_file:
        with open(output_file, "wb") as out_file:
            shutil.copyfileobj(gz_file, out_file)

    log(log_file, f"GZ EXTRACTED TO TEMP: {file_path.name} -> {output_file.name}")
    return output_file


def process_item(item: Path, temp_folder: Path, unzipped_folder: Path, log_file: Path, queue: list):
    if item.is_dir():
        log(log_file, f"FOLDER FOUND, READING INSIDE: {item}")
        for child in item.iterdir():
            queue.append(child)
        return

    if not item.is_file():
        return

    file_type = detect_type(item)

    try:
        if file_type == "zip":
            extracted_dir = extract_zip_to_temp(item, temp_folder, log_file)
            queue.append(extracted_dir)

        elif file_type == "tar":
            extracted_dir = extract_tar_to_temp(item, temp_folder, log_file)
            queue.append(extracted_dir)

        elif file_type == "gz":
            extracted_file = extract_gz_to_temp(item, temp_folder, log_file)
            queue.append(extracted_file)

        elif file_type == "normal":
            copy_final_file(item, unzipped_folder, log_file)

        else:
            log(log_file, f"UNKNOWN / SKIPPED: {item}")

    except Exception as e:
        log(log_file, f"ERROR: {item} | {type(e).__name__}: {e}")


def extract_all_files():
    rcni_root = find_rcni_root()

    zipped_folder = rcni_root / "extraction" / "zipped"
    unzipped_folder = rcni_root / "extraction" / "unzipped"
    logs_folder = rcni_root / "extraction" / "logs"
    temp_folder = rcni_root / "extraction" / "_temp_extract"

    logs_folder.mkdir(parents=True, exist_ok=True)
    log_file = logs_folder / f"extraction_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    log(log_file, "STARTED")
    log(log_file, f"SOURCE ZIPPED: {zipped_folder}")
    log(log_file, f"TARGET UNZIPPED: {unzipped_folder}")

    clean_folder(unzipped_folder)
    clean_folder(temp_folder)

    queue = list(zipped_folder.iterdir())

    while queue:
        item = queue.pop(0)
        process_item(item, temp_folder, unzipped_folder, log_file, queue)

    shutil.rmtree(temp_folder, ignore_errors=True)

    remaining_folders = [p for p in unzipped_folder.iterdir() if p.is_dir()]
    remaining_archives = [
        p for p in unzipped_folder.iterdir()
        if p.is_file() and detect_type(p) in ["zip", "gz", "tar"]
    ]

    for folder in remaining_folders:
        shutil.rmtree(folder)
        log(log_file, f"REMOVED UNWANTED FOLDER FROM FINAL: {folder.name}")

    for archive in remaining_archives:
        archive.unlink()
        log(log_file, f"REMOVED UNWANTED ARCHIVE FROM FINAL: {archive.name}")

    final_files = [p for p in unzipped_folder.iterdir() if p.is_file()]

    log(log_file, f"FINAL FILE COUNT: {len(final_files)}")
    log(log_file, "COMPLETED")


def test_extract_all_files():
    extract_all_files()


if __name__ == "__main__":
    extract_all_files()
