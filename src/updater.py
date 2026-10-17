"""GitHub Releases tabanlı otomatik güncelleme motoru.

Bu modül, GitHub Releases API üzerinden en güncel sürümü denetler,
yayınlanan .exe varlıklarını tespit eder, indirir ve uygulamayı günceller.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Tuple

from src.config import (
    APP_NAME,
    APP_VERSION,
    GITHUB_RELEASES_URL,
    GITHUB_REPO_NAME,
    GITHUB_REPO_OWNER,
    TEMP_DIR,
)


def parse_version(v_str: str) -> Tuple[int, int, int]:
    """Sürüm etiketini (v1.2.3, 1.2.3, 2.0.0-beta) (major, minor, patch) demetine dönüştürür."""
    clean = v_str.strip().lstrip("vV")
    # Sayısal olmayan ekleri (örn. -beta, +build) ayıkla
    clean = re.split(r"[-+]", clean)[0]
    parts = clean.split(".")
    major = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
    minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    patch = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
    return (major, minor, patch)


def is_newer_version(current_v: str, candidate_v: str) -> bool:
    """Aday sürümün mevcut sürümden daha yeni olup olmadığını doğrular."""
    return parse_version(candidate_v) > parse_version(current_v)


@dataclass
class UpdateInfo:
    """Güncelleme bilgilerini tutan veri modeli."""

    version: str
    tag_name: str
    release_name: str
    release_notes: str
    published_at: str
    is_update_available: bool
    asset_name: Optional[str] = None
    download_url: Optional[str] = None
    asset_size: int = 0
    has_exe_asset: bool = False


class AutoUpdater:
    """GitHub Releases üzerinden otomatik güncelleme yöneticisi."""

    def __init__(
        self,
        current_version: str = APP_VERSION,
        repo_owner: str = GITHUB_REPO_OWNER,
        repo_name: str = GITHUB_REPO_NAME,
    ):
        self.current_version = current_version
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"

    def check_for_updates(self, timeout: int = 8) -> Optional[UpdateInfo]:
        """GitHub API üzerinden en güncel yayını denetler."""
        req = urllib.request.Request(
            self.api_url,
            headers={
                "User-Agent": f"{APP_NAME}-AutoUpdater/{self.current_version}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status != 200:
                    return None
                payload = json.loads(response.read().decode("utf-8"))
                return self.parse_release_payload(payload)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, Exception):
            return None

    def parse_release_payload(self, payload: dict) -> UpdateInfo:
        """GitHub Release JSON yanıtını ayrıştırıp UpdateInfo nesnesi üretir."""
        tag_name = payload.get("tag_name", "")
        # Sürüm numarasını 'v' önekini atarak al
        remote_version = tag_name.lstrip("vV")
        release_name = payload.get("name") or tag_name
        body = payload.get("body") or ""
        published_at = payload.get("published_at") or ""

        # Sürüm kıyaslaması
        newer = is_newer_version(self.current_version, remote_version)

        # .exe uzantılı varlığı (asset) ara
        exe_asset = None
        for asset in payload.get("assets", []):
            name = asset.get("name", "")
            if name.lower().endswith(".exe"):
                exe_asset = asset
                break

        has_exe = exe_asset is not None
        asset_name = exe_asset.get("name") if exe_asset else None
        download_url = exe_asset.get("browser_download_url") if exe_asset else None
        asset_size = exe_asset.get("size", 0) if exe_asset else 0

        return UpdateInfo(
            version=remote_version,
            tag_name=tag_name,
            release_name=release_name,
            release_notes=body,
            published_at=published_at,
            is_update_available=newer,
            asset_name=asset_name,
            download_url=download_url,
            asset_size=asset_size,
            has_exe_asset=has_exe,
        )

    def download_asset(
        self,
        url: str,
        target_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        chunk_size: int = 65536,
    ) -> bool:
        """Belirtilen URL'deki dosyayı akış halinde indirir."""
        target_path = Path(target_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = target_path.with_suffix(".part")

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": f"{APP_NAME}-AutoUpdater/{self.current_version}",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.headers.get("Content-Length", 0))
                downloaded = 0
                with open(temp_file, "wb") as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            try:
                                progress_callback(downloaded, total_size)
                            except Exception:
                                pass

            # İndirme başarıyla bittiyse geçici dosyayı asıl konuma taşı
            if temp_file.exists():
                if target_path.exists():
                    target_path.unlink()
                temp_file.rename(target_path)
                return True
            return False
        except Exception:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            return False

    def apply_update(self, downloaded_exe_path: Path) -> bool:
        """İndirilen .exe güncellemesini uygular."""
        downloaded_exe = Path(downloaded_exe_path).resolve()
        if not downloaded_exe.is_file():
            return False

        # Eğer uygulama PyInstaller ile dondurulmuş bir .exe ise
        is_frozen = getattr(sys, "frozen", False)
        if is_frozen:
            current_exe = Path(sys.executable).resolve()
            pid = os.getpid()

            # Windows güvenli değiştirme betiği
            updater_bat = TEMP_DIR / "update_in_place.bat"
            bat_content = f"""@echo off
timeout /t 1 /nobreak >nul
:WAIT_LOOP
tasklist /fi "PID eq {pid}" | find "{pid}" >nul
if %ERRORLEVEL% EQU 0 (
    timeout /t 1 /nobreak >nul
    goto :WAIT_LOOP
)
copy /y "{downloaded_exe}" "{current_exe}" >nul
start "" "{current_exe}"
del "%~f0"
exit
"""
            try:
                with open(updater_bat, "w", encoding="utf-8") as f:
                    f.write(bat_content)

                # Arka planda bağımsız başlat ve uygulamayı sonlandır
                subprocess.Popen(
                    ["cmd.exe", "/c", str(updater_bat)],
                    creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                    | getattr(subprocess, "DETACHED_PROCESS", 0),
                    close_fds=True,
                )
                sys.exit(0)
            except Exception:
                return False
        else:
            # Kaynak koddan çalışırken yeni .exe'yi çalıştır veya klasörü aç
            try:
                subprocess.Popen([str(downloaded_exe)], shell=True)
                return True
            except Exception:
                return False
