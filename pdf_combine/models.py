from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class PdfItem:
    path: Path

    @property
    def display_name(self) -> str:
        return self.path.name


@dataclass(slots=True, frozen=True)
class CombineRequest:
    file_paths: tuple[Path, ...]
    output_path: Path
    size_mode: str


@dataclass(slots=True, frozen=True)
class ProgressEvent:
    current: int
    total: int
    message: str


@dataclass(slots=True, frozen=True)
class StatusEvent:
    message: str


@dataclass(slots=True, frozen=True)
class CombineResult:
    output_path: Path
    total_pages: int


@dataclass(slots=True, frozen=True)
class ErrorEvent:
    message: str
