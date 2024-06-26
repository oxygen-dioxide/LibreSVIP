import pathlib

from libresvip.core.compat import json
from libresvip.extension import base as plugin_base
from libresvip.model.base import Project
from libresvip.model.reset_time_axis import reset_time_axis

from .model import Y77Project
from .options import InputOptions, OutputOptions
from .y77_generator import Y77Generator
from .y77_parser import Y77Parser


class Y77Converter(plugin_base.SVSConverterBase):
    def load(self, path: pathlib.Path, options: InputOptions) -> Project:
        y77_project = Y77Project.model_validate(json.loads(path.read_bytes().decode("utf-8")))
        return Y77Parser(options).parse_project(y77_project)

    def dump(self, path: pathlib.Path, project: Project, options: OutputOptions) -> None:
        project = reset_time_axis(project, options.tempo)
        y77_project = Y77Generator(options).generate_project(project)
        path.write_bytes(
            json.dumps(y77_project.model_dump(mode="json", by_alias=True)).encode("utf-8")
        )
