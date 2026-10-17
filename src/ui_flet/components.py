"""Flet tabanlı Windows 11 Fluent arayüz bileşenleri."""

import os
from typing import Callable, Dict, List, Optional
import flet as ft

from src.ui_flet.theme import (
    ACCENT_LIGHT,
    ACCENT_PRIMARY,
    BG_CARD,
    BG_CARD_SECONDARY,
    BORDER_CARD,
    BTN_NEUTRAL,
    DANGER,
    INPUT_BG,
    INPUT_BORDER,
    TEXT_MAIN,
    TEXT_MUTED,
    TEXT_SUBTLE,
    get_speaker_color,
)


class MetricCard(ft.Container):
    """Windows 11 Fluent metrik göstergesi (Başlık ve Değer)."""

    def __init__(self, title: str, value: str, **kwargs):
        self.lbl_title = ft.Text(
            value=title.upper(),
            size=10,
            weight=ft.FontWeight.BOLD,
            color=TEXT_SUBTLE,
        )
        self.lbl_val = ft.Text(
            value=value,
            size=15,
            weight=ft.FontWeight.BOLD,
            color=TEXT_MAIN,
        )

        super().__init__(
            content=ft.Column(
                controls=[self.lbl_title, self.lbl_val],
                spacing=2,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            bgcolor=BG_CARD_SECONDARY,
            border_radius=6,
            border=ft.Border.all(1, BORDER_CARD),
            padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            expand=True,
            **kwargs,
        )

    def update_value(self, new_val: str):
        """Metrik değerini günceller."""
        self.lbl_val.value = new_val
        try:
            self.lbl_val.update()
        except Exception:
            pass


class ProcessStepper(ft.Container):
    """5 adımlı ses tanıma boru hattı ilerleme göstergesi."""

    STEPS = [
        ("media", "1. Medya"),
        ("enhance", "2. Filtre"),
        ("whisper", "3. Whisper"),
        ("diarize", "4. Konuşmacı"),
        ("align", "5. Hizalama"),
    ]

    def __init__(self, **kwargs):
        self.current_step = -1
        self.step_containers: List[ft.Container] = []
        self.step_labels: List[ft.Text] = []

        controls = []
        for _, label in self.STEPS:
            lbl = ft.Text(
                value=label,
                size=11,
                weight=ft.FontWeight.W_600,
                color=TEXT_SUBTLE,
                text_align=ft.TextAlign.CENTER,
            )
            cnt = ft.Container(
                content=lbl,
                bgcolor=BTN_NEUTRAL,
                border_radius=4,
                padding=ft.Padding.symmetric(vertical=5, horizontal=6),
                alignment=ft.Alignment.CENTER,
                expand=True,
            )
            self.step_labels.append(lbl)
            self.step_containers.append(cnt)
            controls.append(cnt)

        super().__init__(
            content=ft.Row(controls=controls, spacing=4),
            bgcolor=BG_CARD_SECONDARY,
            border_radius=6,
            border=ft.Border.all(1, BORDER_CARD),
            padding=ft.Padding.all(6),
            **kwargs,
        )

    def set_active_step(self, step_index: int):
        """Aktif adımı görsel olarak öne çıkarır (0-indexed)."""
        self.current_step = step_index
        for idx, (cnt, lbl) in enumerate(zip(self.step_containers, self.step_labels)):
            if idx < step_index:
                # Tamamlanan adım
                cnt.bgcolor = "#1a365d"
                lbl.color = ACCENT_LIGHT
            elif idx == step_index:
                # Aktif adım
                cnt.bgcolor = ACCENT_PRIMARY
                lbl.color = "#ffffff"
            else:
                # Bekleyen adım
                cnt.bgcolor = BTN_NEUTRAL
                lbl.color = TEXT_SUBTLE

        try:
            self.update()
        except Exception:
            pass

    def reset(self):
        """Tüm adımları başlangıç durumuna sıfırlar."""
        self.current_step = -1
        for cnt, lbl in zip(self.step_containers, self.step_labels):
            cnt.bgcolor = BTN_NEUTRAL
            lbl.color = TEXT_SUBTLE
        try:
            self.update()
        except Exception:
            pass


class AudioPlayerBar(ft.Container):
    """Yerel ses dosyası için minimalist oynatıcı çubuğu."""

    def __init__(self, **kwargs):
        self.audio_path: Optional[str] = None
        self.is_playing = False

        self.btn_play = ft.Button(
            content="Önizle",
            bgcolor=BTN_NEUTRAL,
            color=TEXT_MAIN,
            height=28,
            disabled=True,
            on_click=lambda _: self.toggle_playback(),
        )

        self.lbl_status = ft.Text(
            value="Ses hazır değil",
            size=11,
            color=TEXT_SUBTLE,
        )

        super().__init__(
            content=ft.Row(
                controls=[
                    self.btn_play,
                    self.lbl_status,
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=BG_CARD_SECONDARY,
            border_radius=6,
            border=ft.Border.all(1, BORDER_CARD),
            padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            **kwargs,
        )

    def set_audio_source(self, wav_path: Optional[str], duration_str: str = ""):
        """Oynatılacak ses dosyasını tanımlar."""
        self.audio_path = wav_path
        if wav_path and os.path.exists(wav_path):
            self.lbl_status.value = f"Ses hazır ({duration_str})" if duration_str else "Ses hazır"
            self.lbl_status.color = ACCENT_LIGHT
            self.btn_play.disabled = False
        else:
            self.lbl_status.value = "Ses hazır değil"
            self.lbl_status.color = TEXT_SUBTLE
            self.btn_play.disabled = True

        try:
            self.update()
        except Exception:
            pass

    def toggle_playback(self):
        """Oynatmayı başlatır veya durdurur."""
        if not self.audio_path or not os.path.exists(self.audio_path):
            return

        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()

    def start_playback(self):
        """Yerel ses çalmayı başlatır."""
        try:
            import winsound
            winsound.PlaySound(self.audio_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            self.is_playing = True
            self.btn_play.content = "Durdur"
            self.btn_play.bgcolor = DANGER
            self.lbl_status.value = "Çalınıyor..."
            self.lbl_status.color = ACCENT_LIGHT
        except Exception as e:
            self.lbl_status.value = f"Hata: {e}"
            self.lbl_status.color = DANGER

        try:
            self.update()
        except Exception:
            pass

    def stop_playback(self):
        """Ses oynatmasını durdurur."""
        try:
            import winsound
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass
        self.is_playing = False
        self.btn_play.content = "Önizle"
        self.btn_play.bgcolor = BTN_NEUTRAL
        self.lbl_status.value = "Ses durduruldu"
        self.lbl_status.color = TEXT_SUBTLE

        try:
            self.update()
        except Exception:
            pass


class TranscriptTurnCard(ft.Container):
    """Bir konuşma parçası kartı (Konuşmacı, Zaman, Metin)."""

    def __init__(
        self,
        turn_data: Dict[str, any],
        on_text_change: Optional[Callable[[int, str], None]] = None,
        on_copy_click: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        self.turn_id = turn_data.get("id", 0)
        speaker = turn_data.get("speaker", "X1")
        text = turn_data.get("text", "")
        start_sec = turn_data.get("start", 0.0)
        end_sec = turn_data.get("end", 0.0)

        # Zaman etiketi formatı
        time_str = f"[{int(start_sec//60):02d}:{int(start_sec%60):02d} - {int(end_sec//60):02d}:{int(end_sec%60):02d}]"
        spk_color = get_speaker_color(speaker)

        spk_badge = ft.Container(
            content=ft.Text(
                value=speaker,
                size=11,
                weight=ft.FontWeight.BOLD,
                color=spk_color,
            ),
            bgcolor=INPUT_BG,
            border=ft.Border.all(1, spk_color),
            border_radius=4,
            padding=ft.Padding.symmetric(horizontal=8, vertical=2),
        )

        time_lbl = ft.Text(
            value=time_str,
            size=11,
            color=TEXT_SUBTLE,
        )

        btn_copy = ft.IconButton(
            icon=ft.Icons.COPY,
            icon_size=14,
            icon_color=TEXT_SUBTLE,
            tooltip="Bu satırı kopyala",
            on_click=lambda _: on_copy_click(f"{speaker} {time_str}: {self.txt_field.value}") if on_copy_click else None,
        )

        header_row = ft.Row(
            controls=[spk_badge, time_lbl, ft.Container(expand=True), btn_copy],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        self.txt_field = ft.TextField(
            value=text,
            multiline=True,
            min_lines=1,
            max_lines=6,
            border_color="transparent",
            bgcolor="transparent",
            color=TEXT_MAIN,
            text_size=12,
            content_padding=ft.Padding.all(0),
            on_change=lambda e: on_text_change(self.turn_id, e.control.value) if on_text_change else None,
        )

        super().__init__(
            content=ft.Column(
                controls=[header_row, self.txt_field],
                spacing=4,
            ),
            bgcolor=BG_CARD,
            border=ft.Border.all(1, BORDER_CARD),
            border_radius=6,
            padding=ft.Padding.all(10),
            margin=ft.Margin.only(bottom=8),
            **kwargs,
        )
