from gettext import gettext as _

import typer
from omegaconf import OmegaConf
from omegaconf.errors import OmegaConfBaseException

from libresvip.core.config import save_settings, settings

app = typer.Typer()


@app.command("list")
def list_configurations():
    for name, value in OmegaConf.to_container(settings, resolve=True).items():
        typer.echo(f"{name}: {value}")


def conf_key_callback(value: str):
    if value not in ["language"]:
        raise typer.BadParameter(
            _("Setting {} is not supported in cli mode.").format(value),
        )
    return value


@app.command("set")
def set_configuration(
    name: str = typer.Argument(callback=conf_key_callback),
    value: str = typer.Argument(),
):
    try:
        settings[name] = value
        save_settings()
        typer.echo(_("Set {} to {}").format(name, value))
    except OmegaConfBaseException as e:
        raise e