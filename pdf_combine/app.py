from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from pdf_combine.resources import configure_tk_environment
from pdf_combine.services.pdf_service import PdfCombineService, PdfDependencyLoader
from pdf_combine.ui.main_window import PdfCombineWindow


def main():
    configure_tk_environment()

    root = tk.Tk()
    style = ttk.Style(root)
    try:
        style.theme_use("vista")
    except tk.TclError:
        pass

    dependency_loader = PdfDependencyLoader()
    combine_service = PdfCombineService(dependency_loader)
    app = PdfCombineWindow(root, combine_service, dependency_loader)

    if not dependency_loader.is_available():
        app.status_var.set(
            "Instala pypdf en el Python actual para habilitar la combinacion."
        )

    root.mainloop()
