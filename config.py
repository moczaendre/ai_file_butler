from pathlib import Path
import platform

BASE_DIR = Path(__file__).resolve().parent

DEBUG = {
    "pdf": False,
    "mp3": True,
    "exe": False,    
    "office" : False,
}

cfg = {
    "base": BASE_DIR,    
    "input": BASE_DIR / "WORK" / "input",
    "output": BASE_DIR / "WORK" / "output",           
    #"office_output": Path("WORK/OFFICE"),    
    "os": platform.system()
}

LOG_DIR = cfg["output"] / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_PATH = LOG_DIR / "log.txt"

cfg["log"] = LOG_PATH
cfg["pdf_output"] = cfg["output"] / "PDF"
cfg["mp3_output"] = cfg["output"] / "MP3"
cfg["exe_output"] = cfg["output"] / "EXE"
cfg["img_output"] = cfg["output"] / "IMG"
cfg["office_output"] = cfg["output"] / "OFFICE"
cfg["failed_output"] = cfg["output"] / "_FAILED"

MINIMUM_AGE = 2 * 3600  # 2 óra másodpercben
