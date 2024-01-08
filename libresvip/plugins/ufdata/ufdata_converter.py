import pathlib

from libresvip.extension import base as plugin_base
from libresvip.model.base import Project, json_dumps, json_loads

from .model import UFData
from .options import InputOptions, OutputOptions
from .ufdata_generator import UFDataGenerator
from .ufdata_parser import UFDataParser


class UFDataConverter(plugin_base.SVSConverterBase):
    def load(self, path: pathlib.Path, options: InputOptions) -> Project:
        ufdata_project = UFData.model_validate(json_loads(path.read_text("utf-8")))
        return UFDataParser(options).parse_project(ufdata_project)

    def dump(self, path: pathlib.Path, project: Project, options: OutputOptions) -> None:
        ufdata_project = UFDataGenerator(options).generate_project(project)
        path.write_text(
            json_dumps(ufdata_project.model_dump(mode="json", by_alias=True)),
            encoding="utf-8",
        )
