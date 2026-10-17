"""Windows 11 Fluent Design masaüstü bileşenleri, kartlar, istatistik göstergeleri ve pencereler."""

import os
import tkinter as tk
from typing import Any, Callable, Dict, List, Optional, Tuple
import customtkinter as ctk

from src.ui.style import FONT_FAMILY, FONT_FALLBACK, get_speaker_color, get_theme_palette


class ModernCard(ctk.CTkFrame):
    """Windows 11 Fluent yükseltilmiş yüzey kartı."""

    def __init__(self, master, border_color="#383838", fg_color="#2b2b2b", corner_radius=8, **kwargs):
        super().__init__(
            master,
            corner_radius=corner_radius,
            border_width=1,
            border_color=border_color,
            fg_color=fg_color,
            **kwargs,
        )


class MetricBadge(ctk.CTkFrame):
    """Windows 11 Fluent metrik göstergesi (Başlık ve Değer)."""

    def __init__(self, master, title: str, value: str, **kwargs):
        super().__init__(
            master,
            fg_color="#262626",
            corner_radius=6,
            border_width=1,
            border_color="#383838",
            **kwargs,
        )
        self.pack_propagate(False)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=10, pady=5)

        self.lbl_title = ctk.CTkLabel(
            inner,
            text=title.upper(),
            font=ctk.CTkFont(family=FONT_FAMILY, size=9, weight="bold"),
            text_color="#9e9e9e",
            anchor="w",
        )
        self.lbl_title.pack(fill="x")

        self.lbl_val = ctk.CTkLabel(
            inner,
            text=value,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color="#ffffff",
            anchor="w",
        )
        self.lbl_val.pack(fill="x", pady=(2, 0))

    def update_value(self, new_value: str):
        """Metrik değerini günceller."""
        self.lbl_val.configure(text=new_value)


class ProcessStepper(ctk.CTkFrame):
    """Çok adımlı boru hattı ilerleme durumunu gösteren Windows 11 gösterge çubuğu."""

    STEPS = [
        ("media", "1. Medya"),
        ("enhance", "2. Filtre"),
        ("whisper", "3. Whisper"),
        ("diarize", "4. Konuşmacı"),
        ("align", "5. Hizalama"),
    ]

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#242424", corner_radius=6, border_width=1, border_color="#383838", **kwargs)
        self.step_labels: List[ctk.CTkLabel] = []
        self._build_steps()

    def _build_steps(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=6, pady=5)

        for step_item in self.STEPS:
            title = step_item[1] if isinstance(step_item, (tuple, list)) else step_item
            step_box = ctk.CTkFrame(container, fg_color="transparent")
            step_box.pack(side="left", expand=True, fill="x", padx=2)

            lbl_badge = ctk.CTkLabel(
                step_box,
                text=f" {title} ",
                font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
                text_color="#888888",
                fg_color="#2d2d2d",
                corner_radius=4,
                height=22,
            )
            lbl_badge.pack(fill="x")

            self.step_labels.append(lbl_badge)

    def set_active_step(self, step_index: int):
        """Aktif adımı görsel olarak öne çıkarır (0-indexed)."""
        for idx, badge in enumerate(self.step_labels):
            if idx < step_index:
                # Tamamlanan adım (Sakin Fluent vurgu)
                badge.configure(
                    fg_color="#1a365d",
                    text_color="#60cdff",
                )
            elif idx == step_index:
                # Aktif adım (Windows 11 Birincil Vurgu)
                badge.configure(
                    fg_color="#1a365d",
                    text_color="#60a5fa",
                )
            else:
                # Bekleyen adım (Sade Nötr)
                badge.configure(
                    fg_color="#2d2d2d",
                    text_color="#888888",
                )

    def reset(self):
        """Tüm adımları başlangıç durumuna sıfırlar."""
        for badge in self.step_labels:
            badge.configure(fg_color="#2d2d2d", text_color="#888888")


class AudioPlayerBar(ctk.CTkFrame):
    """Yerel ses önizlemesi için sade oynat/durdur çubuğu."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#242424", corner_radius=6, border_width=1, border_color="#383838", **kwargs)
        self.audio_path: Optional[str] = None
        self.is_playing = False
        self._build_ui()

    def _build_ui(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=8, pady=5)

        self.btn_play = ctk.CTkButton(
            bar,
            text="Önizle",
            width=65,
            height=26,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            fg_color="#333333",
            hover_color="#404040",
            command=self.toggle_playback,
        )
        self.btn_play.pack(side="left")

        self.lbl_audio_status = ctk.CTkLabel(
            bar,
            text="Ses hazır değil",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color="#888888",
        )
        self.lbl_audio_status.pack(side="left", padx=8)

    def set_audio_source(self, wav_path: Optional[str], duration_str: str = ""):
        """Oynatılacak ses kaynağını belirler."""
        self.audio_path = wav_path
        if wav_path and os.path.exists(wav_path):
            self.lbl_audio_status.configure(
                text=f"Ses hazır ({duration_str})" if duration_str else "Ses hazır",
                text_color="#60cdff",
            )
            self.btn_play.configure(state="normal")
        else:
            self.lbl_audio_status.configure(text="Ses hazır değil", text_color="#888888")
            self.btn_play.configure(state="disabled")

    def toggle_playback(self):
        """Ses oynatmasını başlatır veya durdurur."""
        if not self.audio_path or not os.path.exists(self.audio_path):
            return

        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()

    def start_playback(self):
        """Windows yerel winsound ile ses çalar."""
        try:
            import winsound
            winsound.PlaySound(self.audio_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            self.is_playing = True
            self.btn_play.configure(text="Durdur", fg_color="#e11d48", hover_color="#be123c")
            self.lbl_audio_status.configure(text="Çalınıyor...", text_color="#60cdff")
        except Exception as e:
            self.lbl_audio_status.configure(text=f"Hata: {e}", text_color="#e11d48")

    def stop_playback(self):
        """Oynatmayı durdurur."""
        try:
            import winsound
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass
        self.is_playing = False
        self.btn_play.configure(text="Önizle", fg_color="#333333", hover_color="#404040")
        self.lbl_audio_status.configure(text="Duraklatıldı", text_color="#60cdff")


class ToastNotification:
    """Arayüzde Windows 11 Fluent tarzı bildirim mesajı gösteren metin kutusu."""

    @staticmethod
    def show(parent, message: str, color: str = "#0078d4", duration_ms: int = 2200):
        toast = ctk.CTkFrame(
            parent,
            fg_color="#2b2b2b",
            corner_radius=6,
            border_width=1,
            border_color="#484848",
        )
        lbl = ctk.CTkLabel(
            toast,
            text=f"  {message}  ",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color="#ffffff",
            height=28,
        )
        lbl.pack(padx=12, pady=4)

        toast.place(relx=0.98, rely=0.03, anchor="ne")

        def dismiss():
            try:
                toast.destroy()
            except Exception:
                pass

        parent.after(duration_ms, dismiss)


class RenameSpeakerDialog(ctk.CTkToplevel):
    """Konuşmacı adını topluca değiştirmek için açılan minimalist diyalog penceresi."""

    def __init__(
        self,
        parent,
        current_name: str,
        on_save: Callable[[str, str], None],
    ):
        super().__init__(parent)
        self.current_name = current_name
        self.on_save = on_save

        self.title("Konuşmacıyı Yeniden Adlandır")
        self.geometry("380x210")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 190
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 105
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=16)

        bg_col, fg_col = get_speaker_color(self.current_name)
        header_row = ctk.CTkFrame(container, fg_color="transparent")
        header_row.pack(anchor="w", pady=(0, 6))

        badge = ctk.CTkLabel(
            header_row,
            text=f" {self.current_name} ",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            fg_color=bg_col,
            text_color=fg_col,
            corner_radius=4,
        )
        badge.pack(side="left", padx=(0, 8))

        title = ctk.CTkLabel(
            header_row,
            text="Etiketini Değiştir",
            font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
        )
        title.pack(side="left")

        desc = ctk.CTkLabel(
            container,
            text="Bu değişiklik tüm ilgili konuşma segmentlerine anında uygulanacaktır:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color="#a6a6a6",
            wraplength=340,
            justify="left",
        )
        desc.pack(anchor="w", pady=(0, 12))

        self.entry = ctk.CTkEntry(
            container,
            placeholder_text="Örn: Ahmet Yılmaz, Konuşmacı A...",
            height=32,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
        )
        self.entry.insert(0, self.current_name)
        self.entry.pack(fill="x", pady=(0, 16))
        self.entry.focus_set()
        self.entry.bind("<Return>", lambda e: self._confirm())

        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x")

        cancel_btn = ctk.CTkButton(
            btn_box,
            text="İptal",
            fg_color="#333333",
            hover_color="#404040",
            width=80,
            height=30,
            command=self.destroy,
        )
        cancel_btn.pack(side="right", padx=(8, 0))

        save_btn = ctk.CTkButton(
            btn_box,
            text="Güncelle",
            fg_color="#0078d4",
            hover_color="#1084d9",
            width=90,
            height=30,
            command=self._confirm,
        )
        save_btn.pack(side="right")

    def _confirm(self):
        new_name = self.entry.get().strip()
        if new_name and new_name != self.current_name:
            self.on_save(self.current_name, new_name)
        self.destroy()


class SpeakerManagerModal(ctk.CTkToplevel):
    """Transkriptteki tüm konuşmacıların özetini ve yönetimini sağlayan Windows 11 Fluent penceresi."""

    def __init__(
        self,
        parent,
        transcript: List[Dict[str, Any]],
        on_rename: Callable[[str, str], None],
    ):
        super().__init__(parent)
        self.transcript = transcript
        self.on_rename = on_rename

        self.title("Konuşmacı Yönetimi")
        self.geometry("460x380")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 230
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 190
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=18, pady=16)

        header = ctk.CTkLabel(
            container,
            text="Tespit Edilen Konuşmacılar",
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
        )
        header.pack(anchor="w", pady=(0, 4))

        desc = ctk.CTkLabel(
            container,
            text="Konuşmacı isimlerini aşağıdan güncelleyebilirsiniz:",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color="#a6a6a6",
        )
        desc.pack(anchor="w", pady=(0, 12))

        from src.aligner import compute_transcript_statistics
        stats = compute_transcript_statistics(self.transcript)
        spk_times = stats.get("speaker_speaking_times", {})
        spk_turns = stats.get("speaker_turn_counts", {})

        scroll = ctk.CTkScrollableFrame(container, fg_color="#202020", height=220, corner_radius=6)
        scroll.pack(fill="both", expand=True, pady=(0, 14))

        for spk, total_sec in spk_times.items():
            row = ctk.CTkFrame(scroll, fg_color="#2b2b2b", corner_radius=6, border_width=1, border_color="#383838")
            row.pack(fill="x", pady=3, padx=3)

            bg_col, fg_col = get_speaker_color(spk)
            badge = ctk.CTkLabel(
                row,
                text=f" {spk} ",
                font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
                fg_color=bg_col,
                text_color=fg_col,
                corner_radius=4,
                height=24,
            )
            badge.pack(side="left", padx=8, pady=6)

            turn_cnt = spk_turns.get(spk, 0)
            mins = int(total_sec // 60)
            secs = int(total_sec % 60)
            time_str = f"{mins:02d}:{secs:02d}"
            info_lbl = ctk.CTkLabel(
                row,
                text=f"Süre: {time_str} ({turn_cnt} segment)",
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                text_color="#ffffff",
            )
            info_lbl.pack(side="left", padx=8)

            def make_handler(target_spk):
                def handle():
                    self.destroy()
                    RenameSpeakerDialog(self.master, target_spk, self.on_rename)
                return handle

            btn_edit = ctk.CTkButton(
                row,
                text="Düzenle",
                width=65,
                height=26,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                fg_color="#0078d4",
                hover_color="#1084d9",
                command=make_handler(spk),
            )
            btn_edit.pack(side="right", padx=8)

        btn_close = ctk.CTkButton(
            container,
            text="Kapat",
            height=32,
            fg_color="#333333",
            hover_color="#404040",
            command=self.destroy,
        )
        btn_close.pack(fill="x")
