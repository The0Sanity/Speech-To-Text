"""CustomTkinter tabanlı Minimalist Türkçe Ses Tanıma & Konuşmacı Ayrıştırma Arayüzü."""

import os
import subprocess
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Dict, List, Optional

import customtkinter as ctk

from src.aligner import (
    align_transcription_and_diarization,
    compute_transcript_statistics,
    filter_transcript,
    find_and_replace_in_transcript,
    get_unique_speakers,
    rename_speaker_in_transcript,
)
from src.audio_enhancer import enhance_audio
from src.audio_processor import (
    cleanup_temp_file,
    extract_audio_to_wav,
    find_ffmpeg,
    get_media_info,
)
from src.config import (
    BASE_DIR,
    OUTPUTS_DIR,
    TEMP_DIR,
    load_settings,
    save_settings,
)
from src.diarizer import SpeakerDiarizer
from src.exporter import (
    export_to_csv,
    export_to_json,
    export_to_markdown,
    export_to_srt,
    export_to_txt,
    export_to_vtt,
)
from src.transcriber import WhisperTranscriber
from src.ui.components import (
    AudioPlayerBar,
    MetricBadge,
    ModernCard,
    ProcessStepper,
    RenameSpeakerDialog,
    SpeakerManagerModal,
    ToastNotification,
)
from src.ui.style import FONT_FAMILY, get_speaker_color, get_theme_palette
from src.youtube_downloader import (
    clean_error_message,
    download_youtube_audio,
    get_youtube_video_info,
    is_valid_youtube_url,
)


class SpeechToTextApp(ctk.CTk):
    """Sade ve Minimalist Ses Tanıma ve Konuşmacı Ayrıştırma Masaüstü Uygulaması."""

    APP_VERSION = "2.0"

    def __init__(self):
        super().__init__()

        # Ayarları yükle
        self.settings = load_settings()
        self.current_theme = self.settings.get("theme", "dark")

        # Görünüm Teması
        ctk.set_appearance_mode(self.current_theme.capitalize())
        ctk.set_default_color_theme("blue")

        # Pencere Başlığı ve Boyutları (Emojisiz, sade, ekran ortalama ve duyarlı ölçek)
        self.title(f"SesMetin Pro - Turkce STT ve Konusmaci Ayrastirma (v{self.APP_VERSION})")
        self._min_width = 960
        self._min_height = 640
        self.minsize(self._min_width, self._min_height)

        # Ekran çözünürlüğüne göre duyarlı dinamik boyutlandırma ve ekran ortalama
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        win_w = max(self._min_width, min(1160, int(screen_w * 0.88)))
        win_h = max(self._min_height, min(840, int(screen_h * 0.88)))
        pos_x = max(0, (screen_w - win_w) // 2)
        pos_y = max(0, (screen_h - win_h) // 2)
        self.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")

        # Başlangıçta pürüzsüz açılış için pencere opaklığını 0.0 yap
        try:
            self.attributes("-alpha", 0.0)
        except Exception:
            pass

        # Durum Değişkenleri
        self.selected_file_path: Optional[str] = None
        self.active_wav_path: Optional[str] = None
        self.media_info: Optional[Dict[str, Any]] = None
        self.youtube_info: Optional[Dict[str, Any]] = None
        self.transcribed_data: List[Dict[str, Any]] = []
        self.is_processing = False
        self.cancel_requested = False

        self._build_ui()
        self._check_ffmpeg()

        # Açılış fade-in animasyonunu başlat
        self.after(10, self._animate_window_entrance)

    def _animate_window_entrance(self, current_alpha: float = 0.0):
        """Uygulama açılışında pürüzsüz kademeli opaklık (fade-in) animasyonu uygular."""
        try:
            if not self.winfo_exists():
                return
            next_alpha = min(1.0, round(current_alpha + 0.1, 2))
            self.attributes("-alpha", next_alpha)
            if next_alpha < 1.0 and self.winfo_exists():
                self.after(16, lambda: self._animate_window_entrance(next_alpha))
        except Exception:
            try:
                if self.winfo_exists():
                    self.attributes("-alpha", 1.0)
            except Exception:
                pass

    def _check_ffmpeg(self):
        """Sistemde FFmpeg varlığını kontrol eder."""
        ffmpeg_bin = find_ffmpeg()
        if not ffmpeg_bin:
            messagebox.showwarning(
                "FFmpeg Bulunamadi",
                "Sistemde FFmpeg araci tespit edilemedi! Ses donusturme adimlari icin FFmpeg gereklidir.\n"
                "Lutfen FFmpeg'i kurunuz.",
            )

    def _build_ui(self):
        """Sade ve minimalist kullanıcı arayüzünü oluşturur."""
        palette = get_theme_palette(self.current_theme)

        # Ana Arka Plan
        self.main_container = ctk.CTkFrame(self, fg_color=palette["bg_app"], corner_radius=0)
        self.main_container.pack(fill="both", expand=True)

        # 1. Üst Başlık & Araç Çubuğu
        self._build_header(self.main_container, palette)

        # 2. Gövde Bölümü (İki Sütunlu)
        self.body_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.body_container.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        # Sol Panel (Giriş ve Yapılandırma - Ekran boyutuna duyarlı kaydırılabilir sütun)
        self.left_panel = ctk.CTkScrollableFrame(
            self.body_container,
            width=350,
            fg_color="transparent",
        )
        self.left_panel.pack(side="left", fill="y", padx=(0, 12))

        self._build_media_input_card(self.left_panel, palette)
        self._build_settings_card(self.left_panel, palette)
        self._build_action_card(self.left_panel, palette)

        # Sağ Panel (Transkript, İstatistikler ve Düzenleme)
        self.right_panel = ctk.CTkFrame(self.body_container, fg_color="transparent")
        self.right_panel.pack(side="right", fill="both", expand=True)

        self._build_transcript_view(self.right_panel, palette)

    # ------------------ Üst Başlık (Header) ------------------
    def _build_header(self, parent, palette: Dict[str, str]):
        header = ctk.CTkFrame(
            parent,
            height=58,
            fg_color=palette["bg_card"],
            corner_radius=0,
            border_width=1,
            border_color=palette["border_card"],
        )
        header.pack(fill="x", pady=(0, 12))

        # Sol Logo & Başlık
        brand_frame = ctk.CTkFrame(header, fg_color="transparent")
        brand_frame.pack(side="left", padx=16, pady=8)

        title_row = ctk.CTkFrame(brand_frame, fg_color="transparent")
        title_row.pack(anchor="w")

        lbl_logo = ctk.CTkLabel(
            title_row,
            text="SesMetin Pro",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=palette["text_main"],
        )
        lbl_logo.pack(side="left")

        version_pill = ctk.CTkLabel(
            title_row,
            text=f" v{self.APP_VERSION} ",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            fg_color=palette["bg_card_secondary"],
            text_color=palette["text_muted"],
            corner_radius=4,
            height=20,
        )
        version_pill.pack(side="left", padx=(8, 0))

        lbl_sub = ctk.CTkLabel(
            brand_frame,
            text="Türkçe Transkripsiyon (Whisper) ve Konuşmacı Ayrıştırma (X1, X2...)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=palette["text_muted"],
        )
        lbl_sub.pack(anchor="w", pady=(1, 0))

        # Sağ Eylem Butonları (Windows Fluent Nötr Komut Butonları)
        actions_frame = ctk.CTkFrame(header, fg_color="transparent")
        actions_frame.pack(side="right", padx=16, pady=10)

        theme_text = "Tema: Açık" if self.current_theme == "dark" else "Tema: Koyu"
        self.btn_theme = ctk.CTkButton(
            actions_frame,
            text=theme_text,
            width=88,
            height=28,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=palette["btn_neutral"],
            border_width=1,
            border_color=palette["border_card"],
            hover_color=palette["btn_neutral_hover"],
            command=self._toggle_theme,
        )
        self.btn_theme.pack(side="right", padx=(6, 0))

        btn_folder = ctk.CTkButton(
            actions_frame,
            text="Çıktı Klasörü",
            width=92,
            height=28,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=palette["btn_neutral"],
            border_width=1,
            border_color=palette["border_card"],
            hover_color=palette["btn_neutral_hover"],
            command=self._open_output_folder,
        )
        btn_folder.pack(side="right", padx=(6, 0))

        btn_settings = ctk.CTkButton(
            actions_frame,
            text="Ayarlar",
            width=76,
            height=28,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=palette["btn_neutral"],
            border_width=1,
            border_color=palette["border_card"],
            hover_color=palette["btn_neutral_hover"],
            command=self._open_advanced_settings,
        )
        btn_settings.pack(side="right")

    def _toggle_theme(self):
        """Karanlık ve Aydınlık temalar arasında geçiş yapar."""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.settings["theme"] = self.current_theme
        save_settings(self.settings)

        ctk.set_appearance_mode(self.current_theme.capitalize())
        theme_text = "Tema: Acik" if self.current_theme == "dark" else "Tema: Koyu"
        self.btn_theme.configure(text=theme_text)
        ToastNotification.show(self, f"Tema: {self.current_theme.capitalize()}", duration_ms=1600)

    # ------------------ Sol Panel Kart 1: Medya Girişi ------------------
    def _build_media_input_card(self, parent, palette: Dict[str, str]):
        card = ModernCard(parent, border_color=palette["border_card"], fg_color=palette["bg_card"])
        card.pack(fill="x", pady=(0, 10))

        self.input_tabs = ctk.CTkTabview(
            card,
            height=142,
            corner_radius=6,
            fg_color=palette["bg_card_secondary"],
            segmented_button_fg_color=palette["input_bg"],
            segmented_button_selected_color=palette["accent_primary"],
            segmented_button_selected_hover_color=palette["accent_hover"],
        )
        self.input_tabs.pack(fill="both", expand=True, padx=10, pady=(6, 6))

        tab_file = self.input_tabs.add("Yerel Dosya")
        tab_yt = self.input_tabs.add("YouTube")

        # 1. Yerel Dosya
        self.btn_select_file = ctk.CTkButton(
            tab_file,
            text="Dosya Sec (MP4 / MP3 / WAV)",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=32,
            fg_color=palette["accent_primary"],
            hover_color=palette["accent_hover"],
            command=self._pick_file,
        )
        self.btn_select_file.pack(fill="x", pady=(2, 6))

        self.file_info_box = ctk.CTkFrame(tab_file, fg_color=palette["input_bg"], corner_radius=4)
        self.file_info_box.pack(fill="x")

        self.lbl_file_name = ctk.CTkLabel(
            self.file_info_box,
            text="Dosya secilmedi",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=palette["text_muted"],
            anchor="w",
        )
        self.lbl_file_name.pack(fill="x", padx=8, pady=(4, 2))

        self.lbl_file_meta = ctk.CTkLabel(
            self.file_info_box,
            text="Desteklenen: .mp4, .mp3, .wav, .m4a, .aac, .mkv, .flac",
            font=ctk.CTkFont(size=10),
            text_color=palette["text_subtle"],
            anchor="w",
        )
        self.lbl_file_meta.pack(fill="x", padx=8, pady=(0, 4))

        # 2. YouTube Sekmesi
        yt_box = ctk.CTkFrame(tab_yt, fg_color="transparent")
        yt_box.pack(fill="x", pady=(2, 6))

        self.yt_url_entry = ctk.CTkEntry(
            yt_box,
            placeholder_text="https://www.youtube.com/watch?v=...",
            height=32,
            font=ctk.CTkFont(size=11),
        )
        self.yt_url_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.yt_url_entry.bind("<Return>", lambda e: self._fetch_youtube_info())

        self.yt_fetch_btn = ctk.CTkButton(
            yt_box,
            text="Bilgi Al",
            width=70,
            height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            command=self._fetch_youtube_info,
        )
        self.yt_fetch_btn.pack(side="right")

        self.yt_info_box = ctk.CTkFrame(tab_yt, fg_color=palette["input_bg"], corner_radius=4)
        self.yt_info_box.pack(fill="x")

        self.lbl_yt_title = ctk.CTkLabel(
            self.yt_info_box,
            text="YouTube baglantisi giriniz",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=palette["text_muted"],
            anchor="w",
        )
        self.lbl_yt_title.pack(fill="x", padx=8, pady=(4, 2))

        self.lbl_yt_meta = ctk.CTkLabel(
            self.yt_info_box,
            text="Link girildikten sonra dogrudan baslatabilirsiniz",
            font=ctk.CTkFont(size=10),
            text_color=palette["text_subtle"],
            anchor="w",
        )
        self.lbl_yt_meta.pack(fill="x", padx=8, pady=(0, 4))

        # Ses Oynatıcı Önizleme Çubuğu
        self.audio_player = AudioPlayerBar(card)
        self.audio_player.pack(fill="x", padx=10, pady=(0, 8))

    # ------------------ Sol Panel Kart 2: Model & Ayarlar ------------------
    def _build_settings_card(self, parent, palette: Dict[str, str]):
        card = ModernCard(parent, border_color=palette["border_card"], fg_color=palette["bg_card"])
        card.pack(fill="x", pady=(0, 10))

        header_row = ctk.CTkFrame(card, fg_color="transparent")
        header_row.pack(fill="x", padx=12, pady=(10, 6))

        lbl_title = ctk.CTkLabel(
            header_row,
            text="Model ve Ayrıştırma Ayarları",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=palette["text_main"],
        )
        lbl_title.pack(side="left")

        # Whisper Model Seçimi
        lbl_model = ctk.CTkLabel(
            card,
            text="Whisper Modeli:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=palette["text_muted"],
        )
        lbl_model.pack(anchor="w", padx=12, pady=(0, 2))

        self.cmb_model = ctk.CTkComboBox(
            card,
            values=[
                "small (Dengeli)",
                "medium (Yüksek Doğruluk)",
                "large-v3-turbo (En Yüksek Kalite)",
                "base (Hızlı)",
                "tiny (Ultra Hızlı)",
            ],
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            height=28,
            state="readonly",
        )
        self.cmb_model.set("small (Dengeli)")
        self.cmb_model.pack(fill="x", padx=12, pady=(0, 6))

        # Dil & VAD
        row_opts = ctk.CTkFrame(card, fg_color="transparent")
        row_opts.pack(fill="x", padx=12, pady=(0, 6))

        col_lang = ctk.CTkFrame(row_opts, fg_color="transparent")
        col_lang.pack(side="left", fill="x", expand=True, padx=(0, 4))
        lbl_lang = ctk.CTkLabel(
            col_lang,
            text="Dil:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=palette["text_muted"],
        )
        lbl_lang.pack(anchor="w", pady=(0, 1))
        self.cmb_lang = ctk.CTkComboBox(
            col_lang,
            values=["Türkçe (tr)", "Otomatik (auto)"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            height=28,
            state="readonly",
        )
        self.cmb_lang.set("Türkçe (tr)")
        self.cmb_lang.pack(fill="x")

        col_vad = ctk.CTkFrame(row_opts, fg_color="transparent")
        col_vad.pack(side="right", fill="x", expand=True, padx=(4, 0))
        lbl_vad = ctk.CTkLabel(
            col_vad,
            text="Ses Tespiti (VAD):",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=palette["text_muted"],
        )
        lbl_vad.pack(anchor="w", pady=(0, 1))
        self.cmb_vad = ctk.CTkComboBox(
            col_vad,
            values=["Yüksek (Hassas)", "Normal (Standart)"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            height=28,
            state="readonly",
        )
        self.cmb_vad.set("Yüksek (Hassas)")
        self.cmb_vad.pack(fill="x")

        # Konuşmacı Ayrıştırma
        row_spk = ctk.CTkFrame(card, fg_color="transparent")
        row_spk.pack(fill="x", padx=12, pady=(0, 6))

        col_count = ctk.CTkFrame(row_spk, fg_color="transparent")
        col_count.pack(side="left", fill="x", expand=True, padx=(0, 4))
        lbl_spk_cnt = ctk.CTkLabel(
            col_count,
            text="Konuşmacı Sayısı:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=palette["text_muted"],
        )
        lbl_spk_cnt.pack(anchor="w", pady=(0, 1))
        self.cmb_spk_count = ctk.CTkComboBox(
            col_count,
            values=["Otomatik Tespit", "1 Konuşmacı", "2 Konuşmacı", "3 Konuşmacı", "4 Konuşmacı"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            height=28,
            state="readonly",
        )
        self.cmb_spk_count.set("Otomatik Tespit")
        self.cmb_spk_count.pack(fill="x")

        col_prefix = ctk.CTkFrame(row_spk, fg_color="transparent")
        col_prefix.pack(side="right", fill="x", expand=True, padx=(4, 0))
        lbl_spk_pre = ctk.CTkLabel(
            col_prefix,
            text="Etiket Formatı:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=palette["text_muted"],
        )
        lbl_spk_pre.pack(anchor="w", pady=(0, 1))
        self.cmb_prefix = ctk.CTkComboBox(
            col_prefix,
            values=["X (X1, X2...)", "Konuşmacı (1, 2...)", "Kişi (1, 2...)"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            height=28,
            state="readonly",
        )
        self.cmb_prefix.set("X (X1, X2...)")
        self.cmb_prefix.pack(fill="x")

        # Ses Ön-İyileştirme
        self.chk_enhance = ctk.CTkCheckBox(
            card,
            text="Ses Ön-İyileştirme (80Hz gürültü kesici & dengeleme)",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=palette["accent_primary"],
            hover_color=palette["accent_hover"],
        )
        self.chk_enhance.select()
        self.chk_enhance.pack(anchor="w", padx=12, pady=(2, 10))

    # ------------------ Sol Panel Kart 3: İşlem Durumu & Stepper ------------------
    def _build_action_card(self, parent, palette: Dict[str, str]):
        card = ModernCard(parent, border_color=palette["border_card"], fg_color=palette["bg_card"])
        card.pack(fill="x")

        # Çok Adımlı İlerleme Göstergesi (Sade Metin)
        self.stepper = ProcessStepper(card)
        self.stepper.pack(fill="x", padx=10, pady=(10, 8))

        # Başlat ve İptal Butonları
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 8))

        self.btn_start = ctk.CTkButton(
            btn_row,
            text="Transkripsiyonu Başlat",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            height=36,
            fg_color=palette["accent_primary"],
            hover_color=palette["accent_hover"],
            command=self._start_transcription_thread,
        )
        self.btn_start.pack(side="left", fill="x", expand=True)

        self.btn_cancel = ctk.CTkButton(
            btn_row,
            text="İptal",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            width=65,
            height=36,
            fg_color=palette["btn_neutral"],
            border_width=1,
            border_color=palette["border_card"],
            hover_color=palette["danger"],
            command=self._request_cancel,
            state="disabled",
        )
        self.btn_cancel.pack(side="right", padx=(6, 0))

        # İlerleme Çubuğu (Windows Fluent İnce Çubuk)
        self.progress_bar = ctk.CTkProgressBar(
            card,
            height=4,
            fg_color=palette["input_bg"],
            progress_color=palette["accent_primary"],
        )
        self.progress_bar.set(0.0)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 6))

        self.lbl_status = ctk.CTkLabel(
            card,
            text="Hazır. Medya dosyası veya bağlantı seçerek başlayın.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color=palette["text_muted"],
            wraplength=340,
            justify="left",
        )
        self.lbl_status.pack(anchor="w", padx=10, pady=(0, 10))

    # ------------------ Sağ Panel: Transkript, Düzenleyici & Çıktılar ------------------
    def _build_transcript_view(self, parent, palette: Dict[str, str]):
        card = ModernCard(parent, border_color=palette["border_card"], fg_color=palette["bg_card"])
        card.pack(fill="both", expand=True)

        # 1. Metrik / İstatistik Şeridi (4 Eşit Sütunlu Grid - Boşluksuz ve Dengeli)
        self.stats_ribbon = ctk.CTkFrame(card, fg_color="transparent")
        self.stats_ribbon.pack(fill="x", padx=14, pady=(12, 8))
        for col_idx in range(4):
            self.stats_ribbon.grid_columnconfigure(col_idx, weight=1)

        self.badge_duration = MetricBadge(self.stats_ribbon, title="Süre", value="00:00", height=44)
        self.badge_duration.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.badge_speakers = MetricBadge(self.stats_ribbon, title="Konuşmacı", value="0 Kişi", height=44)
        self.badge_speakers.grid(row=0, column=1, sticky="ew", padx=4)

        self.badge_words = MetricBadge(self.stats_ribbon, title="Kelime", value="0 Kelime", height=44)
        self.badge_words.grid(row=0, column=2, sticky="ew", padx=4)

        self.badge_wpm = MetricBadge(self.stats_ribbon, title="Hız", value="0 WPM", height=44)
        self.badge_wpm.grid(row=0, column=3, sticky="ew", padx=(4, 0))

        # 2. Arama ve Komut Araç Çubuğu (Toolbar)
        toolbar = ctk.CTkFrame(card, fg_color="transparent")
        toolbar.pack(fill="x", padx=14, pady=(0, 8))

        # Arama Alanı (Sol tarafta genişleyen kutu)
        self.search_bar_frame = ctk.CTkFrame(
            toolbar,
            fg_color=palette["input_bg"],
            border_width=1,
            border_color=palette["input_border"],
            corner_radius=6,
        )
        self.search_bar_frame.pack(side="left", fill="x", expand=True)

        search_inner = ctk.CTkFrame(self.search_bar_frame, fg_color="transparent")
        search_inner.pack(fill="x", padx=8, pady=4)

        lbl_s_tag = ctk.CTkLabel(
            search_inner,
            text="Ara:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=palette["text_muted"],
        )
        lbl_s_tag.pack(side="left", padx=(0, 6))

        self.search_entry = ctk.CTkEntry(
            search_inner,
            placeholder_text="Transkriptte ara (metin, konuşmacı veya zaman)...",
            height=26,
            border_width=0,
            fg_color="transparent",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.search_entry.bind("<KeyRelease>", lambda e: self._filter_transcript())

        self.lbl_search_count = ctk.CTkLabel(
            search_inner,
            text="",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=palette["accent_primary"],
        )
        self.lbl_search_count.pack(side="right", padx=(0, 4))

        # Sağ Taraftaki Araç Butonları
        self.btn_find_replace = ctk.CTkButton(
            toolbar,
            text="Bul ve Değiştir",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            height=30,
            width=100,
            fg_color=palette["btn_neutral"],
            border_width=1,
            border_color=palette["border_card"],
            hover_color=palette["btn_neutral_hover"],
            command=self._toggle_find_replace,
        )
        self.btn_find_replace.pack(side="right", padx=(6, 0))

        self.btn_spk_manager = ctk.CTkButton(
            toolbar,
            text="Konuşmacı Yönetimi",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            height=30,
            width=125,
            fg_color=palette["btn_neutral"],
            border_width=1,
            border_color=palette["border_card"],
            hover_color=palette["btn_neutral_hover"],
            command=self._open_speaker_manager,
        )
        self.btn_spk_manager.pack(side="right")

        # Bul & Değiştir Genişleme Paneli
        self.find_replace_frame = ctk.CTkFrame(
            card,
            fg_color=palette["input_bg"],
            border_width=1,
            border_color=palette["input_border"],
            corner_radius=6,
        )

        fr_inner = ctk.CTkFrame(self.find_replace_frame, fg_color="transparent")
        fr_inner.pack(fill="x", padx=8, pady=6)

        lbl_fr = ctk.CTkLabel(
            fr_inner,
            text="Değiştir:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=palette["text_muted"],
        )
        lbl_fr.pack(side="left", padx=(0, 6))

        self.entry_find = ctk.CTkEntry(
            fr_inner,
            placeholder_text="Aranan kelime...",
            width=140,
            height=26,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        )
        self.entry_find.pack(side="left", padx=(0, 6))

        self.entry_replace = ctk.CTkEntry(
            fr_inner,
            placeholder_text="Yeni kelime...",
            width=140,
            height=26,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        )
        self.entry_replace.pack(side="left", padx=(0, 8))

        btn_do_replace = ctk.CTkButton(
            fr_inner,
            text="Tümünü Değiştir",
            width=110,
            height=26,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            fg_color=palette["accent_primary"],
            hover_color=palette["accent_hover"],
            command=self._execute_find_replace,
        )
        btn_do_replace.pack(side="left")

        # 3. Kaydırılabilir Transkript Listesi Alanı
        self.transcript_scroll = ctk.CTkScrollableFrame(
            card,
            fg_color=palette["input_bg"],
            corner_radius=6,
            border_width=1,
            border_color=palette["border_card"],
        )
        self.transcript_scroll.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        # Başlangıç Boş Durum
        self._build_empty_state(palette)

        # 4. Alt Dışa Aktarma ve Eylem Barı (Yeknesak Fluent Stili)
        export_bar = ctk.CTkFrame(card, fg_color="transparent")
        export_bar.pack(fill="x", padx=14, pady=(0, 12))

        self.lbl_total_turns = ctk.CTkLabel(
            export_bar,
            text="0 konuşma parçası",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=palette["text_muted"],
        )
        self.lbl_total_turns.pack(side="left")

        # Format butonları (MD, VTT, CSV, JSON, SRT, TXT)
        for fmt in ["md", "vtt", "csv", "json", "srt", "txt"]:
            btn_exp = ctk.CTkButton(
                export_bar,
                text=fmt.upper(),
                height=28,
                width=52,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
                fg_color=palette["btn_neutral"],
                border_width=1,
                border_color=palette["border_card"],
                hover_color=palette["btn_neutral_hover"],
                command=lambda f=fmt: self._export_result(f),
            )
            btn_exp.pack(side="right", padx=(4, 0))

        btn_copy = ctk.CTkButton(
            export_bar,
            text="Panoya Kopyala",
            height=28,
            width=115,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            fg_color=palette["accent_primary"],
            hover_color=palette["accent_hover"],
            command=self._copy_to_clipboard,
        )
        btn_copy.pack(side="right", padx=(0, 4))

    def _build_empty_state(self, palette: Dict[str, str]):
        """Transkript listesi boşken gösterilen Fluent bilgilendirme paneli."""
        for widget in self.transcript_scroll.winfo_children():
            widget.destroy()

        box = ctk.CTkFrame(
            self.transcript_scroll,
            fg_color=palette["bg_card"],
            border_width=1,
            border_color=palette["border_card"],
            corner_radius=8,
        )
        box.pack(expand=True, padx=40, pady=70)

        self.lbl_empty = ctk.CTkLabel(
            box,
            text="Transkript Henüz Oluşturulmadı",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            text_color=palette["text_main"],
        )
        self.lbl_empty.pack(padx=30, pady=(20, 6))

        lbl_desc = ctk.CTkLabel(
            box,
            text="Sol panelden bir medya dosyası veya YouTube bağlantısı seçerek\n'Transkripsiyonu Başlat' butonuna tıklayınız.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=palette["text_muted"],
            justify="center",
        )
        lbl_desc.pack(padx=30, pady=(0, 16))

        info_box = ctk.CTkFrame(box, fg_color=palette["input_bg"], corner_radius=6)
        info_box.pack(fill="x", padx=20, pady=(0, 18))

        tips = [
            "- 100% Yerel & Çevrimdışı: Ses verileriniz bilgisayarınızda güvenle işlenir.",
            "- Otomatik Konuşmacı Ayrımı: Konuşmacılar 'X1', 'X2' olarak ayrıştırılır.",
            "- Esnek Dışa Aktarım: TXT, SRT, VTT, JSON, CSV ve Markdown çıktıları.",
        ]
        for tip in tips:
            lbl_tip = ctk.CTkLabel(
                info_box,
                text=tip,
                font=ctk.CTkFont(family=FONT_FAMILY, size=10),
                text_color=palette["text_muted"],
                anchor="w",
            )
            lbl_tip.pack(fill="x", padx=12, pady=3)

    # ------------------ Dosya & YouTube Giriş Yönetimi ------------------
    def _pick_file(self):
        """Medya dosyası seçme diyalog penceresi."""
        filetypes = [
            ("Desteklenen Medya Dosyalari", "*.mp4 *.mp3 *.wav *.m4a *.aac *.mkv *.flac *.ogg"),
            ("Video Dosyalari (*.mp4, *.mkv)", "*.mp4 *.mkv"),
            ("Ses Dosyalari (*.mp3, *.wav, *.m4a)", "*.mp3 *.wav *.m4a *.aac *.flac *.ogg"),
            ("Tum Dosyalar", "*.*"),
        ]
        chosen = filedialog.askopenfilename(
            title="Islenecek Ses veya Video Dosyasini Secin",
            filetypes=filetypes,
            initialdir=self.settings.get("last_input_dir", str(BASE_DIR)),
        )
        if chosen:
            self.selected_file_path = chosen
            self.settings["last_input_dir"] = str(Path(chosen).parent)
            save_settings(self.settings)

            try:
                self.media_info = get_media_info(chosen)
                short_name = self.media_info["file_name"]
                if len(short_name) > 36:
                    short_name = short_name[:34] + "..."
                self.lbl_file_name.configure(text=f"Dosya: {short_name}", text_color="#38bdf8")
                self.lbl_file_meta.configure(
                    text=f"Sure: {self.media_info['duration_formatted']} - Boyut: {self.media_info['file_size_mb']} MB ({self.media_info['sample_rate']}Hz)",
                )
                self.lbl_status.configure(
                    text=f"Dosya hazir: {self.media_info['file_name']} ({self.media_info['duration_formatted']})",
                )
                if chosen.lower().endswith(".wav"):
                    self.audio_player.set_audio_source(chosen, self.media_info["duration_formatted"])
                else:
                    self.audio_player.set_audio_source(None)

                ToastNotification.show(self, "Dosya secildi", duration_ms=1600)
            except Exception:
                self.lbl_file_name.configure(text=f"Dosya: {Path(chosen).name}", text_color="#38bdf8")
                self.lbl_file_meta.configure(text="Medya detaylari okunamadi")

    def _fetch_youtube_info(self):
        """Girilen YouTube adresinin video meta verilerini asenkron çeker."""
        url = self.yt_url_entry.get().strip()
        if not url:
            messagebox.showwarning("Eksik URL", "Lutfen bir YouTube baglantisi giriniz.")
            return
        if not is_valid_youtube_url(url):
            messagebox.showwarning("Gecersiz URL", "Lutfen gecerli bir YouTube baglantisi giriniz.")
            return

        self.yt_fetch_btn.configure(state="disabled", text="Aliniyor...")
        self.lbl_yt_title.configure(text="Video bilgileri aliniyor...", text_color="#f59e0b")

        def fetch_worker():
            try:
                info = get_youtube_video_info(url)
                self.youtube_info = info
                self.after(0, lambda: self._apply_youtube_info(info))
            except Exception as e:
                err_clean = clean_error_message(e)
                self.after(0, lambda msg=err_clean: messagebox.showerror("Hata", f"YouTube bilgisi alinamadi:\n{msg}"))
                self.after(0, lambda: self.lbl_yt_title.configure(text="Bilgi alinamadi", text_color="#ef4444"))
            finally:
                self.after(0, lambda: self.yt_fetch_btn.configure(state="normal", text="Bilgi Al"))

        threading.Thread(target=fetch_worker, daemon=True).start()

    def _apply_youtube_info(self, info: Dict[str, Any]):
        title = info.get("title", "")
        short_title = title[:36] + "..." if len(title) > 36 else title
        self.lbl_yt_title.configure(text=f"Video: {short_title}", text_color="#38bdf8")
        self.lbl_yt_meta.configure(text=f"Kanal: {info.get('channel', '')} - Sure: {info.get('duration_formatted', '')}")
        self.lbl_status.configure(text=f"YouTube hazir: {title}")
        ToastNotification.show(self, "YouTube video bilgisi alindi", duration_ms=1600)

    # ------------------ Transkripsiyon Pipeline ------------------
    def _start_transcription_thread(self):
        """İşlemi arka planda başlatır."""
        active_tab = self.input_tabs.get()
        is_youtube = "youtube" in active_tab.lower()

        if is_youtube:
            url = self.yt_url_entry.get().strip()
            if not url or not is_valid_youtube_url(url):
                messagebox.showwarning("Gecersiz Baglanti", "Lutfen gecerli bir YouTube baglantisi giriniz.")
                return
        else:
            if not self.selected_file_path:
                messagebox.showwarning("Dosya Eksik", "Lutfen once bir ses veya video dosyasi seciniz.")
                return

        if self.is_processing:
            return

        self.is_processing = True
        self.cancel_requested = False
        self.btn_start.configure(state="disabled", text="Isleniyor...")
        self.btn_cancel.configure(state="normal")
        self.btn_select_file.configure(state="disabled")
        self.yt_fetch_btn.configure(state="disabled")
        self.stepper.reset()

        threading.Thread(target=self._run_transcription_pipeline, daemon=True).start()

    def _request_cancel(self):
        """Kullanıcı iptal butonuna bastığında bayrak kaldırır."""
        self.cancel_requested = True
        self.lbl_status.configure(text="Islem iptal ediliyor, lutfen bekleyin...")
        self.btn_cancel.configure(state="disabled")

    def _run_transcription_pipeline(self):
        """Tüm ses hazırlığı, STT, Diarization ve hizalama boru hattı."""
        temp_wav: Optional[str] = None
        enhanced_wav: Optional[str] = None
        try:
            active_tab = self.input_tabs.get()
            is_youtube = "youtube" in active_tab.lower()

            # Adım 1: Medya Hazırlığı
            self.after(0, lambda: self.stepper.set_active_step(0))
            if is_youtube:
                url = self.yt_url_entry.get().strip()
                self._update_progress(0.04, "1/5: YouTube uzerinden ses indiriliyor...")

                def yt_dl_hook(pct, msg):
                    self._update_progress(pct * 0.12, f"1/5: {msg}")

                temp_wav, yt_meta = download_youtube_audio(url, progress_callback=yt_dl_hook)
                self.media_info = yt_meta
                self.selected_file_path = temp_wav
                total_dur = yt_meta.get("duration_seconds", 0.0)
            else:
                self._update_progress(0.08, "1/5: Ses dosyasi 16kHz WAV formatina donusturuluyor...")
                temp_wav = extract_audio_to_wav(self.selected_file_path)
                total_dur = self.media_info.get("duration_seconds", 0.0) if self.media_info else 0.0

            if self.cancel_requested:
                raise InterruptedError("Islem kullanici tarafindan iptal edildi.")

            # Ses oynatıcıyı güncelle
            self.active_wav_path = temp_wav
            self.after(0, lambda: self.audio_player.set_audio_source(temp_wav, self.media_info.get("duration_formatted", "")))

            # Adım 2: Ses İyileştirme
            self.after(0, lambda: self.stepper.set_active_step(1))
            audio_for_stt = temp_wav
            should_enhance = hasattr(self, "chk_enhance") and self.chk_enhance.get()
            if should_enhance:
                try:
                    import uuid
                    enhanced_wav = str(TEMP_DIR / f"enhanced_{uuid.uuid4().hex[:8]}.wav")
                    self._update_progress(0.14, "2/5: Ses kalitesi iyilestiriliyor (Gurultu kesici & filtre)...")
                    enhance_audio(temp_wav, enhanced_wav)
                    audio_for_stt = enhanced_wav
                except Exception as enh_err:
                    print(f"Ses iyilestirme atlandi: {enh_err}")
                    audio_for_stt = temp_wav

            if self.cancel_requested:
                raise InterruptedError("Islem kullanici tarafindan iptal edildi.")

            # Adım 3: Whisper STT
            self.after(0, lambda: self.stepper.set_active_step(2))
            model_key = self.cmb_model.get().split()[0].lower()
            lang_choice = "tr" if "tr" in self.cmb_lang.get().lower() else "auto"
            vad_choice = "high" if "yuksek" in self.cmb_vad.get().lower() or "hassas" in self.cmb_vad.get().lower() else "normal"

            self._update_progress(0.20, f"3/5: Whisper '{model_key}' modeli hazirlaniyor...")
            transcriber = WhisperTranscriber(model_size=model_key, cpu_threads=4)

            def whisper_progress(pct, msg, seg):
                if self.cancel_requested:
                    raise InterruptedError("Kullanici iptal etti.")
                scaled = 0.20 + (pct * 0.55)
                self._update_progress(scaled, f"3/5: {msg}")

            stt_segments = transcriber.transcribe(
                audio_path=audio_for_stt,
                language=lang_choice,
                total_duration=total_dur,
                vad_sensitivity=vad_choice,
                apply_postprocessing=True,
                progress_callback=whisper_progress,
            )

            if not stt_segments:
                self._update_progress(1.0, "Ses dosyasinda herhangi bir konusma algilanamadi.")
                self.after(0, self._render_transcript, [])
                return

            if self.cancel_requested:
                raise InterruptedError("Islem kullanici tarafindan iptal edildi.")

            # Adım 4: Konuşmacı Ayrıştırma (Diarization)
            self.after(0, lambda: self.stepper.set_active_step(3))
            self._update_progress(0.78, "4/5: Konusmacilar ayristiriliyor...")

            prefix_val = self.cmb_prefix.get().split()[0]
            spk_choice = self.cmb_spk_count.get()
            num_spk = None
            if "1" in spk_choice:
                num_spk = 1
            elif "2" in spk_choice:
                num_spk = 2
            elif "3" in spk_choice:
                num_spk = 3
            elif "4" in spk_choice:
                num_spk = 4

            diarizer = SpeakerDiarizer(
                speaker_prefix=prefix_val,
                hf_token=self.settings.get("hf_token", ""),
                use_pyannote=self.settings.get("use_pyannote", False),
            )

            def diarizer_progress(pct, msg):
                scaled = 0.76 + (pct * 0.14)
                self._update_progress(scaled, f"4/5: {msg}")

            diar_intervals = diarizer.diarize(
                audio_path=audio_for_stt,
                speech_segments=stt_segments,
                num_speakers=num_spk,
                progress_callback=diarizer_progress,
            )

            # Adım 5: Hizalama ve Çıktı Oluşturma
            self.after(0, lambda: self.stepper.set_active_step(4))
            self._update_progress(0.92, "5/5: Konusmalar ve metin bloklari hizalaniyor...")

            aligned_transcript = align_transcription_and_diarization(
                transcription_segments=stt_segments,
                diarization_intervals=diar_intervals,
                speaker_prefix=prefix_val,
                auto_merge_gap=self.settings.get("auto_merge_gap", 1.5),
            )

            self.transcribed_data = aligned_transcript
            self._auto_save_outputs(aligned_transcript)

            self.after(0, lambda: self.stepper.set_active_step(5))
            self._update_progress(1.0, f"Tamamlandi. {len(aligned_transcript)} konusma segmenti olusturuldu.")
            self.after(0, self._render_transcript, aligned_transcript)
            self.after(0, lambda: ToastNotification.show(self, "Transkripsiyon tamamlandi", color="#10b981"))

        except InterruptedError:
            self._update_progress(0.0, "Islem kullanici tarafindan iptal edildi.")
            self.after(0, lambda: ToastNotification.show(self, "Islem iptal edildi", color="#ef4444"))
        except Exception as e:
            self._update_progress(0.0, f"Hata: {str(e)}")
            self.after(0, lambda: messagebox.showerror("Islem Hatasi", f"Islem sirasinda bir hata olustu:\n{str(e)}"))
        finally:
            if temp_wav and temp_wav != self.selected_file_path:
                cleanup_temp_file(temp_wav)
            if enhanced_wav:
                cleanup_temp_file(enhanced_wav)
            self.is_processing = False
            self.after(0, self._reset_action_buttons)

    def _update_progress(self, fraction: float, message: str):
        """Thread-safe ilerleme güncellemesi."""
        self.after(0, lambda: self._apply_progress(fraction, message))

    def _apply_progress(self, fraction: float, message: str):
        self.progress_bar.set(fraction)
        self.lbl_status.configure(text=message)

    def _reset_action_buttons(self):
        self.btn_start.configure(state="normal", text="Transkripsiyonu Baslat")
        self.btn_cancel.configure(state="disabled")
        self.btn_select_file.configure(state="normal")
        self.yt_fetch_btn.configure(state="normal")

    # ------------------ Transkript Çizimi ------------------
    def _render_transcript(self, transcript_items: List[Dict[str, Any]]):
        """Segment kartlarını Windows 11 Fluent tasarımına uygun olarak listeler."""
        palette = get_theme_palette(self.current_theme)

        for widget in self.transcript_scroll.winfo_children():
            widget.destroy()

        if not transcript_items:
            self._build_empty_state(palette)
            self.lbl_total_turns.configure(text="0 konuşma parçası")
            self._update_metrics_ribbon([])
            return

        self.lbl_total_turns.configure(text=f"{len(transcript_items)} konuşma parçası")
        self._update_metrics_ribbon(transcript_items)

        for idx, item in enumerate(transcript_items):
            spk = item.get("speaker", "X1")
            ts = item.get("timestamp_display", f"[{item.get('start', 0):.1f}s - {item.get('end', 0):.1f}s]")
            text = item.get("text", "")
            duration = max(0.0, float(item.get("end", 0.0)) - float(item.get("start", 0.0)))

            item_card = ModernCard(
                self.transcript_scroll,
                fg_color=palette["bg_card"],
                border_color=palette["border_card"],
                corner_radius=6,
            )
            item_card.pack(fill="x", pady=4, padx=3)

            # Üst Başlık Satırı
            header_row = ctk.CTkFrame(item_card, fg_color="transparent")
            header_row.pack(fill="x", padx=10, pady=(8, 3))

            bg_col, fg_col = get_speaker_color(spk)

            def make_rename_caller(target_spk):
                return lambda: RenameSpeakerDialog(self, target_spk, self._apply_speaker_rename)

            spk_btn = ctk.CTkButton(
                header_row,
                text=f" {spk} ",
                font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
                fg_color=bg_col,
                text_color=fg_col,
                hover_color=bg_col,
                corner_radius=4,
                height=22,
                width=40,
                command=make_rename_caller(spk),
            )
            spk_btn.pack(side="left")

            ts_label = ctk.CTkLabel(
                header_row,
                text=f"  {ts} ({duration:.1f}s)",
                font=ctk.CTkFont(family=FONT_FAMILY, size=10),
                text_color=palette["text_muted"],
            )
            ts_label.pack(side="left")

            def make_copy_turn(t):
                def do_copy():
                    self.clipboard_clear()
                    self.clipboard_append(t)
                    ToastNotification.show(self, "Segment kopyalandı", duration_ms=1400)
                return do_copy

            btn_turn_copy = ctk.CTkButton(
                header_row,
                text="Kopyala",
                width=55,
                height=20,
                font=ctk.CTkFont(family=FONT_FAMILY, size=10),
                fg_color=palette["btn_neutral"],
                border_width=1,
                border_color=palette["border_card"],
                hover_color=palette["btn_neutral_hover"],
                command=make_copy_turn(text),
            )
            btn_turn_copy.pack(side="right")

            # Düzenlenebilir Metin Kutusu
            line_count = max(2, min(7, len(text) // 75 + text.count("\n") + 1))
            box_height = 22 * line_count

            text_box = ctk.CTkTextbox(
                item_card,
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                fg_color=palette["input_bg"],
                border_width=1,
                border_color=palette["input_border"],
                text_color=palette["text_main"],
                height=box_height,
                wrap="word",
                corner_radius=6,
            )
            text_box.insert("1.0", text)
            text_box.pack(fill="x", padx=10, pady=(0, 8))

            def make_listener(item_ref, txt_box):
                def on_edit(event=None):
                    item_ref["text"] = txt_box.get("1.0", "end-1c").strip()
                return on_edit

            text_box.bind("<KeyRelease>", make_listener(item, text_box))

    def _update_metrics_ribbon(self, items: List[Dict[str, Any]]):
        """Üst istatistik göstergelerini günceller."""
        stats = compute_transcript_statistics(items)
        sec = stats.get("speaking_duration_seconds", 0.0)
        mins = int(sec // 60)
        secs = int(sec % 60)
        dur_str = f"{mins:02d}:{secs:02d}"

        self.badge_duration.update_value(dur_str)
        self.badge_speakers.update_value(f"{stats.get('unique_speakers_count', 0)} Kişi")
        self.badge_words.update_value(f"{stats.get('total_words', 0):,}")
        self.badge_wpm.update_value(f"{stats.get('words_per_minute', 0.0)} WPM")

    # ------------------ Arama ve Değiştirme ------------------
    def _filter_transcript(self):
        """Arama kutusuna yazılan kelimeye göre canlı filtreler."""
        query = self.search_entry.get().strip()
        if not query:
            self.lbl_search_count.configure(text="")
            self._render_transcript(self.transcribed_data)
            return

        filtered = filter_transcript(self.transcribed_data, query)
        self.lbl_search_count.configure(text=f"{len(filtered)} / {len(self.transcribed_data)} eşleşme")
        self._render_transcript(filtered)

    def _toggle_find_replace(self):
        """Bul ve değiştir panelini açar/kapatır."""
        if self.find_replace_frame.winfo_ismapped():
            self.find_replace_frame.pack_forget()
            self.btn_find_replace.configure(fg_color="#1e293b")
        else:
            self.find_replace_frame.pack(fill="x", padx=14, pady=(0, 6), after=self.search_bar_frame)
            self.btn_find_replace.configure(fg_color="#2563eb")
            self.entry_find.focus_set()

    def _execute_find_replace(self):
        """Tüm transkriptte aranan kelimeyi topluca değiştirir."""
        find_txt = self.entry_find.get().strip()
        replace_txt = self.entry_replace.get().strip()
        if not find_txt:
            messagebox.showwarning("Eksik Arama", "Lutfen aranacak kelimeyi giriniz.")
            return

        updated, count = find_and_replace_in_transcript(
            self.transcribed_data,
            find_str=find_txt,
            replace_str=replace_txt,
            case_sensitive=False,
        )
        self.transcribed_data = updated
        self._render_transcript(self.transcribed_data)
        ToastNotification.show(self, f"{count} kelime degistirildi", duration_ms=2000)

    # ------------------ Konuşmacı Yönetimi ------------------
    def _open_speaker_manager(self):
        """Tüm konuşmacıları listeleme ve yönetme penceresi."""
        if not self.transcribed_data:
            messagebox.showinfo("Bilgi", "Henuz islenmis bir transkript bulunmuyor.")
            return

        SpeakerManagerModal(self, self.transcribed_data, self._apply_speaker_rename)

    def _apply_speaker_rename(self, old_name: str, new_name: str):
        """Transkriptteki tüm 'old_name' konuşmacılarını 'new_name' yapar."""
        self.transcribed_data = rename_speaker_in_transcript(self.transcribed_data, old_name, new_name)
        self._render_transcript(self.transcribed_data)
        ToastNotification.show(self, f"'{old_name}' -> '{new_name}' guncellendi", duration_ms=1800)

    # ------------------ Dışa Aktarma & Otomatik Kayıt ------------------
    def _auto_save_outputs(self, transcript: List[Dict[str, Any]]):
        """Her işlem bitiminde outputs/ klasörüne otomatik olarak kaydeder."""
        if not self.selected_file_path or not transcript:
            return

        base_name = Path(self.selected_file_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"{base_name}_{timestamp}"

        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        txt_path = str(OUTPUTS_DIR / f"{prefix}.txt")
        srt_path = str(OUTPUTS_DIR / f"{prefix}.srt")
        vtt_path = str(OUTPUTS_DIR / f"{prefix}.vtt")
        json_path = str(OUTPUTS_DIR / f"{prefix}.json")
        csv_path = str(OUTPUTS_DIR / f"{prefix}.csv")
        md_path = str(OUTPUTS_DIR / f"{prefix}.md")

        export_to_txt(transcript, txt_path, self.media_info)
        export_to_srt(transcript, srt_path, include_speaker=True)
        export_to_vtt(transcript, vtt_path, include_speaker=True)
        export_to_json(transcript, json_path, self.media_info)
        export_to_csv(transcript, csv_path)
        export_to_markdown(transcript, md_path, self.media_info)

    def _export_result(self, fmt: str):
        """Kullanıcının seçeceği konuma transkript dosyasını kaydeder."""
        if not self.transcribed_data:
            messagebox.showinfo("Bilgi", "Disa aktarilacak transkript verisi bulunmuyor.")
            return

        base_name = Path(self.selected_file_path).stem if self.selected_file_path else "transkript"
        ext_map = {
            "txt": "Metin Dosyasi (*.txt)",
            "srt": "Altyazi Dosyasi (*.srt)",
            "vtt": "WebVTT Altyazi (*.vtt)",
            "json": "JSON Verisi (*.json)",
            "csv": "CSV Tablosu (*.csv)",
            "md": "Markdown Belgesi (*.md)",
        }

        save_path = filedialog.asksaveasfilename(
            title=f"{fmt.upper()} Formatinda Kaydet",
            initialfile=f"{base_name}_transkript.{fmt}",
            filetypes=[(ext_map.get(fmt, fmt.upper()), f"*.{fmt}")],
            initialdir=self.settings.get("last_output_dir", str(OUTPUTS_DIR)),
        )

        if not save_path:
            return

        if fmt == "txt":
            export_to_txt(self.transcribed_data, save_path, self.media_info)
        elif fmt == "srt":
            export_to_srt(self.transcribed_data, save_path)
        elif fmt == "vtt":
            export_to_vtt(self.transcribed_data, save_path)
        elif fmt == "json":
            export_to_json(self.transcribed_data, save_path, self.media_info)
        elif fmt == "csv":
            export_to_csv(self.transcribed_data, save_path)
        elif fmt == "md":
            export_to_markdown(self.transcribed_data, save_path, self.media_info)

        ToastNotification.show(self, f"Kaydedildi: {Path(save_path).name}", duration_ms=2000)

    def _copy_to_clipboard(self):
        """Transkriptin tamamını panoya kopyalar."""
        if not self.transcribed_data:
            messagebox.showinfo("Bilgi", "Kopyalanacak transkript bulunmuyor.")
            return

        lines = []
        for item in self.transcribed_data:
            spk = item.get("speaker", "X1")
            ts = item.get("timestamp_display", "")
            text = item.get("text", "")
            lines.append(f"{ts} {spk}: {text}")

        full_text = "\n".join(lines)
        self.clipboard_clear()
        self.clipboard_append(full_text)
        ToastNotification.show(self, "Panoya kopyalandi", duration_ms=1800)

    def _open_output_folder(self):
        """Çıktı klasörünü Windows Dosya Gezgini'nde açar."""
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        os.startfile(str(OUTPUTS_DIR))

    # ------------------ Gelişmiş Ayarlar Penceresi ------------------
    def _open_advanced_settings(self):
        """Gelişmiş ayarlar ve HuggingFace token penceresi."""
        palette = get_theme_palette(self.current_theme)

        win = ctk.CTkToplevel(self)
        win.title("Gelişmiş Ayarlar")
        win.geometry("450x380")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()

        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 225
        y = self.winfo_y() + (self.winfo_height() // 2) - 190
        win.geometry(f"+{max(0, x)}+{max(0, y)}")

        container = ctk.CTkFrame(win, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=18)

        lbl = ctk.CTkLabel(
            container,
            text="Gelişmiş Yapılandırma",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            text_color=palette["text_main"],
        )
        lbl.pack(anchor="w", pady=(0, 10))

        # HF Token
        lbl_hf = ctk.CTkLabel(
            container,
            text="Hugging Face Token (Pyannote Diarization için):",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=palette["text_muted"],
        )
        lbl_hf.pack(anchor="w", pady=(0, 2))

        entry_hf = ctk.CTkEntry(
            container,
            placeholder_text="hf_xxxxxxxxxxxxxxxxxxxxxx",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            height=32,
            show="*",
        )
        entry_hf.insert(0, self.settings.get("hf_token", ""))
        entry_hf.pack(fill="x", pady=(0, 12))

        # Otomatik Birleştirme Eşiği
        lbl_gap = ctk.CTkLabel(
            container,
            text="Aynı Konuşmacıyı Birleştirme Zaman Eşiği (Saniye):",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=palette["text_muted"],
        )
        lbl_gap.pack(anchor="w", pady=(0, 2))

        entry_gap = ctk.CTkEntry(
            container,
            height=32,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        )
        entry_gap.insert(0, str(self.settings.get("auto_merge_gap", 1.5)))
        entry_gap.pack(fill="x", pady=(0, 14))

        # Sistem Durumu Bilgisi
        sys_box = ctk.CTkFrame(
            container,
            fg_color=palette["input_bg"],
            border_width=1,
            border_color=palette["border_card"],
            corner_radius=6,
        )
        sys_box.pack(fill="x", pady=(0, 16))

        ffmpeg_status = "Mevcut" if find_ffmpeg() else "Bulunamadı"
        info_lines = [
            f"- FFmpeg Durumu: {ffmpeg_status}",
            "- Whisper Hızlandırıcı: CTranslate2 (CPU INT8)",
            f"- Uygulama Sürümü: v{self.APP_VERSION}",
        ]
        lbl_sys = ctk.CTkLabel(
            sys_box,
            text="\n".join(info_lines),
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=palette["text_muted"],
            justify="left",
        )
        lbl_sys.pack(padx=12, pady=10, anchor="w")

        def save_and_close():
            self.settings["hf_token"] = entry_hf.get().strip()
            self.settings["use_pyannote"] = bool(self.settings["hf_token"])
            try:
                self.settings["auto_merge_gap"] = float(entry_gap.get().strip())
            except ValueError:
                self.settings["auto_merge_gap"] = 1.5

            save_settings(self.settings)
            win.destroy()
            ToastNotification.show(self, "Ayarlar kaydedildi", duration_ms=1800)

        btn_save = ctk.CTkButton(
            container,
            text="Kaydet ve Kapat",
            command=save_and_close,
            height=34,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            fg_color=palette["accent_primary"],
            hover_color=palette["accent_hover"],
        )
        btn_save.pack(fill="x")


def run_gui():
    """Uygulamayı başlatır."""
    app = SpeechToTextApp()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
