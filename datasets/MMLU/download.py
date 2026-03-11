from pathlib import Path
import shutil
import tempfile
import urllib.request
import zipfile
import tarfile


MMLU_ZIP_URL = "https://github.com/hendrycks/test/archive/refs/heads/master.zip"
MMLU_DATA_TAR_URL = "https://people.eecs.berkeley.edu/~hendrycks/data.tar"
MIN_SUBJECT_FILES = 50


def _csv_count(path: Path) -> int:
    return len(list(path.glob("*.csv")))


def _is_dataset_ready(root: Path) -> bool:
    dev_dir = root / "dev"
    val_dir = root / "val"
    return _csv_count(dev_dir) >= MIN_SUBJECT_FILES and _csv_count(val_dir) >= MIN_SUBJECT_FILES


def download(force: bool = False) -> None:
    """Download full MMLU dev/val CSVs if not present.

    Target layout:
      datasets/MMLU/data/dev/*.csv
      datasets/MMLU/data/val/*.csv
    """
    data_root = Path(__file__).resolve().parent / "data"
    dev_dir = data_root / "dev"
    val_dir = data_root / "val"
    dev_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)

    if not force and _is_dataset_ready(data_root):
        return

    with tempfile.TemporaryDirectory(prefix="mmlu_download_") as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Try official data tar first (contains actual CSV data).
        tar_path = tmp_path / "mmlu_data.tar"
        urllib.request.urlretrieve(MMLU_DATA_TAR_URL, tar_path)
        with tarfile.open(tar_path, "r") as tf:
            tf.extractall(tmp_path)

        src_dev = tmp_path / "data" / "dev"
        src_val = tmp_path / "data" / "val"

        # Fallback to repo zip if data.tar layout is unavailable.
        if not src_dev.exists() or not src_val.exists():
            zip_path = tmp_path / "mmlu_master.zip"
            urllib.request.urlretrieve(MMLU_ZIP_URL, zip_path)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmp_path)
            extracted_root = tmp_path / "test-master" / "data"
            src_dev = extracted_root / "dev"
            src_val = extracted_root / "val"

        if not src_dev.exists() or not src_val.exists():
            raise RuntimeError("Downloaded archives do not contain expected MMLU dev/val folders.")

        shutil.rmtree(dev_dir, ignore_errors=True)
        shutil.rmtree(val_dir, ignore_errors=True)
        shutil.copytree(src_dev, dev_dir)
        shutil.copytree(src_val, val_dir)

    if not _is_dataset_ready(data_root):
        raise RuntimeError("MMLU download completed but dev/val file counts are insufficient.")
