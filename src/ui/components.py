"""Modern CustomTkinter bileşenleri, kartlar, istatistik göstergeleri ve pencereler."""

import os
import threading
import tkinter as tk
from typing import Any, Callable, Dict, List, Optional, Tuple
import customtkinter as ctk

from src.ui.style import get_speaker_color, get_theme_palette


class ModernCard(ctk.CTkFrame):
    """Zarif kenarlıklı ve yuvarlatılmış köşeli modern kart çerçevesi."""

    def __init__(self, master, border_color="#232e40", fg_color="#131a26", corner_radius=12, **kwargs):
        super().__init__(
            master,
            corner_radius=corner_radius,
            border_width=1,
            border_color=border_color,
            fg_color=fg_color,
            **kwargs,
        )


class MetricBadge(ctk.CTkFrame):
    """Kompakt istatistik / metrik rozeti (İkon, Değer ve Başlık)."""

    def __init__(self, master, icon: str, title: str, value: str, **kwargs):
        super().__init__(
            master,
            fg_color="#0e141f",
            corner_radius=8,
            border_width=1,
            border_color="#1f2937",
            **kwargs,
        )
        self.pack_propagate(False)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=8, pady=4)

        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x")

        self.lbl_icon = ctk.CTkLabel(top_row, text=icon, font=ctk.CTkFont(size=14))
        self.lbl_icon.pack(side="left", padx=(0, 4))

        self.lbl_title = ctk.CTkLabel(
            top_row,
            text=title,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#94a3b8",
        )
        self.lbl_title.pack(side="left")

        self.lbl_val = ctk.CTkLabel(
            inner,
            text=value,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f8fafc",
            anchor="w",
        )
        self.lbl_val.pack(fill="x", pady=(2, 0))

    def update_value(self, new_value: str):
        """Metrik değerini günceller."""
        self.lbl_val.configure(text=new_value)


class ProcessStepper(ctk.CTkFrame):
    """Çok adımlı ilerleme durumunu görselleştiren şık gösterge çubuğu."""

    STEPS = [
        ("1. Medya", "📥"),
        ("2. İyileştirme", "🎧"),
        ("3. Whisper", "🎙️"),
        ("4. Konuşmacı", "👥"),
        ("5. Hizalama", "✨"),
    ]

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#0e141f", corner_radius=10, border_width=1, border_color="#243042", **kwargs)
        self.step_labels: List[Tuple[ctk.CTkLabel, ctk.CTkLabel]] = []
        self._build_steps()

    def _build_steps(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=10, pady=8)

        total = len(self.STEPS)
        for idx, (title, icon) in enumerate(self.STEPS):
            step_box = ctk.CTkFrame(container, fg_color="transparent")
            step_box.pack(side="left", expand=True, fill="x")

            lbl_badge = ctk.CTkLabel(
                step_box,
                text=f" {icon} {title} ",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="#64748b",
                fg_color="#182232",
                corner_radius=6,
                height=24,
            )
            lbl_badge.pack()

            self.step_labels.append(lbl_badge)

    def set_active_step(self, step_index: int):
        """Aktif adımı görsel olarak öne çıkarır (0-indexed)."""
        for idx, badge in enumerate(self.step_labels):
            if idx < step_index:
                # Tamamlanan adım (Yeşil)
                badge.configure(
                    fg_color="#064e3b",
                    text_color="#34d399",
                )
            elif idx == step_index:
                # Aktif adım (Mavi / Parlak)
                badge.configure(
                    fg_color="#1e3a8a",
                    text_color="#60a5fa",
                )
            else:
                # Bekleyen adım (Gri)
                badge.configure(
                    fg_color="#182232",
                    text_color="#64748b",
                )

    def reset(self):
        """Tüm adımları başlangıç durumuna sıfırlar."""
        for badge in self.step_labels:
            badge.configure(fg_color="#182232", text_color="#64748b")


class AudioPlayerBar(ctk.CTkFrame):
    """Yerel ses önizlemesi için oynat/durdur çubuğu."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#0f141d", corner_radius=8, border_width=1, border_color="#222c3d", **kwargs)
        self.audio_path: Optional[str] = None
        self.is_playing = False
        self._build_ui()

    def _build_ui(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=8, pady=6)

        self.btn_play = ctk.CTkButton(
            bar,
            text="▶ Önizle",
            width=80,
            height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#1e293b",
            hover_color="#334155",
            command=self.toggle_playback,
        )
        self.btn_play.pack(side="left")

        self.lbl_audio_status = ctk.CTkLabel(
            bar,
            text="Ses önizlemesi hazır değil",
            font=ctk.CTkFont(size=11),
            text_color="#64748b",
        )
        self.lbl_audio_status.pack(side="left", padx=10)

    def set_audio_source(self, wav_path: Optional[str], duration_str: str = ""):
        """Oynatılacak ses kaynağını belirler."""
        self.audio_path = wav_path
        if wav_path and os.path.exists(wav_path):
            self.lbl_audio_status.configure(
                text=f"🔊 Ses hazır ({duration_str})" if duration_str else "🔊 Ses hazır",
                text_color="#38bdf8",
            )
            self.btn_play.configure(state="normal")
        else:
            self.lbl_audio_status.configure(text="Ses önizlemesi hazır değil", text_color="#64748b")
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
        """Windows yerel winsound veya arka plan iş parçacığıyla ses çalar."""
        try:
            import winsound
            winsound.PlaySound(self.audio_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            self.is_playing = True
            self.btn_play.configure(text="⏸ Durdur", fg_color="#ef4444", hover_color="#dc2626")
            self.lbl_audio_status.configure(text="▶ Çalınıyor...", text_color="#34d399")
        except Exception as e:
            self.lbl_audio_status.configure(text=f"Çalma hatası: {e}", text_color="#ef4444")

    def stop_playback(self):
        """Oynatmayı durdurur."""
        try:
            import winsound
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass
        self.is_playing = False
        self.btn_play.configure(text="▶ Önizle", fg_color="#1e293b", hover_color="#334155")
        self.lbl_audio_status.configure(text="🔊 Duraklatıldı", text_color="#38bdf8")


class ToastNotification:
    """Arayüzde geçici bildirim mesajı gösteren modern toast balonu."""

    @staticmethod
    def show(parent, message: str, color: str = "#10b981", duration_ms: int = 2500):
        toast = ctk.CTkFrame(
            parent,
            fg_color=color,
            corner_radius=8,
            border_width=0,
        )
        lbl = ctk.CTkLabel(
            toast,
            text=f"  {message}  ",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ffffff",
            height=32,
        )
        lbl.pack(padx=14, pady=6)

        # Sağ üst köşeye yerleştir
        toast.place(relx=0.98, rely=0.03, anchor="ne")

        def dismiss():
            try:
                toast.destroy()
            except Exception:
                pass

        parent.after(duration_ms, dismiss)


class RenameSpeakerDialog(ctk.CTkToplevel):
    """Konuşmacı adını topluca değiştirmek için açılan modern diyalog penceresi."""

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
        self.geometry("400x240")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Ekranın ortasına konumlandır
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 200
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 120
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=22, pady=20)

        # Başlık ve Rozet
        bg_col, fg_col = get_speaker_color(self.current_name)
        header_row = ctk.CTkFrame(container, fg_color="transparent")
        header_row.pack(anchor="w", pady=(0, 6))

        badge = ctk.CTkLabel(
            header_row,
            text=f" {self.current_name} ",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=bg_col,
            text_color=fg_col,
            corner_radius=6,
        )
        badge.pack(side="left", padx=(0, 8))

        title = ctk.CTkLabel(
            header_row,
            text="Etiketini Değiştir",
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        title.pack(side="left")

        desc = ctk.CTkLabel(
            container,
            text="Bu değişiklik transkriptteki tüm ilgili konuşma segmentlerine anında uygulanacaktır:",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
            wraplength=350,
            justify="left",
        )
        desc.pack(anchor="w", pady=(0, 14))

        self.entry = ctk.CTkEntry(
            container,
            placeholder_text="Örn: Ahmet Yılmaz, Moderatör...",
            height=38,
            font=ctk.CTkFont(size=13),
        )
        self.entry.insert(0, self.current_name)
        self.entry.pack(fill="x", pady=(0, 20))
        self.entry.focus_set()
        self.entry.bind("<Return>", lambda e: self._confirm())

        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x")

        cancel_btn = ctk.CTkButton(
            btn_box,
            text="İptal",
            fg_color="#334155",
            hover_color="#475569",
            width=90,
            height=34,
            command=self.destroy,
        )
        cancel_btn.pack(side="right", padx=(8, 0))

        save_btn = ctk.CTkButton(
            btn_box,
            text="💾 Güncelle",
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            width=110,
            height=34,
            command=self._confirm,
        )
        save_btn.pack(side="right")

    def _confirm(self):
        new_name = self.entry.get().strip()
        if new_name and new_name != self.current_name:
            self.on_save(self.current_name, new_name)
        self.destroy()


class SpeakerManagerModal(ctk.CTkToplevel):
    """Transkriptteki tüm konuşmacıların özetini ve toplu yönetimini sağlayan pencere."""

    def __init__(
        self,
        parent,
        transcript: List[Dict[str, Any]],
        on_rename: Callable[[str, str], None],
    ):
        super().__init__(parent)
        self.transcript = transcript
        self.on_rename = on_rename

        self.title("👥 Konuşmacı Yönetimi")
        self.geometry("480x420")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 240
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 210
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        header = ctk.CTkLabel(
            container,
            text="👥 Tespit Edilen Konuşmacılar",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        header.pack(anchor="w", pady=(0, 6))

        desc = ctk.CTkLabel(
            container,
            text="Aşağıdan herhangi bir konuşmacının ismini değiştirebilirsiniz:",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
        )
        desc.pack(anchor="w", pady=(0, 14))

        from src.aligner import compute_transcript_statistics
        stats = compute_transcript_statistics(self.transcript)
        spk_times = stats.get("speaker_speaking_times", {})
        spk_turns = stats.get("speaker_turn_counts", {})

        scroll = ctk.CTkScrollableFrame(container, fg_color="#111622", height=240, corner_radius=8)
        scroll.pack(fill="both", expand=True, pady=(0, 16))

        for spk, total_sec in spk_times.items():
            row = ctk.CTkFrame(scroll, fg_color="#182030", corner_radius=8)
            row.pack(fill="x", pady=4, padx=4)

            # Sol Rozet
            bg_col, fg_col = get_speaker_color(spk)
            badge = ctk.CTkLabel(
                row,
                text=f" {spk} ",
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=bg_col,
                text_color=fg_col,
                corner_radius=6,
                height=26,
            )
            badge.pack(side="left", padx=10, pady=8)

            # İstatistik Metni
            turn_cnt = spk_turns.get(spk, 0)
            mins = int(total_sec // 60)
            secs = int(total_sec % 60)
            time_str = f"{mins:02d}:{secs:02d}"
            info_lbl = ctk.CTkLabel(
                row,
                text=f"Süre: {time_str} • {turn_cnt} konuşma",
                font=ctk.CTkFont(size=12),
                text_color="#cbd5e1",
            )
            info_lbl.pack(side="left", padx=10)

            # Değiştir Butonu
            def make_handler(target_spk):
                def handle():
                    self.destroy()
                    RenameSpeakerDialog(self.master, target_spk, self.on_rename)
                return handle

            btn_edit = ctk.CTkButton(
                row,
                text="✏️ Düzenle",
                width=80,
                height=28,
                font=ctk.CTkFont(size=11),
                fg_color="#2563eb",
                hover_color="#1d4ed8",
                command=make_handler(spk),
            )
            btn_edit.pack(side="right", padx=10)

        btn_close = ctk.CTkButton(
            container,
            text="Kapat",
            height=34,
            fg_color="#334155",
            hover_color="#475569",
            command=self.destroy,
        )
        btn_close.pack(fill="x")
