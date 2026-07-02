"""Textual TUI package for editing Pydantic configuration models."""

from .app import (
    ConfigEditorApp,
    main,
    run_editor,
)
from .controller import ConfigEditorController
from .demo import (
    ExampleAudioSettings,
    ExampleProgramSettings,
    ExampleStorageSettings,
    TimeInputEditor,
)
from .dialogs import MessageScreen
from .editors import (
    BaseEditor,
    CheckboxEditor,
    InputEditor,
    JsonEditor,
    SectionEditor,
    SelectEditor,
)
from .models import FieldNode
from .tree import ConfigTree
from .tree_presenter import TreePresenter

__all__ = [
    "BaseEditor",
    "CheckboxEditor",
    "ConfigEditorApp",
    "ConfigEditorController",
    "ConfigTree",
    "ExampleAudioSettings",
    "ExampleProgramSettings",
    "ExampleStorageSettings",
    "FieldNode",
    "InputEditor",
    "JsonEditor",
    "MessageScreen",
    "SectionEditor",
    "SelectEditor",
    "TimeInputEditor",
    "TreePresenter",
    "main",
    "run_editor",
]
