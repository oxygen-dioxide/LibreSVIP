import functools
import json
import pathlib

import qtawesome
from qmlease import slot
from qtpy.QtCore import QObject, QUrl


class FontLoader(QObject):
    @functools.cached_property
    def font_base_dir(self) -> pathlib.Path:
        return pathlib.Path(qtawesome._instance()._get_fonts_directory())

    @functools.cache
    def char_map(self, font_family: str) -> dict[str, str]:
        return next(
            (
                json.load((self.font_base_dir / fargs[2]).open())
                for fargs in qtawesome._BUNDLED_FONTS
                if fargs[0] == font_family
            ),
            {},
        )

    @slot(str, result=str)
    def font_path(self, font_family: str) -> str:
        return QUrl.fromLocalFile(
            next(
                (
                    self.font_base_dir / fargs[1]
                    for fargs in qtawesome._BUNDLED_FONTS
                    if fargs[0] == font_family
                ),
                "",
            )
        ).toString()

    @slot(str, result=str)
    def icon(self, icon_name: str) -> str:
        font_family, _, icon_name = icon_name.partition(".")
        char_map = self.char_map(font_family)
        return chr(int(char_map.get(icon_name, "0"), 16))
