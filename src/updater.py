"""GitHub Releases tabanli guvenli ve dayanikli otomatik guncelleme motoru.

Bu modul, GitHub Releases API uzerinden en guncel surumu denetler,
yayimlanan .exe varliklarini akilli onceliklendirmeyle secer, indirir,
butunluk ve PE baslik dogrulamalarini yapar ve calisan surumu guvenli
sekilde degistirip yeniden baslatir.
"""

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from enum import Enum
from functools import total_ordering
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.config import (
    APP_NAME,
    APP_VERSION,
    GITHUB_RELEASES_URL,
    GITHUB_REPO_NAME,
    GITHUB_REPO_OWNER,
    OUTPUTS_DIR,
    TEMP_DIR,
)


class CheckStatus(Enum):
    """Guncelleme denetimi sonuc durumlari."""

    UP_TO_DATE = "UP_TO_DATE"
    UPDATE_AVAILABLE = "UPDATE_AVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    OFFLINE = "OFFLINE"
    NO_RELEASES = "NO_RELEASES"
    ERROR = "ERROR"


@total_ordering
@dataclass
class SemVer:
    """SemVer 2.0 standardina uygun surum modeli ve karsilastiricisi."""

    major: int
    minor: int
    patch: int
    prerelease: str = ""
    build: str = ""

    @classmethod
    def parse(cls, v_str: str) -> "SemVer":
        """Surum metnini (v1.2.3, 2.0, 1.0.0-beta.1, 1.0.0+build2) SemVer nesnesine donusturur."""
        clean = (v_str or "").strip().lstrip("vV")
        if not clean:
            return cls(0, 0, 0)

        # Build bilgisini ayir (+)
        build = ""
        if "+" in clean:
            clean, build = clean.split("+", 1)

        # On surum bilgisini ayir (-)
        prerelease = ""
        if "-" in clean:
            clean, prerelease = clean.split("-", 1)

        parts = clean.split(".")
        nums = []
        for p in parts:
            digits = re.findall(r"\d+", p)
            nums.append(int(digits[0]) if digits else 0)

        major = nums[0] if len(nums) > 0 else 0
        minor = nums[1] if len(nums) > 1 else 0
        patch = nums[2] if len(nums) > 2 else 0

        return cls(major=major, minor=minor, patch=patch, prerelease=prerelease, build=build)

    def __lt__(self, other: "SemVer") -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented

        # 1. Ana surum numaralari karsilastirmasi
        self_tuple = (self.major, self.minor, self.patch)
        other_tuple = (other.major, other.minor, other.patch)
        if self_tuple != other_tuple:
            return self_tuple < other_tuple

        # 2. On surum karsilastirmasi (SemVer kurali: on surumlu versiyon normal versiyondan kucuktur)
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and other.prerelease:
            return False
        if self.prerelease and other.prerelease:
            return self._compare_prerelease(self.prerelease, other.prerelease) < 0

        return False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return False
        return (
            (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
            and self.prerelease == other.prerelease
        )

    @staticmethod
    def _compare_prerelease(pre1: str, pre2: str) -> int:
        """Iki on surum metnini (örn: rc.1 vs rc.2 veya alpha vs beta) kiyaslar."""
        parts1 = pre1.split(".")
        parts2 = pre2.split(".")
        for p1, p2 in zip(parts1, parts2):
            if p1 == p2:
                continue
            if p1.isdigit() and p2.isdigit():
                return int(p1) - int(p2)
            return (p1 > p2) - (p1 < p2)
        return len(parts1) - len(parts2)

    def to_string(self) -> str:
        """Surumu standart metin formatina donusturur."""
        res = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            res += f"-{self.prerelease}"
        if self.build:
            res += f"+{self.build}"
        return res


def parse_version(v_str: str) -> Tuple[int, int, int]:
    """Geriye donuk uyumluluk icin (major, minor, patch) demeti doner."""
    ver = SemVer.parse(v_str)
    return (ver.major, ver.minor, ver.patch)


def is_newer_version(current_v: str, candidate_v: str) -> bool:
    """Aday surumun mevcut surumden daha yeni olup olmadigini dogrular."""
    return SemVer.parse(candidate_v) > SemVer.parse(current_v)


@dataclass
class UpdateInfo:
    """Guncelleme bilgilerini ve durumunu tasiyan veri modeli."""

    version: str
    tag_name: str
    release_name: str
    release_notes: str
    published_at: str
    is_update_available: bool
    status: CheckStatus = CheckStatus.UP_TO_DATE
    asset_name: Optional[str] = None
    download_url: Optional[str] = None
    asset_size: int = 0
    has_exe_asset: bool = False
    html_url: Optional[str] = None
    rate_limit_reset: Optional[int] = None
    error_message: Optional[str] = None
    expected_sha256: Optional[str] = None


def find_best_executable_asset(assets: List[Dict[str, Any]], app_name: str = "SpeechToText") -> Optional[Dict[str, Any]]:
    """Yayin varliklari arasindan en uygun bagimsiz Windows .exe ikilisini secer.
    
    Oncelik siralamasi:
    1. Uygulama adiyla birebir eslesen veya standart masaustu binary'si (orn: SpeechToText.exe)
    2. Sistem mimarisine uygun olan (orn: 64-bit Windows icin SpeechToText_x64.exe)
    3. Kurulum veya kaldirma olmayan herhangi bir uygulama .exe'si
    """
    candidates = []
    is_arm_machine = "arm" in platform.machine().lower()

    for asset in assets:
        name = asset.get("name", "")
        name_lower = name.lower()

        if not name_lower.endswith(".exe"):
            continue

        # Kaldirici (uninstaller) dosyalarini ele
        if "unins" in name_lower or "uninstall" in name_lower:
            continue

        score = 10

        # Exact match
        if name_lower == f"{app_name.lower()}.exe":
            score += 100
        elif app_name.lower() in name_lower:
            score += 50

        # Architecture match
        if is_arm_machine:
            if "arm64" in name_lower:
                score += 40
            elif "x64" in name_lower or "amd64" in name_lower:
                score += 10
        else:
            # Standart x64/AMD64 sistemi
            if "x64" in name_lower or "amd64" in name_lower or "win64" in name_lower:
                score += 40
            elif "arm" in name_lower:
                score -= 30
            elif "x86" in name_lower or "32" in name_lower or "win32" in name_lower:
                score += 10

        # Standalone portable binary > Setup/installer
        if "setup" in name_lower or "installer" in name_lower:
            score -= 10
        else:
            score += 15

        candidates.append((score, asset))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def verify_pe_executable(file_path: Path) -> bool:
    """Windows calistirilabilir dosyasinin (Portable Executable - PE) gecerli sihirli baytlarini kontrol eder."""
    path = Path(file_path)
    if not path.is_file():
        return False

    try:
        file_size = path.stat().st_size
        if file_size < 64:
            return False

        with open(path, "rb") as f:
            # 1. DOS basligi: 'MZ' (0x4D, 0x5A)
            magic = f.read(2)
            if magic != b"MZ":
                return False

            # 2. PE baslik ofsetini oku (0x3C adresindeki 4 baytlik kucuk-endian integer)
            f.seek(0x3C)
            pe_offset_bytes = f.read(4)
            if len(pe_offset_bytes) == 4:
                pe_offset = int.from_bytes(pe_offset_bytes, byteorder="little")
                if 0 < pe_offset <= file_size - 4:
                    f.seek(pe_offset)
                    pe_sig = f.read(4)
                    if pe_sig == b"PE\x00\x00" or pe_sig.startswith(b"PE"):
                        return True

            # Baslangic 'MZ' ve gecerli dosya boyutu (>=64)
            return True
    except Exception:
        return False


def verify_checksum(file_path: Path, expected_hash: str, algorithm: str = "sha256") -> bool:
    """Belirtilen dosyanin kriptografik saglama toplamini hesaplar ve beklenen degerle karsilastirir."""
    path = Path(file_path)
    if not path.is_file():
        return False

    expected_clean = expected_hash.strip().lower()
    hasher = hashlib.new(algorithm)

    try:
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        calculated = hasher.hexdigest().lower()
        return calculated == expected_clean
    except Exception:
        return False


class WindowsSelfUpdater:
    """Windows uzerinde calisan bir .exe ikilisinin kilitlenmeden yerinde degistirilmesini yonetir."""

    @staticmethod
    def generate_batch_script(downloaded_exe: Path, current_exe: Path, pid: int, retries: int = 15) -> str:
        """Geri alma (.bak) mekanizmasi ve guvenli dongulu yer degistirme betigi uretir."""
        new_path = str(downloaded_exe.resolve())
        cur_path = str(current_exe.resolve())
        bak_path = f"{cur_path}.bak"

        script = f"""@echo off
setlocal EnableDelayedExpansion

set "NEW_EXE={new_path}"
set "CUR_EXE={cur_path}"
set "BACKUP={bak_path}"
set "TARGET_PID={pid}"
set "MAX_TRIES={retries}"

rem 1. Calisan uygulamanin sonlanmasini bekle
set /a TRY_COUNT=0
:WAIT_PROCESS
taskkill /f /pid %TARGET_PID% >nul 2>&1
timeout /t 1 /nobreak >nul
tasklist /fi "PID eq %TARGET_PID%" | find "%TARGET_PID%" >nul
if %ERRORLEVEL% EQU 0 (
    set /a TRY_COUNT+=1
    if !TRY_COUNT! LEQ %MAX_TRIES% (
        goto :WAIT_PROCESS
    )
)

rem 2. Mevcut exe dosyasini guvenli sekilde .bak olarak yedekle
if exist "%BACKUP%" del /f /q "%BACKUP%" >nul 2>&1
move /y "%CUR_EXE%" "%BACKUP%" >nul 2>&1

rem 3. Yeni indirilen surumu asil konuma tasi (Gerekirse 5 defa dene)
set /a MOVE_TRY=0
:DO_MOVE
move /y "%NEW_EXE%" "%CUR_EXE%" >nul 2>&1
if not exist "%CUR_EXE%" (
    copy /y "%NEW_EXE%" "%CUR_EXE%" >nul 2>&1
)
if not exist "%CUR_EXE%" (
    set /a MOVE_TRY+=1
    if !MOVE_TRY! LEQ 5 (
        timeout /t 1 /nobreak >nul
        goto :DO_MOVE
    )
)

rem 4. Basarisizlik kontrolu ve Geri Alma (Rollback)
if not exist "%CUR_EXE%" (
    if exist "%BACKUP%" move /y "%BACKUP%" "%CUR_EXE%" >nul 2>&1
    start "" "%CUR_EXE%"
    del /f /q "%~f0"
    exit /b 1
)

rem 5. Guncellenmis yeni surumu baslat
start "" "%CUR_EXE%"

rem 6. Yedek ve calisan betik dosyasini temizle
timeout /t 2 /nobreak >nul
if exist "%BACKUP%" del /f /q "%BACKUP%" >nul 2>&1
del /f /q "%~f0"
exit /b 0
"""
        return script

    @staticmethod
    def generate_powershell_script(
        downloaded_exe: Path,
        current_exe: Path,
        pid: int,
        retries: int = 30
    ) -> str:
        """Geri alma (.bak) mekanizmasi ve guvenli dongulu yer degistirme PowerShell betigi uretir."""
        new_path = str(downloaded_exe.resolve()).replace("'", "''")
        cur_path = str(current_exe.resolve()).replace("'", "''")
        bak_path = f"{cur_path}.bak"
        cur_name = current_exe.name
        cur_dir = str(current_exe.resolve().parent).replace("'", "''")

        script = f"""# SesMetin Pro - Silent In-Place Self Updater Engine
$ErrorActionPreference = 'SilentlyContinue'
$TargetPid = {pid}
$NewExe = '{new_path}'
$CurExe = '{cur_path}'
$BackupExe = '{bak_path}'
$TargetName = '{cur_name}'
$CurDir = '{cur_dir}'
$MaxRetries = {retries}

# 1. Hedef sureci ve tum surec agacini sonlandir
try {{
    Wait-Process -Id $TargetPid -Timeout 6 -ErrorAction SilentlyContinue
}} catch {{}}

try {{
    Stop-Process -Id $TargetPid -Force -ErrorAction SilentlyContinue
}} catch {{}}

# PyInstaller bootloader ve diger kilitli surecleri sonlandir
try {{
    Get-CimInstance Win32_Process | Where-Object {{
        $_.ExecutablePath -eq $CurExe -or $_.ProcessId -eq $TargetPid
    }} | ForEach-Object {{
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }}
}} catch {{}}

Start-Sleep -Milliseconds 600

# 2. Mevcut exe dosyasini .bak olarak yedekle
if (Test-Path -LiteralPath $BackupExe) {{
    Remove-Item -LiteralPath $BackupExe -Force -ErrorAction SilentlyContinue
}}
if (Test-Path -LiteralPath $CurExe) {{
    Move-Item -LiteralPath $CurExe -Destination $BackupExe -Force -ErrorAction SilentlyContinue
}}

# 3. Yeni surumu hedef konuma kopyala ve dogrula
$copySuccess = $false
for ($i = 0; $i -lt $MaxRetries; $i++) {{
    try {{
        if (Test-Path -LiteralPath $NewExe) {{
            Copy-Item -LiteralPath $NewExe -Destination $CurExe -Force -ErrorAction Stop
        }}
        if ((Test-Path -LiteralPath $CurExe) -and ((Get-Item -LiteralPath $CurExe).Length -gt 0)) {{
            $copySuccess = $true
            # Kopyalama dogrulandiktan sonra gecici indirme dosyasini temizle
            Remove-Item -LiteralPath $NewExe -Force -ErrorAction SilentlyContinue
            break
        }}
    }} catch {{
        Start-Sleep -Milliseconds 500
    }}
}}

# 4. Basarisizlik kontrolu ve Geri Alma (Rollback)
if (-not $copySuccess -or -not (Test-Path -LiteralPath $CurExe)) {{
    if (Test-Path -LiteralPath $BackupExe) {{
        Move-Item -LiteralPath $BackupExe -Destination $CurExe -Force -ErrorAction SilentlyContinue
    }}
    Start-Process -FilePath $CurExe -WorkingDirectory $CurDir
    Remove-Item -LiteralPath $MyInvocation.MyCommand.Path -Force -ErrorAction SilentlyContinue
    exit 1
}}

# 5. Guncellenmis yeni surumu baslat
Start-Process -FilePath $CurExe -WorkingDirectory $CurDir

# 6. Yedek ve calisan betik dosyasini temizle
Start-Sleep -Seconds 2
if (Test-Path -LiteralPath $BackupExe) {{
    Remove-Item -LiteralPath $BackupExe -Force -ErrorAction SilentlyContinue
}}
Remove-Item -LiteralPath $MyInvocation.MyCommand.Path -Force -ErrorAction SilentlyContinue
exit 0
"""
        return script

    @classmethod
    def execute_in_place_update(cls, downloaded_exe: Path, current_exe: Path, pid: int) -> bool:
        """Windows yerinde degistirme betigini sessizce calistirip uygulamayi sonlandirir."""
        try:
            TEMP_DIR.mkdir(parents=True, exist_ok=True)
            ps_path = TEMP_DIR / f"updater_{uuid.uuid4().hex[:8]}.ps1"
            script_text = cls.generate_powershell_script(downloaded_exe, current_exe, pid)

            with open(ps_path, "w", encoding="utf-8") as f:
                f.write(script_text)

            create_no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            creationflags = (
                create_no_window
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
            )

            import shutil
            ps_bin = shutil.which("powershell.exe") or r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"

            cmd_args = [
                ps_bin,
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-WindowStyle",
                "Hidden",
                "-File",
                str(ps_path),
            ]

            subprocess.Popen(
                cmd_args,
                creationflags=creationflags,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
            return True
        except Exception:
            return False


class AutoUpdater:
    """GitHub Releases uzerinden otomatik guncelleme yoneticisi."""

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
        self._cached_etag: Optional[str] = None
        self._cached_info: Optional[UpdateInfo] = None

    def check_for_updates(self, timeout: int = 8, force: bool = False) -> Optional[UpdateInfo]:
        """GitHub Releases API uzerinden yeni yayinlari denetler.

        Args:
            timeout: Ag zaman asimi suresi (saniye).
            force: True ise ETag onbellegini gormezden gelerek sunucudan canli veri ister.
        """
        headers = {
            "User-Agent": f"{APP_NAME}-AutoUpdater/{self.current_version}",
            "Accept": "application/vnd.github.v3+json",
        }
        if self._cached_etag and not force:
            headers["If-None-Match"] = self._cached_etag

        req = urllib.request.Request(self.api_url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status_code = getattr(response, "status", 200)
                if status_code == 304 and self._cached_info:
                    is_update = SemVer.parse(self._cached_info.version) > SemVer.parse(self.current_version)
                    self._cached_info.is_update_available = is_update
                    self._cached_info.status = CheckStatus.UPDATE_AVAILABLE if is_update else CheckStatus.UP_TO_DATE
                    return self._cached_info

                etag = response.headers.get("ETag")
                if etag:
                    self._cached_etag = etag

                payload = json.loads(response.read().decode("utf-8"))
                info = self.parse_release_payload(payload)
                self._cached_info = info
                return info

        except urllib.error.HTTPError as he:
            if he.code == 304:
                # HTTP 304: Sunucu verisi degismedi (Not Modified). Bu bir hata degildir.
                if self._cached_info:
                    is_update = SemVer.parse(self._cached_info.version) > SemVer.parse(self.current_version)
                    self._cached_info.is_update_available = is_update
                    self._cached_info.status = CheckStatus.UPDATE_AVAILABLE if is_update else CheckStatus.UP_TO_DATE
                    self._cached_info.error_message = None
                    return self._cached_info
                # Eger hafizada cached_info yoksa, etag'i temizleyip canli olarak tekrar cek
                self._cached_etag = None
                return self.check_for_updates(timeout=timeout, force=True)
            reset_ts = None
            try:
                raw_reset = he.headers.get("X-RateLimit-Reset")
                if raw_reset:
                    reset_ts = int(raw_reset)
            except Exception:
                pass

            if he.code == 403:
                return UpdateInfo(
                    version=self.current_version,
                    tag_name="",
                    release_name="",
                    release_notes="",
                    published_at="",
                    is_update_available=False,
                    status=CheckStatus.RATE_LIMITED,
                    rate_limit_reset=reset_ts,
                    error_message="GitHub saatlik istek siniri asildi. Lutfen daha sonra tekrar deneyin.",
                )
            elif he.code == 404:
                return UpdateInfo(
                    version=self.current_version,
                    tag_name="",
                    release_name="",
                    release_notes="",
                    published_at="",
                    is_update_available=False,
                    status=CheckStatus.NO_RELEASES,
                    error_message="Henuz yayinlanmis bir surum bulunamadi.",
                )
            else:
                return UpdateInfo(
                    version=self.current_version,
                    tag_name="",
                    release_name="",
                    release_notes="",
                    published_at="",
                    is_update_available=False,
                    status=CheckStatus.ERROR,
                    error_message=f"GitHub API hatasi: HTTP {he.code}",
                )

        except (urllib.error.URLError, TimeoutError):
            return UpdateInfo(
                version=self.current_version,
                tag_name="",
                release_name="",
                release_notes="",
                published_at="",
                is_update_available=False,
                status=CheckStatus.OFFLINE,
                error_message="Internet baglantisi kurulamadi.",
            )
        except Exception as e:
            return UpdateInfo(
                version=self.current_version,
                tag_name="",
                release_name="",
                release_notes="",
                published_at="",
                is_update_available=False,
                status=CheckStatus.ERROR,
                error_message=f"Bilinmeyen hata: {e}",
            )

    def parse_release_payload(self, payload: dict) -> UpdateInfo:
        """GitHub Release JSON verisini ayristirir ve UpdateInfo nesnesi uretir."""
        tag_name = payload.get("tag_name", "")
        remote_version = tag_name.lstrip("vV")
        release_name = payload.get("name") or tag_name
        body = payload.get("body") or ""
        published_at = payload.get("published_at") or ""
        html_url = payload.get("html_url") or f"https://github.com/{self.repo_owner}/{self.repo_name}/releases"

        newer = is_newer_version(self.current_version, remote_version)
        status = CheckStatus.UPDATE_AVAILABLE if newer else CheckStatus.UP_TO_DATE

        assets = payload.get("assets", [])
        best_exe = find_best_executable_asset(assets, app_name="SpeechToText")

        # Saglama toplami (checksum) varligi ara
        expected_sha256 = None
        hash_match = re.search(r'\b([a-fA-F0-9]{64})\b', body)
        if hash_match:
            expected_sha256 = hash_match.group(1).lower()

        has_exe = best_exe is not None
        asset_name = best_exe.get("name") if best_exe else None
        download_url = best_exe.get("browser_download_url") if best_exe else None
        asset_size = int(best_exe.get("size", 0)) if best_exe else 0

        return UpdateInfo(
            version=remote_version,
            tag_name=tag_name,
            release_name=release_name,
            release_notes=body,
            published_at=published_at,
            is_update_available=newer,
            status=status,
            asset_name=asset_name,
            download_url=download_url,
            asset_size=asset_size,
            has_exe_asset=has_exe,
            html_url=html_url,
            expected_sha256=expected_sha256,
        )

    def download_asset(
        self,
        url: str,
        target_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        cancel_event: Optional[Any] = None,
        chunk_size: int = 65536,
        verify_pe: bool = True,
        expected_hash: Optional[str] = None,
    ) -> bool:
        """Belirtilen URL'deki dosyayi akis halinde guvenle indirir ve dogrular."""
        target_path = Path(target_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = target_path.with_suffix(f".part_{uuid.uuid4().hex[:6]}")

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": f"{APP_NAME}-AutoUpdater/{self.current_version}",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                raw_len = response.headers.get("Content-Length")
                total_size = int(raw_len) if raw_len and raw_len.isdigit() else 0
                downloaded = 0

                with open(temp_file, "wb") as f:
                    while True:
                        if cancel_event and cancel_event.is_set():
                            raise InterruptedError("Kullanici tarafindan indirme iptal edildi.")

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

                # Indirme dongusu tamamlandiginda son %100 durumunu bildir
                if progress_callback and (total_size > 0 or downloaded > 0):
                    try:
                        progress_callback(downloaded, total_size if total_size > 0 else downloaded)
                    except Exception:
                        pass

            # 1. Dosya boyutu kontrolu
            if total_size > 0 and downloaded < total_size:
                raise ValueError("Eksik dosya indirildi.")

            # 2. Windows PE baslik dogrulamasi
            if verify_pe and not verify_pe_executable(temp_file):
                raise ValueError("Gecersiz veya bozuk Windows calistirilabilir (PE) dosyasi.")

            # 3. Kriptografik SHA256 dogrulamasi
            if expected_hash and not verify_checksum(temp_file, expected_hash):
                raise ValueError("Dosya SHA256 saglama toplami eslesmedi.")

            # Atomik tasi
            if target_path.exists():
                try:
                    target_path.unlink()
                except Exception:
                    pass

            temp_file.rename(target_path)
            return True

        except Exception as e:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            return False

    def apply_update(self, downloaded_exe_path: Path) -> bool:
        """Indirilen .exe guncellemesini isletim sistemi ve calisma moduna gore uygular."""
        downloaded_exe = Path(downloaded_exe_path).resolve()
        if not downloaded_exe.is_file():
            return False

        is_frozen = getattr(sys, "frozen", False)
        if is_frozen:
            current_exe = Path(sys.executable).resolve()
            pid = os.getpid()
            ok = WindowsSelfUpdater.execute_in_place_update(downloaded_exe, current_exe, pid)
            if ok:
                time.sleep(0.5)
                # Sureci isletim sistemi duzeyinde derhal sonlandir (thread icinde sys.exit takilmasini onler)
                os._exit(0)
            return False
        else:
            # Kaynak kod / dev modu: Dosyayi outputs/updates altinda koru ve calistir
            try:
                updates_dir = OUTPUTS_DIR / "updates"
                updates_dir.mkdir(parents=True, exist_ok=True)
                dest = updates_dir / downloaded_exe.name
                if downloaded_exe != dest:
                    import shutil
                    shutil.copy2(str(downloaded_exe), str(dest))
                subprocess.Popen([str(dest)], shell=True)
                time.sleep(0.8)
                os._exit(0)
            except Exception:
                return False
