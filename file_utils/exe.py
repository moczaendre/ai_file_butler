import os
from pathlib import Path
import shutil
import win32api
try:
    import win32com.client as win32
except ImportError:
    win32 = None
from config import DEBUG
from config import cfg
from file_utils.common import log
from file_utils.common import log_rename

out_dir = cfg["exe_output"]
out_dir.mkdir(parents=True, exist_ok=True)


def get_exe_info(file_path):
    """
    Exe információit próbálja összeszedni azonosításhoz.
    """
    try:
        info = win32api.GetFileVersionInfo(file_path, '\\')
        if not info:
            if DEBUG["pdf"]: 
                log(f"⚠️ Nincs exe információ: {file_path.name}", level="DEBUG", module="exe")
            return {}

        # Struktúra elérés
        str_info = {}
        if 'VarFileInfo' in info and 'Translation' in info['VarFileInfo']:
            for lang, codepage in info['VarFileInfo']['Translation']:
                str_info['CompanyName'] = win32api.VerQueryValue(info, f'\\StringFileInfo\\{lang:04X}{codepage:04X}\\CompanyName')
                str_info['ProductName'] = win32api.VerQueryValue(info, f'\\StringFileInfo\\{lang:04X}{codepage:04X}\\ProductName')
                str_info['FileDescription'] = win32api.VerQueryValue(info, f'\\StringFileInfo\\{lang:04X}{codepage:04X}\\FileDescription')
                str_info['OriginalFilename'] = win32api.VerQueryValue(info, f'\\StringFileInfo\\{lang:04X}{codepage:04X}\\OriginalFilename')
                break  # csak az első nyelvi adatot nézzük
        else:            
            log(f"⚠️ Nincs 'VarFileInfo' blokk: {file_path.name}", level="DEBUG", module="exe", to_console=True)            
            return {}

        return str_info
    except Exception as e:
        log(f"⚠️ Hiba az .exe fájl vizsgálatánál: {file_path} – {e}", level="ERROR", module="exe", to_console=True)        
        return {}

from typing import Optional

def categorize_exe(filename: str, info: Optional[dict[str, str]] = None) -> str:
    """
    Besorolja az EXE fájlt a fájlnév és – ha van – verzióinformáció alapján.

    :param filename: A fájl neve.
    :param info: (Opcionális) A fájlból kinyert verzióinformáció.
    :return: Kategória mappanév.
    """
    name = filename.lower()
    
    if info:
        desc = info.get("FileDescription", "").lower()
        prod = info.get("ProductName", "").lower()
        combined = f"{desc} {prod} {name}"
    else:
        combined = name

    if any(x in combined for x in ['driver', 'vga', 'nvidia']):
        return 'illesztoprogramok'
    elif any(x in combined for x in ['setup', 'install', 'telepit']):
        return 'telepitok'
    elif any(x in combined for x in ['update', 'updater']):
        return 'frissitok'
    elif any(x in combined for x in ['game', 'launcher']):
        return 'jatekok'
    elif any(x in combined for x in ['python', 'rust']):
        return 'fejlesztoi_eszkozok'
    elif any(x in combined for x in ['media', 'dvd', 'burn']):
        return 'multimedia'
    else:
        return 'ismeretlen'


def move_exe_to_category(file_path: Path, category: str):
    """
    EXE áthelyezése
    """
    target_dir = out_dir / category
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / file_path.name
    shutil.move(str(file_path), str(target_path))
    log_rename(str(file_path), str(target_path))
    print(f"[EXE] Áthelyezve: {file_path.name} → {category}/")


def process_exe(file_path: Path):
    info = get_exe_info(str(file_path))
    category = categorize_exe(file_path.name, info if info else None)                  
    move_exe_to_category(file_path, category)