from __future__ import annotations

import queue
from pathlib import Path
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from pdf_combine import DEVELOPER_EMAIL, DEVELOPER_HANDLE, DEVELOPER_NAME
from pdf_combine.models import (
    CombineRequest,
    CombineResult,
    ErrorEvent,
    PdfItem,
    ProgressEvent,
    StatusEvent,
)
from pdf_combine.resources import resource_path
from pdf_combine.services.pdf_service import PdfCombineService, PdfDependencyError, PdfDependencyLoader
from pdf_combine.ui.widgets import DragDropListbox


class PdfCombineWindow:
    def __init__(
        self,
        root: tk.Tk,
        combine_service: PdfCombineService,
        dependency_loader: PdfDependencyLoader,
    ):
        self.root = root
        self.combine_service = combine_service
        self.dependency_loader = dependency_loader

        self.root.title("Combinador de PDF")
        self.root.geometry("780x520")
        self.root.minsize(720, 460)

        self.app_icon: tk.PhotoImage | None = None
        self.items: list[PdfItem] = []
        self.status_var = tk.StringVar(value="Agrega dos o mas PDF para empezar.")
        self.target_size_var = tk.StringVar(value="max")
        self.loader_var = tk.StringVar(value="Preparando documentos...")
        self.action_widgets: list[tk.Widget] = []
        self.worker_queue: queue.Queue[
            ProgressEvent | StatusEvent | CombineResult | ErrorEvent
        ] = queue.Queue()
        self.worker_thread: threading.Thread | None = None
        self.is_processing = False

        self._build_ui()
        self._set_window_icon()

    def _set_window_icon(self):
        icon_path = resource_path("logo_pdf_app.png")
        if not icon_path.exists():
            return

        try:
            self.app_icon = tk.PhotoImage(file=str(icon_path))
            self.root.iconphoto(True, self.app_icon)
        except tk.TclError:
            self.app_icon = None

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        header = ttk.Frame(self.root, padding=(16, 16, 16, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="Combinar PDF con paginas normalizadas",
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text=(
                "Carga 2 o mas archivos, ordenalos manualmente y genera un unico PDF "
                "con todas las paginas en un tamano uniforme."
            ),
            wraplength=700,
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        content = ttk.Frame(self.root, padding=(16, 0, 16, 16))
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=0)
        content.rowconfigure(1, weight=1)

        controls = ttk.Frame(content)
        controls.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        controls.columnconfigure(5, weight=1)

        add_button = ttk.Button(controls, text="Agregar PDF", command=self.add_files)
        add_button.grid(row=0, column=0, padx=(0, 8))
        remove_button = ttk.Button(controls, text="Quitar seleccionado", command=self.remove_selected)
        remove_button.grid(row=0, column=1, padx=(0, 8))
        clear_button = ttk.Button(controls, text="Limpiar lista", command=self.clear_files)
        clear_button.grid(row=0, column=2, padx=(0, 16))

        ttk.Label(controls, text="Tamano final:").grid(row=0, column=3, padx=(0, 8))
        size_combo = ttk.Combobox(
            controls,
            textvariable=self.target_size_var,
            state="readonly",
            values=["max", "first"],
            width=16,
        )
        size_combo.grid(row=0, column=4, padx=(0, 12))
        size_combo.set("max")

        ttk.Label(
            controls,
            text="max: usa el tamano mas grande encontrado. first: usa la primera pagina.",
        ).grid(row=0, column=5, sticky="w")

        list_frame = ttk.LabelFrame(
            content,
            text="Archivos cargados",
            padding=(12, 12, 12, 12),
        )
        list_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.file_list = DragDropListbox(
            list_frame,
            on_reorder=self.reorder_items,
            activestyle="none",
            selectmode=tk.SINGLE,
            font=("Segoe UI", 10),
        )
        self.file_list.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_list.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_list.configure(yscrollcommand=scrollbar.set)

        side_actions = ttk.Frame(content)
        side_actions.grid(row=1, column=1, sticky="ns")

        move_up_button = ttk.Button(side_actions, text="Subir", command=self.move_selected_up, width=16)
        move_up_button.grid(row=0, column=0, pady=(0, 8))
        move_down_button = ttk.Button(side_actions, text="Bajar", command=self.move_selected_down, width=16)
        move_down_button.grid(row=1, column=0, pady=(0, 8))
        combine_button = ttk.Button(
            side_actions,
            text="Combinar PDF",
            command=self.combine_pdfs,
            width=16,
        )
        combine_button.grid(row=2, column=0, pady=(24, 8))

        help_box = ttk.LabelFrame(content, text="Notas", padding=(12, 10))
        help_box.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Label(
            help_box,
            text=(
                "Puedes reordenar arrastrando los elementos o usando los botones de subir y bajar. "
                "Cada pagina del PDF final se escala proporcionalmente y se centra para que todas "
                "queden con el mismo tamano de hoja."
            ),
            wraplength=710,
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            help_box,
            text=(
                f"Desarrollado por {DEVELOPER_NAME} | {DEVELOPER_HANDLE} | {DEVELOPER_EMAIL}"
            ),
            wraplength=710,
        ).grid(row=1, column=0, sticky="w", pady=(10, 0))

        self.loader_frame = ttk.Frame(self.root, padding=(16, 0, 16, 8))
        self.loader_frame.grid(row=2, column=0, sticky="ew")
        self.loader_frame.columnconfigure(0, weight=1)
        self.loader_frame.grid_remove()

        ttk.Label(self.loader_frame, textvariable=self.loader_var).grid(row=0, column=0, sticky="w")
        self.progressbar = ttk.Progressbar(self.loader_frame, mode="indeterminate", length=240)
        self.progressbar.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        status = ttk.Label(self.root, textvariable=self.status_var, padding=(16, 8))
        status.grid(row=3, column=0, sticky="ew")

        self.action_widgets.extend(
            [
                add_button,
                remove_button,
                clear_button,
                size_combo,
                move_up_button,
                move_down_button,
                combine_button,
                self.file_list,
            ]
        )

    def set_busy(self, is_busy: bool, message: str = "Procesando PDF..."):
        state = "disabled" if is_busy else "normal"
        for widget in self.action_widgets:
            widget.configure(state=state)

        if is_busy:
            self.loader_var.set(message)
            self.progressbar.configure(mode="indeterminate", maximum=100, value=0)
            self.loader_frame.grid()
            self.progressbar.start(12)
            self.root.configure(cursor="watch")
        else:
            self.progressbar.stop()
            self.progressbar.configure(value=0)
            self.loader_frame.grid_remove()
            self.root.configure(cursor="")

        self.root.update_idletasks()

    def set_progress(self, event: ProgressEvent):
        if event.total <= 0:
            self.progressbar.configure(mode="indeterminate")
            self.progressbar.start(12)
        else:
            self.progressbar.stop()
            self.progressbar.configure(mode="determinate", maximum=event.total, value=event.current)

        self.loader_var.set(event.message)
        self.status_var.set(event.message)

    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="Selecciona los PDF",
            filetypes=[("PDF", "*.pdf")],
        )
        if not paths:
            return

        added = 0
        for raw_path in paths:
            path = Path(raw_path)
            if path.suffix.lower() != ".pdf":
                continue
            if any(item.path == path for item in self.items):
                continue
            self.items.append(PdfItem(path=path))
            added += 1

        self.refresh_listbox()
        self.status_var.set(f"Se agregaron {added} archivo(s). Total cargado: {len(self.items)}.")

    def remove_selected(self):
        selection = self.file_list.curselection()
        if not selection:
            return

        index = selection[0]
        removed = self.items.pop(index)
        self.refresh_listbox()
        self.status_var.set(f"Se quito: {removed.display_name}")

    def clear_files(self):
        if not self.items:
            return

        self.items.clear()
        self.refresh_listbox()
        self.status_var.set("La lista quedo vacia.")

    def move_selected_up(self):
        selection = self.file_list.curselection()
        if not selection or selection[0] == 0:
            return

        index = selection[0]
        self.reorder_items(index, index - 1)
        self.file_list.selection_set(index - 1)

    def move_selected_down(self):
        selection = self.file_list.curselection()
        if not selection or selection[0] >= len(self.items) - 1:
            return

        index = selection[0]
        self.reorder_items(index, index + 1)
        self.file_list.selection_set(index + 1)

    def reorder_items(self, from_index: int, to_index: int):
        if from_index == to_index:
            return

        item = self.items.pop(from_index)
        self.items.insert(to_index, item)
        self.refresh_listbox()

    def refresh_listbox(self):
        self.file_list.delete(0, tk.END)
        for index, item in enumerate(self.items, start=1):
            self.file_list.insert(tk.END, f"{index:02d}. {item.display_name}")

    def combine_pdfs(self):
        if self.is_processing:
            return

        if not self.dependency_loader.is_available():
            messagebox.showerror(
                "Dependencia faltante",
                self.dependency_loader.install_hint(),
            )
            return

        if len(self.items) < 2:
            messagebox.showwarning(
                "Faltan archivos",
                "Debes cargar al menos 2 archivos PDF para combinarlos.",
            )
            return

        output_path = filedialog.asksaveasfilename(
            title="Guardar PDF combinado",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="combinado.pdf",
        )
        if not output_path:
            return

        request = CombineRequest(
            file_paths=tuple(item.path for item in self.items),
            output_path=Path(output_path),
            size_mode=self.target_size_var.get(),
        )

        self.is_processing = True
        self._clear_worker_queue()
        self.set_busy(True, "Preparando combinacion...")
        self.status_var.set("Preparando combinacion...")

        self.worker_thread = threading.Thread(
            target=self._combine_worker,
            args=(request,),
            daemon=True,
        )
        self.worker_thread.start()
        self.root.after(80, self._poll_worker_queue)

    def _combine_worker(self, request: CombineRequest):
        try:
            result = self.combine_service.combine(request, progress_callback=self.worker_queue.put)
            self.worker_queue.put(result)
        except (PdfDependencyError, Exception) as exc:  # pragma: no cover - background path
            self.worker_queue.put(ErrorEvent(message=str(exc)))

    def _poll_worker_queue(self):
        pending_retry = False

        while True:
            try:
                event = self.worker_queue.get_nowait()
            except queue.Empty:
                pending_retry = self.worker_thread is not None and self.worker_thread.is_alive()
                break

            if isinstance(event, ProgressEvent):
                self.set_progress(event)
            elif isinstance(event, StatusEvent):
                self.loader_var.set(event.message)
                self.status_var.set(event.message)
            elif isinstance(event, CombineResult):
                self.is_processing = False
                self.worker_thread = None
                self.set_busy(False)
                self.status_var.set(
                    f"PDF generado correctamente: {event.output_path.name} ({event.total_pages} paginas)."
                )
                messagebox.showinfo(
                    "Proceso completado",
                    "El PDF fue combinado correctamente con tamano de pagina uniforme.",
                )
                return
            elif isinstance(event, ErrorEvent):
                self.is_processing = False
                self.worker_thread = None
                self.set_busy(False)
                self.status_var.set("Ocurrio un error durante la combinacion.")
                messagebox.showerror("Error al combinar PDF", event.message)
                return

        if pending_retry:
            self.root.after(80, self._poll_worker_queue)
        elif self.is_processing:
            self.is_processing = False
            self.worker_thread = None
            self.set_busy(False)
            self.status_var.set("El proceso finalizo sin una respuesta valida.")
            messagebox.showerror(
                "Error al combinar PDF",
                "La tarea termino de forma inesperada. Intenta de nuevo.",
            )

    def _clear_worker_queue(self):
        while not self.worker_queue.empty():
            try:
                self.worker_queue.get_nowait()
            except queue.Empty:
                break
