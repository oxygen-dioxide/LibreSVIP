import enum
import pathlib
from typing import Any, get_args, get_type_hints

from pydantic.color import Color
from qmlease import slot
from qtpy.QtCore import QObject, Signal

from libresvip.core.config import settings
from libresvip.extension.manager import plugin_manager, plugin_registry
from libresvip.model.base import BaseComplexModel

from .model_proxy import ModelProxy


class TaskManager(QObject):
    input_format_changed = Signal(str)
    output_format_changed = Signal(str)
    input_fileds_changed = Signal()
    output_fileds_changed = Signal()
    tasks_size_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.tasks = ModelProxy(
            {
                "path": "",
                "name": "",
                "stem": "",
                "success": False,
                "error": "",
                "warning": "",
            }
        )
        self.input_formats = ModelProxy({"value": "", "text": ""})
        self.output_formats = ModelProxy({"value": "", "text": ""})
        self.input_fields = ModelProxy(
            {
                "name": "",
                "title": "",
                "description": "",
                "default": "",
                "type": "",
                "value": "",
                "choices": [],
            }
        )
        self.output_fields = ModelProxy(
            {
                "name": "",
                "title": "",
                "description": "",
                "default": "",
                "type": "",
                "value": "",
                "choices": [],
            }
        )
        self.input_formats.insert_many(
            0,
            [
                {
                    "text": f"{plugin.file_format} (*.{plugin.suffix})",
                    "value": plugin.suffix,
                }
                for plugin in plugin_registry.values()
            ],
        )
        self.output_formats.insert_many(
            0,
            [
                {
                    "text": f"{plugin.file_format} (*.{plugin.suffix})",
                    "value": plugin.suffix,
                }
                for plugin in plugin_registry.values()
            ],
        )
        self.input_format = ""
        self.output_format = ""
        self.input_format_changed.connect(self.set_input_fields)
        self.output_format_changed.connect(self.set_output_fields)

    @property
    def output_ext(self) -> str:
        if settings.auto_set_output_extension:
            return f".{self.output_format}"
        return ""

    @slot(str)
    def set_input_fields(self, input_format) -> None:
        if input_format == self.input_format:
            return
        self.input_format = input_format
        self.input_fields.clear()
        plugin_input = plugin_registry[self.input_format]
        if hasattr(plugin_input.plugin_object, "load"):
            option_class = get_type_hints(plugin_input.plugin_object.load)["options"]
            input_fields = []
            for i, option in enumerate(option_class.__fields__.values()):
                option_key = option.name
                if issubclass(option.type_, bool):
                    input_fields.append(
                        {
                            "type": "bool",
                            "name": option_key,
                            "title": option.field_info.title,
                            "description": option.field_info.description or "",
                            "default": option.default,
                            "value": option.default,
                        }
                    )
                elif issubclass(
                    option.type_, (str, int, float, Color, BaseComplexModel)
                ):
                    if issubclass(option.type_, BaseComplexModel):
                        default_value = option.type_.default_repr()
                    else:
                        default_value = option.default
                    input_fields.append(
                        {
                            "type": "color"
                            if issubclass(option.type_, Color)
                            else "other",
                            "name": option_key,
                            "title": option.field_info.title,
                            "description": option.field_info.description or "",
                            "default": default_value,
                            "value": default_value,
                        }
                    )
                elif issubclass(option.type_, enum.Enum):
                    annotations = get_type_hints(option.type_, include_extras=True)
                    choices = []
                    for enum_item in option.type_:
                        if enum_item.name in annotations:
                            annotated_args = list(get_args(annotations[enum_item.name]))
                            if len(annotated_args) >= 2:
                                _, enum_field = annotated_args[:2]
                            else:
                                continue
                            choices.append(
                                {
                                    "value": enum_item.value,
                                    "text": enum_field.title,
                                }
                            )
                        else:
                            print(enum_item.name)
                    input_fields.append(
                        {
                            "type": "enum",
                            "name": option_key,
                            "title": option.field_info.title,
                            "description": option.field_info.description or "",
                            "default": option.default.value,
                            "value": option.default.value,
                            "choices": choices,
                        }
                    )
            self.input_fields.insert_many(0, input_fields)
            self.input_fileds_changed.emit()

    @slot(str)
    def set_output_fields(self, output_format) -> None:
        if output_format == self.output_format:
            return
        self.output_format = output_format
        self.output_fields.clear()
        plugin_output = plugin_registry[self.output_format]
        if hasattr(plugin_output.plugin_object, "dump"):
            option_class = get_type_hints(plugin_output.plugin_object.dump)["options"]
            output_fields = []
            for i, option in enumerate(option_class.__fields__.values()):
                option_key = option.name
                if issubclass(option.type_, bool):
                    output_fields.append(
                        {
                            "type": "bool",
                            "name": option_key,
                            "title": option.field_info.title,
                            "description": option.field_info.description or "",
                            "default": option.default,
                            "value": option.default,
                        }
                    )
                elif issubclass(
                    option.type_, (str, int, float, Color, BaseComplexModel)
                ):
                    if issubclass(option.type_, BaseComplexModel):
                        default_value = option.type_.default_repr()
                    else:
                        default_value = option.default
                    output_fields.append(
                        {
                            "type": "color"
                            if issubclass(option.type_, Color)
                            else "other",
                            "name": option_key,
                            "title": option.field_info.title,
                            "description": option.field_info.description or "",
                            "default": default_value,
                            "value": default_value,
                        }
                    )
                elif issubclass(option.type_, enum.Enum):
                    annotations = get_type_hints(option.type_, include_extras=True)
                    choices = []
                    for enum_item in option.type_:
                        if enum_item.name in annotations:
                            annotated_args = list(get_args(annotations[enum_item.name]))
                            if len(annotated_args) >= 2:
                                _, enum_field = annotated_args[:2]
                            else:
                                continue
                            choices.append(
                                {
                                    "value": enum_item.value,
                                    "text": enum_field.title,
                                }
                            )
                        else:
                            print(enum_item.name)
                    output_fields.append(
                        {
                            "type": "enum",
                            "name": option_key,
                            "title": option.field_info.title,
                            "description": option.field_info.description or "",
                            "default": option.default.value,
                            "value": option.default.value,
                            "choices": choices,
                        }
                    )
            self.output_fields.insert_many(0, output_fields)
            self.output_fileds_changed.emit()

    @slot(str, result=dict)
    def plugin_info(self, name: str) -> dict:
        assert name in {"input_format", "output_format"}
        if (suffix := getattr(self, name)) in plugin_registry:
            plugin = plugin_registry[suffix]
            return {
                "name": plugin.name,
                "author": plugin.author,
                "website": plugin.website,
                "description": plugin.description,
                "version": plugin.version_string,
                "format_desc": f"{plugin.file_format} (*.{plugin.suffix})",
                "icon_base64": f"data:image/png;base64,{plugin.icon_base64}",
            }
        return {
            "name": "",
            "author": "",
            "website": "",
            "description": "",
            "version": "",
            "format_desc": "",
            "icon_base64": "",
        }

    @slot()
    def reset_stems(self) -> None:
        for i, task in enumerate(self.tasks):
            self.tasks.update(i, {"stem": pathlib.Path(task["path"]).stem})

    @slot(list)
    def add_task_paths(self, paths: list[str]) -> None:
        tasks = []
        path_obj = None
        for path in paths:
            path_obj = pathlib.Path(path)
            tasks.append(
                {
                    "path": path,
                    "name": path_obj.name,
                    "stem": path_obj.stem,
                    "success": None,
                    "error": "",
                    "warning": "",
                }
            )
        self.tasks.append_many(tasks)
        self.tasks_size_changed.emit()
        if (
            settings.auto_detect_input_format
            and path_obj is not None
            and (suffix := path_obj.suffix[1:]) in plugin_registry
        ):
            self.set_str("input_format", suffix)

    @slot()
    def reset(self) -> None:
        self.tasks.clear()
        self.tasks_size_changed.emit()

    @slot(str, result=object)
    def qget(self, name: str) -> Any:
        return getattr(self, name)

    @slot(str, object)
    def qset(self, name: str, value: Any) -> None:
        setattr(self, name, value)

    @slot(str, result=str)
    def get_str(self, name: str) -> str:
        assert name in {"input_format", "output_format"}
        return getattr(self, name)

    @slot(str, str)
    def set_str(self, name: str, value: str) -> None:
        assert name in {"input_format", "output_format"}
        getattr(self, f"{name}_changed").emit(value)

    @slot(str, result=bool)
    def install_plugin(self, path: str) -> bool:
        return plugin_manager.installFromZIP(path)

    @slot()
    def start(self):
        print(
            self.input_format,
        )
        print(
            self.output_format,
        )
        input_kwargs = {field["name"]: field["value"] for field in self.input_fields}
        output_kwargs = {field["name"]: field["value"] for field in self.output_fields}
