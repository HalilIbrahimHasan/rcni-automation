from pathlib import Path
import shutil
import gzip
import lzma
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


def clean_folder(folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    for item in folder.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)


def detect_type(file_path: Path) -> str:
    try:
        with open(file_path, "rb") as f:
            header = f.read(8)

        if header.startswith(b"PK"):
            return "zip"

        if header.startswith(b"\x1f\x8b"):
            return "gz"

        if header.startswith(b"\xfd7zXZ"):
            return "xz"

        if tarfile.is_tarfile(file_path):
            return "tar"

        return "normal"
    except Exception:
        return "unknown"


def copy_final(file_path: Path, unzipped_folder: Path, log_file: Path):
    destination = unique_path(unzipped_folder / file_path.name)
    shutil.copy2(file_path, destination)
    log(log_file, f"COPIED FINAL FILE: {file_path.name} -> {destination.name}")


def extract_zip(file_path: Path, temp_folder: Path, log_file: Path) -> Path:
    extract_dir = unique_path(temp_folder / f"{file_path.stem}_zip")
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(file_path, "r") as z:
        z.extractall(extract_dir)

    log(log_file, f"ZIP EXTRACTED: {file_path.name}")
    return extract_dir


def extract_tar(file_path: Path, temp_folder: Path, log_file: Path) -> Path:
    extract_dir = unique_path(temp_folder / f"{file_path.stem}_tar")
    extract_dir.mkdir(parents=True, exist_ok=True)

    with tarfile.open(file_path, "r:*") as t:
        t.extractall(extract_dir)

    log(log_file, f"TAR EXTRACTED: {file_path.name}")
    return extract_dir


def extract_gz(file_path: Path, temp_folder: Path, log_file: Path) -> Path:
    output_name = file_path.name[:-3] if file_path.name.lower().endswith(".gz") else file_path.stem
    output_file = unique_path(temp_folder / output_name)

    with gzip.open(file_path, "rb") as gz:
        with open(output_file, "wb") as out:
            shutil.copyfileobj(gz, out)

    log(log_file, f"GZ EXTRACTED: {file_path.name} -> {output_file.name}")
    return output_file


def extract_xz(file_path: Path, temp_folder: Path, log_file: Path) -> Path:
    output_name = file_path.name[:-3] if file_path.name.lower().endswith(".xz") else file_path.stem
    output_file = unique_path(temp_folder / output_name)

    with lzma.open(file_path, "rb") as xz:
        with open(output_file, "wb") as out:
            shutil.copyfileobj(xz, out)

    log(log_file, f"XZ EXTRACTED: {file_path.name} -> {output_file.name}")
    return output_file


def process_item(item: Path, temp_folder: Path, unzipped_folder: Path, log_file: Path, queue: list):
    if item.is_dir():
        for child in item.iterdir():
            queue.append(child)
        return

    if not item.is_file():
        return

    file_type = detect_type(item)

    try:
        if file_type == "zip":
            queue.append(extract_zip(item, temp_folder, log_file))

        elif file_type == "tar":
            queue.append(extract_tar(item, temp_folder, log_file))

        elif file_type == "gz":
            queue.append(extract_gz(item, temp_folder, log_file))

        elif file_type == "xz":
            queue.append(extract_xz(item, temp_folder, log_file))

        elif file_type == "normal":
            copy_final(item, unzipped_folder, log_file)

        else:
            log(log_file, f"SKIPPED UNKNOWN TYPE: {item}")

    except Exception as e:
        log(log_file, f"ERROR: {item} | {type(e).__name__}: {e}")


def extract_all_files():
    rcni_root = find_rcni_root()

    zipped_folder = rcni_root / "extraction" / "zipped"
    unzipped_folder = rcni_root / "extraction" / "unzipped"
    temp_folder = rcni_root / "extraction" / "_temp_extract"
    logs_folder = rcni_root / "extraction" / "logs"

    logs_folder.mkdir(parents=True, exist_ok=True)
    log_file = logs_folder / f"extraction_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    clean_folder(unzipped_folder)
    clean_folder(temp_folder)

    log(log_file, "STARTED")
    log(log_file, f"SOURCE: {zipped_folder}")
    log(log_file, f"TARGET: {unzipped_folder}")

    queue = list(zipped_folder.iterdir())

    while queue:
        item = queue.pop(0)
        process_item(item, temp_folder, unzipped_folder, log_file, queue)

    shutil.rmtree(temp_folder, ignore_errors=True)

    final_files = [p for p in unzipped_folder.iterdir() if p.is_file()]
    final_folders = [p for p in unzipped_folder.iterdir() if p.is_dir()]

    for folder in final_folders:
        shutil.rmtree(folder)
        log(log_file, f"REMOVED FINAL FOLDER: {folder.name}")

    log(log_file, f"FINAL FILE COUNT: {len(final_files)}")
    log(log_file, "COMPLETED")


def test_extract_all_files():
    extract_all_files()


if __name__ == "__main__":
    extract_all_files()
