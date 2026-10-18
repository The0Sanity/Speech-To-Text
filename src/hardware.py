"""Sistem donanımı, işlemci mimarisi ve CUDA hızlandırma tanılayıcısı."""

import os
import platform
import sys
from typing import Any, Dict, List, Optional, Tuple


def format_memory_size(bytes_size: float) -> str:
    """Bayt cinsinden verilen boyutu okunabilir birime (B, KB, MB, GB) dönüştürür."""
    if bytes_size < 1024:
        return f"{bytes_size:.1f} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.1f} GB"


def has_avx2_support() -> bool:
    """İşlemcinin AVX2 vektör komut kümesi desteğini tespit eder.
    
    Windows ve diğer işletim sistemlerinde güvenli sorgulama yapar.
    """
    try:
        # Windows işletim sisteminde IsProcessorFeaturePresent kontrolü
        if sys.platform == "win32":
            import ctypes
            # PF_AVX2_INSTRUCTIONS_AVAILABLE = 40
            try:
                kernel32 = ctypes.windll.kernel32
                if hasattr(kernel32, "IsProcessorFeaturePresent"):
                    return bool(kernel32.IsProcessorFeaturePresent(40))
            except Exception:
                pass

        # Linux / Unix /proc/cpuinfo üzerinden kontrol
        if os.path.exists("/proc/cpuinfo"):
            try:
                with open("/proc/cpuinfo", "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    return "avx2" in content.lower()
            except Exception:
                pass
    except Exception:
        pass

    # Tespit edilemezse modern x86_64 işlemciler için varsayılan True
    return platform.machine().lower() in ("amd64", "x86_64")


def get_memory_info() -> Tuple[float, float]:
    """Sistem toplam ve boş bellek miktarını GB cinsinden döndürür."""
    total_gb = 8.0
    avail_gb = 4.0

    try:
        if sys.platform == "win32":
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                total_gb = round(stat.ullTotalPhys / (1024 ** 3), 2)
                avail_gb = round(stat.ullAvailPhys / (1024 ** 3), 2)
                return total_gb, avail_gb
    except Exception:
        pass

    try:
        import psutil
        mem = psutil.virtual_memory()
        total_gb = round(mem.total / (1024 ** 3), 2)
        avail_gb = round(mem.available / (1024 ** 3), 2)
    except Exception:
        pass

    return total_gb, avail_gb


def detect_cuda_capabilities() -> Tuple[bool, List[Dict[str, Any]]]:
    """NVIDIA CUDA grafik işlemci ve VRAM durumunu tespit eder."""
    cuda_available = False
    devices: List[Dict[str, Any]] = []

    # 1. CTranslate2 üzerinden kontrol
    try:
        import ctranslate2
        device_count = ctranslate2.get_cuda_device_count()
        if device_count > 0:
            cuda_available = True
    except Exception:
        pass

    # 2. PyTorch yüklüyse detaylı aygıt bilgileri
    try:
        import torch
        if torch.cuda.is_available():
            cuda_available = True
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                devices.append({
                    "id": i,
                    "name": props.name,
                    "total_vram_gb": round(props.total_memory / (1024 ** 3), 2),
                    "compute_capability": f"{props.major}.{props.minor}",
                })
    except Exception:
        pass

    if cuda_available and not devices:
        devices.append({
            "id": 0,
            "name": "NVIDIA GPU (CUDA Uyumlu)",
            "total_vram_gb": 0.0,
            "compute_capability": "Bilinmiyor",
        })

    return cuda_available, devices


def get_recommended_device_and_compute(cuda_available: bool = False) -> Tuple[str, str]:
    """Donanıma en uygun çalışma cihazı (device) ve hesaplama hassasiyetini (compute_type) belirler."""
    if cuda_available:
        return "cuda", "float16"
    return "cpu", "int8"


def get_system_hardware_info() -> Dict[str, Any]:
    """Tüm donanım ve hızlandırma bilgilerini kapsayan özet sözlük oluşturur."""
    cpu_name = platform.processor() or platform.machine() or "Bilinmeyen CPU"
    cpu_count = os.cpu_count() or 4
    avx2 = has_avx2_support()
    total_ram, avail_ram = get_memory_info()
    cuda_avail, cuda_devs = detect_cuda_capabilities()
    rec_dev, rec_compute = get_recommended_device_and_compute(cuda_avail)

    return {
        "cpu_name": cpu_name,
        "cpu_count": cpu_count,
        "avx2_support": avx2,
        "ram_total_gb": total_ram,
        "ram_available_gb": avail_ram,
        "cuda_available": cuda_avail,
        "cuda_devices": cuda_devs,
        "recommended_device": rec_dev,
        "recommended_compute_type": rec_compute,
    }


def resolve_execution_device_and_compute(
    mode: str = "auto",
    cuda_available: Optional[bool] = None,
) -> Tuple[str, str]:
    """Kullanıcı tercihi ve sistem imkanlarına göre nihai cihaz ve hassasiyeti belirler."""
    if cuda_available is None:
        cuda_available, _ = detect_cuda_capabilities()

    clean_mode = (mode or "auto").strip().lower()

    if clean_mode == "cuda":
        if cuda_available:
            return "cuda", "float16"
        # CUDA mevcut değilse güvenli biçimde CPU INT8'e düş
        return "cpu", "int8"

    if clean_mode == "cpu":
        return "cpu", "int8"

    # auto modu
    if cuda_available:
        return "cuda", "float16"
    return "cpu", "int8"


def evaluate_model_compatibility(model_id: str, mode: str = "auto") -> Dict[str, Any]:
    """Seçili modelin sistem RAM ve VRAM gereksinimlerini karşılaştırıp uyumluluk raporu üretir."""
    from src.models.catalog import get_model_spec

    spec = get_model_spec(model_id)
    req_ram_gb = spec.ram_req_gb if spec else 2.0
    req_size_mb = spec.size_mb if spec else 500

    total_ram, avail_ram = get_memory_info()
    cuda_avail, cuda_devs = detect_cuda_capabilities()
    target_device, target_compute = resolve_execution_device_and_compute(mode, cuda_available=cuda_avail)

    vram_avail_gb = 0.0
    if cuda_devs:
        vram_avail_gb = float(cuda_devs[0].get("total_vram_gb", 0.0))

    # Uyumluluk kararı
    status = "compatible"
    status_label = "Tam Uyumlu"
    warning_msg = ""
    can_run = True

    if target_device == "cuda":
        # GPU VRAM değerlendirmesi
        # Whisper modelleri int8/fp16 için model boyutunun yaklaşık 1.2 katı VRAM tüketir
        req_vram_gb = round((req_size_mb * 1.25) / 1024, 2)
        if vram_avail_gb > 0 and vram_avail_gb < req_vram_gb:
            status = "tight"
            status_label = "Sistem Sınırında (Yetersiz VRAM)"
            warning_msg = f"Seçilen model yaklaşık {req_vram_gb} GB VRAM gerektirir. Cihazınızda {vram_avail_gb} GB VRAM mevcut."
        else:
            status = "compatible"
            status_label = "Tam Uyumlu (CUDA Hızlandırma)"
    else:
        # CPU RAM değerlendirmesi
        if avail_ram < (req_ram_gb * 0.6):
            status = "tight"
            status_label = "Sistem Sınırında (Düşük Boş RAM)"
            warning_msg = f"Model {req_ram_gb} GB RAM gerektirir. Sistemde yalnızca {avail_ram} GB boş RAM var; disk takası yaşanabilir."
        elif total_ram < req_ram_gb:
            status = "tight"
            status_label = "Sistem Sınırında (Yüksek RAM İhtiyacı)"
            warning_msg = f"Model {req_ram_gb} GB RAM gerektirir. Cihazın toplam belleği {total_ram} GB."
        else:
            status = "compatible"
            status_label = "Tam Uyumlu (AVX2 INT8)"

    return {
        "model_id": model_id,
        "mode": mode,
        "target_device": target_device,
        "target_compute": target_compute,
        "status": status,
        "status_label": status_label,
        "warning_msg": warning_msg,
        "can_run": can_run,
        "required_ram_gb": req_ram_gb,
        "available_ram_gb": avail_ram,
        "total_ram_gb": total_ram,
        "vram_available_gb": vram_avail_gb,
    }

