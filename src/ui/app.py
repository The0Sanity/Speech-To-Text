"""CustomTkinter tabanlı Modern Masaüstü Kullanıcı Arayüzü."""

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
    get_unique_speakers,
    rename_speaker_in_transcript,
)
from src.audio_processor import (
    cleanup_temp_file,
    extract_audio_to_wav,
    find_ffmpeg,
    get_media_info,
)
from src.audio_enhancer import enhance_audio
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
    export_to_srt,
    export_to_txt,
)
from src.transcriber import WhisperTranscriber
from src.ui.components import CardFrame, RenameSpeakerDialog
from src.ui.style import PALETTE, get_speaker_color
from src.youtube_downloader import (
    clean_error_message,
    download_youtube_audio,
    get_youtube_video_info,
    is_valid_youtube_url,
)


class SpeechToTextApp(ctk.CTk):
    """Ana Masaüstü Uygulama Penceresi."""

    def __init__(self):
        super().__init__()

        # Tema ve Pencere Yapılandırması
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.title("Türkçe Ses Tanıma & Konuşmacı Ayrıştırma (STT + Diarization)")
        self.geometry("1100x820")
        self.minsize(950, 700)

        # Durum değişkenleri
        self.settings = load_settings()
        self.selected_file_path: Optional[str] = None
        self.media_info: Optional[Dict[str, Any]] = None
        self.youtube_info: Optional[Dict[str, Any]] = None
        self.transcribed_data: List[Dict[str, Any]] = []
        self.is_processing = False
        self.transcriber: Optional[WhisperTranscriber] = None

        self._build_ui()
        self._check_ffmpeg()

    def _check_ffmpeg(self):
        """FFmpeg kullanılabilirliğini kontrol eder."""
        ffmpeg_bin = find_ffmpeg()
        if not ffmpeg_bin:
            messagebox.showwarning(
                "FFmpeg Uyarısı",
                "Sistemde FFmpeg bulunamadı! Ses dönüştürme işlemi için FFmpeg gereklidir.\n"
                "Lütfen winget ile kurulan FFmpeg'in yolunu kontrol ediniz.",
            )

    def _build_ui(self):
        """Kullanıcı arayüzünü oluşturur."""
        # Ana Konteyner
        self.main_container = ctk.CTkFrame(self, fg_color="#0f1117", corner_radius=0)
        self.main_container.pack(fill="both", expand=True)

        # 1. Üst Başlık ve Durum Çubuğu
        self._build_header(self.main_container)

        # 2. İki Sütunlu Gövde (Sol: Kontroller & Ayarlar, Sağ: Transkript & Çıktı)
        self.body_paned = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.body_paned.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # Sol Panel (380px)
        self.left_panel = ctk.CTkFrame(self.body_paned, width=390, fg_color="transparent")
        self.left_panel.pack(side="left", fill="y", padx=(0, 15))
        self.left_panel.pack_propagate(False)

        self._build_file_picker_card(self.left_panel)
        self._build_settings_card(self.left_panel)
        self._build_action_card(self.left_panel)

        # Sağ Panel (Transkript Alanı)
        self.right_panel = ctk.CTkFrame(self.body_paned, fg_color="transparent")
        self.right_panel.pack(side="right", fill="both", expand=True)

        self._build_transcript_card(self.right_panel)

    def _build_header(self, parent):
        """Üst bilgi ve başlık bölümü."""
        header = ctk.CTkFrame(parent, height=70, fg_color="#161922", corner_radius=0)
        header.pack(fill="x", pady=(0, 15))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", padx=20, pady=12)

        main_title = ctk.CTkLabel(
            title_box,
            text="🎙️ Türkçe Ses Tanıma & Konuşmacı Ayrıştırma",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#f8fafc",
        )
        main_title.pack(anchor="w")

        sub_title = ctk.CTkLabel(
            title_box,
            text="MP4 / MP3 Dosyalarını Türkçe Metne Çevirin • Konuşmacıları Ayrıştırın (X1, X2...)",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
        )
        sub_title.pack(anchor="w")

        # Sağ üst ayarlar butonu
        settings_btn = ctk.CTkButton(
            header,
            text="⚙️ Ayarlar",
            width=100,
            height=32,
            fg_color="#1e293b",
            hover_color="#334155",
            command=self._open_advanced_settings,
        )
        settings_btn.pack(side="right", padx=20, pady=15)

    def _build_file_picker_card(self, parent):
        """Dosya seçimi ve YouTube URL giriş kartı."""
        card = CardFrame(parent)
        card.pack(fill="x", pady=(0, 12), padx=0)

        # Sekmeli Girdi Seçici
        self.input_tabs = ctk.CTkTabview(
            card,
            height=165,
            corner_radius=8,
            fg_color="#131620",
            segmented_button_fg_color="#1e2330",
            segmented_button_selected_color="#2563eb",
            segmented_button_selected_hover_color="#1d4ed8",
        )
        self.input_tabs.pack(fill="both", expand=True, padx=10, pady=(6, 10))

        tab_file = self.input_tabs.add("📁 Yerel Dosya")
        tab_yt = self.input_tabs.add("🔴 YouTube Linki")

        # --- 1. Yerel Dosya Sekmesi ---
        self.select_btn = ctk.CTkButton(
            tab_file,
            text="Dosya Seç (MP4 / MP3 / WAV)",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=36,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self._pick_file,
        )
        self.select_btn.pack(fill="x", pady=(4, 6))

        self.file_info_frame = ctk.CTkFrame(tab_file, fg_color="#0f1118", corner_radius=6)
        self.file_info_frame.pack(fill="x", pady=(0, 2))

        self.lbl_file_name = ctk.CTkLabel(
            self.file_info_frame,
            text="Henüz bir dosya seçilmedi",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#94a3b8",
            anchor="w",
        )
        self.lbl_file_name.pack(fill="x", padx=10, pady=(6, 2))

        self.lbl_file_meta = ctk.CTkLabel(
            self.file_info_frame,
            text="Desteklenen: .mp4, .mp3, .wav, .m4a, .aac, .mkv",
            font=ctk.CTkFont(size=11),
            text_color="#64748b",
            anchor="w",
        )
        self.lbl_file_meta.pack(fill="x", padx=10, pady=(0, 6))

        # --- 2. YouTube Sekmesi ---
        url_box = ctk.CTkFrame(tab_yt, fg_color="transparent")
        url_box.pack(fill="x", pady=(4, 6))

        self.yt_url_entry = ctk.CTkEntry(
            url_box,
            placeholder_text="https://www.youtube.com/watch?v=...",
            height=34,
            font=ctk.CTkFont(size=12),
        )
        self.yt_url_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.yt_url_entry.bind("<Return>", lambda e: self._fetch_youtube_info())

        self.yt_fetch_btn = ctk.CTkButton(
            url_box,
            text="Bilgi Getir",
            width=80,
            height=34,
            fg_color="#334155",
            hover_color="#475569",
            command=self._fetch_youtube_info,
        )
        self.yt_fetch_btn.pack(side="right")

        self.yt_info_frame = ctk.CTkFrame(tab_yt, fg_color="#0f1118", corner_radius=6)
        self.yt_info_frame.pack(fill="x", pady=(0, 2))

        self.lbl_yt_title = ctk.CTkLabel(
            self.yt_info_frame,
            text="YouTube video linki yapıştırın",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#94a3b8",
            anchor="w",
        )
        self.lbl_yt_title.pack(fill="x", padx=10, pady=(6, 2))

        self.lbl_yt_meta = ctk.CTkLabel(
            self.yt_info_frame,
            text="Link girip doğrudan 'Transkripsiyonu Başlat'a basabilirsiniz",
            font=ctk.CTkFont(size=11),
            text_color="#64748b",
            anchor="w",
        )
        self.lbl_yt_meta.pack(fill="x", padx=10, pady=(0, 6))

    def _fetch_youtube_info(self):
        """Girilen YouTube bağlantısının video bilgilerini arka planda çeker."""
        url = self.yt_url_entry.get().strip()
        if not url:
            messagebox.showwarning("Eksik Bağlantı", "Lütfen bir YouTube video linki giriniz!")
            return
        if not is_valid_youtube_url(url):
            messagebox.showwarning(
                "Geçersiz Bağlantı",
                "Lütfen geçerli bir YouTube video linki giriniz!\nÖrnek: https://www.youtube.com/watch?v=...",
            )
            return

        self.yt_fetch_btn.configure(state="disabled", text="Alınıyor...")
        self.lbl_yt_title.configure(text="Video bilgileri alınıyor...", text_color="#f59e0b")

        def fetch_worker():
            try:
                info = get_youtube_video_info(url)
                self.youtube_info = info
                self.after(0, lambda: self._apply_youtube_info(info))
            except Exception as e:
                err_clean = clean_error_message(e)
                self.after(0, lambda msg=err_clean: messagebox.showerror("Hata", f"YouTube bilgileri alınamadı:\n{msg}"))
                self.after(0, lambda: self.lbl_yt_title.configure(text="Bilgiler alınamadı", text_color="#ef4444"))
            finally:
                self.after(0, lambda: self.yt_fetch_btn.configure(state="normal", text="Bilgi Getir"))

        threading.Thread(target=fetch_worker, daemon=True).start()

    def _apply_youtube_info(self, info: Dict[str, Any]):
        """Çekilen YouTube bilgilerini arayüze yansıtır."""
        short_title = info["title"][:38] + "..." if len(info["title"]) > 38 else info["title"]
        self.lbl_yt_title.configure(text=f"🎬 {short_title}", text_color="#38bdf8")
        self.lbl_yt_meta.configure(text=f"Kanal: {info['channel']} • Süre: {info['duration_formatted']}")
        self.lbl_status.configure(text=f"YouTube hazır: {info['title']} ({info['duration_formatted']})")

    def _build_settings_card(self, parent):
        """Model ve konuşmacı yapılandırma kartı."""
        card = CardFrame(parent)
        card.pack(fill="x", pady=(0, 12), padx=0)

        card_title = ctk.CTkLabel(
            card,
            text="⚙️ Tanıma & Ayrıştırma Ayarları",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#e2e8f0",
        )
        card_title.pack(anchor="w", padx=16, pady=(14, 10))

        # 1. Whisper Model Seçimi
        # 1. Whisper Model Seçimi
        lbl_model = ctk.CTkLabel(card, text="Whisper Modeli:", font=ctk.CTkFont(size=12), text_color="#cbd5e1")
        lbl_model.pack(anchor="w", padx=16, pady=(0, 2))

        self.cmb_model = ctk.CTkComboBox(
            card,
            values=[
                "small (Dengeli - Hızlı)",
                "medium (Yüksek Doğruluk)",
                "large-v3-turbo (En Yüksek Türkçe Kalitesi)",
                "base (Hızlı)",
                "tiny (Ultra Hızlı)",
            ],
            font=ctk.CTkFont(size=12),
            height=32,
        )
        self.cmb_model.set("small (Dengeli - Hızlı)")
        self.cmb_model.pack(fill="x", padx=16, pady=(0, 10))

        # 2. Dil Seçimi
        lbl_lang = ctk.CTkLabel(card, text="Konuşma Dili:", font=ctk.CTkFont(size=12), text_color="#cbd5e1")
        lbl_lang.pack(anchor="w", padx=16, pady=(0, 2))

        self.cmb_lang = ctk.CTkComboBox(
            card,
            values=["Türkçe (tr)", "Otomatik Tespit (auto)"],
            font=ctk.CTkFont(size=12),
            height=32,
        )
        self.cmb_lang.set("Türkçe (tr)")
        self.cmb_lang.pack(fill="x", padx=16, pady=(0, 10))

        # 3. Ses Tespiti (VAD) Hassasiyeti
        lbl_vad = ctk.CTkLabel(card, text="Ses Tespiti (VAD) Hassasiyeti:", font=ctk.CTkFont(size=12), text_color="#cbd5e1")
        lbl_vad.pack(anchor="w", padx=16, pady=(0, 2))

        self.cmb_vad = ctk.CTkComboBox(
            card,
            values=["Yüksek (Fısıltı/Hızlı sesleri kaçırmaz)", "Normal (Standart Konuşma)"],
            font=ctk.CTkFont(size=12),
            height=32,
        )
        self.cmb_vad.set("Yüksek (Fısıltı/Hızlı sesleri kaçırmaz)")
        self.cmb_vad.pack(fill="x", padx=16, pady=(0, 10))

        # 4. Konuşmacı Sayısı (Diarization)
        lbl_spk = ctk.CTkLabel(card, text="Konuşmacı Sayısı:", font=ctk.CTkFont(size=12), text_color="#cbd5e1")
        lbl_spk.pack(anchor="w", padx=16, pady=(0, 2))

        self.cmb_spk_count = ctk.CTkComboBox(
            card,
            values=["Otomatik Tespit", "1 Konuşmacı (Tek Kişi)", "2 Konuşmacı (Mülakat/Diyalog)", "3 Konuşmacı", "4 Konuşmacı"],
            font=ctk.CTkFont(size=12),
            height=32,
        )
        self.cmb_spk_count.set("Otomatik Tespit")
        self.cmb_spk_count.pack(fill="x", padx=16, pady=(0, 10))

        # 5. Konuşmacı Ön Eki
        lbl_prefix = ctk.CTkLabel(card, text="Etiket Biçimi:", font=ctk.CTkFont(size=12), text_color="#cbd5e1")
        lbl_prefix.pack(anchor="w", padx=16, pady=(0, 2))

        self.cmb_prefix = ctk.CTkComboBox(
            card,
            values=["X (X1, X2, X3...)", "Konuşmacı (Konuşmacı 1, 2...)", "Kişi (Kişi 1, 2...)"],
            font=ctk.CTkFont(size=12),
            height=32,
        )
        self.cmb_prefix.set("X (X1, X2, X3...)")
        self.cmb_prefix.pack(fill="x", padx=16, pady=(0, 10))

        # 6. Gelişmiş Ses İyileştirme Onay Kutusu
        self.chk_enhance = ctk.CTkCheckBox(
            card,
            text="🎧 Ses Ön-İyileştirme (Gürültü Filtresi & Normalizasyon)",
            font=ctk.CTkFont(size=12),
            fg_color="#38bdf8",
            hover_color="#0284c7",
        )
        self.chk_enhance.select()
        self.chk_enhance.pack(anchor="w", padx=16, pady=(4, 14))

    def _build_action_card(self, parent):
        """İşlemi başlatma, ilerleme çubuğu ve durum kartı."""
        card = CardFrame(parent)
        card.pack(fill="x", pady=(0, 0), padx=0)

        self.btn_start = ctk.CTkButton(
            card,
            text="🚀 Transkripsiyonu Başlat",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            fg_color="#16a34a",
            hover_color="#15803d",
            command=self._start_transcription_thread,
        )
        self.btn_start.pack(fill="x", padx=16, pady=(16, 10))

        self.progress_bar = ctk.CTkProgressBar(card, height=10, fg_color="#1e293b", progress_color="#2563eb")
        self.progress_bar.set(0.0)
        self.progress_bar.pack(fill="x", padx=16, pady=(0, 8))

        self.lbl_status = ctk.CTkLabel(
            card,
            text="Hazır. Bir medya dosyası seçip başlatın.",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8",
            wraplength=340,
            justify="left",
        )
        self.lbl_status.pack(anchor="w", padx=16, pady=(0, 16))

    def _build_transcript_card(self, parent):
        """Transkript görüntüleme ve dışa aktarma alanı."""
        card = CardFrame(parent)
        card.pack(fill="both", expand=True)

        # Kart Üst Barı (Başlık, Filtre, Yeniden Adlandır)
        top_bar = ctk.CTkFrame(card, fg_color="transparent")
        top_bar.pack(fill="x", padx=16, pady=(14, 10))

        lbl_header = ctk.CTkLabel(
            top_bar,
            text="📝 Transkript ve Konuşma Akışı",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#f1f5f9",
        )
        lbl_header.pack(side="left")

        # Konuşmacıyı Yeniden Adlandır Butonu
        self.btn_rename_spk = ctk.CTkButton(
            top_bar,
            text="🏷️ Konuşmacı İsmini Değiştir",
            font=ctk.CTkFont(size=12),
            height=30,
            width=175,
            fg_color="#334155",
            hover_color="#475569",
            command=self._open_rename_dialog,
        )
        self.btn_rename_spk.pack(side="right", padx=(8, 0))

        # Arama kutusu
        self.search_entry = ctk.CTkEntry(
            top_bar,
            placeholder_text="Metin veya konuşmacı ara...",
            width=180,
            height=30,
            font=ctk.CTkFont(size=12),
        )
        self.search_entry.pack(side="right")
        self.search_entry.bind("<KeyRelease>", lambda e: self._filter_transcript())

        # Kaydırılabilir Transkript Listesi Alanı
        self.transcript_scroll = ctk.CTkScrollableFrame(
            card,
            fg_color="#12141c",
            corner_radius=8,
            border_width=1,
            border_color="#1f2430",
        )
        self.transcript_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        # Başlangıç boş durum mesajı
        self.lbl_empty = ctk.CTkLabel(
            self.transcript_scroll,
            text="Transkript henüz oluşturulmadı.\nSol taraftan bir MP4 veya MP3 dosyası seçerek 'Başlat' butonuna tıklayın.",
            font=ctk.CTkFont(size=14),
            text_color="#64748b",
            justify="center",
        )
        self.lbl_empty.pack(expand=True, pady=120)

        # Alt Dışa Aktarma Barı
        export_bar = ctk.CTkFrame(card, fg_color="transparent")
        export_bar.pack(fill="x", padx=16, pady=(0, 14))

        self.lbl_total_turns = ctk.CTkLabel(
            export_bar,
            text="0 konuşma parçası",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
        )
        self.lbl_total_turns.pack(side="left")

        # Dışa aktarma butonları
        btn_open_folder = ctk.CTkButton(
            export_bar,
            text="📂 Çıktı Klasörü",
            height=32,
            width=110,
            fg_color="#1e293b",
            hover_color="#334155",
            command=self._open_output_folder,
        )
        btn_open_folder.pack(side="right", padx=(8, 0))

        btn_copy = ctk.CTkButton(
            export_bar,
            text="📋 Kopyala",
            height=32,
            width=90,
            fg_color="#374151",
            hover_color="#4b5563",
            command=self._copy_to_clipboard,
        )
        btn_copy.pack(side="right", padx=(8, 0))

        btn_export_json = ctk.CTkButton(
            export_bar,
            text="💾 JSON",
            height=32,
            width=75,
            fg_color="#0f766e",
            hover_color="#115e59",
            command=lambda: self._export_result("json"),
        )
        btn_export_json.pack(side="right", padx=(8, 0))

        btn_export_srt = ctk.CTkButton(
            export_bar,
            text="🎬 SRT",
            height=32,
            width=75,
            fg_color="#7c3aed",
            hover_color="#6d28d9",
            command=lambda: self._export_result("srt"),
        )
        btn_export_srt.pack(side="right", padx=(8, 0))

        btn_export_txt = ctk.CTkButton(
            export_bar,
            text="📄 TXT",
            height=32,
            width=75,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=lambda: self._export_result("txt"),
        )
        btn_export_txt.pack(side="right")

    # ------------------ Dosya Seçimi ------------------
    def _pick_file(self):
        """Medya dosyası seçme iletişim penceresi."""
        filetypes = [
            ("Desteklenen Medya Dosyaları", "*.mp4 *.mp3 *.wav *.m4a *.aac *.mkv *.flac *.ogg"),
            ("Video Dosyaları (*.mp4, *.mkv)", "*.mp4 *.mkv"),
            ("Ses Dosyaları (*.mp3, *.wav, *.m4a)", "*.mp3 *.wav *.m4a *.aac *.flac *.ogg"),
            ("Tüm Dosyalar", "*.*"),
        ]
        chosen = filedialog.askopenfilename(
            title="İşlenecek Ses veya Video Dosyasını Seçin",
            filetypes=filetypes,
            initialdir=self.settings.get("last_input_dir", str(BASE_DIR)),
        )
        if chosen:
            self.selected_file_path = chosen
            self.settings["last_input_dir"] = str(Path(chosen).parent)
            save_settings(self.settings)

            # Bilgileri al
            try:
                self.media_info = get_media_info(chosen)
                self.lbl_file_name.configure(
                    text=f"📄 {self.media_info['file_name']}",
                    text_color="#38bdf8",
                )
                self.lbl_file_meta.configure(
                    text=f"Süre: {self.media_info['duration_formatted']} • Boyut: {self.media_info['file_size_mb']} MB",
                )
                self.lbl_status.configure(
                    text=f"Dosya hazır: {self.media_info['file_name']} ({self.media_info['duration_formatted']})",
                    text_color="#94a3b8",
                )
            except Exception as e:
                self.lbl_file_name.configure(text=f"📄 {Path(chosen).name}", text_color="#38bdf8")
                self.lbl_file_meta.configure(text="Medya detayları alınamadı")

    # ------------------ Transkripsiyon Başlatma (Thread) ------------------
    def _start_transcription_thread(self):
        """İşlemi arka plan iş parçacığında başlatır."""
        active_tab = self.input_tabs.get()
        is_youtube = "youtube" in active_tab.lower()

        if is_youtube:
            url = self.yt_url_entry.get().strip()
            if not url:
                messagebox.showwarning("URL Eksik", "Lütfen bir YouTube video bağlantısı giriniz!")
                return
            if not is_valid_youtube_url(url):
                messagebox.showwarning("Geçersiz URL", "Lütfen geçerli bir YouTube video bağlantısı giriniz!")
                return
        else:
            if not self.selected_file_path:
                messagebox.showwarning("Dosya Eksik", "Lütfen önce işlenecek bir MP4 veya MP3 dosyası seçiniz!")
                return

        if self.is_processing:
            return

        self.is_processing = True
        self.btn_start.configure(state="disabled", text="⏳ İşleniyor...")
        self.select_btn.configure(state="disabled")
        self.yt_fetch_btn.configure(state="disabled")

        # İş parçacığı başlat
        worker = threading.Thread(target=self._run_transcription_pipeline, daemon=True)
        worker.start()

    def _run_transcription_pipeline(self):
        """Tüm dönüştürme, transkripsiyon, diarization ve hizalama adımlarını sırayla icra eder."""
        temp_wav: Optional[str] = None
        enhanced_wav: Optional[str] = None
        try:
            active_tab = self.input_tabs.get()
            is_youtube = "youtube" in active_tab.lower()

            if is_youtube:
                url = self.yt_url_entry.get().strip()
                self._update_progress(0.02, "0/4: YouTube'dan ses akışı indiriliyor (yt-dlp)...")

                def yt_dl_hook(pct, msg):
                    self._update_progress(pct * 0.12, f"0/4: {msg}")

                temp_wav, yt_meta = download_youtube_audio(url, progress_callback=yt_dl_hook)
                self.media_info = yt_meta
                self.selected_file_path = temp_wav
                total_dur = yt_meta.get("duration_seconds", 0.0)
            else:
                # 1. Ses Çıkarma / Dönüştürme (16kHz Mono WAV)
                self._update_progress(0.05, "1/4: Ses dosyası 16kHz WAV formatına dönüştürülüyor (FFmpeg)...")
                temp_wav = extract_audio_to_wav(self.selected_file_path)
                total_dur = self.media_info.get("duration_seconds", 0.0) if self.media_info else 0.0

            # 1.5. Ses Ön-İyileştirme (Gürültü temizleme, 80Hz filtre, normalizasyon)
            audio_for_stt = temp_wav
            should_enhance = hasattr(self, "chk_enhance") and self.chk_enhance.get()
            if should_enhance:
                try:
                    import uuid
                    enhanced_wav = str(TEMP_DIR / f"enhanced_{uuid.uuid4().hex[:8]}.wav")
                    self._update_progress(0.10, "1.5/4: Ses ön-iyileştirme (Gürültü bastırma & seviye dengeleme)...")
                    enhance_audio(temp_wav, enhanced_wav)
                    audio_for_stt = enhanced_wav
                except Exception as enh_err:
                    print(f"Ses iyileştirme atlandı: {enh_err}")
                    audio_for_stt = temp_wav

            # 2. Whisper Model Seçimi & Türkçe STT
            model_key = self.cmb_model.get().split()[0].lower()
            lang_choice = "tr" if "tr" in self.cmb_lang.get().lower() else "auto"

            vad_choice = "high"
            if hasattr(self, "cmb_vad"):
                vad_choice = "high" if "yüksek" in self.cmb_vad.get().lower() else "normal"

            self._update_progress(0.15, f"2/4: Türkçe Whisper '{model_key}' modeli hazırlanıyor...")
            transcriber = WhisperTranscriber(model_size=model_key, cpu_threads=4)

            def whisper_progress(pct, msg, seg):
                self._update_progress(pct, f"2/4: {msg}")

            stt_segments = transcriber.transcribe(
                audio_path=audio_for_stt,
                language=lang_choice,
                total_duration=total_dur,
                vad_sensitivity=vad_choice,
                apply_postprocessing=True,
                progress_callback=whisper_progress,
            )

            if not stt_segments:
                self._update_progress(1.0, "Ses dosyasında herhangi bir konuşma algılanamadı.")
                self.after(0, self._render_transcript, [])
                return

            # 3. Konuşmacı Ayrıştırma (Diarization)
            self._update_progress(0.76, "3/4: Konuşmacılar ayrıştırılıyor (X1, X2 etiketleri)...")

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
                self._update_progress(pct, f"3/4: {msg}")

            diar_intervals = diarizer.diarize(
                audio_path=audio_for_stt,
                speech_segments=stt_segments,
                num_speakers=num_spk,
                progress_callback=diarizer_progress,
            )

            # 4. Hizalama ve Birleştirme
            self._update_progress(0.92, "4/4: Metin ve konuşmacı aralıkları hizalanıyor...")
            aligned_transcript = align_transcription_and_diarization(
                transcription_segments=stt_segments,
                diarization_intervals=diar_intervals,
                speaker_prefix=prefix_val,
                auto_merge_gap=self.settings.get("auto_merge_gap", 1.5),
            )

            self.transcribed_data = aligned_transcript

            # Otomatik çıktı kaydet
            self._auto_save_outputs(aligned_transcript)

            self._update_progress(1.0, f"✅ Tamamlandı! {len(aligned_transcript)} konuşma segmenti oluşturuldu.")
            self.after(0, self._render_transcript, aligned_transcript)

        except Exception as e:
            self._update_progress(0.0, f"❌ Hata oluştu: {str(e)}")
            self.after(0, lambda: messagebox.showerror("İşlem Hatası", f"İşlem sırasında bir hata meydana geldi:\n{str(e)}"))
        finally:
            if temp_wav:
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
        self.btn_start.configure(state="normal", text="🚀 Transkripsiyonu Başlat")
        self.select_btn.configure(state="normal")
        self.yt_fetch_btn.configure(state="normal")

    # ------------------ Transkript Çizimi & UI Listesi ------------------
    def _render_transcript(self, transcript_items: List[Dict[str, Any]]):
        """Transkript parçalarını sağ taraftaki kaydırılabilir alanda şık kartlar olarak listeler."""
        # Mevcut widget'ları temizle
        for widget in self.transcript_scroll.winfo_children():
            widget.destroy()

        if not transcript_items:
            self.lbl_empty = ctk.CTkLabel(
                self.transcript_scroll,
                text="Görüntülenecek transkript metni bulunamadı.",
                font=ctk.CTkFont(size=14),
                text_color="#64748b",
            )
            self.lbl_empty.pack(expand=True, pady=120)
            self.lbl_total_turns.configure(text="0 konuşma parçası")
            return

        self.lbl_total_turns.configure(text=f"{len(transcript_items)} konuşma parçası")

        for idx, item in enumerate(transcript_items):
            spk = item.get("speaker", "X1")
            ts = item.get("timestamp_display", f"[{item.get('start', 0):.1f}s - {item.get('end', 0):.1f}s]")
            text = item.get("text", "")

            # Tekil konuşma kartı
            item_frame = ctk.CTkFrame(
                self.transcript_scroll,
                fg_color="#181b24",
                corner_radius=8,
                border_width=1,
                border_color="#242938",
            )
            item_frame.pack(fill="x", pady=4, padx=4)

            # Kart Başlığı (Konuşmacı Rozeti + Zaman Damgası)
            header_row = ctk.CTkFrame(item_frame, fg_color="transparent")
            header_row.pack(fill="x", padx=10, pady=(8, 4))

            # Renkli konuşmacı rozeti
            bg_col, fg_col = get_speaker_color(spk)
            spk_badge = ctk.CTkLabel(
                header_row,
                text=f" {spk} ",
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=bg_col,
                text_color=fg_col,
                corner_radius=6,
            )
            spk_badge.pack(side="left")

            # Zaman damgası etiketi
            ts_label = ctk.CTkLabel(
                header_row,
                text=f"  {ts}",
                font=ctk.CTkFont(size=11),
                text_color="#94a3b8",
            )
            ts_label.pack(side="left")

            # Düzenlenebilir Metin Kutusu
            text_box = ctk.CTkTextbox(
                item_frame,
                font=ctk.CTkFont(size=13),
                fg_color="#12141c",
                text_color="#f1f5f9",
                height=56,
                wrap="word",
                corner_radius=6,
            )
            text_box.insert("1.0", text)
            text_box.pack(fill="x", padx=10, pady=(0, 8))

            # Kullanıcı metni doğrudan düzenlerse veriyi güncelle
            def make_listener(item_ref, txt_box):
                def on_edit(event=None):
                    item_ref["text"] = txt_box.get("1.0", "end-1c").strip()
                return on_edit

            text_box.bind("<KeyRelease>", make_listener(item, text_box))

    def _filter_transcript(self):
        """Arama kutusuna yazılan kelimeye göre filtreler."""
        query = self.search_entry.get().strip().lower()
        if not query:
            self._render_transcript(self.transcribed_data)
            return

        filtered = [
            item for item in self.transcribed_data
            if query in item.get("text", "").lower() or query in item.get("speaker", "").lower()
        ]
        self._render_transcript(filtered)

    # ------------------ Konuşmacı Yeniden Adlandırma ------------------
    def _open_rename_dialog(self):
        """Konuşmacı adını topluca değiştirme penceresini açar."""
        if not self.transcribed_data:
            messagebox.showinfo("Bilgi", "Henüz işlenmiş bir transkript bulunmuyor.")
            return

        speakers = get_unique_speakers(self.transcribed_data)
        if not speakers:
            messagebox.showinfo("Bilgi", "Değiştirilecek konuşmacı etiketi bulunamadı.")
            return

        # Seçim penceresi
        dialog = ctk.CTkToplevel(self)
        dialog.title("Konuşmacı Seçin")
        dialog.geometry("320x240")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        lbl = ctk.CTkLabel(dialog, text="Hangi konuşmacıyı değiştirmek istiyorsunuz?", font=ctk.CTkFont(size=13, weight="bold"))
        lbl.pack(padx=16, pady=(20, 10))

        cmb = ctk.CTkComboBox(dialog, values=speakers, height=34)
        cmb.pack(fill="x", padx=20, pady=(0, 15))

        def proceed():
            target_spk = cmb.get()
            dialog.destroy()
            RenameSpeakerDialog(self, target_spk, self._apply_speaker_rename)

        btn = ctk.CTkButton(dialog, text="Devam Et", command=proceed, height=34, fg_color="#2563eb")
        btn.pack(fill="x", padx=20)

    def _apply_speaker_rename(self, old_name: str, new_name: str):
        """Tüm transkriptte eski konuşmacı ismini yenisiyle günceller."""
        self.transcribed_data = rename_speaker_in_transcript(self.transcribed_data, old_name, new_name)
        self._render_transcript(self.transcribed_data)
        messagebox.showinfo("Başarılı", f"Tüm '{old_name}' etiketleri '{new_name}' olarak güncellendi.")

    # ------------------ Dışa Aktarma ------------------
    def _auto_save_outputs(self, transcript: List[Dict[str, Any]]):
        """Transkripti outputs/ klasörüne otomatik olarak kaydeder."""
        if not self.selected_file_path or not transcript:
            return

        base_name = Path(self.selected_file_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"{base_name}_{timestamp}"

        txt_path = str(OUTPUTS_DIR / f"{prefix}.txt")
        srt_path = str(OUTPUTS_DIR / f"{prefix}.srt")
        json_path = str(OUTPUTS_DIR / f"{prefix}.json")

        export_to_txt(transcript, txt_path, self.media_info)
        export_to_srt(transcript, srt_path, include_speaker=True)
        export_to_json(transcript, json_path, self.media_info)

    def _export_result(self, fmt: str):
        """Kullanıcının belirleyeceği bir konuma dışa aktarma yapar."""
        if not self.transcribed_data:
            messagebox.showinfo("Bilgi", "Dışa aktarılacak transkript verisi bulunmuyor.")
            return

        base_name = Path(self.selected_file_path).stem if self.selected_file_path else "transkript"
        ext_map = {"txt": "Metin Dosyası (*.txt)", "srt": "Altyazı Dosyası (*.srt)", "json": "JSON Dosyası (*.json)"}

        save_path = filedialog.asksaveasfilename(
            title=f"{fmt.upper()} Formatında Kaydet",
            initialfile=f"{base_name}_transkript.{fmt}",
            filetypes=[(ext_map[fmt], f"*.{fmt}")],
            initialdir=self.settings.get("last_output_dir", str(OUTPUTS_DIR)),
        )

        if not save_path:
            return

        if fmt == "txt":
            export_to_txt(self.transcribed_data, save_path, self.media_info)
        elif fmt == "srt":
            export_to_srt(self.transcribed_data, save_path)
        elif fmt == "json":
            export_to_json(self.transcribed_data, save_path, self.media_info)

        messagebox.showinfo("Başarılı", f"Dosya başarıyla kaydedildi:\n{save_path}")

    def _copy_to_clipboard(self):
        """Transkripti panoya kopyalar."""
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
        messagebox.showinfo("Kopyalandı", "Transkript başarıyla panoya kopyalandı!")

    def _open_output_folder(self):
        """Çıktı klasörünü Windows Gezgini'nde açar."""
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        os.startfile(str(OUTPUTS_DIR))

    # ------------------ Gelişmiş Ayarlar Penceresi ------------------
    def _open_advanced_settings(self):
        """Gelişmiş ayarlar ve HuggingFace token penceresi."""
        win = ctk.CTkToplevel(self)
        win.title("Gelişmiş Ayarlar")
        win.geometry("450x320")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()

        container = ctk.CTkFrame(win, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        lbl = ctk.CTkLabel(container, text="⚙️ Gelişmiş Ayarlar", font=ctk.CTkFont(size=16, weight="bold"))
        lbl.pack(anchor="w", pady=(0, 10))

        # HF Token
        lbl_hf = ctk.CTkLabel(
            container,
            text="Hugging Face Token (Pyannote için opsiyonel):",
            font=ctk.CTkFont(size=12),
        )
        lbl_hf.pack(anchor="w", pady=(0, 2))

        entry_hf = ctk.CTkEntry(
            container,
            placeholder_text="hf_xxxxxxxxxxxxxxxxxxxxxx",
            font=ctk.CTkFont(size=12),
            height=34,
            show="*",
        )
        entry_hf.insert(0, self.settings.get("hf_token", ""))
        entry_hf.pack(fill="x", pady=(0, 12))

        # Birleştirme Eşiği
        lbl_gap = ctk.CTkLabel(
            container,
            text="Aynı Konuşmacıyı Birleştirme Zaman Eşiği (Saniye):",
            font=ctk.CTkFont(size=12),
        )
        lbl_gap.pack(anchor="w", pady=(0, 2))

        entry_gap = ctk.CTkEntry(container, height=34, font=ctk.CTkFont(size=12))
        entry_gap.insert(0, str(self.settings.get("auto_merge_gap", 1.5)))
        entry_gap.pack(fill="x", pady=(0, 20))

        def save_and_close():
            self.settings["hf_token"] = entry_hf.get().strip()
            self.settings["use_pyannote"] = bool(self.settings["hf_token"])
            try:
                self.settings["auto_merge_gap"] = float(entry_gap.get().strip())
            except ValueError:
                self.settings["auto_merge_gap"] = 1.5

            save_settings(self.settings)
            win.destroy()
            messagebox.showinfo("Ayarlar", "Ayarlar başarıyla kaydedildi.")

        btn_save = ctk.CTkButton(container, text="Kaydet", command=save_and_close, height=36, fg_color="#2563eb")
        btn_save.pack(fill="x")


def run_gui():
    """Uygulamayı başlatır."""
    app = SpeechToTextApp()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
