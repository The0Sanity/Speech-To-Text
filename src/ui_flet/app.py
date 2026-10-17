"""Flet tabanlı Windows 11 Fluent Ses Tanıma ve Konuşmacı Ayrıştırma Masaüstü Uygulaması."""

import os
import sys
import threading
import time
from typing import Any, Dict, List, Optional
import flet as ft

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
from src.ui_flet.components import (
    AudioPlayerBar,
    MetricCard,
    ProcessStepper,
    TranscriptTurnCard,
)
from src.ui_flet.theme import (
    ACCENT_HOVER,
    ACCENT_LIGHT,
    ACCENT_PRIMARY,
    BG_APP,
    BG_CARD,
    BG_CARD_SECONDARY,
    BORDER_CARD,
    BTN_NEUTRAL,
    BTN_NEUTRAL_HOVER,
    DANGER,
    INPUT_BG,
    INPUT_BORDER,
    SUCCESS,
    TEXT_MAIN,
    TEXT_MUTED,
    TEXT_SUBTLE,
    WARNING,
)
from src.youtube_downloader import (
    clean_error_message,
    download_youtube_audio,
    get_youtube_video_info,
    is_valid_youtube_url,
)


class FletSpeechToTextApp:
    """Flet tabanlı sade ve minimalist masaüstü ses tanıma uygulaması."""

    APP_VERSION = "2.0"

    def __init__(self, page: Optional[ft.Page] = None):
        self.page = page
        self.settings = load_settings()

        # Durum Değişkenleri
        self.selected_file_path: Optional[str] = None
        self.active_wav_path: Optional[str] = None
        self.media_info: Optional[Dict[str, Any]] = None
        self.youtube_info: Optional[Dict[str, Any]] = None
        self.transcribed_data: List[Dict[str, Any]] = []
        self.is_processing = False
        self.cancel_requested = False
        self.current_input_mode = "file"  # "file" veya "youtube"

        self._init_controls()

    def _safe_update(self, control: Optional[ft.Control] = None):
        """Hata vermeden güvenli UI güncellemesi."""
        try:
            if control:
                control.update()
            elif self.page:
                self.page.update()
        except Exception:
            pass

    def _init_controls(self):
        """Tüm arayüz kontrollerini başlatır."""
        # 1. Sol Panel: Model ve Ayrıştırma Açılır Menüleri (Dropdown - Salt Okunur / Sadece Tıklanabilir)
        self.cmb_model = ft.Dropdown(
            options=[
                ft.dropdown.Option("small (Dengeli)"),
                ft.dropdown.Option("medium (Yüksek Doğruluk)"),
                ft.dropdown.Option("large-v3-turbo (En Yüksek Kalite)"),
                ft.dropdown.Option("base (Hızlı)"),
                ft.dropdown.Option("tiny (Ultra Hızlı)"),
            ],
            value="small (Dengeli)",
            height=36,
            bgcolor=INPUT_BG,
            border_color=INPUT_BORDER,
            color=TEXT_MAIN,
            text_size=12,
            content_padding=ft.Padding.symmetric(horizontal=10),
        )

        self.cmb_lang = ft.Dropdown(
            options=[
                ft.dropdown.Option("Türkçe (tr)"),
                ft.dropdown.Option("Otomatik (auto)"),
            ],
            value="Türkçe (tr)",
            height=36,
            bgcolor=INPUT_BG,
            border_color=INPUT_BORDER,
            color=TEXT_MAIN,
            text_size=12,
            content_padding=ft.Padding.symmetric(horizontal=10),
            expand=True,
        )

        self.cmb_vad = ft.Dropdown(
            options=[
                ft.dropdown.Option("Yüksek (Hassas)"),
                ft.dropdown.Option("Normal (Standart)"),
            ],
            value="Yüksek (Hassas)",
            height=36,
            bgcolor=INPUT_BG,
            border_color=INPUT_BORDER,
            color=TEXT_MAIN,
            text_size=12,
            content_padding=ft.Padding.symmetric(horizontal=10),
            expand=True,
        )

        self.cmb_spk_count = ft.Dropdown(
            options=[
                ft.dropdown.Option("Otomatik Tespit"),
                ft.dropdown.Option("1 Konuşmacı"),
                ft.dropdown.Option("2 Konuşmacı"),
                ft.dropdown.Option("3 Konuşmacı"),
                ft.dropdown.Option("4 Konuşmacı"),
            ],
            value="Otomatik Tespit",
            height=36,
            bgcolor=INPUT_BG,
            border_color=INPUT_BORDER,
            color=TEXT_MAIN,
            text_size=12,
            content_padding=ft.Padding.symmetric(horizontal=10),
            expand=True,
        )

        self.cmb_prefix = ft.Dropdown(
            options=[
                ft.dropdown.Option("X (X1, X2...)"),
                ft.dropdown.Option("Konuşmacı (1, 2...)"),
                ft.dropdown.Option("Kişi (1, 2...)"),
            ],
            value="X (X1, X2...)",
            height=36,
            bgcolor=INPUT_BG,
            border_color=INPUT_BORDER,
            color=TEXT_MAIN,
            text_size=12,
            content_padding=ft.Padding.symmetric(horizontal=10),
            expand=True,
        )

        self.chk_enhance = ft.Checkbox(
            label="Ses Ön-İyileştirme (80Hz gürültü kesici & dengeleme)",
            value=True,
            check_color=TEXT_MAIN,
            active_color=ACCENT_PRIMARY,
            label_style=ft.TextStyle(size=11, color=TEXT_MUTED),
        )

        # Dosya ve YouTube Girişleri
        self.file_picker = ft.FilePicker(on_result=self._on_file_picked)
        self.lbl_file_name = ft.Text(value="Dosya seçilmedi", size=11, weight=ft.FontWeight.BOLD, color=TEXT_MUTED)
        self.lbl_file_meta = ft.Text(
            value="Desteklenen: .mp4, .mp3, .wav, .m4a, .aac, .mkv, .flac",
            size=10,
            color=TEXT_SUBTLE,
        )

        self.yt_url_entry = ft.TextField(
            hint_text="https://www.youtube.com/watch?v=...",
            height=34,
            text_size=11,
            bgcolor=INPUT_BG,
            border_color=INPUT_BORDER,
            color=TEXT_MAIN,
            expand=True,
            content_padding=ft.Padding.symmetric(horizontal=10),
            on_submit=lambda _: self._fetch_youtube_info(),
        )
        self.lbl_yt_title = ft.Text(value="YouTube bağlantısı giriniz", size=11, weight=ft.FontWeight.BOLD, color=TEXT_MUTED)
        self.lbl_yt_meta = ft.Text(
            value="Link girildikten sonra doğrudan başlatabilirsiniz",
            size=10,
            color=TEXT_SUBTLE,
        )

        # Giriş Bölümü Değiştirici Butonları
        self.btn_tab_file = ft.FilledButton("Yerel Dosya", bgcolor=ACCENT_PRIMARY, color=TEXT_MAIN, height=30, on_click=lambda _: self._switch_input_mode("file"))
        self.btn_tab_yt = ft.Button("YouTube", bgcolor=BTN_NEUTRAL, color=TEXT_MAIN, height=30, on_click=lambda _: self._switch_input_mode("youtube"))

        self.box_file_input = ft.Container(
            content=ft.Column(
                controls=[
                    ft.FilledButton(
                        "Dosya Seç (MP4 / MP3 / WAV)",
                        bgcolor=ACCENT_PRIMARY,
                        color=TEXT_MAIN,
                        height=34,
                        on_click=lambda _: self.file_picker.pick_files(
                            allow_multiple=False,
                            allowed_extensions=["mp4", "mp3", "wav", "m4a", "aac", "mkv", "flac"],
                        ),
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[self.lbl_file_name, self.lbl_file_meta],
                            spacing=2,
                        ),
                        bgcolor=INPUT_BG,
                        border_radius=4,
                        padding=ft.Padding.all(8),
                    ),
                ],
                spacing=8,
            ),
            visible=True,
        )

        self.box_yt_input = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            self.yt_url_entry,
                            ft.Button(
                                "Bilgi Al",
                                bgcolor=BTN_NEUTRAL,
                                color=TEXT_MAIN,
                                height=34,
                                on_click=lambda _: self._fetch_youtube_info(),
                            ),
                        ],
                        spacing=6,
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[self.lbl_yt_title, self.lbl_yt_meta],
                            spacing=2,
                        ),
                        bgcolor=INPUT_BG,
                        border_radius=4,
                        padding=ft.Padding.all(8),
                    ),
                ],
                spacing=8,
            ),
            visible=False,
        )

        # Ses Oynatıcı Önizleme Çubuğu
        self.audio_player = AudioPlayerBar()

        # İlerleme Göstergeleri ve Eylemler
        self.stepper = ProcessStepper()
        self.progress_bar = ft.ProgressBar(value=0.0, bgcolor=INPUT_BG, color=ACCENT_PRIMARY, height=4)
        self.lbl_status = ft.Text(
            value="Hazır. Medya dosyası veya bağlantı seçerek başlayın.",
            size=11,
            color=TEXT_MUTED,
        )

        self.btn_start = ft.FilledButton(
            "Transkripsiyonu Başlat",
            bgcolor=ACCENT_PRIMARY,
            color=TEXT_MAIN,
            height=38,
            on_click=lambda _: self.start_transcription(),
        )

        self.btn_cancel = ft.OutlinedButton(
            "İptal",
            height=38,
            width=70,
            disabled=True,
            on_click=lambda _: self.request_cancel(),
        )

        # 2. Sağ Panel: İstatistik Kartları (Metrics Ribbon)
        self.badge_duration = MetricCard(title="Süre", value="00:00")
        self.badge_speakers = MetricCard(title="Konuşmacı", value="0 Kişi")
        self.badge_words = MetricCard(title="Kelime", value="0 Kelime")
        self.badge_wpm = MetricCard(title="Hız", value="0 WPM")

        # Canlı Arama ve Bul & Değiştir
        self.search_entry = ft.TextField(
            hint_text="Transkriptte ara (metin, konuşmacı veya zaman)...",
            height=32,
            text_size=11,
            bgcolor=INPUT_BG,
            border_color=INPUT_BORDER,
            color=TEXT_MAIN,
            expand=True,
            content_padding=ft.Padding.symmetric(horizontal=10),
            on_change=lambda e: self.filter_transcript(e.control.value),
        )
        self.lbl_search_count = ft.Text(value="", size=11, color=ACCENT_LIGHT)

        self.entry_find = ft.TextField(
            hint_text="Aranan kelime...",
            width=140,
            height=30,
            text_size=11,
            bgcolor=INPUT_BG,
            border_color=INPUT_BORDER,
            color=TEXT_MAIN,
            content_padding=ft.Padding.symmetric(horizontal=8),
        )
        self.entry_replace = ft.TextField(
            hint_text="Yeni kelime...",
            width=140,
            height=30,
            text_size=11,
            bgcolor=INPUT_BG,
            border_color=INPUT_BORDER,
            color=TEXT_MAIN,
            content_padding=ft.Padding.symmetric(horizontal=8),
        )

        self.find_replace_container = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(value="Değiştir:", size=11, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                    self.entry_find,
                    self.entry_replace,
                    ft.FilledButton(
                        "Tümünü Değiştir",
                        bgcolor=ACCENT_PRIMARY,
                        color=TEXT_MAIN,
                        height=30,
                        on_click=lambda _: self.execute_find_replace(),
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            visible=False,
            bgcolor=INPUT_BG,
            border=ft.Border.all(1, INPUT_BORDER),
            border_radius=6,
            padding=ft.Padding.all(8),
            margin=ft.Margin.only(bottom=8),
        )

        # Transkript Kaydırılabilir Listesi
        self.transcript_list = ft.ListView(
            expand=True,
            spacing=4,
            padding=ft.Padding.all(10),
            auto_scroll=False,
        )

        # Dışa Aktarma Çubuğu
        self.lbl_total_turns = ft.Text(value="0 konuşma parçası", size=11, color=TEXT_MUTED)

    def _switch_input_mode(self, mode: str):
        """Yerel dosya ve YouTube sekmesi arasında geçiş yapar."""
        self.current_input_mode = mode
        if mode == "file":
            self.btn_tab_file.bgcolor = ACCENT_PRIMARY
            self.btn_tab_yt.bgcolor = BTN_NEUTRAL
            self.box_file_input.visible = True
            self.box_yt_input.visible = False
        else:
            self.btn_tab_file.bgcolor = BTN_NEUTRAL
            self.btn_tab_yt.bgcolor = ACCENT_PRIMARY
            self.box_file_input.visible = False
            self.box_yt_input.visible = True

        self._safe_update(self.btn_tab_file)
        self._safe_update(self.btn_tab_yt)
        self._safe_update(self.box_file_input)
        self._safe_update(self.box_yt_input)

    def build_layout(self) -> ft.Control:
        """Tam arayüz düzenini oluşturur."""
        # Sol Panel (350px)
        # Kart 1: Medya Girişi
        media_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(controls=[self.btn_tab_file, self.btn_tab_yt], spacing=6),
                    self.box_file_input,
                    self.box_yt_input,
                    self.audio_player,
                ],
                spacing=8,
            ),
            bgcolor=BG_CARD,
            border=ft.Border.all(1, BORDER_CARD),
            border_radius=8,
            padding=ft.Padding.all(12),
        )

        # Kart 2: Model ve Ayarlar
        settings_card = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(value="Model ve Ayrıştırma Ayarları", size=13, weight=ft.FontWeight.BOLD, color=TEXT_MAIN),
                    ft.Text(value="Whisper Modeli:", size=10, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                    self.cmb_model,
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(value="Dil:", size=10, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                                    self.cmb_lang,
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(value="Ses Tespiti (VAD):", size=10, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                                    self.cmb_vad,
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text(value="Konuşmacı Sayısı:", size=10, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                                    self.cmb_spk_count,
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(value="Etiket Formatı:", size=10, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                                    self.cmb_prefix,
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=8,
                    ),
                    self.chk_enhance,
                ],
                spacing=8,
            ),
            bgcolor=BG_CARD,
            border=ft.Border.all(1, BORDER_CARD),
            border_radius=8,
            padding=ft.Padding.all(12),
        )

        # Kart 3: Eylemler & Durum
        action_card = ft.Container(
            content=ft.Column(
                controls=[
                    self.stepper,
                    ft.Row(
                        controls=[
                            ft.Container(content=self.btn_start, expand=True),
                            self.btn_cancel,
                        ],
                        spacing=8,
                    ),
                    self.progress_bar,
                    self.lbl_status,
                ],
                spacing=8,
            ),
            bgcolor=BG_CARD,
            border=ft.Border.all(1, BORDER_CARD),
            border_radius=8,
            padding=ft.Padding.all(12),
        )

        left_column = ft.Container(
            content=ft.Column(
                controls=[media_card, settings_card, action_card],
                spacing=10,
                scroll=ft.ScrollMode.ADAPTIVE,
            ),
            width=350,
        )

        # Sağ Panel: Transkript, Düzenleme ve Dışa Aktarma
        stats_ribbon_row = ft.Row(
            controls=[
                self.badge_duration,
                self.badge_speakers,
                self.badge_words,
                self.badge_wpm,
            ],
            spacing=8,
        )

        search_toolbar = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text(value="Ara:", size=11, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                            self.search_entry,
                            self.lbl_search_count,
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=INPUT_BG,
                    border=ft.Border.all(1, INPUT_BORDER),
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                    expand=True,
                ),
                ft.Button(
                    "Bul ve Değiştir",
                    bgcolor=BTN_NEUTRAL,
                    color=TEXT_MAIN,
                    height=34,
                    on_click=lambda _: self._toggle_find_replace(),
                ),
                ft.Button(
                    "Konuşmacı Yönetimi",
                    bgcolor=BTN_NEUTRAL,
                    color=TEXT_MAIN,
                    height=34,
                    on_click=lambda _: self.open_speaker_manager(),
                ),
            ],
            spacing=8,
        )

        export_row = ft.Row(
            controls=[
                self.lbl_total_turns,
                ft.Container(expand=True),
                ft.FilledButton(
                    "Panoya Kopyala",
                    bgcolor=ACCENT_PRIMARY,
                    color=TEXT_MAIN,
                    height=28,
                    on_click=lambda _: self.copy_to_clipboard(),
                ),
                *[
                    ft.Button(
                        fmt.upper(),
                        bgcolor=BTN_NEUTRAL,
                        color=TEXT_MAIN,
                        height=28,
                        width=52,
                        on_click=lambda _, f=fmt: self.export_result(f),
                    )
                    for fmt in ["md", "vtt", "csv", "json", "srt", "txt"]
                ],
            ],
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        right_column = ft.Container(
            content=ft.Column(
                controls=[
                    stats_ribbon_row,
                    search_toolbar,
                    self.find_replace_container,
                    ft.Container(
                        content=self.transcript_list,
                        bgcolor=INPUT_BG,
                        border=ft.Border.all(1, BORDER_CARD),
                        border_radius=6,
                        expand=True,
                    ),
                    export_row,
                ],
                spacing=8,
                expand=True,
            ),
            bgcolor=BG_CARD,
            border=ft.Border.all(1, BORDER_CARD),
            border_radius=8,
            padding=ft.Padding.all(14),
            expand=True,
        )

        # Üst Başlık
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        value="SesMetin Pro",
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT_MAIN,
                    ),
                    ft.Text(
                        value="| Türkçe Ses Tanıma ve Konuşmacı Ayrıştırma İstasyonu",
                        size=12,
                        color=TEXT_SUBTLE,
                    ),
                    ft.Container(expand=True),
                    ft.Text(
                        value=f"v{self.APP_VERSION}",
                        size=11,
                        color=ACCENT_LIGHT,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=BG_CARD,
            border=ft.Border.all(1, BORDER_CARD),
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    header,
                    ft.Row(
                        controls=[left_column, right_column],
                        spacing=12,
                        expand=True,
                    ),
                ],
                spacing=10,
                expand=True,
            ),
            bgcolor=BG_APP,
            padding=ft.Padding.all(14),
            expand=True,
        )

    # ------------------ Dosya ve YouTube Olayları ------------------
    def _on_file_picked(self, e: ft.FilePickerResultEvent):
        """Kullanıcı dosya seçtiğinde tetiklenir."""
        if not e.files or len(e.files) == 0:
            return

        file_path = e.files[0].path
        self.selected_file_path = file_path
        self.active_wav_path = None
        self.media_info = None

        file_name = os.path.basename(file_path)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

        self.lbl_file_name.value = file_name
        self.lbl_file_meta.value = f"Boyut: {file_size_mb:.1f} MB | Yol: {file_path}"
        self.lbl_status.value = f"Hazır: {file_name} seçildi."
        self.audio_player.set_audio_source(None)

        self._safe_update(self.lbl_file_name)
        self._safe_update(self.lbl_file_meta)
        self._safe_update(self.lbl_status)

    def _fetch_youtube_info(self):
        """YouTube video bilgilerini çeker."""
        url = self.yt_url_entry.value.strip() if self.yt_url_entry.value else ""
        if not url:
            self._show_toast("Lütfen geçerli bir YouTube URL'si giriniz.", is_error=True)
            return

        if not is_valid_youtube_url(url):
            self._show_toast("Geçersiz YouTube bağlantısı!", is_error=True)
            return

        self.lbl_yt_title.value = "Video bilgileri alınıyor..."
        self._safe_update(self.lbl_yt_title)

        def _worker():
            success, info, err = get_youtube_video_info(url)
            if success and info:
                self.youtube_info = info
                self.lbl_yt_title.value = info.get("title", "Bilinmeyen Başlık")
                duration_sec = info.get("duration", 0)
                dur_str = f"{duration_sec // 60}:{duration_sec % 60:02d}"
                self.lbl_yt_meta.value = f"Kanal: {info.get('uploader', '-')} | Süre: {dur_str}"
                self.lbl_status.value = f"YouTube hazır: {info.get('title')}"
            else:
                self.lbl_yt_title.value = "Hata oluştu"
                self.lbl_yt_meta.value = clean_error_message(err or "Bilinmeyen hata")
                self.lbl_status.value = "YouTube bilgisi alınamadı."

            self._safe_update(self.lbl_yt_title)
            self._safe_update(self.lbl_yt_meta)
            self._safe_update(self.lbl_status)

        threading.Thread(target=_worker, daemon=True).start()

    # ------------------ Transkripsiyon Boru Hattı ------------------
    def start_transcription(self):
        """Transkripsiyon işlemini arka plan iş parçacığında başlatır."""
        if self.is_processing:
            return

        media_source = self.selected_file_path or (self.yt_url_entry.value.strip() if self.yt_url_entry.value else None)
        if not media_source:
            self._show_toast("Lütfen önce bir yerel dosya veya YouTube bağlantısı seçin!", is_error=True)
            return

        self.is_processing = True
        self.cancel_requested = False
        self.btn_start.disabled = True
        self.btn_cancel.disabled = False
        self.progress_bar.value = None
        self.stepper.set_active_step(0)
        self.lbl_status.value = "İşlem başlatılıyor..."

        self._safe_update(self.btn_start)
        self._safe_update(self.btn_cancel)
        self._safe_update(self.progress_bar)
        self._safe_update(self.lbl_status)

        threading.Thread(target=self._transcription_worker, args=(media_source,), daemon=True).start()

    def _transcription_worker(self, media_source: str):
        """Adım adım ses çıkarma, filtreleme, Whisper, Diarization ve hizalama işlemini yürütür."""
        temp_wav = None
        enhanced_wav = None

        try:
            # Adım 1: Medya Hazırlama / Ses Çıkarma
            self._update_progress(0.05, "1/5: Ses dosyası hazırlanıyor...")
            self.stepper.set_active_step(0)

            if media_source.startswith("http://") or media_source.startswith("https://"):
                def yt_prog(pct, msg):
                    self._update_progress(0.05 + (pct * 0.10), f"1/5: {msg}")

                dl_ok, wav_path, dl_err = download_youtube_audio(media_source, progress_callback=yt_prog)
                if not dl_ok or not wav_path:
                    raise RuntimeError(f"YouTube sesi indirilemedi: {clean_error_message(dl_err)}")
                temp_wav = wav_path
            else:
                ext_ok, wav_path, ext_err = extract_audio_to_wav(media_source)
                if not ext_ok or not wav_path:
                    raise RuntimeError(f"Ses donusturulemedi: {ext_err}")
                temp_wav = wav_path

            if self.cancel_requested:
                raise InterruptedError("İşlem kullanıcı tarafından iptal edildi.")

            audio_for_stt = temp_wav
            media_info = get_media_info(temp_wav)
            total_dur = media_info.get("duration", 0.0)

            # Adım 2: Ses Ön-İyileştirme
            if self.chk_enhance.value:
                self.stepper.set_active_step(1)
                self._update_progress(0.18, "2/5: Ses frekans ve gürültü dengesi optimize ediliyor...")
                enh_ok, enh_path, enh_err = enhance_audio(temp_wav)
                if enh_ok and enh_path:
                    enhanced_wav = enh_path
                    audio_for_stt = enh_path
                else:
                    audio_for_stt = temp_wav

            if self.cancel_requested:
                raise InterruptedError("İşlem kullanıcı tarafından iptal edildi.")

            # Adım 3: Whisper STT
            self.stepper.set_active_step(2)
            raw_model = self.cmb_model.value or "small"
            model_key = raw_model.split()[0].lower()
            raw_lang = self.cmb_lang.value or "Türkçe (tr)"
            lang_choice = "tr" if "tr" in raw_lang.lower() or "türkçe" in raw_lang.lower() else "auto"
            raw_vad = self.cmb_vad.value or "Yüksek"
            vad_choice = "high" if "yüksek" in raw_vad.lower() or "hassas" in raw_vad.lower() else "normal"

            self._update_progress(0.20, f"3/5: Whisper '{model_key}' modeli hazırlanıyor...")
            transcriber = WhisperTranscriber(model_size=model_key, cpu_threads=4)

            def whisper_progress(pct, msg, seg):
                if self.cancel_requested:
                    raise InterruptedError("Kullanıcı iptal etti.")
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
                self._update_progress(1.0, "Ses dosyasında herhangi bir konuşma algılanamadı.")
                self.set_transcribed_data([])
                return

            if self.cancel_requested:
                raise InterruptedError("İşlem kullanıcı tarafından iptal edildi.")

            # Adım 4: Konuşmacı Ayrıştırma (Diarization)
            self.stepper.set_active_step(3)
            self._update_progress(0.78, "4/5: Konuşmacılar ayrıştırılıyor...")

            raw_prefix = self.cmb_prefix.value or "X"
            prefix_val = raw_prefix.split()[0]
            raw_spk = self.cmb_spk_count.value or "Otomatik"
            num_spk = None
            for ch in raw_spk:
                if ch.isdigit():
                    num_spk = int(ch)
                    break

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
            self.stepper.set_active_step(4)
            self._update_progress(0.92, "5/5: Konuşmalar ve metin blokları hizalanıyor...")

            aligned_transcript = align_transcription_and_diarization(
                transcription_segments=stt_segments,
                diarization_intervals=diar_intervals,
                speaker_prefix=prefix_val,
                auto_merge_gap=self.settings.get("auto_merge_gap", 1.5),
            )

            self.stepper.set_active_step(5)
            self._update_progress(1.0, f"Tamamlandı. {len(aligned_transcript)} konuşma segmenti oluşturuldu.")
            self.set_transcribed_data(aligned_transcript)

            if audio_for_stt and os.path.exists(audio_for_stt):
                self.active_wav_path = audio_for_stt
                self.audio_player.set_audio_source(audio_for_stt, self.badge_duration.lbl_val.value)

            self._show_toast("Transkripsiyon başarıyla tamamlandı!", is_error=False)

        except InterruptedError:
            self._update_progress(0.0, "İşlem kullanıcı tarafından iptal edildi.")
            self.stepper.reset()
            self._show_toast("İşlem iptal edildi.", is_error=False)
        except Exception as e:
            self._update_progress(0.0, f"Hata: {str(e)}")
            self.stepper.reset()
            self._show_toast(f"Hata: {str(e)}", is_error=True)
        finally:
            if temp_wav and temp_wav != self.selected_file_path:
                cleanup_temp_file(temp_wav)
            if enhanced_wav:
                cleanup_temp_file(enhanced_wav)
            self.is_processing = False
            self.btn_start.disabled = False
            self.btn_cancel.disabled = True
            self._safe_update(self.btn_start)
            self._safe_update(self.btn_cancel)

    def _update_progress(self, fraction: float, message: str):
        """İlerleme çubuğunu ve durum mesajını günceller."""
        self.progress_bar.value = fraction
        self.lbl_status.value = message
        self._safe_update(self.progress_bar)
        self._safe_update(self.lbl_status)

    def request_cancel(self):
        """Devam eden işlemi iptal eder."""
        if self.is_processing:
            self.cancel_requested = True
            self.lbl_status.value = "İptal ediliyor, lütfen bekleyin..."
            self._safe_update(self.lbl_status)

    # ------------------ Transkript Yönetimi ve Filtreleme ------------------
    def set_transcribed_data(self, data: List[Dict[str, Any]]):
        """Transkript listesini yükler, istatistikleri hesaplar ve kartları çizer."""
        self.transcribed_data = data

        stats = compute_transcript_statistics(data)
        dur_secs = stats.get("speaking_duration_seconds", 0.0)
        dur_mins = int(dur_secs // 60)
        dur_rem = int(dur_secs % 60)
        dur_str = f"{dur_mins:02d}:{dur_rem:02d}"

        spk_cnt = stats.get("unique_speakers_count", stats.get("speaker_count", 0))
        word_cnt = stats.get("total_words", stats.get("word_count", 0))
        wpm = stats.get("words_per_minute", stats.get("wpm", 0.0))

        self.badge_duration.update_value(dur_str)
        self.badge_speakers.update_value(f"{spk_cnt} Kişi")
        self.badge_words.update_value(f"{word_cnt} Kelime")
        self.badge_wpm.update_value(f"{wpm} WPM")
        self.lbl_total_turns.value = f"{len(data)} konuşma parçası"

        self._render_transcript_cards(data)
        self._safe_update(self.lbl_total_turns)

    def _render_transcript_cards(self, turns: List[Dict[str, Any]]):
        """Kartları ListView içine ekler."""
        self.transcript_list.controls.clear()

        if not turns:
            self.transcript_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(value="Henüz transkript oluşturulmadı", size=13, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                            ft.Text(value="Sol panelden medya seçerek transkripsiyonu başlatın.", size=11, color=TEXT_SUBTLE),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding.all(30),
                    alignment=ft.Alignment.CENTER,
                )
            )
        else:
            for item in turns:
                card = TranscriptTurnCard(
                    turn_data=item,
                    on_text_change=self._on_turn_text_edited,
                    on_copy_click=self.copy_to_clipboard,
                )
                self.transcript_list.controls.append(card)

        self._safe_update(self.transcript_list)

    def _on_turn_text_edited(self, turn_id: int, new_text: str):
        """Kullanıcı bir konuşma kartını düzenlediğinde veriyi günceller."""
        for item in self.transcribed_data:
            if item.get("id") == turn_id:
                item["text"] = new_text
                break

    def filter_transcript(self, query: Optional[str] = None):
        """Canlı arama filtresini uygular."""
        if query is None:
            query = self.search_entry.value or ""

        query_clean = query.strip()
        if not query_clean:
            self.lbl_search_count.value = ""
            self._render_transcript_cards(self.transcribed_data)
            self._safe_update(self.lbl_search_count)
            return

        filtered = filter_transcript(self.transcribed_data, query_clean)
        self.lbl_search_count.value = f"{len(filtered)} / {len(self.transcribed_data)} eşleşme"
        self._render_transcript_cards(filtered)
        self._safe_update(self.lbl_search_count)

    def _toggle_find_replace(self):
        """Bul ve Değiştir panelini açar/kapatır."""
        self.find_replace_container.visible = not self.find_replace_container.visible
        self._safe_update(self.find_replace_container)

    def execute_find_replace(self) -> int:
        """Transkriptteki metinleri toplu olarak değiştirir."""
        target = self.entry_find.value or ""
        replacement = self.entry_replace.value or ""

        if not target:
            self._show_toast("Lütfen aranacak kelimeyi giriniz.", is_error=True)
            return 0

        updated_data, replaced_count = find_and_replace_in_transcript(
            self.transcribed_data,
            find_str=target,
            replace_str=replacement,
        )

        if replaced_count > 0:
            self.set_transcribed_data(updated_data)
            self._show_toast(f"Toplam {replaced_count} konuşma parçasında değişiklik yapıldı.", is_error=False)
        else:
            self._show_toast("Eşleşen kelime bulunamadı.", is_error=True)

        return replaced_count

    def open_speaker_manager(self):
        """Konuşmacıları yeniden adlandırma modal penceresini açar."""
        if not self.transcribed_data:
            self._show_toast("Henüz transkript verisi bulunmuyor.", is_error=True)
            return

        unique_speakers = get_unique_speakers(self.transcribed_data)
        rename_fields: Dict[str, ft.TextField] = {}

        dialog_rows = []
        for spk in unique_speakers:
            tf = ft.TextField(
                value=spk,
                width=160,
                height=32,
                text_size=11,
                bgcolor=INPUT_BG,
                border_color=INPUT_BORDER,
                color=TEXT_MAIN,
                content_padding=ft.Padding.symmetric(horizontal=8),
            )
            rename_fields[spk] = tf
            dialog_rows.append(
                ft.Row(
                    controls=[
                        ft.Text(value=f"{spk} ->", size=11, weight=ft.FontWeight.BOLD, color=TEXT_MUTED, width=60),
                        tf,
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        def _apply_rename(_):
            current_data = self.transcribed_data
            for old_spk, tf in rename_fields.items():
                new_spk = tf.value.strip()
                if new_spk and new_spk != old_spk:
                    current_data = rename_speaker_in_transcript(current_data, old_spk, new_spk)

            self.set_transcribed_data(current_data)
            dialog.open = False
            self._safe_update()
            self._show_toast("Konuşmacı isimleri güncellendi.", is_error=False)

        dialog = ft.AlertDialog(
            title=ft.Text(value="Konuşmacı İsimlerini Düzenle", size=14, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(controls=dialog_rows, spacing=8),
                width=280,
                padding=ft.Padding.symmetric(vertical=8),
            ),
            actions=[
                ft.TextButton("İptal", on_click=lambda _: setattr(dialog, "open", False) or self._safe_update()),
                ft.Button("Uygula", bgcolor=ACCENT_PRIMARY, color=TEXT_MAIN, on_click=_apply_rename),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        if self.page:
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()

    # ------------------ Dışa Aktarma ve Panoya Kopyalama ------------------
    def copy_to_clipboard(self, custom_text: Optional[str] = None):
        """Metni sistem panosuna kopyalar."""
        if custom_text:
            text_to_copy = custom_text
        else:
            lines = []
            for item in self.transcribed_data:
                spk = item.get("speaker", "X1")
                t_str = f"[{int(item['start']//60):02d}:{int(item['start']%60):02d}]"
                lines.append(f"{spk} {t_str}: {item.get('text', '')}")
            text_to_copy = "\n".join(lines)

        if not text_to_copy.strip():
            self._show_toast("Kopyalanacak metin bulunamadı.", is_error=True)
            return

        if self.page:
            self.page.set_clipboard(text_to_copy)
        self._show_toast("Panoya kopyalandı!", is_error=False)

    def export_result(self, fmt: str):
        """Transkripti belirtilen formatta dosyaya kaydeder."""
        if not self.transcribed_data:
            self._show_toast("Dışa aktarılacak transkript verisi yok!", is_error=True)
            return

        os.makedirs(str(OUTPUTS_DIR), exist_ok=True)
        base_name = "transkript_cikti"
        if self.selected_file_path:
            base_name = os.path.splitext(os.path.basename(self.selected_file_path))[0]
        elif self.youtube_info:
            base_name = "".join(c for c in self.youtube_info.get("title", "youtube") if c.isalnum() or c in ("-", "_")).rstrip()

        out_path = os.path.join(str(OUTPUTS_DIR), f"{base_name}.{fmt.lower()}")

        try:
            fmt_lower = fmt.lower()
            if fmt_lower == "txt":
                export_to_txt(self.transcribed_data, out_path)
            elif fmt_lower == "srt":
                export_to_srt(self.transcribed_data, out_path)
            elif fmt_lower == "vtt":
                export_to_vtt(self.transcribed_data, out_path)
            elif fmt_lower == "csv":
                export_to_csv(self.transcribed_data, out_path)
            elif fmt_lower == "json":
                export_to_json(self.transcribed_data, out_path)
            elif fmt_lower == "md":
                export_to_markdown(self.transcribed_data, out_path)

            self._show_toast(f"Kaydedildi: {out_path}", is_error=False)
        except Exception as e:
            self._show_toast(f"Dışa aktarma hatası: {e}", is_error=True)

    def _show_toast(self, message: str, is_error: bool = False):
        """Kullanıcıya sade bilgi bildirimi (SnackBar) gösterir."""
        if self.page:
            snack = ft.SnackBar(
                content=ft.Text(value=message, color=TEXT_MAIN, size=12),
                bgcolor=DANGER if is_error else BTN_NEUTRAL,
                duration=3000,
            )
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()


def run_flet_app(page: ft.Page):
    """Flet masaüstü pencere başlatıcısı ve açılış animasyonu."""
    page.title = f"SesMetin Pro - Turkce STT ve Konusmaci Ayrastirma (v{FletSpeechToTextApp.APP_VERSION})"
    page.bgcolor = BG_APP
    page.padding = 0
    page.spacing = 0

    # Pencere Boyutları ve Ortalama
    try:
        page.window.width = 1180
        page.window.height = 840
        page.window.min_width = 960
        page.window.min_height = 640
        try:
            if hasattr(page, "run_task"):
                page.run_task(page.window.center)
            else:
                page.window.center()
        except Exception:
            pass
        # Başlangıç opaklığı
        page.window.opacity = 0.0
        page.update()
    except Exception:
        pass

    app = FletSpeechToTextApp(page)
    page.overlay.append(app.file_picker)
    page.add(app.build_layout())

    # Açılış fade-in animasyonu (60 FPS pürüzsüz geçiş)
    def _fade_in_worker():
        try:
            for op in range(1, 11):
                page.window.opacity = op / 10.0
                page.update()
                time.sleep(0.016)
        except Exception:
            try:
                page.window.opacity = 1.0
                page.update()
            except Exception:
                pass

    threading.Thread(target=_fade_in_worker, daemon=True).start()
