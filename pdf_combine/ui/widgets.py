from __future__ import annotations

import tkinter as tk


class DragDropListbox(tk.Listbox):
    def __init__(self, master: tk.Misc, on_reorder, **kwargs):
        super().__init__(master, **kwargs)
        self.on_reorder = on_reorder
        self.dragging_index: int | None = None
        self.bind("<Button-1>", self._start_drag)
        self.bind("<B1-Motion>", self._drag_motion)
        self.bind("<ButtonRelease-1>", self._end_drag)

    def _start_drag(self, event):
        index = self.nearest(event.y)
        if index >= 0:
            self.dragging_index = index
            self.selection_clear(0, tk.END)
            self.selection_set(index)

    def _drag_motion(self, event):
        if self.dragging_index is None:
            return

        target_index = self.nearest(event.y)
        if target_index == self.dragging_index or target_index < 0:
            return

        self.on_reorder(self.dragging_index, target_index)
        self.dragging_index = target_index
        self.selection_clear(0, tk.END)
        self.selection_set(target_index)

    def _end_drag(self, _event):
        self.dragging_index = None
