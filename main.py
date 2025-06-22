### AI File Butler ###

import time
import os
import shutil
from pathlib import Path

import file_utils.pdf as pdf
import file_utils.office as office
import file_utils.exe as exe
import file_utils.images as img
import file_utils.mp3 as mp3
from config import cfg, MINIMUM_AGE
#from file_utils.common import clean_filename
from file_utils.common import log, clear_terminal

INPUT_DIR = Path(cfg["input"])
failed_dir = cfg["failed_output"]

def should_delete(file_path: Path):
    """
    törlendő fájlok azonosítása kiterjesztés szerint
    """
    return file_path.suffix.lower() in [".torrent", ".tmp", ".crdownload"]


def main():
    clear_terminal()

    if not INPUT_DIR.exists():
        log(f"❌ A bemeneti mappa nem található: {INPUT_DIR}", level="ERROR")
        print(f"❌ A bemeneti mappa nem található: {INPUT_DIR}")
        return

    for file_path in INPUT_DIR.glob("**/*"):
        if file_path.is_file():
            if file_path.name.startswith("~$"):
                continue
            elif should_delete(file_path):
                file_path.unlink()
                log(f"🗑️ Törölve: {file_path.name}", level="INFO", to_console=True)                
                continue
            elif time.time() - os.path.getmtime(file_path) > MINIMUM_AGE:
                ext = file_path.suffix.lower()
                if ext == ".pdf":
                    pdf.process_pdf(file_path)
                elif ext in [".mp3", ".wav"]:
                    mp3.process_mp3(file_path)
                elif ext in [".jpg", ".jpeg", ".png"]:
                    img.process_image(file_path)
                elif ext in [".doc", ".docx", ".xls", ".xlsx"]:
                    office.process_office(file_path)                                        
                elif ext == ".exe":
                    exe.process_exe(file_path)                                        
                else:
                    log(f"[INFO] Nem támogatott fájltípus: {file_path.name}", level="INFO", to_console=True)
                    failed_dir.mkdir(parents=True, exist_ok=True)                    
                    destination_path = os.path.join(failed_dir, file_path.name)                        
                    shutil.move(file_path, destination_path)
                    log(f"[INFO] Áthelyezve ide: {destination_path}", level="INFO", to_console=True)                    

if __name__ == "__main__":
    main()

"""
ÖTLETK:
- szolgáltatás és exe-t is csináljunk (hogy gyakoroljam)
- zip, iso ?
"""
