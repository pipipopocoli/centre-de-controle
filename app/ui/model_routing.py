from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


class ModelRoutingWidget(QFrame):
    load_requested = Signal()
    save_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("modelRouting")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)

        self.voice_model = QLineEdit("google/gemini-2.5-flash")
        self.l1_model = QLineEdit("liquid/lfm-2.5-1.2b-thinking:free")
        self.l2_model = QLineEdit("arcee-ai/trinity-large-preview:free")
        self.lfm_spawn_max = QSpinBox()
        self.lfm_spawn_max.setRange(1, 10)
        self.lfm_spawn_max.setValue(10)
        self.stream_enabled = QCheckBox("Stream enabled")
        self.stream_enabled.setChecked(True)

        form.addRow("Voice STT model", self.voice_model)
        form.addRow("L1 model", self.l1_model)
        form.addRow("L2 scene model", self.l2_model)
        form.addRow("LFM spawn max", self.lfm_spawn_max)
        form.addRow("", self.stream_enabled)

        actions = QHBoxLayout()
        self.load_btn = QPushButton("Load API")
        self.save_btn = QPushButton("Save API")
        self.load_btn.clicked.connect(self.load_requested.emit)
        self.save_btn.clicked.connect(self.save_requested.emit)
        actions.addWidget(self.load_btn)
        actions.addWidget(self.save_btn)
        actions.addStretch(1)

        layout.addLayout(form)
        layout.addLayout(actions)
        layout.addStretch(1)

    def profile_payload(self) -> dict[str, Any]:
        return {
            "voice_stt_model": self.voice_model.text().strip(),
            "l1_model": self.l1_model.text().strip(),
            "l2_scene_model": self.l2_model.text().strip(),
            "lfm_spawn_max": int(self.lfm_spawn_max.value()),
            "stream_enabled": bool(self.stream_enabled.isChecked()),
        }

    def set_profile_payload(self, payload: dict[str, Any]) -> None:
        self.voice_model.setText(str(payload.get("voice_stt_model") or "google/gemini-2.5-flash"))
        self.l1_model.setText(str(payload.get("l1_model") or "liquid/lfm-2.5-1.2b-thinking:free"))
        self.l2_model.setText(str(payload.get("l2_scene_model") or "arcee-ai/trinity-large-preview:free"))
        try:
            spawn = int(payload.get("lfm_spawn_max") or 10)
        except (TypeError, ValueError):
            spawn = 10
        self.lfm_spawn_max.setValue(max(1, min(spawn, 10)))
        self.stream_enabled.setChecked(bool(payload.get("stream_enabled", True)))

