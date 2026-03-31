from __future__ import annotations

import importlib
import math
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Callable

from pdf_combine.models import CombineRequest, CombineResult, ProgressEvent, StatusEvent


@dataclass(slots=True)
class PdfLibrary:
    PdfReader: Any
    PdfWriter: Any
    Transformation: Any
    PageObject: Any


class PdfDependencyError(RuntimeError):
    pass


class PdfDependencyLoader:
    def __init__(self):
        self._library: PdfLibrary | None = None
        self.import_error: ImportError | None = None
        self.refresh()

    def refresh(self) -> bool:
        try:
            pypdf_module = importlib.import_module("pypdf")
        except ImportError as exc:  # pragma: no cover - runtime path
            self._library = None
            self.import_error = exc
            return False

        self._library = PdfLibrary(
            PdfReader=pypdf_module.PdfReader,
            PdfWriter=pypdf_module.PdfWriter,
            Transformation=pypdf_module.Transformation,
            PageObject=pypdf_module.PageObject,
        )
        self.import_error = None
        return True

    def is_available(self) -> bool:
        return self._library is not None or self.refresh()

    def load(self) -> PdfLibrary:
        if self._library is not None:
            return self._library
        if self.refresh():
            return self._library
        raise PdfDependencyError(self.install_hint())

    @staticmethod
    def install_hint() -> str:
        return (
            "No se encontro la libreria pypdf en el Python que ejecuta esta app.\n\n"
            f"Python actual:\n{sys.executable}\n\n"
            "Instalala con:\n"
            f"\"{sys.executable}\" -m pip install pypdf"
        )


class PdfCombineService:
    def __init__(self, dependency_loader: PdfDependencyLoader):
        self.dependency_loader = dependency_loader

    def combine(
        self,
        request: CombineRequest,
        progress_callback: Callable[[ProgressEvent | StatusEvent], None] | None = None,
    ) -> CombineResult:
        library = self.dependency_loader.load()

        readers = [library.PdfReader(str(path)) for path in request.file_paths]
        target_width, target_height = self.resolve_target_size(readers, request.size_mode)
        total_source_pages = sum(len(reader.pages) for reader in readers)

        self._emit(
            progress_callback,
            ProgressEvent(
                current=0,
                total=total_source_pages,
                message="Analizando tamanos de pagina...",
            ),
        )

        writer = library.PdfWriter()
        total_pages = 0

        for reader in readers:
            for page in reader.pages:
                normalized = self.normalize_page(
                    page=page,
                    target_width=target_width,
                    target_height=target_height,
                    library=library,
                )
                writer.add_page(normalized)
                total_pages += 1
                self._emit(
                    progress_callback,
                    ProgressEvent(
                        current=total_pages,
                        total=total_source_pages,
                        message=f"Procesando pagina {total_pages} de {total_source_pages}...",
                    ),
                )

        self._emit(progress_callback, StatusEvent(message="Escribiendo archivo final..."))
        with request.output_path.open("wb") as file_obj:
            writer.write(file_obj)

        return CombineResult(output_path=request.output_path, total_pages=total_pages)

    @staticmethod
    def resolve_target_size(readers, mode: str) -> tuple[float, float]:
        all_sizes: list[tuple[float, float]] = []
        for reader in readers:
            for page in reader.pages:
                width = float(page.mediabox.width)
                height = float(page.mediabox.height)
                rotation = int(page.get("/Rotate", 0)) % 180
                if rotation:
                    width, height = height, width
                all_sizes.append((width, height))

        if not all_sizes:
            raise ValueError("No fue posible leer paginas validas en los PDF seleccionados.")

        if mode == "first":
            return all_sizes[0]

        max_width = max(width for width, _ in all_sizes)
        max_height = max(height for _, height in all_sizes)
        return max_width, max_height

    @staticmethod
    def normalize_page(page, target_width: float, target_height: float, library: PdfLibrary):
        source_page = page
        if int(source_page.get("/Rotate", 0)) % 360:
            source_page.transfer_rotation_to_content()

        width = float(source_page.mediabox.width)
        height = float(source_page.mediabox.height)

        if math.isclose(width, 0.0) or math.isclose(height, 0.0):
            raise ValueError("Se encontro una pagina con dimensiones invalidas.")

        scale = min(target_width / width, target_height / height)
        scaled_width = width * scale
        scaled_height = height * scale
        offset_x = (target_width - scaled_width) / 2
        offset_y = (target_height - scaled_height) / 2

        blank_page = library.PageObject.create_blank_page(
            width=target_width,
            height=target_height,
        )
        transform = library.Transformation().scale(scale).translate(offset_x, offset_y)
        blank_page.merge_transformed_page(source_page, transform)
        return blank_page

    @staticmethod
    def _emit(
        progress_callback: Callable[[ProgressEvent | StatusEvent], None] | None,
        event: ProgressEvent | StatusEvent,
    ):
        if progress_callback is not None:
            progress_callback(event)
