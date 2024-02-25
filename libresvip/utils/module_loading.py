import pathlib
import sys
import types
import zipfile
from importlib.abc import Loader
from importlib.machinery import ModuleSpec, SourcelessFileLoader
from importlib.util import module_from_spec, spec_from_file_location
from typing import cast

from libresvip.core.compat import Traversable


class ZipLoader(SourcelessFileLoader):
    def __init__(self, zip_file: zipfile.ZipFile, file_path: str) -> None:
        self.zip_file = zip_file
        self.file_path = file_path

    def create_module(self, spec: ModuleSpec) -> types.ModuleType:
        return sys.modules.get(spec.name)

    def get_filename(self, fullname: str) -> str:  # type: ignore[override]
        return self.file_path

    def get_data(self, path: str) -> bytes:
        return self.zip_file.read(path)

    def exec_module(self, module: types.ModuleType) -> None:
        if compiled := super().get_code(module.__name__):
            exec(compiled, module.__dict__)


def load_module(name: str, plugin_path: Traversable) -> types.ModuleType:
    spec = None
    if isinstance(plugin_path, zipfile.Path) and plugin_path.root.filename is not None:
        loader = ZipLoader(zip_file=plugin_path.root, file_path=plugin_path.at)
        spec = ModuleSpec(name, cast(Loader, loader), is_package=True, origin=plugin_path.at)
    else:
        spec = spec_from_file_location(
            name,
            cast(pathlib.Path, plugin_path),
            submodule_search_locations=[
                str(plugin_path)
                if plugin_path.is_dir()
                else str(plugin_path).removesuffix(plugin_path.name)
            ],
        )
    if spec is None or spec.loader is None:
        msg = f"Cannot load plugin from {plugin_path}"
        raise ImportError(msg)
    module = module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        msg = f"{e}: {plugin_path}"
        raise ImportError(msg) from e
    return module