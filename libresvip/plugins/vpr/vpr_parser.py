import dataclasses

from libresvip.core.constants import DEFAULT_ENGLISH_LYRIC
from libresvip.model.base import (
    InstrumentalTrack,
    Note,
    Project,
    SingingTrack,
    SongTempo,
    TimeSignature,
    Track,
)

from .constants import (
    BPM_RATE,
    PITCH_BEND_NAME,
    PITCH_BEND_SENSITIVITY_NAME,
)
from .model import (
    VocaloidAudioTrack,
    VocaloidNotes,
    VocaloidPartPitchData,
    VocaloidPoint,
    VocaloidProject,
    VocaloidTimeSig,
    VocaloidTracks,
)
from .options import InputOptions
from .vocaloid_pitch import pitch_from_vocaloid_parts


@dataclasses.dataclass
class VocaloidParser:
    options: InputOptions
    comp_id2name: dict[str, str] = dataclasses.field(init=False)

    def parse_project(self, vpr_project: VocaloidProject) -> Project:
        self.comp_id2name = {voice.comp_id: voice.name for voice in vpr_project.voices}
        project = Project(
            time_signature_list=self.parse_time_signatures(
                vpr_project.master_track.time_sig.events
            ),
            song_tempo_list=self.parse_tempos(vpr_project.master_track.tempo.events),
        )
        project.track_list = self.parse_tracks(vpr_project.tracks)
        return project

    def parse_time_signatures(self, time_signatures: list[VocaloidTimeSig]) -> list[TimeSignature]:
        return [
            TimeSignature(
                bar_index=time_signature.bar,
                numerator=time_signature.numer,
                denominator=time_signature.denom,
            )
            for time_signature in time_signatures
        ]

    def parse_tempos(self, tempos: list[VocaloidPoint]) -> list[SongTempo]:
        return [
            SongTempo(
                position=tempo.pos,
                bpm=tempo.value / BPM_RATE,
            )
            for tempo in tempos
        ]

    def parse_tracks(self, tracks: list[VocaloidTracks]) -> list[Track]:
        track_list = []
        for track in tracks:
            if isinstance(track, VocaloidAudioTrack):
                for part in track.parts:
                    # wav_path = f"Project/Audio/{part.name}"
                    instrumental_track = InstrumentalTrack(
                        title=part.name,
                        offset=part.pos,
                        mute=track.is_muted,
                        solo=track.is_solo_mode,
                        audio_file_path=part.wav.original_name,
                    )
                    track_list.append(instrumental_track)
            else:
                for part in track.parts:
                    comp_id = None
                    if part.voice is not None:
                        comp_id = part.voice.comp_id
                    elif part.ai_voice is not None:
                        comp_id = part.ai_voice.comp_id
                    singing_track = SingingTrack(
                        title=part.name,
                        mute=track.is_muted,
                        solo=track.is_solo_mode,
                        note_list=self.parse_notes(part.notes, part.pos),
                        ai_singer_name=self.comp_id2name.get(comp_id, ""),
                    )
                    part_data = VocaloidPartPitchData(
                        start_pos=part.pos,
                        pit=part.get_controller_events(PITCH_BEND_NAME),
                        pbs=part.get_controller_events(PITCH_BEND_SENSITIVITY_NAME),
                    )
                    if (
                        part_pitch := pitch_from_vocaloid_parts(
                            [part_data], singing_track.note_list
                        )
                    ) is not None:
                        singing_track.edited_params.pitch = part_pitch
                    track_list.append(singing_track)
        return track_list

    def parse_notes(self, notes: list[VocaloidNotes], pos: int) -> list[Note]:
        return [
            Note(
                start_pos=note.pos + pos,
                length=note.duration,
                key_number=note.number,
                lyric=note.lyric or DEFAULT_ENGLISH_LYRIC,
                pronunciation=note.phoneme,
            )
            for note in notes
        ]
