#! /usr/bin/python3
import argparse
import asyncio
import dataclasses
import enum
import functools
import gettext
import io
import pathlib
import secrets
import tempfile
import textwrap
import traceback
import warnings
import zipfile
from concurrent.futures import ThreadPoolExecutor
from operator import not_
from typing import Optional, TypedDict, Union, get_args, get_type_hints

from nicegui import app, ui
from nicegui.events import UploadEventArguments
from nicegui.globals import get_client
from pydantic_core import PydanticUndefined
from pydantic_extra_types.color import Color
from pyfakefs.fake_filesystem import FakeFilesystem
from pyfakefs.fake_pathlib import FakePathlibModule
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import Response

import libresvip
from libresvip.core.config import DarkMode, Language, settings
from libresvip.core.constants import PACKAGE_NAME, app_dir, res_dir
from libresvip.core.warning_types import BaseWarning
from libresvip.extension.manager import plugin_registry
from libresvip.model.base import BaseComplexModel
from libresvip.utils import shorten_error_message
from libresvip.web.elements import QFab, QFabAction

fake_pathlib = FakePathlibModule(FakeFilesystem(
    create_temp_dir=True,
))


def dark_mode2str(mode: DarkMode) -> Optional[bool]:
    if mode == DarkMode.LIGHT:
        return False
    elif mode == DarkMode.DARK:
        return True

def int_validator(value: Union[int, float, str]) -> bool:
    return value.isdigit() if isinstance(value, str) else isinstance(value, int)

def float_validator(value: str) -> bool:
    try:
        float(value)
    except (ValueError, TypeError):
        return False
    else:
        return True


@dataclasses.dataclass
class ConversionTask:
    name: str
    upload_path: pathlib.Path
    output_path: pathlib.Path
    converting: bool
    success: Optional[bool]
    error: Optional[str]
    warning: Optional[str]

    def reset(self):
        self.converting = False
        self.success = None
        self.error = None
        self.warning = None
        if self.output_path.exists():
            self.output_path.unlink()

    def __del__(self):
        self.upload_path.unlink()
        if self.output_path.exists():
            self.output_path.unlink()


@ui.page("/")
@ui.page("/?lang={lang}")
def page_layout(lang: Optional[str] = None):
    cur_client = get_client()

    if "lang" not in app.storage.user:
        app.storage.user["lang"] = "en_US"
    if lang is None:
        lang = app.storage.user["lang"]
    try:
        Language.from_locale(lang)
    except ValueError:
        lang = "en_US"
    if lang != app.storage.user["lang"]:
        app.storage.user["lang"] = lang
    translation = None
    try:
        translation = gettext.translation(PACKAGE_NAME, res_dir / "locales", [lang], fallback=True)
        gettext.textdomain(PACKAGE_NAME)
    except OSError:
        pass
    if translation is None:
        translation = gettext.NullTranslations()
        gettext.textdomain("messages")

    def _(message: str) -> str:
        return translation.gettext(message)

    if "dark_mode" not in app.storage.user:
        app.storage.user["dark_mode"] = dark_mode2str(DarkMode.SYSTEM)

    plugin_details = {
        identifier: {
            "name": plugin.name,
            "author": plugin.author,
            "website": plugin.website,
            "description": plugin.description,
            "version": plugin.version_string,
            "suffix": f"(*.{plugin.suffix})",
            "file_format": plugin.file_format,
            "icon_base64": plugin.icon_base64,
        }
        for identifier, plugin in plugin_registry.items()
    }

    def plugin_info(attr_name: str):
        attr = getattr(selected_formats, attr_name)
        with ui.row().classes(
            "w-full h-full"
        ):
            with ui.element("div").classes("w-100 h-100") as icon:
                icon._props["style"] = f"""background: url('data:image/png;base64,{plugin_details[attr]["icon_base64"]}'); background-size: contain; border-radius: 50%; width: 100px; height: 100px"""
            ui.separator().props("vertical")
            with ui.column().classes("justify-center flex-grow"):
                ui.label(_(plugin_details[attr]["name"])).classes("text-h5 w-full font-bold text-center")
                with ui.row().classes("w-full"):
                    with ui.element("q-chip").props("icon=tag"):
                        ui.label(plugin_details[attr]["version"])
                        ui.tooltip(_("Version"))
                    ui.separator().props("vertical")
                    with ui.element("q-chip").props("icon=person"):
                        with ui.row().classes("items-center"):
                            ui.label(_("Author") + ": ")
                            ui.link(
                                plugin_details[attr]["author"],
                                plugin_details[attr]["website"],
                                new_tab=True,
                            )
                            ui.icon("open_in_new")
                        ui.tooltip(plugin_details[attr]["website"])
                with ui.element("q-chip").props("icon=outline_insert_drive_file"):
                    ui.label(_(plugin_details[attr]["file_format"]) + " " + plugin_details[attr]["suffix"])
        ui.separator()
        with ui.card_section().classes("w-full"):
            ui.label(_("Introduction")).classes("text-subtitle1 font-bold")
            ui.label(_(plugin_details[attr]["description"]))


    input_plugin_info = ui.refreshable(
        functools.partial(plugin_info, "input_format")
    )
    output_plugin_info = ui.refreshable(
        functools.partial(plugin_info, "output_format")
    )

    def panel_header(attr_name: str, title: str, prefix: str, icon: str):
        attr = getattr(selected_formats, attr_name)
        with ui.row().classes("w-full items-center"):
            ui.icon(icon).classes('text-lg')
            ui.label(title).classes('text-subtitle1 font-bold')
            ui.label(prefix + _(
                plugin_details[attr]["file_format"]
            ) + "]").classes('flex-grow')

    input_panel_header = ui.refreshable(
        functools.partial(panel_header, "input_format", _("Input Options"), _("[Import as "), "input")
    )
    output_panel_header = ui.refreshable(
        functools.partial(panel_header, "output_format", _("Output Options"), _("[Export to "), "output")
    )

    def options_form(attr_prefix: str, method: str):
        attr = getattr(selected_formats, attr_prefix + "_format")
        plugin_input = plugin_registry[attr]
        field_types = {}
        option_class = None
        if hasattr(plugin_input.plugin_object, method):
            if option_class := get_type_hints(getattr(plugin_input.plugin_object, method)).get("options"):
                if hasattr(option_class, "model_fields"):
                    for option_key, field_info in option_class.model_fields.items():
                        if issubclass(
                            field_info.annotation, (str, Color, enum.Enum, BaseComplexModel)
                        ):
                            field_types[option_key] = str
                        else:
                            field_types[option_key] = field_info.annotation
        if not option_class or not field_types:
            return
        setattr(selected_formats, attr_prefix + "_options", TypedDict(
            f"{attr_prefix.title()}Options", field_types
        )())
        option_dict = getattr(selected_formats, attr_prefix + "_options")
        with ui.column():
            for i, (option_key, field_info) in enumerate(option_class.model_fields.items()):
                default_value = (
                    None if field_info.default is PydanticUndefined else field_info.default
                )
                with ui.row().classes("items-center w-full") as row:
                    if i:
                        row._props["style"] = """
                            background-image: linear-gradient(to right, #ccc 0%, #ccc 50%, transparent 50%);
                            background-size: 8px 1px;
                            background-repeat: repeat-x;
                        """
                    if issubclass(field_info.annotation, bool):
                        ui.switch(
                            _(field_info.title),
                            value=default_value,
                        ).bind_value(
                            option_dict, option_key
                        ).classes("flex-grow")
                    elif issubclass(field_info.annotation, enum.Enum):
                        default_value = default_value.value if default_value else None
                        annotations = get_type_hints(
                            field_info.annotation, include_extras=True
                        )
                        choices = {}
                        for enum_item in field_info.annotation:
                            if enum_item.name in annotations:
                                annotated_args = list(get_args(annotations[enum_item.name]))
                                if len(annotated_args) >= 2:
                                    enum_field = annotated_args[1]
                                else:
                                    continue
                                choices[
                                    enum_item.value
                                ] = _(enum_field.title)
                        ui.select(
                            choices,
                            label=_(field_info.title),
                            value=default_value,
                        ).classes("flex-grow")
                    elif issubclass(field_info.annotation, Color):
                        ui.color_input(
                            label=_(field_info.title),
                            value=default_value,
                        ).classes("flex-grow")
                    elif issubclass(field_info.annotation, (str, BaseComplexModel)):
                        if issubclass(field_info.annotation, BaseComplexModel):
                            default_value = field_info.annotation.default_repr()
                        ui.input(
                            label=_(field_info.title),
                            value=default_value,
                        ).classes("flex-grow")
                    elif issubclass(field_info.annotation, (int, float)):
                        with ui.number(
                            label=_(field_info.title),
                            value=default_value,
                        ).classes("flex-grow") as num_input:
                            if issubclass(field_info.annotation, int):
                                num_input.validation = {
                                    _("Invalid integer"): int_validator
                                }
                            else:
                                num_input.validation = {
                                    _("Invalid float"): float_validator
                                }
                    else:
                        continue
                    if field_info.description:
                        with ui.icon("help_outline").classes("text-3xl").style("cursor: help"):
                            ui.tooltip(_(field_info.description))

    input_options = ui.refreshable(
        functools.partial(options_form, "input", "load")
    )

    output_options = ui.refreshable(
        functools.partial(options_form, "output", "dump")
    )

    @dataclasses.dataclass
    class SelectedFormats:
        _input_format: str = dataclasses.field(init=False)
        _output_format: str = dataclasses.field(init=False)
        input_options: TypedDict = dataclasses.field(default_factory=dict)
        output_options: TypedDict = dataclasses.field(default_factory=dict)
        files_to_convert: dict[str, ConversionTask] = dataclasses.field(default_factory=dict)

        def __post_init__(self):
            self.input_format = app.storage.user.get("last_input_format") or next(iter(plugin_registry), "")
            self.output_format = app.storage.user.get("last_output_format") or next(iter(plugin_registry), "")
            app.storage.user.setdefault("auto_detect_input_format", settings.auto_detect_input_format)
            app.storage.user.setdefault("reset_tasks_on_input_change", settings.reset_tasks_on_input_change)
            app.add_route(f"/export/{cur_client.id}/", self.export_all, methods=["GET"])
            app.add_route(f"/export/{cur_client.id}/{{filename}}", self.export_one, methods=["GET"])

        @functools.cached_property
        def temp_path(self) -> fake_pathlib.Path:
            user_temp_path = fake_pathlib.Path(tempfile.gettempdir()) / f"{cur_client.id}"
            if not user_temp_path.exists():
                user_temp_path.mkdir(exist_ok=True)
            return user_temp_path

        @ui.refreshable
        def tasks_container(self):
            with ui.column().classes("w-full"):
                for info in self.files_to_convert.values():
                    with ui.row().classes("w-full items-center"):
                        def remove_row():
                            del self.files_to_convert[info.name]
                            self.tasks_container.refresh()
                        ui.label(info.name).classes('flex-grow')
                        ui.spinner().props("size=lg").bind_visibility_from(info, "converting")
                        ui.icon("check", size="lg").classes("text-green-500").bind_visibility_from(info, "success")
                        with ui.dialog() as error_dialog, ui.element("q-banner").classes("bg-red-500 w-auto") as error_banner:
                            ui.label().classes("text-lg").style("word-break: break-all; white-space: pre-wrap;").bind_text_from(info, "error", backward=shorten_error_message)
                            with error_banner.add_slot("action"):
                                ui.button(_("Copy to clipboard"), on_click=lambda: ui.run_javascript(
                                    f"navigator.clipboard.writeText({repr(info.error)})", respond=False
                                ))
                                ui.button(_("Close"), on_click=error_dialog.close)
                        ui.button(icon="error", color="red", on_click=error_dialog.open).props("round").bind_visibility_from(info, "error")
                        with ui.dialog() as warn_dialog, ui.element("q-banner").classes("bg-yellow-500 w-auto") as warn_banner:
                            ui.label().classes("text-lg").style("word-break: break-all; white-space: pre-wrap;").bind_text_from(info, "warning", backward=str)
                            with warn_banner.add_slot("action"):
                                ui.button(_("Copy to clipboard"), on_click=lambda: ui.run_javascript(
                                    f"navigator.clipboard.writeText({repr(info.warning)})", respond=False
                                ))
                                ui.button(_("Close"), on_click=warn_dialog.close)
                        ui.button(icon="warning", color="yellow", on_click=warn_dialog.open).props("round").bind_visibility_from(info, "warning")
                        ui.button(icon="download", on_click=lambda: ui.download(f"/export/{cur_client.id}/{info.name}")).props("round").bind_visibility_from(info, "success")
                        with ui.button(icon="close", on_click=remove_row).props("round"):
                            ui.tooltip(_("Remove"))

        def add_task(self, args: UploadEventArguments) -> None:
            if app.storage.user.get('auto_detect_input_format'):
                cur_suffix = args.name.rpartition(".")[-1].lower()
                if cur_suffix in plugin_registry and cur_suffix != self.input_format:
                    self.input_format = cur_suffix
            upload_path = self.temp_path / args.name
            args.content.seek(0)
            upload_path.write_bytes(args.content.read())
            output_path = self.temp_path / tempfile.mktemp()
            conversion_task = ConversionTask(
                name=args.name,
                upload_path=upload_path,
                output_path=output_path,
                converting=False,
                success=None,
                error=None,
                warning=None,
            )
            self.files_to_convert[args.name] = conversion_task
            self.tasks_container.refresh()

        @property
        def input_format(self) -> str:
            return self._input_format

        @input_format.setter
        def input_format(self, value: str) -> None:
            self._input_format = value
            if app.storage.user.get('reset_tasks_on_input_change'):
                self.files_to_convert.clear()
            app.storage.user['last_input_format'] = value
            input_plugin_info.refresh()
            input_panel_header.refresh()
            input_options.refresh()

        @property
        def output_format(self) -> str:
            return self._output_format

        @output_format.setter
        def output_format(self, value: str) -> None:
            self._output_format = value
            app.storage.user['last_output_format'] = value
            output_plugin_info.refresh()
            output_panel_header.refresh()
            output_options.refresh()

        @property
        def task_count(self) -> int:
            return len(self.files_to_convert)

        def convert_one(self, task: ConversionTask):
            task.converting = True
            try:
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always", BaseWarning)
                    input_plugin = plugin_registry[self.input_format]
                    output_plugin = plugin_registry[self.output_format]
                    input_option = get_type_hints(input_plugin.plugin_object.load).get(
                        "options"
                    )
                    output_option = get_type_hints(output_plugin.plugin_object.dump).get(
                        "options"
                    )
                    project = input_plugin.plugin_object.load(
                        task.upload_path,
                        input_option(**self.input_options),
                    )
                    task.output_path = task.output_path.with_suffix(f".{self.output_format}")
                    output_plugin.plugin_object.dump(
                        task.output_path, project, output_option(**self.output_options)
                    )
                task.success = True
                if len(w):
                    task.warning = "\n".join(
                        str(warning)
                        for warning in w
                    )
            except Exception:
                task.success = False
                task.error = traceback.format_exc()
            task.converting = False

        async def batch_convert(self):
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(
                max_workers=max(len(self.files_to_convert), 4)
            ) as executor:
                for task in self.files_to_convert.values():
                    task.reset()
                    await loop.run_in_executor(
                        executor,
                        self.convert_one,
                        task,
                    )
            if any(
                not task.success for task in self.files_to_convert.values()
            ):
                ui.notify(_("Conversion Failed"), closeBtn=_("Close"), type="negative")
            else:
                ui.notify(_("Conversion Successful"), closeBtn=_("Close"), type="positive")

        def export_all(self, request: Request):
            if len(self.files_to_convert) == 0:
                raise HTTPException(400, "No files to export")
            elif len(self.files_to_convert) == 1:
                filename = next(iter(self.files_to_convert))
                return self._export_one(filename)
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as zip_file:
                for task in self.files_to_convert.values():
                    if task.success:
                        zip_file.writestr(
                            task.upload_path.with_suffix(task.output_path.suffix).name,
                            task.output_path.read_bytes(),
                        )
            return Response(content=buffer.getvalue(), media_type="application/zip", headers={
                "Content-Disposition": "attachment; filename=export.zip"
            })

        def export_one(self, request: Request):
            return self._export_one(request.path_params["filename"])

        def _export_one(self, filename: str):
            if task := self.files_to_convert.get(filename):
                if task.success:
                    return Response(
                        content=task.output_path.read_bytes(),
                        media_type="application/octet-stream",
                        headers={
                            "Content-Disposition": f"attachment; filename={task.upload_path.with_suffix(task.output_path.suffix).name}"
                        }
                    )
            raise HTTPException(404, "File not found")


    dark_toggler = ui.dark_mode().bind_value(app.storage.user, "dark_mode")
    selected_formats = SelectedFormats()
    ui.add_head_html('<script src="https://cdn.jsdelivr.net/npm/axios@1/dist/axios.min.js"></script>')
    with ui.element('style') as style:  # fix icon position
        style._text = textwrap.dedent('''
        .q-icon {
            justify-content: flex-end;
        }
        ''').strip()

    def switch_values():
        select1.value, select2.value = select2.value, select1.value

    with ui.left_drawer(value=False) as drawer:
        pass

    with ui.header(elevated=True).style("background-color: curious-blue").classes(
        "items-center"
    ):
        ui.button(icon="menu", on_click=drawer.toggle)
        with ui.button(_("Convert"), on_click=lambda: convert_menu.open(), icon="loop"):
            with ui.menu() as convert_menu:
                with ui.menu_item(on_click=lambda: ui.run_javascript(
                    'add_upload()', respond=False
                )):
                    with ui.row().classes("items-center"):
                        ui.icon("file_open").classes("text-lg")
                        ui.label(_("Import project"))
                with ui.menu_item().bind_visibility(
                    selected_formats, "task_count", backward=bool, forward=bool
                ):
                    with ui.row().classes("items-center"):
                        ui.icon("play_arrow").classes("text-lg")
                        ui.label(_("Convert"))
                with ui.menu_item().bind_visibility(
                    selected_formats, "task_count", backward=bool, forward=bool
                ):
                    with ui.row().classes("items-center"):
                        ui.icon("refresh").classes("text-lg")
                        ui.label(_("Clear Task List"))
                ui.separator()
                with ui.menu_item(on_click=switch_values):
                    with ui.row().classes("items-center"):
                        ui.icon("swap_vert").classes("text-lg")
                        ui.label(_("Swap Input and Output"))
        with ui.button(_("Switch Theme"), on_click=lambda: theme_menu.open(), icon="palette"):
            with ui.menu() as theme_menu:
                with ui.menu_item(on_click=dark_toggler.disable):
                    with ui.row().classes("items-center"):
                        ui.icon("light_mode").classes("text-lg")
                        ui.label(_("Light"))
                with ui.menu_item(on_click=dark_toggler.enable):
                    with ui.row().classes("items-center"):
                        ui.icon("dark_mode").classes("text-lg")
                        ui.label(_("Dark"))
                with ui.menu_item(on_click=dark_toggler.auto):
                    with ui.row().classes("items-center"):
                        ui.icon("brightness_auto").classes("text-lg")
                        ui.label(_("System"))
        with ui.button(_("Switch Language"), on_click=lambda: lang_menu.open(), icon="language"):
            with ui.menu() as lang_menu:
                ui.menu_item("简体中文", on_click=lambda: ui.open('/?lang=zh_CN') if lang != 'zh_CN' else None)
                ui.menu_item("English", on_click=lambda: ui.open('/?lang=en_US') if lang != 'en_US' else None)
                ui.menu_item("日本語").props('disabled')
        with ui.dialog() as about_dialog, ui.card():
            ui.label(_("About")).classes('text-lg')
            with ui.column().classes("text-center w-full"):
                ui.label(_("LibreSVIP")).classes('text-h4 font-bold w-full')
                ui.label(_("Version: ") + libresvip.__version__).classes('text-md w-full')
                ui.label(_("Author: SoulMelody")).classes('text-md w-full')
                with ui.row().classes("w-full justify-center"):
                    with ui.element("q-chip").props("icon=live_tv"):
                        ui.link(_("Author's Profile"), "https://space.bilibili.com/175862486", new_tab=True)
                    with ui.element("q-chip").props("icon=logo_dev"):
                        ui.link(_("Repo URL"), "https://github.com/SoulMelody/LibreSVIP", new_tab=True)
                ui.label(
                    _("LibreSVIP is an open-sourced, liberal and extensionable framework that can convert your singing synthesis projects between different file formats.")
                ).classes('text-md w-full')
                ui.label(
                    _("All people should have the right and freedom to choose. That's why we're committed to giving you a second chance to keep your creations free from the constraints of platforms and coterie.")
                ).classes('text-md w-full')
            with ui.card_actions().props("align=right").classes("w-full"):
                ui.button(_('Close'), on_click=about_dialog.close)
        with ui.button(_("Help"), on_click=lambda: help_menu.open(), icon="help"):
            with ui.menu() as help_menu:
                with ui.menu_item(on_click=about_dialog.open):
                    with ui.row().classes("items-center"):
                        ui.icon("info").classes("text-lg")
                        ui.label(_("About"))

    with ui.card().classes('w-full').style('height: calc(100vh - 100px)'):
        with ui.splitter(
            limits=(40, 60)
        ).classes("h-full w-full") as main_splitter:
            with main_splitter.before:
                with ui.splitter(
                    limits=(40, 50), horizontal=True
                ) as left_splitter:
                    with left_splitter.before:
                        with ui.card().classes("h-full"):
                            with ui.column().classes("w-full"):
                                ui.label(_("Choose file format")).classes('text-h5 font-bold')
                                with ui.grid().classes('grid grid-cols-11 gap-4 w-full'):
                                    with ui.select(
                                        {k: _(v["file_format"]) + "" + v["suffix"] for k, v in plugin_details.items()},
                                        label=_("Import format"),
                                    ).classes('col-span-10').bind_value(
                                        selected_formats, "input_format"
                                    ) as select1:
                                        pass
                                    with ui.dialog() as input_info, ui.card():
                                        input_plugin_info()
                                        with ui.card_actions().props("align=right").classes("w-full"):
                                            ui.button(_('Close'), on_click=input_info.close)
                                    with ui.button(icon="info", on_click=input_info.open).classes('min-w-[45px] max-w-[45px] aspect-square'):
                                        ui.tooltip(_("View Detail Information"))
                                    ui.switch(_("Auto detect import format")).classes('col-span-5').bind_value(
                                        app.storage.user, "auto_detect_input_format"
                                    )
                                    ui.switch(_("Reset list when import format changed")).classes('col-span-5').bind_value(
                                        app.storage.user, "reset_tasks_on_input_change"
                                    )
                                    with ui.button(icon="swap_vert", on_click=switch_values).classes('w-fit aspect-square').props('round'):
                                        ui.tooltip(_("Swap Input and Output"))
                                    with ui.select(
                                        {k: _(v["file_format"]) + "" + v["suffix"] for k, v in plugin_details.items()},
                                        label=_("Export format"),
                                    ).classes('col-span-10').bind_value(
                                        selected_formats, "output_format"
                                    ) as select2:
                                        pass
                                    with ui.dialog().classes("h-400 w-600") as output_info, ui.card():
                                        output_plugin_info()
                                        with ui.element("q-card-actions").props("align=right").classes("w-full"):
                                            ui.button(_('Close'), on_click=output_info.close)
                                    with ui.button(icon="info", on_click=output_info.open).classes('min-w-[45px] max-w-[45px] aspect-square'):
                                        ui.tooltip(_("View Detail Information"))
                    with left_splitter.after:
                        with ui.card().classes(
                            'w-full h-full opacity-80 hover:opacity-100'
                        ) as tasks_card:
                            ui.label(_("Import project")).classes('text-h5 font-bold')
                            selected_formats.tasks_container()
                            tasks_card.bind_visibility_from(selected_formats, "task_count", backward=bool)
                            with ui.upload(
                                multiple=True,
                                on_upload=selected_formats.add_task,
                                auto_upload=True,
                            ).props('hidden') as uploader:
                                pass
                            with QFab(
                                icon='construction',
                            ).classes('absolute bottom-0 left-0 m-2 z-10') as fab:
                                with fab.add_slot("active-icon"):
                                    ui.icon("construction").classes("rotate-45")
                                def add_class(element: ui.element, open: bool = False):
                                    element.classes("toolbar-fab-active")
                                    if open:
                                        element.run_method("show")
                                def remove_class(element: ui.element):
                                    call_times = 0
                                    async def hide():
                                        nonlocal call_times
                                        if call_times and await ui.run_javascript('!document.querySelector(".toolbar-fab-active")'):
                                            fab.run_method("hide")
                                            timer.deactivate()
                                        call_times += 1
                                    timer = ui.timer(0.5, hide)
                                    element.classes(remove="toolbar-fab-active")
                                fab.on("mouseover", lambda: add_class(fab, open=True))
                                fab.on("mouseout", lambda: remove_class(fab))
                                with QFabAction(icon='refresh') as fab_action_1:
                                    fab_action_1.on("mouseover", lambda: add_class(fab_action_1))
                                    fab_action_1.on("mouseout", lambda: remove_class(fab_action_1))
                                    ui.tooltip(_("Clear Task List"))
                                with QFabAction(icon='filter_alt_off') as fab_action_2:
                                    fab_action_2.on("mouseover", lambda: add_class(fab_action_2))
                                    fab_action_2.on("mouseout", lambda: remove_class(fab_action_2))
                                    ui.tooltip(_("Remove Tasks With Other Extensions"))
                            with ui.button(
                                icon='add', on_click=lambda: ui.run_javascript(
                                    "add_upload()", respond=False
                                )
                            ).props("round").classes('absolute bottom-0 right-2 m-2 z-10'):
                                ui.badge().props("floating color=orange").bind_text_from(selected_formats, "task_count", backward=str)
                                ui.tooltip(_("Continue Adding files"))
                        with ui.card().classes(
                            'w-full h-full opacity-80 hover:opacity-100 flex items-center justify-center border-dashed border-2 border-indigo-300 hover:border-indigo-500'
                        ).style(
                            "cursor: pointer"
                        ) as upload_card:
                            upload_card.bind_visibility_from(selected_formats, "task_count", backward=not_)
                            ui.icon("file_upload").classes('text-6xl')
                            ui.label(_("Drag and drop files here or click to upload")).classes('text-lg')
            with main_splitter.after:
                with ui.card().classes('w-full h-auto min-h-full'):
                    with ui.row().classes('absolute top-0 right-2 m-2 z-10'):
                        with ui.button(
                            icon='play_arrow', on_click=selected_formats.batch_convert
                        ).props("round").bind_visibility(
                            selected_formats, "task_count", backward=bool, forward=bool
                        ):
                            ui.tooltip(_("Start Conversion"))
                        with ui.button(
                            icon='download_for_offline', on_click=lambda: ui.download(f"/export/{cur_client.id}/")
                        ).props("round").bind_visibility(
                            selected_formats, "task_count", backward=bool, forward=bool
                        ):
                            ui.tooltip(_("Export"))
                    ui.label(_("Advanced Options")).classes('text-h5 font-bold')
                    with ui.expansion().classes('w-full') as import_panel:
                        with import_panel.add_slot("header"):
                            input_panel_header()
                        input_options()
                    ui.separator()
                    with ui.expansion().classes('w-full') as export_panel:
                        with export_panel.add_slot("header"):
                            output_panel_header()
                        output_options()
    ui.add_body_html(
        textwrap.dedent(f"""
        <script>
            function add_upload() {{
                if (window.showOpenFilePicker) {{
                    let format_desc = document.querySelector('[role="combobox"]').value
                    let suffix = format_desc.match(/\\((?:\\*)(\\..*?)\\)/)[1]
                    let file_format = format_desc.split('(')[0]
                    window.showOpenFilePicker(
                        {{
                            types: [
                                {{
                                    description: file_format,
                                    accept: {{
                                        '*/*': [suffix],
                                    }}
                                }}
                            ],
                            multiple: true
                        }}
                    ).then(async function (fileHandles) {{
                        for (const fileHandle of fileHandles) {{
                            const file = await fileHandle.getFile();
                            let file_name = file.name
                            axios.postForm('{uploader._props['url']}', {{
                                file_name: file
                            }})
                        }}
                    }});
                }} else {{
                    document.querySelector(".q-uploader__input").click()
                }}
            }}
            document.addEventListener('DOMContentLoaded', () => {{
                let uploader = document.querySelector("[id='{uploader.id}']")

                let task_card = document.querySelector("[id='{tasks_card.id}']")
                task_card.addEventListener('dragover', (event) => {{
                    event.preventDefault()
                }})
                task_card.addEventListener('drop', (event) => {{
                    for (let file of event.dataTransfer.files) {{
                        let file_name = file.name
                        axios.postForm('{uploader._props['url']}', {{
                            file_name: file
                        }})
                    }}
                    event.preventDefault()
                }})

                let upload_card = document.querySelector("[id='{upload_card.id}']")
                upload_card.addEventListener('dragover', (event) => {{
                    event.preventDefault()
                }})
                upload_card.addEventListener('click', (event) => {{
                    event.preventDefault()
                    add_upload()
                }})
                upload_card.addEventListener('drop', (event) => {{
                    for (let file of event.dataTransfer.files) {{
                        let file_name = file.name
                        axios.postForm('{uploader._props['url']}', {{
                            file_name: file
                        }})
                    }}
                    event.preventDefault()
                }})
            }})
        </script>
        """).strip()
    )


if __name__ in {"__main__", "__mp_main__"}:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--port", type=int, default=8080)
    arg_parser.add_argument("--reload", action="store_true")
    args = arg_parser.parse_args()

    secrets_path = app_dir.user_config_path / "secrets.txt"
    if not secrets_path.exists():
        secrets_path.write_text(secrets.token_urlsafe(32))
    storage_secret = secrets_path.read_text()

    ui.run(
        reload=args.reload,
        dark=dark_mode2str(settings.dark_mode),
        port=args.port,
        storage_secret=storage_secret,
        exclude="chart,mermaid,plotly",
        title="LibreSVIP",
        favicon=res_dir / "libresvip.ico",
    )
