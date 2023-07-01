import dataclasses

import pypinyin

from libresvip.model.base import (
    Note,
    Params,
    Point,
    Project,
    SingingTrack,
    SongTempo,
    TimeSignature,
)

from .model import NNInfoLine, NNNote, NNProject, NNTimeSignature
from .options import InputOptions


@dataclasses.dataclass
class NiaoNiaoParser:
    options: InputOptions
    length_multiplier: int = dataclasses.field(init=False)

    def parse_project(self, nn_project: NNProject) -> Project:
        if nn_project.info_line.version == 19:
            self.length_multiplier = 60
        else:
            self.length_multiplier = 30
        project = Project(
            SongTempoList=self.parse_tempos(nn_project.info_line),
            TimeSignatureList=self.parse_time_signatures(
                nn_project.info_line.time_signature
            ),
            TrackList=self.parse_tracks(nn_project.notes),
        )
        return project

    def parse_tempos(self, info_line: NNInfoLine) -> list[SongTempo]:
        return [SongTempo(BPM=info_line.tempo, Position=0)]

    def parse_time_signatures(
        self, time_signature: NNTimeSignature
    ) -> list[TimeSignature]:
        return [
            TimeSignature(
                Numerator=time_signature.numerator,
                Denominator=time_signature.denominator,
            )
        ]

    def parse_tracks(self, notes: list[NNNote]) -> list[SingingTrack]:
        return [
            SingingTrack(
                NoteList=self.parse_notes(notes),
                EditedParams=self.parse_params(notes),
            )
        ]

    def parse_notes(self, notes: list[NNNote]) -> list[Note]:
        note_list = []
        for nn_note in notes:
            note = Note(
                Lyric=nn_note.lyric,
                StartPos=nn_note.start * self.length_multiplier,
                Length=nn_note.duration * self.length_multiplier,
                KeyNumber=88 - nn_note.key,
            )
            phonemes = pypinyin.pinyin(
                nn_note.lyric, heteronym=True, style=pypinyin.STYLE_NORMAL
            )
            if len(phonemes[0]) > 1 or phonemes[0][0] != nn_note.pronunciation:
                note.pronunciation = nn_note.pronunciation
            note_list.append(note)
        return note_list

    def parse_params(self, notes: list[NNNote]) -> Params:
        params = Params()
        for nn_note in notes:
            if nn_note.pitch.point_count > 0 and any(
                point != 50 for point in nn_note.pitch.points
            ):
                step = (
                    nn_note.duration
                    * self.length_multiplier
                    / (nn_note.pitch.point_count - 1)
                )
                pbs = nn_note.pitch_bend_sensitivity + 1
                params.pitch.points.append(
                    Point(nn_note.start * self.length_multiplier - 5 + 1920, -100)
                )
                for i in range(nn_note.pitch.point_count):
                    params.pitch.points.append(
                        Point(
                            round(nn_note.start * self.length_multiplier + i * step)
                            + 1920,
                            round(
                                (
                                    (nn_note.pitch.points[i] - 50) / 50 * pbs
                                    + 88
                                    - nn_note.key
                                )
                                * 100
                            ),
                        )
                    )
                params.pitch.points.append(
                    Point(
                        (nn_note.start + nn_note.duration) * self.length_multiplier
                        + 5
                        + 1920,
                        -100,
                    )
                )
            # TODO: volume
        return params
