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


def unique_path(target: Path) -> Path:
    if not target.exists():
        return target

    counter = 1
    while True:
        new_path = target.with_name(f"{target.stem}__duplicate_{counter}{target.suffix}")
        if not new_path.exists():
            return new_path
        counter += 1


def log(log_file: Path, message: str):
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    print(line)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def detect_file_type(file_path: Path) -> str:
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


def copy_file(file_path: Path, output_folder: Path, log_file: Path):
    destination = unique_path(output_folder / file_path.name)
    shutil.copy2(file_path, destination)
    log(log_file, f"COPIED NORMAL FILE: {file_path.name} -> {destination.name}")


def extract_zip(file_path: Path, output_folder: Path, log_file: Path):
    with zipfile.ZipFile(file_path, "r") as zip_ref:
        for member in zip_ref.infolist():
            if member.is_dir():
                continue

            file_name = Path(member.filename).name
            if not file_name:
                continue

            destination = unique_path(output_folder / file_name)

            with zip_ref.open(member) as source, open(destination, "wb") as target:
                shutil.copyfileobj(source, target)

            log(log_file, f"ZIP EXTRACTED: {file_path.name} -> {destination.name}")


def extract_gz(file_path: Path, output_folder: Path, log_file: Path):
    output_name = file_path.stem

    if not output_name.lower().endswith(".xml"):
        output_name = output_name + ".xml"

    destination = unique_path(output_folder / output_name)

    with gzip.open(file_path, "rb") as gz_file, open(destination, "wb") as out_file:
        shutil.copyfileobj(gz_file, out_file)

    log(log_file, f"GZ EXTRACTED: {file_path.name} -> {destination.name}")


def extract_tar(file_path: Path, output_folder: Path, log_file: Path):
    with tarfile.open(file_path, "r:*") as tar_ref:
        for member in tar_ref.getmembers():
            if not member.isfile():
                continue

            file_name = Path(member.name).name
            if not file_name:
                continue

            destination = unique_path(output_folder / file_name)
            source = tar_ref.extractfile(member)

            if source:
                with source, open(destination, "wb") as target:
                    shutil.copyfileobj(source, target)

                log(log_file, f"TAR EXTRACTED: {file_path.name} -> {destination.name}")


def process_file(file_path: Path, output_folder: Path, log_file: Path):
    file_type = detect_file_type(file_path)

    try:
        if file_type == "zip":
            extract_zip(file_path, output_folder, log_file)

        elif file_type == "gz":
            extract_gz(file_path, output_folder, log_file)

        elif file_type == "tar":
            extract_tar(file_path, output_folder, log_file)

        elif file_type == "normal":
            copy_file(file_path, output_folder, log_file)

        else:
            log(log_file, f"UNKNOWN FILE TYPE SKIPPED: {file_path}")

    except Exception as e:
        log(log_file, f"ERROR: {file_path.name} | {type(e).__name__}: {e}")


def clear_unzipped_folder(unzipped_folder: Path, log_file: Path):
    for item in unzipped_folder.iterdir():
        try:
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        except Exception as e:
            log(log_file, f"ERROR CLEANING: {item} | {type(e).__name__}: {e}")


def extract_all_files():
    rcni_root = find_rcni_root()

    zipped_folder = rcni_root / "extraction" / "zipped"
    unzipped_folder = rcni_root / "extraction" / "unzipped"
    logs_folder = rcni_root / "extraction" / "logs"

    unzipped_folder.mkdir(parents=True, exist_ok=True)
    logs_folder.mkdir(parents=True, exist_ok=True)

    log_file = logs_folder / f"extraction_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    log(log_file, "STARTED")
    log(log_file, f"SOURCE: {zipped_folder}")
    log(log_file, f"TARGET: {unzipped_folder}")

    clear_unzipped_folder(unzipped_folder, log_file)

    processed = set()

    while True:
        files_to_process = [
            p for p in zipped_folder.rglob("*")
            if p.is_file() and p.resolve() not in processed
        ] + [
            p for p in unzipped_folder.rglob("*")
            if p.is_file()
            and p.resolve() not in processed
            and detect_file_type(p) in ["zip", "gz", "tar"]
        ]

        if not files_to_process:
            break

        for file_path in files_to_process:
            processed.add(file_path.resolve())
            process_file(file_path, unzipped_folder, log_file)

            if file_path.is_file() and file_path.parent.resolve() == unzipped_folder.resolve():
                if detect_file_type(file_path) in ["zip", "gz", "tar"]:
                    file_path.unlink()
                    log(log_file, f"REMOVED ARCHIVE FROM UNZIPPED: {file_path.name}")

    for folder in sorted([p for p in unzipped_folder.rglob("*") if p.is_dir()], reverse=True):
        shutil.rmtree(folder)
        log(log_file, f"REMOVED FOLDER: {folder}")

    total_output = len([p for p in unzipped_folder.rglob("*") if p.is_file()])

    log(log_file, f"TOTAL OUTPUT FILES: {total_output}")
    log(log_file, "COMPLETED")


def test_extract_all_files():
    extract_all_files()


if __name__ == "__main__":
    extract_all_files()
