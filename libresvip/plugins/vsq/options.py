from pydantic import BaseModel, Field


class InputOptions(BaseModel):
    pass


class OutputOptions(BaseModel):
    ticks_per_beat: int = Field(
        default=480,
        title="Ticks per beat",
        description="Also known as parts per quarter, ticks per quarter note, the number of pulses per quarter note. This setting should not be changed unless you know what it is.",
    )
    lyric_encoding: str = Field(
        default="shift-jis",
        title="Lyric text encoding",
        description="Unless the lyrics are garbled, this option should not be changed.",
    )
