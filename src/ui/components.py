"""Özelleştirilmiş CustomTkinter bileşenleri ve iletişim pencereleri."""

import tkinter as tk
from typing import Callable, Optional
import customtkinter as ctk

from src.ui.style import get_speaker_color


class CardFrame(ctk.CTkFrame):
    """Modern görünümlü kart çerçevesi."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            corner_radius=10,
            border_width=1,
            border_color="#2d3343",
            fg_color="#1a1e29",
            **kwargs,
        )


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
        self.geometry("380x220")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Ekranın ortasına konumlandır
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 190
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 110
        self.geometry(f"+{max(0, x)}+{max(0, y)}")

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        title = ctk.CTkLabel(
            container,
            text=f"'{self.current_name}' Etiketini Değiştir",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        title.pack(anchor="w", pady=(0, 5))

        desc = ctk.CTkLabel(
            container,
            text="Bu değişiklik transkriptteki tüm ilgili konuşmalara uygulanacaktır:",
            font=ctk.CTkFont(size=12),
            text_color="#9ca3af",
            wraplength=340,
            justify="left",
        )
        desc.pack(anchor="w", pady=(0, 15))

        self.entry = ctk.CTkEntry(
            container,
            placeholder_text="Örn: Ahmet Yılmaz, Mülakatçı...",
            height=36,
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
            fg_color="#374151",
            hover_color="#4b5563",
            width=90,
            height=32,
            command=self.destroy,
        )
        cancel_btn.pack(side="right", padx=(8, 0))

        save_btn = ctk.CTkButton(
            btn_box,
            text="Güncelle",
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            width=100,
            height=32,
            command=self._confirm,
        )
        save_btn.pack(side="right")

    def _confirm(self):
        new_name = self.entry.get().strip()
        if new_name and new_name != self.current_name:
            self.on_save(self.current_name, new_name)
        self.destroy()
