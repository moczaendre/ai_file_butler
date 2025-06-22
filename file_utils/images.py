from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
import os
from pathlib import Path
import shutil
import time

from file_utils.common import log
from file_utils.common import log_rename
from file_utils.common import get_file_creation_date
from file_utils.common import ensure_unique_filename
from config import cfg

out_dir = cfg["img_output"]
out_dir.mkdir(parents=True, exist_ok=True)


def get_exif_date_info(
    file_path: Path,
    as_string: bool = False,
    fallback_to_mtime: bool = True
) -> str | dict | None:
    """
    EXIF dátum olvasása képfájlból. (A fénykép készítési időpontjának kiolvasása képfájl EXIF metainformációiból telefonnal készült képeknél.)

    :param file_path: A képfájl elérési útja.
    :param as_string: Ha True, akkor "YYYY_MM_DD" formátumú stringet ad vissza. Egyébként dict.
    :param fallback_to_mtime: Ha nincs EXIF, visszatér-e fájl módosítási dátummal.
    :return: dict vagy string (vagy None, ha nem található dátum és nincs fallback)
    """
    try:
        img = Image.open(file_path)
        exif_data = img._getexif()
        if not exif_data:
            raise ValueError("Nincs EXIF adat a képen.")

        # Keressük a DateTimeOriginal mezőt először
        for tag, value in exif_data.items():
            decoded = TAGS.get(tag)
            if decoded in ["DateTimeOriginal", "DateTimeDigitized", "DateTime"]:
                dt_str = value
                date_taken = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")
                if as_string:
                    return date_taken.strftime("%Y_%m_%d")
                return {
                    "year": date_taken.year,
                    "month": date_taken.month,
                    "day": date_taken.day
                }

        raise ValueError("Nem található EXIF dátum mező.")

    except Exception as e:
        log(f"⚠️ EXIF dátum olvasási hiba: {file_path.name} – {e}", level="WARNING", module="image")

    # Fallback a fájl módosítási dátumára
    if fallback_to_mtime:
        try:
            t = file_path.stat().st_mtime
            date_taken = datetime.fromtimestamp(t)
            if as_string:
                return date_taken.strftime("%Y_%m_%d")
            return {
                "year": date_taken.year,
                "month": date_taken.month,
                "day": date_taken.day
            }
        except Exception as e:
            log(f"⚠️ Fallback dátumolvasási hiba: {file_path.name} – {e}", level="ERROR", module="image")

    return None


"""
def get_gps_info(exif_data):
    gps_info = exif_data.get("GPSInfo")
    if not gps_info:
        return None

    try:
        lat = get_decimal_from_dms(gps_info[2], gps_info[1])
        lon = get_decimal_from_dms(gps_info[4], gps_info[3])
        if lat is not None and lon is not None:
            print(f"[GPS] Helyadat: {lat:.5f}, {lon:.5f} → https://maps.google.com/?q={lat:.5f},{lon:.5f}")
            return lat, lon
    except Exception as e:
        print(f"⚠️ Helyadat olvasási hiba: {e}")
    return None
"""

def get_gps_info(image_path):
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()
        if not exif_data:
            raise ValueError("Nincs EXIF adat a képen.")            

        gps_info = exif_data.get(34853)  # GPSInfo kulcs számkódja: 34853
        if not gps_info:
            raise ValueError("Nem található EXIF helyadat mező.")

        gps_data = {}
        for key in gps_info:
            decode = GPSTAGS.get(key, key)
            gps_data[decode] = gps_info[key]

        # Koordináta konverzió
        lat = lon = None
        if 'GPSLatitude' in gps_data and 'GPSLatitudeRef' in gps_data:
            lat = get_decimal_from_dms(gps_data['GPSLatitude'], gps_data['GPSLatitudeRef'])
        if 'GPSLongitude' in gps_data and 'GPSLongitudeRef' in gps_data:
            lon = get_decimal_from_dms(gps_data['GPSLongitude'], gps_data['GPSLongitudeRef'])

        #return {"lat": lat, "lon": lon}
        return (lat, lon)

      

    except Exception as e:
        log(f"⚠️ EXIF helyadat (GPS) olvasási hiba: {image_path.name} – {e}", level="WARNING", module="image")        
        return None

def get_decimal_from_dms(dms, ref):
    """
    Koordináta átváltás: fok(degrees), perc(minutes), másodperc(seconds) → tizedesfok
    Irány figyelembe vételével: ref
    """
    try:
        d, m, s = dms
        degrees = float(d)
        minutes = float(m)
        seconds = float(s)
        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        if ref in ['S', 'W']:
            decimal *= -1
        return decimal
    except Exception as e:
        log(f"⚠️ Koordináta konverziós hiba: {e}", level="ERROR", module="image", to_console=True)
        return None


def move_img_file(file_path: Path, target_path: Path):
    """
    Kép fájl áthelyezése
    """
    target_dir = target_path.parent
    target_dir.mkdir(parents=True, exist_ok=True)    
    shutil.move(str(file_path), str(target_path))
    log_rename(str(file_path), str(target_path))
    #print(f"[IMG] Áthelyezve: {file_path.name} → {target_dir}")
    log(f"[KÉP] Áthelyezve: {target_path.relative_to(out_dir.parent)}", module="image", to_console=True)


def process_image(file_path: Path):
    try:
        # Dátum kinyerése
        datum = get_exif_date_info(file_path, as_string=True) or get_file_creation_date(file_path)
        ev = datum.split("_")[0]
        subdir = f"{datum} -"
        target_dir = out_dir / ev / subdir
        target_dir.mkdir(parents=True, exist_ok=True)
        
        gps = get_gps_info(file_path)
        if gps:
            lat, lon = gps
            try:
                lat_f = float(lat)
                lon_f = float(lon)
                subdir += f" {lat_f:.5f}_{lon_f:.5f}"
                log(f"[GPS] Helyadat: {file_path.name}; {lat_f:.5f}, {lon_f:.5f} → https://maps.google.com/?q={lat_f:.5f},{lon_f:.5f}", module="img", to_console=True)
            except (ValueError, TypeError) as e:
                log(f"⚠️ Helyadat konverziós hiba: {file_path.name} – {e}", level="ERROR", module="img", to_console=True)
            

        # Duplikátumkezelés
        new_path = ensure_unique_filename(target_dir / file_path.name)

        move_img_file(file_path, new_path)

    except Exception as e:
        log(f"⚠️ Hiba KÉP feldolgozásánál: {file_path.name} – {e}", level="ERROR", module = "img", to_console=True)






