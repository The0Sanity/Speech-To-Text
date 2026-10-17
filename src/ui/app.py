"""Flet tabanlı Windows 11 Fluent Ses Tanıma ve Konuşmacı Ayrıştırma Masaüstü Uygulaması."""

import os
import sys
import threading
import time
import webbrowser
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
    APP_NAME,
    APP_VERSION,
    BASE_DIR,
    OUTPUTS_DIR,
    TEMP_DIR,
    load_settings,
    save_settings,
)
from src.updater import AutoUpdater, CheckStatus, UpdateInfo, is_newer_version
from src.exporter import (
    export_to_csv,
    export_to_json,
    export_to_markdown,
    export_to_srt,
    export_to_txt,
    export_to_vtt,
)
from src.ui.components import (
    AudioPlayerBar,
    MetricCard,
    ProcessStepper,
    SkeletonCard,
    SkeletonLoader,
    TranscriptTurnCard,
)
from src.ui.theme import (
    ACCENT,
    ACCENT_HOVER,
    ACCENT_LIGHT,
    ACCENT_PRIMARY,
    BG_APP,
    BG_CARD,
    BG_CARD_SECONDARY,
    BORDER_CARD,
    BORDER_SUBTLE,
    BTN_NEUTRAL,
    BTN_NEUTRAL_HOVER,
    DANGER,
    ERROR,
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

    APP_VERSION = APP_VERSION

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
        self.cancel_event = threading.Event()
        self.current_input_mode = "file"  # "file" veya "youtube"
        self.updater = AutoUpdater(current_version=self.APP_VERSION)

        if self.page:
            self.page.bgcolor = BG_APP
            if hasattr(self.page, "window") and self.page.window:
                try:
                    self.page.window.opacity = 1.0
                except Exception:
                    pass

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
            label="Ses Ön-İyileştirme (80Hz - 7600Hz bant filtre)",
            value=self.settings.get("enhance_audio", True),
            check_color=TEXT_MAIN,
            active_color=ACCENT_PRIMARY,
            label_style=ft.TextStyle(size=11, color=TEXT_MUTED),
        )

        self.chk_loudnorm = ft.Checkbox(
            label="EBU R128 Ses Normalizasyonu (-16 LUFS)",
            value=self.settings.get("normalize_loudness", True),
            check_color=TEXT_MAIN,
            active_color=ACCENT_PRIMARY,
            label_style=ft.TextStyle(size=11, color=TEXT_MUTED),
        )

        self.chk_itn = ft.Checkbox(
            label="Türkçe Sayı & Yüzde Dönüşümü (ITN)",
            value=self.settings.get("apply_itn", True),
            check_color=TEXT_MAIN,
            active_color=ACCENT_PRIMARY,
            label_style=ft.TextStyle(size=11, color=TEXT_MUTED),
        )

        self.chk_disfluencies = ft.Checkbox(
            label="Dolgu Sözcük Temizliği (ııı, şey vb.)",
            value=self.settings.get("clean_disfluencies", True),
            check_color=TEXT_MAIN,
            active_color=ACCENT_PRIMARY,
            label_style=ft.TextStyle(size=11, color=TEXT_MUTED),
        )

        self.entry_vocab = ft.TextField(
            hint_text="Teknik terim / sözlük ipuçları (örn: Supabase, TEKNOFEST, API)",
            value=self.settings.get("vocabulary_bias", ""),
            height=32,
            text_size=11,
            bgcolor=INPUT_BG,
            border_color=INPUT_BORDER,
            color=TEXT_MAIN,
            content_padding=ft.Padding.symmetric(horizontal=10),
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
        self.btn_tab_file = ft.FilledButton(
            content=ft.Text("Yerel Dosya", size=12, weight=ft.FontWeight.W_500),
            bgcolor=ACCENT_PRIMARY,
            color=TEXT_MAIN,
            height=32,
            on_click=lambda _: self._switch_input_mode("file"),
        )
        self.btn_tab_yt = ft.FilledButton(
            content=ft.Text("YouTube", size=12, weight=ft.FontWeight.W_500),
            bgcolor=BTN_NEUTRAL,
            color=TEXT_MAIN,
            height=32,
            on_click=lambda _: self._switch_input_mode("youtube"),
        )

        self.box_file_input = ft.Container(
            content=ft.Column(
                controls=[
                    ft.FilledButton(
                        content=ft.Text("Dosya Seç (MP4 / MP3 / WAV)", size=12, weight=ft.FontWeight.W_500),
                        bgcolor=ACCENT_PRIMARY,
                        color=TEXT_MAIN,
                        height=36,
                        on_click=self._pick_file_dialog,
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
                            ft.FilledButton(
                                content=ft.Text("Bilgi Al", size=11, weight=ft.FontWeight.W_500),
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
            content=ft.Text("Transkripsiyonu Başlat", size=13, weight=ft.FontWeight.BOLD),
            bgcolor=ACCENT_PRIMARY,
            color=TEXT_MAIN,
            height=38,
            expand=True,
            animate_scale=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
            on_hover=self._on_btn_start_hover,
            on_click=lambda _: self.start_transcription(),
        )

        self.btn_cancel = ft.FilledButton(
            content=ft.Text("İptal", size=12, weight=ft.FontWeight.W_500),
            bgcolor=BTN_NEUTRAL,
            color=TEXT_MAIN,
            height=38,
            width=70,
            disabled=True,
            animate_scale=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
            on_hover=self._on_btn_cancel_hover,
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

    def _on_btn_start_hover(self, e: Any):
        """Başlat butonu üzerine gelindiğinde mikro ölçek ve hafif ton aydınlatması sağlar."""
        if self.btn_start.disabled:
            return
        if getattr(e, "data", "") == "true":
            self.btn_start.scale = 1.02
            self.btn_start.bgcolor = ACCENT_LIGHT
        else:
            self.btn_start.scale = 1.0
            self.btn_start.bgcolor = ACCENT_PRIMARY
        self._safe_update(self.btn_start)

    def _on_btn_cancel_hover(self, e: Any):
        """İptal butonu üzerine gelindiğinde mikro ölçek animasyonu uygular."""
        if self.btn_cancel.disabled:
            return
        if getattr(e, "data", "") == "true":
            self.btn_cancel.scale = 1.03
        else:
            self.btn_cancel.scale = 1.0
        self._safe_update(self.btn_cancel)

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
                    self.chk_loudnorm,
                    self.chk_itn,
                    self.chk_disfluencies,
                    ft.Column(
                        controls=[
                            ft.Text(value="Alan Sözlüğü / Terim İpuçları:", size=10, weight=ft.FontWeight.BOLD, color=TEXT_MUTED),
                            self.entry_vocab,
                        ],
                        spacing=2,
                    ),
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
            opacity=0.0,
            offset=ft.Offset(-0.03, 0),
            animate_opacity=ft.Animation(380, ft.AnimationCurve.EASE_OUT),
            animate_offset=ft.Animation(380, ft.AnimationCurve.EASE_OUT),
        )
        self.left_column_container = left_column

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
                ft.FilledButton(
                    content=ft.Text("Bul ve Değiştir", size=12, weight=ft.FontWeight.W_500),
                    bgcolor=BTN_NEUTRAL,
                    color=TEXT_MAIN,
                    height=34,
                    on_click=lambda _: self._toggle_find_replace(),
                ),
                ft.FilledButton(
                    content=ft.Text("Konuşmacı Yönetimi", size=12, weight=ft.FontWeight.W_500),
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
                    content=ft.Text("Panoya Kopyala", size=12, weight=ft.FontWeight.W_500),
                    bgcolor=ACCENT_PRIMARY,
                    color=TEXT_MAIN,
                    height=30,
                    style=ft.ButtonStyle(padding=ft.Padding.symmetric(horizontal=14, vertical=2)),
                    on_click=lambda _: self.copy_to_clipboard(),
                ),
                *[
                    ft.FilledButton(
                        content=ft.Text(fmt.upper(), size=11, weight=ft.FontWeight.W_600),
                        bgcolor=BTN_NEUTRAL,
                        color=TEXT_MAIN,
                        height=30,
                        style=ft.ButtonStyle(padding=ft.Padding.symmetric(horizontal=12, vertical=2)),
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
            opacity=0.0,
            offset=ft.Offset(0.03, 0),
            animate_opacity=ft.Animation(420, ft.AnimationCurve.EASE_OUT),
            animate_offset=ft.Animation(420, ft.AnimationCurve.EASE_OUT),
        )
        self.right_column_container = right_column

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
                    ft.TextButton(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.CODE, size=14, color=ACCENT_LIGHT),
                                ft.Text(
                                    value="The0Sanity/Speech-To-Text",
                                    size=11,
                                    weight=ft.FontWeight.W_600,
                                    color=TEXT_MAIN,
                                ),
                            ],
                            spacing=4,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        url="https://github.com/The0Sanity/Speech-To-Text",
                        tooltip="Orijinal Proje Kaynağı: https://github.com/The0Sanity/Speech-To-Text",
                        style=ft.ButtonStyle(
                            bgcolor=INPUT_BG,
                            padding=ft.Padding.symmetric(horizontal=10, vertical=4),
                            shape=ft.RoundedRectangleBorder(radius=4),
                        ),
                    ),
                    ft.Container(
                        content=ft.Text(
                            value=f"v{self.APP_VERSION}",
                            size=11,
                            color=ACCENT_LIGHT,
                            weight=ft.FontWeight.W_600,
                        ),
                        bgcolor=INPUT_BG,
                        border=ft.Border.all(1, INPUT_BORDER),
                        border_radius=4,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
                    ),
                    ft.FilledButton(
                        content=ft.Text("Güncellemeleri Denetle", size=11, weight=ft.FontWeight.W_500),
                        bgcolor=BTN_NEUTRAL,
                        color=TEXT_MAIN,
                        height=28,
                        style=ft.ButtonStyle(padding=ft.Padding.symmetric(horizontal=10, vertical=0)),
                        on_click=lambda _: self.check_updates_dialog(manual=True),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=BG_CARD,
            border=ft.Border.all(1, BORDER_CARD),
            border_radius=6,
            padding=ft.Padding.symmetric(horizontal=14, vertical=10),
            opacity=0.0,
            offset=ft.Offset(0, -0.04),
            animate_opacity=ft.Animation(320, ft.AnimationCurve.EASE_OUT),
            animate_offset=ft.Animation(320, ft.AnimationCurve.EASE_OUT),
        )
        self.header_container = header

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

    def play_entrance_animation(self):
        """Arayüz bölümlerinin kademeli açılış (staggered entrance) animasyonunu tetikler."""
        def _animate():
            time.sleep(0.04)
            if hasattr(self, "header_container") and self.header_container:
                self.header_container.opacity = 1.0
                self.header_container.offset = ft.Offset(0, 0)
                self._safe_update(self.header_container)

            time.sleep(0.05)
            if hasattr(self, "left_column_container") and self.left_column_container:
                self.left_column_container.opacity = 1.0
                self.left_column_container.offset = ft.Offset(0, 0)
                self._safe_update(self.left_column_container)

            time.sleep(0.05)
            if hasattr(self, "right_column_container") and self.right_column_container:
                self.right_column_container.opacity = 1.0
                self.right_column_container.offset = ft.Offset(0, 0)
                self._safe_update(self.right_column_container)

        threading.Thread(target=_animate, daemon=True).start()

    # ------------------ Dosya ve YouTube Olayları ------------------
    def _pick_file_dialog(self, _=None):
        """Dosya seçiciyi güvenli şekilde başlatır."""
        async def _pick():
            try:
                await self.file_picker.pick_files(
                    allow_multiple=False,
                    allowed_extensions=["mp4", "mp3", "wav", "m4a", "aac", "mkv", "flac"],
                )
            except Exception:
                pass

        if self.page and hasattr(self.page, "run_task"):
            self.page.run_task(_pick)
        else:
            try:
                import asyncio
                asyncio.create_task(_pick())
            except Exception:
                pass

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
            try:
                info = get_youtube_video_info(url)
                self.youtube_info = info
                self.lbl_yt_title.value = info.get("title", "Bilinmeyen Başlık")
                duration_sec = int(info.get("duration", 0) or 0)
                dur_str = f"{duration_sec // 60}:{duration_sec % 60:02d}"
                self.lbl_yt_meta.value = f"Kanal: {info.get('uploader', '-')} | Süre: {dur_str}"
                self.lbl_status.value = f"YouTube hazır: {info.get('title')}"
            except Exception as err:
                self.lbl_yt_title.value = "Hata oluştu"
                self.lbl_yt_meta.value = clean_error_message(str(err) or "Bilinmeyen hata")
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

        # İskelet (Skeleton) yükleme animasyonunu transkript alanına yerleştir
        self.transcript_column.controls.clear()
        self.transcript_column.controls.append(SkeletonLoader(count=3))
        self._safe_update(self.transcript_column)

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

                try:
                    wav_path, _ = download_youtube_audio(media_source, progress_callback=yt_prog)
                    temp_wav = wav_path
                except Exception as dl_err:
                    raise RuntimeError(f"YouTube sesi indirilemedi: {clean_error_message(dl_err)}")
            else:
                try:
                    temp_wav = extract_audio_to_wav(
                        media_source,
                        normalize_loudness=bool(self.chk_loudnorm.value),
                        apply_bandpass=bool(self.chk_enhance.value),
                    )
                except Exception as ext_err:
                    raise RuntimeError(f"Ses dönüştürülemedi: {ext_err}")

            if self.cancel_requested:
                raise InterruptedError("İşlem kullanıcı tarafından iptal edildi.")

            audio_for_stt = temp_wav
            media_info = get_media_info(temp_wav)
            total_dur = media_info.get("duration", 0.0)

            # Adım 2: Ses Ön-İyileştirme
            if self.chk_enhance.value:
                self.stepper.set_active_step(1)
                self._update_progress(0.18, "2/5: Ses frekans ve gürültü dengesi optimize ediliyor...")
                try:
                    out_enh = str(TEMP_DIR / f"enhanced_{os.path.basename(temp_wav)}")
                    enhanced_wav = enhance_audio(temp_wav, out_enh)
                    audio_for_stt = enhanced_wav
                except Exception as enh_err:
                    print(f"Ses iyileştirme atlandı: {enh_err}")
                    audio_for_stt = temp_wav

            if self.cancel_requested:
                raise InterruptedError("İşlem kullanıcı tarafından iptal edildi.")

            # Adım 3: Whisper STT (Tembel / İhtiyaç Anında Yükleme)
            self.stepper.set_active_step(2)
            raw_model = self.cmb_model.value or "small"
            model_key = raw_model.split()[0].lower()
            raw_lang = self.cmb_lang.value or "Türkçe (tr)"
            lang_choice = "tr" if "tr" in raw_lang.lower() or "türkçe" in raw_lang.lower() else "auto"
            raw_vad = self.cmb_vad.value or "Yüksek"
            vad_choice = "high" if "yüksek" in raw_vad.lower() or "hassas" in raw_vad.lower() else "normal"

            self._update_progress(0.20, f"3/5: Whisper '{model_key}' modeli hazırlanıyor...")
            from src.transcriber import WhisperTranscriber
            transcriber = WhisperTranscriber(model_size=model_key, cpu_threads=4)

            def whisper_progress(pct, msg, seg):
                if self.cancel_requested:
                    raise InterruptedError("Kullanıcı iptal etti.")
                scaled = 0.20 + (pct * 0.55)
                self._update_progress(scaled, f"3/5: {msg}")

            vocab_prompt = self.entry_vocab.value.strip() if self.entry_vocab.value else None
            stt_segments = transcriber.transcribe(
                audio_path=audio_for_stt,
                language=lang_choice,
                total_duration=total_dur,
                initial_prompt=vocab_prompt,
                vad_sensitivity=vad_choice,
                apply_postprocessing=True,
                apply_itn=bool(self.chk_itn.value),
                clean_disfluencies=bool(self.chk_disfluencies.value),
                progress_callback=whisper_progress,
                cancel_event=self.cancel_event,
            )

            if not stt_segments:
                self._update_progress(1.0, "Ses dosyasında herhangi bir konuşma algılanamadı.")
                self.set_transcribed_data([])
                return

            if self.cancel_requested:
                raise InterruptedError("İşlem kullanıcı tarafından iptal edildi.")

            # Adım 4: Konuşmacı Ayrıştırma (Diarization - Tembel / İhtiyaç Anında Yükleme)
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

            from src.diarizer import SpeakerDiarizer
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
            if temp_wav and temp_wav != self.selected_file_path and temp_wav != self.active_wav_path:
                cleanup_temp_file(temp_wav)
            if enhanced_wav and enhanced_wav != self.active_wav_path:
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
            if hasattr(self, "cancel_event"):
                self.cancel_event.set()
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

    def on_search_change(self, e=None):
        """Arama girdisi değiştiğinde tetiklenen yardımcı metot."""
        self.filter_transcript(self.search_entry.value if self.search_entry else "")

    def apply_speaker_rename(self, old_spk: str, new_spk: str):
        """Konuşmacı ismini transkript içinde günceller."""
        self.transcribed_data = rename_speaker_in_transcript(self.transcribed_data, old_spk, new_spk)
        self.set_transcribed_data(self.transcribed_data)

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
            if hasattr(self.page, "overlay") and self.page.overlay is not None:
                self.page.overlay = [ctl for ctl in self.page.overlay if not isinstance(ctl, ft.AlertDialog) or getattr(ctl, "open", False)]
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
            if hasattr(self.page, "overlay") and self.page.overlay is not None:
                self.page.overlay = [ctl for ctl in self.page.overlay if not isinstance(ctl, ft.SnackBar)]
            snack = ft.SnackBar(
                content=ft.Text(value=message, color=TEXT_MAIN, size=12),
                bgcolor=DANGER if is_error else BTN_NEUTRAL,
                duration=3000,
            )
            self.page.overlay.append(snack)
            snack.open = True
            self.page.update()



    # ------------------ Otomatik Güncelleme (Auto-Updater) ------------------
    def start_background_update_check(self):
        """Uygulama başlangıcında arka planda yeni sürüm denetimi yapar.
        
        Yeni bir sürüm tespit edildiğinde kullanıcıyı bilgilendirmek için
        doğrudan modal güncelleme penceresini açar.
        """
        def _check():
            try:
                info = self.updater.check_for_updates(timeout=8)
                if info and info.is_update_available and self.page:
                    self._show_update_modal(info)
            except Exception as e:
                print(f"Başlangıç güncelleme denetimi atlandı: {e}")

        threading.Thread(target=_check, daemon=True).start()

    def _check_can_update(self) -> bool:
        """Aktif bir transkripsiyon işlemi olup olmadığını denetler."""
        if getattr(self, "is_processing", False):
            self._show_toast("Transkripsiyon devam ederken güncelleme yapılamaz.", is_error=True)
            return False
        return True

    def check_updates_dialog(self, manual: bool = True):
        """Kullanıcı tarafından tetiklenen güncelleme denetimi."""
        if not self.page:
            return
        if not self._check_can_update():
            return

        if manual:
            self._show_toast("Güncellemeler denetleniyor...", is_error=False)

        def _do_check():
            try:
                info = self.updater.check_for_updates(timeout=8, force=manual)
                if not self.page:
                    return

                if not info or info.status == CheckStatus.ERROR:
                    if manual:
                        err = info.error_message if (info and info.error_message) else "Güncellemeler denetlenemedi."
                        self._show_toast(err, is_error=True)
                elif info.status == CheckStatus.RATE_LIMITED:
                    if manual:
                        self._show_toast(info.error_message or "GitHub saatlik istek sınırı aşıldı.", is_error=True)
                elif info.status == CheckStatus.OFFLINE:
                    if manual:
                        self._show_toast("İnternet bağlantısı kurulamadı.", is_error=True)
                elif info.status == CheckStatus.NO_RELEASES:
                    if manual:
                        self._show_toast("Henüz yayınlanmış bir sürüm bulunamadı.", is_error=False)
                elif info.is_update_available:
                    self._show_update_modal(info)
                else:
                    if manual:
                        self._show_toast(f"Uygulamanız güncel: v{self.APP_VERSION}", is_error=False)
            except Exception as e:
                print(f"Güncelleme penceresi açılırken hata: {e}")
                if manual:
                    self._show_toast("Güncelleme denetimi sırasında hata oluştu.", is_error=True)

        threading.Thread(target=_do_check, daemon=True).start()

    def _create_smooth_progress_handler(
        self,
        total_bytes: int = 0,
        ui_updater: Optional[Any] = None,
        throttle_interval: float = 0.08,
    ):
        """Websocket IPC yukunu engelleyen ve akici hiz/ETA hesaplayan ilerleme isleyicisi."""
        last_update_time = [0.0]
        last_bytes = [0]
        rolling_speed_mb = [0.0]
        alpha = 0.3

        def _handler(dl: int, tot: int):
            effective_tot = tot if tot > 0 else total_bytes
            now = time.monotonic()
            is_finished = (effective_tot > 0 and dl >= effective_tot) or (dl > 0 and effective_tot <= 0 and dl == total_bytes)
            time_diff = now - last_update_time[0]

            if not is_finished and time_diff < throttle_interval:
                return

            if time_diff > 0.001 and last_bytes[0] > 0 and dl > last_bytes[0]:
                bytes_delta = dl - last_bytes[0]
                inst_speed = (bytes_delta / (1024 * 1024)) / time_diff
                if rolling_speed_mb[0] <= 0.01:
                    rolling_speed_mb[0] = inst_speed
                else:
                    rolling_speed_mb[0] = alpha * inst_speed + (1 - alpha) * rolling_speed_mb[0]

            last_bytes[0] = dl
            last_update_time[0] = now

            prog_val = (dl / effective_tot) if effective_tot > 0 else 0.0
            prog_val = min(1.0, max(0.0, prog_val))
            pct = int(prog_val * 100)

            speed_str = f" | {rolling_speed_mb[0]:.1f} MB/s" if rolling_speed_mb[0] > 0.05 else ""
            eta_str = ""
            if rolling_speed_mb[0] > 0.05 and effective_tot > dl:
                rem_mb = (effective_tot - dl) / (1024 * 1024)
                eta_s = int(rem_mb / rolling_speed_mb[0])
                if eta_s < 60:
                    eta_str = f" | Kalan: ~{eta_s}s"
                else:
                    eta_str = f" | Kalan: ~{eta_s // 60}dk {eta_s % 60}s"

            if effective_tot > 0:
                status_text = f"İndiriliyor: %{pct} ({dl // 1048576}MB / {effective_tot // 1048576}MB{speed_str}{eta_str})"
            else:
                status_text = f"İndiriliyor: {dl // 1048576}MB{speed_str}"

            if is_finished:
                prog_val = 1.0
                tot_mb = (effective_tot // 1048576) if effective_tot > 0 else (dl // 1048576)
                status_text = f"İndirme tamamlandı: %100 ({dl // 1048576}MB / {tot_mb}MB)"

            if ui_updater:
                ui_updater(prog_val, status_text)

        return _handler

    def _postpone_update(self, info: UpdateInfo):
        """Kullanici 'Daha Sonra' sectiginde guncellemeyi sonraki acilista hatirlatmak uzere kaydeder."""
        try:
            self.settings["postponed_update"] = {
                "version": info.version,
                "tag_name": info.tag_name,
                "release_name": info.release_name,
                "release_notes": info.release_notes,
                "published_at": info.published_at,
                "download_url": info.download_url,
                "asset_size": info.asset_size,
                "has_exe_asset": info.has_exe_asset,
                "html_url": info.html_url,
            }
            save_settings(self.settings)
        except Exception as e:
            print(f"Guncelleme erteleme kaydi hatasi: {e}")

    def check_and_prompt_postponed_update(self) -> bool:
        """Uygulama acilisinda ertelenmis bir guncelleme varsa kullaniciya sunar."""
        postponed = self.settings.get("postponed_update")
        if not postponed or not isinstance(postponed, dict):
            return False

        postponed_ver = postponed.get("version", "")
        if not is_newer_version(self.APP_VERSION, postponed_ver):
            self.settings["postponed_update"] = None
            save_settings(self.settings)
            return False

        info = UpdateInfo(
            version=postponed.get("version", ""),
            tag_name=postponed.get("tag_name", f"v{postponed_ver}"),
            release_name=postponed.get("release_name", f"v{postponed_ver}"),
            release_notes=postponed.get("release_notes", ""),
            published_at=postponed.get("published_at", ""),
            html_url=postponed.get("html_url", ""),
            download_url=postponed.get("download_url"),
            asset_name=f"SpeechToText_v{postponed_ver}.exe",
            asset_size=postponed.get("asset_size"),
            has_exe_asset=postponed.get("has_exe_asset", True),
            is_update_available=True,
            status=CheckStatus.UPDATE_AVAILABLE,
        )
        self._show_update_modal(info)
        return True

    def check_and_show_patch_notes(self) -> bool:
        """Guncelleme sonrasindaki ilk acilista yama notlarini gosterir."""
        last_seen = self.settings.get("last_seen_version", "0.0.0")
        pending_notes = self.settings.get("pending_patch_notes", "")

        has_newer = is_newer_version(last_seen, self.APP_VERSION)
        if has_newer or bool(pending_notes):
            notes = pending_notes if pending_notes else f"SesMetin Pro v{self.APP_VERSION} surumune basariyla guncellendi."
            self._show_patch_notes_dialog(notes, self.APP_VERSION)
            self.settings["last_seen_version"] = self.APP_VERSION
            self.settings["pending_patch_notes"] = ""
            save_settings(self.settings)
            return True
        return False

    def _show_patch_notes_dialog(self, notes: str, version: str):
        """Guncelleme sonrasi surum notlarini (Patch Notes) sik bir modal ile sunar."""
        if not self.page:
            return

        def _close(_=None):
            if hasattr(self.page, "close"):
                self.page.close(dialog)
            else:
                dialog.open = False
                self._safe_update(self.page)

        btn_ok = ft.FilledButton(
            content=ft.Text("Harika, Basla", size=12, weight=ft.FontWeight.BOLD),
            bgcolor=ACCENT_PRIMARY,
            color=TEXT_MAIN,
            on_click=_close,
        )

        formatted_notes = notes.strip() if notes and notes.strip() else "Bu surum icin degisiklik notu belirtilmemis."

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.NEW_RELEASES, color=ACCENT_LIGHT, size=22),
                    ft.Text(f"Yenilikler ve Surum Notlari (v{version})", size=15, weight=ft.FontWeight.BOLD, color=TEXT_MAIN),
                ],
                spacing=8,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "SesMetin Pro basariyla guncellendi! Iste bu surumdeki baslica yenilikler:",
                            size=12,
                            color=TEXT_SUBTLE,
                        ),
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Markdown(
                                        formatted_notes,
                                        selectable=True,
                                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                                    ),
                                ],
                                scroll=ft.ScrollMode.AUTO,
                            ),
                            bgcolor=INPUT_BG,
                            border=ft.Border.all(1, INPUT_BORDER),
                            border_radius=6,
                            padding=ft.Padding.all(12),
                            height=260,
                        ),
                    ],
                    spacing=10,
                    tight=True,
                ),
                width=480,
            ),
            actions=[btn_ok],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        if hasattr(self.page, "open"):
            self.page.open(dialog)
        else:
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()

    def _show_update_modal(self, info: UpdateInfo):
        """Yeni sürüm bulunduğunda modal güncelleme penceresi açar."""
        if not self.page:
            return
        if not self._check_can_update():
            return

        size_mb = f"{info.asset_size / (1024*1024):.1f} MB" if info.asset_size else "Belirtilmedi"

        lbl_status = ft.Text(
            value=f"Dosya Boyutu: {size_mb}" if info.has_exe_asset else "Yeni sürüm var ancak Windows .exe dosyası henüz eklenmemiş.",
            size=11,
            color=TEXT_MUTED if info.has_exe_asset else DANGER,
        )
        progress_bar = ft.ProgressBar(visible=False, color=ACCENT_PRIMARY, bgcolor=BTN_NEUTRAL)

        cancel_event = threading.Event()

        def _close_dialog(_=None):
            cancel_event.set()
            self._postpone_update(info)
            if hasattr(self.page, "close"):
                self.page.close(dialog)
            else:
                dialog.open = False
                self._safe_update(self.page)

        def _cancel_download(_):
            cancel_event.set()
            btn_cancel_download.visible = False
            btn_update.visible = True
            btn_update.disabled = False
            btn_later.disabled = False
            progress_bar.visible = False
            lbl_status.value = "İndirme kullanıcı tarafından iptal edildi."
            lbl_status.color = TEXT_MUTED
            self._safe_update(btn_cancel_download)
            self._safe_update(btn_update)
            self._safe_update(btn_later)
            self._safe_update(progress_bar)
            self._safe_update(lbl_status)

        def _start_download(_):
            if not self._check_can_update():
                return
            if not info.download_url:
                return

            cancel_event.clear()
            btn_update.visible = False
            btn_cancel_download.visible = True
            btn_later.disabled = True
            progress_bar.visible = True
            progress_bar.value = 0.0
            lbl_status.value = "Güncelleme indiriliyor..."
            lbl_status.color = TEXT_MUTED
            self._safe_update(btn_update)
            self._safe_update(btn_cancel_download)
            self._safe_update(btn_later)
            self._safe_update(progress_bar)
            self._safe_update(lbl_status)

            def _download_task():
                target_exe = TEMP_DIR / f"SpeechToText_v{info.version}.exe"

                def _ui_update(prog_val, status_text):
                    progress_bar.value = prog_val
                    lbl_status.value = status_text
                    self._safe_update(progress_bar)
                    self._safe_update(lbl_status)

                smooth_prog = self._create_smooth_progress_handler(
                    total_bytes=info.asset_size or 0,
                    ui_updater=_ui_update,
                    throttle_interval=0.08,
                )

                ok = self.updater.download_asset(
                    info.download_url,
                    target_exe,
                    progress_callback=smooth_prog,
                    cancel_event=cancel_event,
                    verify_pe=True,
                )

                if cancel_event.is_set():
                    btn_cancel_download.visible = False
                    btn_update.visible = True
                    btn_update.disabled = False
                    btn_later.disabled = False
                    progress_bar.visible = False
                    lbl_status.value = "İndirme iptal edildi."
                    lbl_status.color = TEXT_MUTED
                    self._safe_update(btn_cancel_download)
                    self._safe_update(btn_update)
                    self._safe_update(btn_later)
                    self._safe_update(progress_bar)
                    self._safe_update(lbl_status)
                    return

                if ok:
                    btn_cancel_download.visible = False
                    btn_update.visible = False
                    btn_later.disabled = True
                    progress_bar.value = 1.0
                    lbl_status.value = "İndirme ve bütünlük doğrulaması tamamlandı. Güncelleme uygulanıyor ve yeniden başlatılıyor..."
                    lbl_status.color = SUCCESS
                    self._safe_update(btn_cancel_download)
                    self._safe_update(btn_update)
                    self._safe_update(btn_later)
                    self._safe_update(progress_bar)
                    self._safe_update(lbl_status)
                    # Bir sonraki açılışta gösterilmek üzere sürüm notlarını kaydet ve ertelenmiş güncellemeyi temizle
                    self.settings["pending_patch_notes"] = info.release_notes or ""
                    self.settings["postponed_update"] = None
                    save_settings(self.settings)
                    time.sleep(1.2)
                    self.updater.apply_update(target_exe)
                else:
                    btn_cancel_download.visible = False
                    btn_update.visible = True
                    btn_update.disabled = False
                    btn_later.disabled = False
                    progress_bar.visible = False
                    lbl_status.value = "İndirme veya doğrulama başarısız oldu. Lütfen tekrar deneyin."
                    lbl_status.color = DANGER
                    self._safe_update(btn_cancel_download)
                    self._safe_update(btn_update)
                    self._safe_update(btn_later)
                    self._safe_update(progress_bar)
                    self._safe_update(lbl_status)

            threading.Thread(target=_download_task, daemon=True).start()

        def _open_github(_):
            url = info.html_url or f"https://github.com/{self.updater.repo_owner}/{self.updater.repo_name}/releases"
            try:
                webbrowser.open(url)
            except Exception:
                pass

        btn_update = ft.FilledButton(
            content=ft.Text("Şimdi Güncelle", size=12, weight=ft.FontWeight.BOLD),
            bgcolor=ACCENT_PRIMARY,
            color=TEXT_MAIN,
            disabled=not info.has_exe_asset,
            on_click=_start_download,
        )
        btn_cancel_download = ft.FilledButton(
            content=ft.Text("İptal Et", size=11, weight=ft.FontWeight.W_500),
            bgcolor=DANGER,
            color=TEXT_MAIN,
            visible=False,
            on_click=_cancel_download,
        )
        btn_github = ft.FilledButton(
            content=ft.Text("GitHub'da İncele", size=11, weight=ft.FontWeight.W_500),
            bgcolor=BTN_NEUTRAL,
            color=TEXT_MAIN,
            on_click=_open_github,
        )
        btn_later = ft.FilledButton(
            content=ft.Text("Daha Sonra", size=12, weight=ft.FontWeight.W_500),
            bgcolor=BTN_NEUTRAL,
            color=TEXT_MAIN,
            on_click=_close_dialog,
        )

        full_notes = info.release_notes.strip() if (info.release_notes and info.release_notes.strip()) else "Bu sürüm için değişiklik notu girilmemiş."

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Yeni Sürüm Mevcut: v{info.version}", size=16, weight=ft.FontWeight.BOLD, color=TEXT_MAIN),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(f"Mevcut Sürümünüz: v{self.APP_VERSION}", size=12, color=TEXT_SUBTLE),
                        ft.Text(f"Yayın Tarihi: {info.published_at[:10]}", size=12, color=TEXT_SUBTLE),
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Text("Sürüm Notları:", size=11, weight=ft.FontWeight.BOLD, color=ACCENT_LIGHT),
                                    ft.Markdown(
                                        full_notes,
                                        selectable=True,
                                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                                    ),
                                ],
                                spacing=6,
                                scroll=ft.ScrollMode.AUTO,
                            ),
                            bgcolor=INPUT_BG,
                            border=ft.Border.all(1, INPUT_BORDER),
                            border_radius=6,
                            padding=ft.Padding.all(10),
                            height=220,
                        ),
                        lbl_status,
                        progress_bar,
                    ],
                    spacing=8,
                    tight=True,
                ),
                width=520,
            ),
            actions=[btn_github, btn_cancel_download, btn_update, btn_later],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        if hasattr(self.page, "open"):
            self.page.open(dialog)
        else:
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()

    def check_and_prompt_prerequisites(self):
        """Uygulama baslangicinda FFmpeg gereksinimini denetler ve eksikse kurulum onerir."""
        def _check():
            try:
                from src.bootstrapper import DependencyBootstrapper
                bootstrapper = DependencyBootstrapper()
                status = bootstrapper.check_ffmpeg_status()
                if not status["installed"] and self.page:
                    self._show_ffmpeg_bootstrapper_dialog(bootstrapper)
            except Exception as e:
                print(f"Gereksinim denetimi atlandi: {e}")

        threading.Thread(target=_check, daemon=True).start()

    def _show_ffmpeg_bootstrapper_dialog(self, bootstrapper=None):
        """FFmpeg eksik oldugunda tek tikla otomatik indirme ve ayiklama modali sunar."""
        if not self.page:
            return

        if bootstrapper is None:
            from src.bootstrapper import DependencyBootstrapper
            bootstrapper = DependencyBootstrapper()

        progress_bar = ft.ProgressBar(value=0.0, visible=False, color=ACCENT, bgcolor=BORDER_SUBTLE)
        lbl_status = ft.Text(
            "Ses/video dosyalari ve YouTube medyalarini islemek icin FFmpeg gereklidir. Sisteminizde FFmpeg bulunamadi.",
            size=12,
            color=TEXT_MUTED,
        )

        cancel_event = threading.Event()

        def _close_dialog(e=None):
            cancel_event.set()
            if hasattr(self.page, "close"):
                self.page.close(dialog)
            else:
                dialog.open = False
                self.page.update()

        btn_later = ft.TextButton("Daha Sonra", on_click=_close_dialog)
        btn_install = ft.ElevatedButton(
            "Otomatik Indir ve Kur",
            bgcolor=ACCENT,
            color=TEXT_MAIN,
        )

        def _do_install(e):
            btn_install.disabled = True
            btn_later.disabled = True
            progress_bar.visible = True
            progress_bar.value = None
            lbl_status.value = "FFmpeg paketi hazirlaniyor..."
            self.page.update()

            def _progress(pct, msg):
                def _update():
                    if pct > 0:
                        progress_bar.value = pct
                    lbl_status.value = msg
                    if self.page:
                        self.page.update()
                if self.page:
                    if hasattr(self.page, "run_task"):
                        import asyncio
                        async def _coro():
                            _update()
                        self.page.run_task(_coro)
                    else:
                        _update()

            def _worker():
                success = bootstrapper.download_and_extract_ffmpeg(
                    progress_callback=_progress,
                    cancel_event=cancel_event,
                )
                def _done():
                    btn_later.disabled = False
                    if success:
                        lbl_status.value = "FFmpeg basariyla kuruldu ve etkinlestirildi."
                        lbl_status.color = SUCCESS
                        progress_bar.value = 1.0
                        btn_install.text = "Tamamlandi"
                        btn_later.text = "Kapat"
                    else:
                        lbl_status.value = "Kurulum tamamlanamadi. Lutfen internet baglantinizi kontrol edin."
                        lbl_status.color = ERROR
                        btn_install.disabled = False
                    if self.page:
                        self.page.update()

                if self.page:
                    if hasattr(self.page, "run_task"):
                        import asyncio
                        async def _coro_done():
                            _done()
                        self.page.run_task(_coro_done)
                    else:
                        _done()

            threading.Thread(target=_worker, daemon=True).start()

        btn_install.on_click = _do_install

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("FFmpeg Gereksinimi", size=16, weight=ft.FontWeight.BOLD, color=TEXT_MAIN),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        lbl_status,
                        progress_bar,
                    ],
                    spacing=12,
                    tight=True,
                ),
                width=420,
            ),
            actions=[btn_install, btn_later],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        if hasattr(self.page, "open"):
            self.page.open(dialog)
        else:
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()


def run_flet_app(page: ft.Page):
    """Flet masaüstü pencere başlatıcısı ve anında ön plana getirme."""
    page.title = f"SesMetin Pro - Turkce STT ve Konusmaci Ayrastirma (v{FletSpeechToTextApp.APP_VERSION})"
    page.bgcolor = BG_APP
    page.padding = 0
    page.spacing = 0

    # Pencere Boyutları, Görünürlük ve Doğrudan Ön Planda Odaklanma
    try:
        page.window.width = 1180
        page.window.height = 840
        page.window.min_width = 960
        page.window.min_height = 640
        page.window.visible = True
        page.window.opacity = 1.0
        page.window.focused = True
        try:
            if hasattr(page.window, "to_front"):
                page.window.to_front()
            elif hasattr(page.window, "bring_to_front"):
                page.window.bring_to_front()
        except Exception:
            pass

        try:
            if hasattr(page, "run_task"):
                page.run_task(page.window.center)
            else:
                page.window.center()
        except Exception:
            pass
        page.update()
    except Exception:
        pass

    app = FletSpeechToTextApp(page)
    if hasattr(page, "services") and app.file_picker not in page.services:
        page.services.append(app.file_picker)
    page.add(app.build_layout())
    app.play_entrance_animation()

    # 1. Guncelleme sonrasi ilk acilista yama notlarini goster
    patch_notes_shown = app.check_and_show_patch_notes()

    # 2. Yama notlari gosterilmediyse, ertelenmis bir guncelleme var mi kontrol et
    if not patch_notes_shown:
        postponed_prompted = app.check_and_prompt_postponed_update()
        if not postponed_prompted:
            app.start_background_update_check()
    else:
        app.start_background_update_check()

    app.check_and_prompt_prerequisites()

    # Pencereyi odakla ve ön planda tut; pencere opaklığını 1.0 olarak sabit tut (DWM şeffaflık hatasını önler)
    try:
        page.window.opacity = 1.0
        page.window.focused = True
        if hasattr(page.window, "to_front"):
            page.window.to_front()
        page.update()
    except Exception:
        pass


# Geriye dönük uyumluluk takma adı (alias)
SpeechToTextApp = FletSpeechToTextApp

