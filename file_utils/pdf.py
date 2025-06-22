import re
import shutil
from pathlib import Path
from datetime import datetime
import fitz  # PyMuPDF
from file_utils.common import log, log_rename, clean_filename, ensure_unique_filename
from config import DEBUG, cfg


out_dir = cfg["pdf_output"]
out_dir.mkdir(parents=True, exist_ok=True)

# PDF típusok kulcsszavai
TÍPUS_KULCSSZAVAK = {
    "SZAMLA": ["számla", "invoice", "díjbekérő"],
    "BANKKIVONAT": ["bankkivonat", "tranzakció", "jóváírás"],
    "LELET": ["lelet", "vizsgálat", "labor"],
    "SZERZODES": ["szerződés", "megállapodás"],
    "IGAZOLAS": ["igazolás", "tanúsítvány"],
}

# Regex dátumra: 2023-09-27 vagy 2023.09.27
DATE_REGEX = r"(20\d{2}[-\.](0[1-9]|1[0-2])[-\.](0[1-9]|[12]\d|3[01]))"

# Regex számlaszámra (pl. #123456 vagy 2023/456 vagy hasonlók)
SZAMLA_REGEX = r"(?i)(?:számlasorszám|sorszám)\s*[:\-]?\s*(\S+)"

def is_pdf(file_path: Path) -> bool:
    return file_path.suffix.lower() == ".pdf"

def extract_pdf_text(pdf_path: Path, pages: int=-1) -> str:
    """
    PDF fájl szöveges tartalmát kinyeri a megadott oldalszám erejéig (pages=-1 esetén a teljes dokumentumot)
    """
    text = ""
    try:         
        doc = fitz.open(str(pdf_path))
        
        pagecount = 0        
        for pagecount, page in enumerate(doc):
            if 0 <= pages <= pagecount:
                break
            text += page.get_text()                    
        text = text.strip()

        if DEBUG["pdf"]:  
            if text:
                page_info = f"{pages} oldal" if pages >= 0 else "minden oldal"
                msg = f"[PDF] {pdf_path.name} → szövege ({page_info}):\n{text[:500]}\n"                
                log(msg, level="DEBUG", module="pdf", to_console=True)
            else:
                msg = f"[PDF] Nincs szöveg a fájlban: {pdf_path.name}"                
                log(msg, level="DEBUG", module="pdf", to_console=True)
    except Exception as e:
        msg = f"⚠️ Hiba PDF olvasásánál: {pdf_path.name} – {e}"        
        log(msg, level="ERROR", module="pdf", to_console=True)
        return ""
    finally:
        doc.close()
    return text

def extract_pdf_info(text: str):
    """
    pdf tartalmi szövegéből beazonosítja a dokumentum típusát
    """
    lower = text.lower()
    for tipus, kulcsszavak in TÍPUS_KULCSSZAVAK.items():
        if any(kw in lower for kw in kulcsszavak):
            if DEBUG["pdf"]: 
                log(f"tipus='{tipus}'", level="DEBUG", module="pdf")
            return tipus
    if DEBUG["pdf"]: 
        log(f"tipus azonositasa sikertelen", level="DEBUG", module="pdf")
    return None

def extract_date(text: str):
    """
    szövegből dátum maszknak megfelelő stringek közül az elsőt adja vissza
    """
    match = re.search(DATE_REGEX, text)
    if DEBUG["pdf"]: 
        msg = f"datum='{match.group(1).replace('.', '-')}'" if match else "datum azonosítasa sikertelen"
        log(msg , level="DEBUG", module="pdf")
    return match.group(1).replace(".", "-") if match else None

def extract_szamlaszam(text: str):
    """
    szövegből számlasorszámnak megfeleltethető stringek közül az elsőt adja vissza
    """
    match = re.search(SZAMLA_REGEX, text, re.IGNORECASE)
    if DEBUG["pdf"]: 
        log(f"szamlaszam='{match.group(1)}'" if match else "szamlaszam azonositasa sikertelen", level="DEBUG", module="pdf")
    return match.group(1) if match else None

def gen_new_name(file_path: Path, tipus: str, datum: str, szamla: str) -> str:
    """
    Ha a PDF tartalma alapján egy számla, akkor saját fájlnevet kap
    """

    # Rövid cégnév: max 2 szó, min 3 karakter 
    ceg = file_path.stem
    #ceg = "_".join([w for w in text.strip().split() if len(w) > 2][:2])
    #ceg = clean_filename(ceg)

    if tipus == "SZAMLA":
        parts = []
        if datum != "0000-00-00":
            parts.append(datum)            
        if ceg:
            parts.append(ceg)
        if szamla and szamla.lower() not in file_path.stem.lower():
            parts.append(szamla)
        new_name = "_".join(parts) + ".pdf"        
    else:
        #new_name = f"{tipus.lower()}_{file_path.name}"
        new_name = file_path.name
    new_name = clean_filename(new_name)

    if DEBUG["pdf"]: 
        log(f"new_name='{new_name}'", level="DEBUG", module="pdf")

    return new_name

def move_pdf_to_output(pdf_path: Path, target_path: Path):
    """
    PDF áthelyezése
    """
    t_dir = target_path.parent
    t_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(pdf_path), str(target_path))
    log_rename(str(pdf_path), str(target_path))
    if DEBUG["pdf"]:
        print(f"[PDF] Áthelyezve: {target_path}")

def process_pdf(file_path: Path):
    try:
        if not is_pdf(file_path):
            return
        text = extract_pdf_text(file_path, 1)        
        tipus = extract_pdf_info(text) or "ISMERETLEN"
        datum = extract_date(text) or "0000-00-00"
        szamla = extract_szamlaszam(text)
        new_name = gen_new_name(file_path, tipus, datum, szamla)
        target_dir = out_dir / tipus
        new_path = ensure_unique_filename(target_dir / new_name)       
        move_pdf_to_output(file_path, new_path)

    except Exception as e:
        log(f"⚠️ Hiba PDF-nél: {file_path.name} – {e}", level="ERROR", module="pdf", to_console=True)        








