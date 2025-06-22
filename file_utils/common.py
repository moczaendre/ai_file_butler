import os
import time
import platform
import unicodedata
from datetime import datetime
from pathlib import Path
from config import LOG_PATH
from config import DEBUG


def clear_terminal():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

def clean_filename(text: str) -> str:
    """
    Fájlnév tisztítása érvénytelen karakterektől.
    """    
    invalid_chars = r'<>:"/\|?*'
    for ch in invalid_chars:
        text = text.replace(ch, "_")
    return text.strip()

def is_file_locked(path):
    try:
        with open(path, 'r+'):
            return False
    except IOError:
        return True
    
def get_file_creation_date(file_path):
    """
    Fájl létrehozásának dátuma (Windows-specifikus)
    """
    t = time.localtime(os.path.getctime(file_path))
    return f"{t.tm_year}_{t.tm_mon:02}_{t.tm_mday:02}"

def get_file_modify_date(file_path):
    """
    Fájl utolsó módosításának dátuma
    """
    t = time.localtime(os.path.getmtime(file_path))
    return f"{t.tm_year}_{t.tm_mon:02}_{t.tm_mday:02}"

def ensure_unique_filename(target_path: Path) -> Path:
    """
    Ha a megadott path már létezik, akkor _1, _2 stb. toldalékkal egyedi path-ot ad vissza.
    """
    if not target_path.exists():
        return target_path
    counter = 1
    orig_dir = target_path.parent
    orig_name = target_path.stem
    ext = target_path.suffix

    while target_path.exists():
        target_path = orig_dir / f"{orig_name}({counter}){ext}"
        counter += 1

    return target_path

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR"]

def log(message: str, level: str = "INFO", module: str = "general", to_console=False):
    """
    Általános logoló függvény. Modulonként szűrhető a DEBUG kapcsolóval.
    """
    if level == "DEBUG" and not DEBUG.get(module, False):
        return
    
    timestamp = datetime.now().isoformat(sep=' ', timespec='seconds')
    log_entry = f"{timestamp} | {level.upper():<5} | {module:<10} | {message}\n"

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as logf:
        logf.write(log_entry)
    if to_console:
        print(message)


def log_rename(original_path: Path, new_path: Path):
    log(f"{original_path} → {new_path}", level="INFO", module="rename")

def normalize_text(text):
    """
    ASCII-ra konvertálja, kiszedi az ékezetet, kisbetűsre alakítja
    """
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode().lower()    