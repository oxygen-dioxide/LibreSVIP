import pathlib

import yaml

from libresvip.extension import base as plugin_base
from libresvip.model.base import Project
from libresvip.utils import to_unicode

from .model import USTXProject
from .options import InputOptions, OutputOptions
from .ustx_generator import UstxGenerator
from .ustx_parser import UstxParser


class OpenUtauConverter(plugin_base.SVSConverterBase):
    def load(self, path: pathlib.Path, options: InputOptions) -> Project:
        proj_text = to_unicode(path.read_bytes())
        ustx_project = USTXProject.model_validate(
            yaml.load(proj_text, getattr(yaml, "CSafeLoader", yaml.SafeLoader))
        )
        return UstxParser(options).parse_project(ustx_project)

    def dump(self, path: pathlib.Path, project: Project, options: OutputOptions) -> None:
        ustx_project = UstxGenerator(options).generate_project(project)
        proj_dict = ustx_project.model_dump(by_alias=True, exclude_none=True)
        proj_text = yaml.dump(
            proj_dict,
            None,
            getattr(yaml, "CSafeDumper", yaml.SafeDumper),
            allow_unicode=True,
            sort_keys=False,
        )
        path.write_bytes(proj_text.encode("utf-8"))
