import dataclasses
import enum
import pathlib

from omegaconf import OmegaConf

from .constants import app_dir


class Language(enum.Enum):
    CHINESE = "简体中文"
    ENGLISH = "English"
    JAPANESE = "日本語"


class DarkMode(enum.Enum):
    LIGHT = "Light"
    DARK = "Dark"
    SYSTEM = "System"


class ConflictPolicy(enum.Enum):
    SKIP = "Skip"
    OVERWRITE = "Overwrite"
    PROMPT = "Prompt"


@dataclasses.dataclass
class LibreSvipSettings:
    # Both Web and GUI
    language: Language = dataclasses.field(default=Language.CHINESE)
    dark_mode: DarkMode = dataclasses.field(default=DarkMode.SYSTEM)
    # GUI Only
    save_folder: pathlib.Path = dataclasses.field(default=pathlib.Path("./"))
    conflict_policy: ConflictPolicy = dataclasses.field(default=ConflictPolicy.PROMPT)
    auto_detect_input_format: bool = dataclasses.field(default=True)
    auto_set_output_extension: bool = dataclasses.field(default=True)
    reset_tasks_on_input_change: bool = dataclasses.field(default=True)
    multi_threaded_conversion: bool = dataclasses.field(default=True)
    open_save_folder_on_completion: bool = dataclasses.field(default=True)


config_path = app_dir.user_config_path / "settings.yml"


settings = OmegaConf.structured(LibreSvipSettings)
if config_path.exists():
    settings = OmegaConf.merge(settings, OmegaConf.load(config_path))
