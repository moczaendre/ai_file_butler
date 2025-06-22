from mutagen import File as AudioFile
import os
from pathlib import Path
import shutil
import asyncio
from shazamio import Shazam
import requests
import re

from config import DEBUG
from config import cfg
from file_utils.common import log, log_rename, clean_filename, ensure_unique_filename, normalize_text

out_dir = cfg["mp3_output"]
out_dir.mkdir(parents=True, exist_ok=True)


def identify_song(filepath):
    api_token = "SAJÁT_API_KULCS_IDE"
    with open(filepath, 'rb') as f:
        response = requests.post(
            'https://api.audd.io/',
            data={'api_token': api_token, 'return': 'apple_music,spotify'},
            files={'file': f}
        )
    result = response.json()
    return result.get('result')

async def identify_mp3(file_path: str) -> dict:
    """
    MP3 fájl azonosítása Shazammal.
    """
    shazam = Shazam()
    try:
        result = await shazam.recognize(file_path)
        #print(f"[DEBUG] Shazam nyers válasz: {result}")

        track = result.get('track', {})
        if track:
            album = ''
            sections = track.get('sections', [])
            if sections:
                metadata = sections[0].get('metadata', [])
                for item in metadata:
                    if item.get('title') == 'Album':
                        album = item.get('text', '')
                        break                

            return {
                'title': track.get('title', ''),
                'artist': track.get('subtitle', ''),
                'album': album
            }

        # fallback: mutagen
        audio = AudioFile(file_path)
        if audio and audio.tags:            
            artist = audio.tags.get('TPE1') or audio.tags.get('artist')
            albumartist = audio.tags.get('TPE2') or audio.tags.get('albumartist')
            title = audio.tags.get('TIT2') or audio.tags.get('title')
            log(f"MP3 azonosítva. title='{title}', artist='{artist}', albumartist='{albumartist}'", module="mp3", to_console=True)

            artist_text = str(artist) if artist else ''
            if normalize_text(artist_text.strip())=="ismeretlen eloado": artist_text= ''
            albumartist_text = str(albumartist) if albumartist else ''
            title_text = str(title).strip() if title else ''
            if not title_text or is_placeholder_title(title_text):
                title_text = f"~{os.path.splitext(os.path.basename(file_path))[0]}~"                
            final_artist = artist_text or albumartist_text or "Ismeretlen előadó"

            return {
                'title': title_text,
                'artist': final_artist,
                'album': ''
            }
        log(f"MP3 azonosítás eredménytelen: {file_path.name}", module="mp3", to_console=True)
        return {'title': '', 'artist': '', 'album': ''}

    except Exception as e:
        log(f"[ERROR] Azonosítás sikertelen: {e}", level="ERROR", module="mp3", to_console=True)
        return {'title': '', 'artist': '', 'album': ''}

def is_placeholder_title(title: str) -> bool:
    """
    True, ha nem valódi zenecímnek tűnik a cím (pl. "Szám 2", "Track01", "Audio_01"), azaz placeholder
    """
    norm_title = title.strip().lower()
    return bool(re.fullmatch(r"(szám|track|audio)[ _-]*\d+", norm_title))

def move_mp3_to_output(mp3_path: Path, artist: str, song_title: str):
    """
    MP3 áthelyezése
    """
    if artist == "Ismeretlen előadó":
        new_name =  mp3_path.name
        artist_dir = out_dir / "_unknown"    
    else:
        new_name = f"{artist} - {song_title}.mp3"
        artist_dir = out_dir / artist
    artist_dir.mkdir(parents=True, exist_ok=True)    
    target_path = artist_dir / new_name
    target_path = ensure_unique_filename(target_path)
    shutil.move(str(mp3_path), str(target_path))
    log_rename(str(mp3_path), str(target_path))
    if DEBUG["mp3"]:
        print(f"[MP3] Áthelyezve: {target_path}")


def process_mp3(file_path: Path):
    try:
        metadata = asyncio.run(identify_mp3(str(file_path)))
        if DEBUG["mp3"]:
            print(f"[DEBUG] Metadata: {metadata}")

        artist = clean_filename(metadata.get("artist", "ISMERETLEN"))
        title = clean_filename(metadata.get("title", "ISMERETLEN"))

        if artist and title:
            move_mp3_to_output(file_path, artist, title)
        else:
            log(f"⚠️ Hiányzik az előadó vagy a cím: {file_path.name}", module="mp3", to_console=True)

    except Exception as e:
        log(f"⚠️ Hiba MP3-nál: {file_path.name} – {e}", level="ERROR", module="mp3", to_console=True)
