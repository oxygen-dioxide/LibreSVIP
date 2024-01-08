import dataclasses
import re
from typing import Optional

from libresvip.core.constants import DEFAULT_CHINESE_LYRIC
from libresvip.core.time_sync import TimeSynchronizer
from libresvip.model.base import (
    InstrumentalTrack,
    Note,
    ParamCurve,
    Params,
    Phones,
    Project,
    SingingTrack,
    SongTempo,
    TimeSignature,
    Track,
    VibratoParam,
)

from .models import OpenSvipNoteHeadTags, OpenSvipReverbPresets, opensvip_singers
from .msnrbf.constants import (
    VALUE_LIST_VERSION_SONG_BEAT,
    VALUE_LIST_VERSION_SONG_ITRACK,
    VALUE_LIST_VERSION_SONG_NOTE,
    VALUE_LIST_VERSION_SONG_TEMPO,
)
from .msnrbf.xstudio_models import (
    XSAppModel,
    XSBeatSize,
    XSInstrumentTrack,
    XSITrack,
    XSLineParam,
    XSLineParamNode,
    XSNote,
    XSNotePhoneInfo,
    XSSingingTrack,
    XSSongBeat,
    XSSongTempo,
    XSVibratoPercentInfo,
    XSVibratoStyle,
)
from .options import OutputOptions


@dataclasses.dataclass
class BinarySvipGenerator:
    options: OutputOptions
    is_absolute_time_mode: bool = dataclasses.field(init=False)
    synchronizer: TimeSynchronizer = dataclasses.field(init=False)
    first_bar_tick: int = dataclasses.field(init=False)
    first_bar_tempo: list[SongTempo] = dataclasses.field(init=False)

    def generate_project(self, project: Project) -> tuple[str, XSAppModel]:
        version = (
            project.version
            if re.match(r"^SVIP\d\.\d\.\d$", project.version) is not None
            else "SVIP6.0.0"
        )
        model = XSAppModel()
        self.first_bar_tick = int(
            round(
                1920.0
                * project.time_signature_list[0].numerator
                / project.time_signature_list[0].denominator
            )
        )
        self.first_bar_tempo = [
            tempo for tempo in project.song_tempo_list if tempo.position < self.first_bar_tick
        ]
        self.is_absolute_time_mode = any(
            (tempo.bpm < 20 or tempo.bpm > 300) for tempo in project.song_tempo_list
        )
        self.synchronizer = TimeSynchronizer(
            project.song_tempo_list,
            self.first_bar_tick,
            self.is_absolute_time_mode,
            self.options.tempo,
        )

        # beat
        beat_list = model.beat_list.buf.items
        if self.is_absolute_time_mode or any(
            (beat.numerator > 255 or beat.denominator > 32) for beat in project.time_signature_list
        ):
            beat_list.append(XSSongBeat(bar_index=0, beat_size=XSBeatSize(x=4, y=4)))
        else:
            for beat in project.time_signature_list:
                beat_list.append(self.generate_time_signature(beat))
        model.beat_list.buf.size = len(beat_list)
        model.beat_list.buf.version = VALUE_LIST_VERSION_SONG_BEAT
        model.beat_list.buf1 = model.beat_list.buf

        # tempo
        tempo_list = model.tempo_list.buf.items
        if self.is_absolute_time_mode:
            tempo_list.append(XSSongTempo(pos=0, tempo=self.options.tempo * 100))
        else:
            for tempo in project.song_tempo_list:
                tempo_list.append(self.generate_song_tempo(tempo))
        model.tempo_list.buf.size = len(tempo_list)
        model.tempo_list.buf.version = VALUE_LIST_VERSION_SONG_TEMPO
        model.tempo_list.buf1 = model.tempo_list.buf

        # tracks
        track_list = []
        for track in project.track_list:
            ele = self.generate_track(track)
            if ele is not None:
                track_list.append(ele)
        model.track_list.size = len(track_list)
        model.track_list.version = VALUE_LIST_VERSION_SONG_ITRACK
        model.track_list.items = track_list
        return version, model

    @staticmethod
    def generate_song_tempo(tempo: SongTempo) -> XSSongTempo:
        xs_tempo = XSSongTempo(pos=tempo.position, tempo=round(tempo.bpm * 100))
        return xs_tempo

    @staticmethod
    def generate_time_signature(signature: TimeSignature) -> XSSongBeat:
        beat = XSSongBeat(
            bar_index=signature.bar_index,
            beat_size=XSBeatSize(x=signature.numerator, y=signature.denominator),
        )
        return beat

    def generate_track(self, track: Track) -> Optional[XSITrack]:
        if isinstance(track, SingingTrack):
            singer_id = opensvip_singers.get_id(track.ai_singer_name)
            if singer_id == "":
                singer_id = opensvip_singers.get_id(self.options.singer)
            s_track = XSSingingTrack(
                ai_singer_id=singer_id,
                reverb_preset=OpenSvipReverbPresets.get_index(track.reverb_preset),
            )

            note_list = s_track.note_list.buf.items
            for note in track.note_list:
                new_note = self.generate_note(note)
                if new_note is not None:
                    note_list.append(new_note)
            s_track.note_list.buf.size = len(note_list)
            s_track.note_list.buf.version = VALUE_LIST_VERSION_SONG_NOTE
            s_track.note_list.buf1 = s_track.note_list.buf

            params = self.generate_params(track.edited_params)
            s_track.edited_pitch_line = params["Pitch"]
            s_track.edited_volume_line = params["Volume"]
            s_track.edited_breath_line = params["Breath"]
            s_track.edited_gender_line = params["Gender"]
            if self.options.version == "SVIP7.0.0":
                s_track.edited_power_line = params["Strength"]
        elif isinstance(track, InstrumentalTrack):
            s_track = XSInstrumentTrack(
                instrument_file_path=track.audio_file_path,
                offset_in_pos=track.offset,
            )
        else:
            return None
        s_track.name = track.title
        s_track.mute = track.mute
        s_track.solo = track.solo
        s_track.volume = track.volume
        s_track.pan = track.pan
        return s_track

    def generate_note(self, note: Note) -> XSNote:
        if note.lyric or note.pronunciation:
            xs_note = XSNote(
                start_pos=round(self.synchronizer.get_actual_ticks_from_ticks(note.start_pos)),
                key_index=note.key_number + 12,
                head_tag=OpenSvipNoteHeadTags.get_index(note.head_tag),
                lyric=note.lyric or DEFAULT_CHINESE_LYRIC,
            )
            xs_note.width_pos = (
                round(self.synchronizer.get_actual_ticks_from_ticks(note.end_pos))
                - xs_note.start_pos
            )
            if note.pronunciation:
                xs_note.pronouncing = note.pronunciation
            if note.edited_phones is not None:
                xs_note.note_phone_info = self.generate_phones(note.edited_phones)
            if note.vibrato is not None:
                percent, vibrato = self.generate_vibrato(note.vibrato)
                xs_note.vibrato_percent_info = percent
                xs_note.vibrato = vibrato
            return xs_note

    @staticmethod
    def generate_phones(edited_phones: Phones) -> XSNotePhoneInfo:
        phone = XSNotePhoneInfo(
            head_phone_time_in_sec=edited_phones.head_length_in_secs,
            mid_part_over_tail_part_ratio=edited_phones.mid_ratio_over_tail,
        )
        return phone

    def generate_vibrato(
        self, vibrato: VibratoParam
    ) -> tuple[XSVibratoPercentInfo, XSVibratoStyle]:
        percent = XSVibratoPercentInfo(
            start_percent=vibrato.start_percent, end_percent=vibrato.end_percent
        )
        vibrato_style = XSVibratoStyle(
            is_anti_phase=vibrato.is_anti_phase,
            amp_line=self.generate_param_curve(
                vibrato.amplitude, left=-1, right=100001, is_ticks=False
            ),
            freq_line=self.generate_param_curve(
                vibrato.frequency, left=-1, right=100001, is_ticks=False
            ),
        )
        return percent, vibrato_style

    def generate_params(self, edited_params: Params) -> dict[str, XSLineParam]:
        return {
            "Pitch": self.generate_param_curve(
                edited_params.pitch, op=lambda x: x + 1150 if x > -100 else -100
            ),
            "Volume": self.generate_param_curve(edited_params.volume),
            "Breath": self.generate_param_curve(edited_params.breath),
            "Gender": self.generate_param_curve(edited_params.gender),
            "Strength": self.generate_param_curve(edited_params.strength),
        }

    def generate_param_curve(
        self,
        param_curve: ParamCurve,
        op=None,
        left=-192000,
        right=1073741823,
        termination=0,
        is_ticks: bool = True,
    ) -> XSLineParam:
        if op is None:
            op = lambda x: x
        line = XSLineParam()
        # param_curve.points = sorted(param_curve.points, key=operator.attrgetter("x"))
        for p in param_curve.points.root:
            if left <= p.x <= right:
                if self.is_absolute_time_mode and is_ticks and p.x != left and p.x != right:
                    pos = (
                        round(
                            self.synchronizer.get_actual_ticks_from_ticks(p.x - self.first_bar_tick)
                        )
                        + 1920
                    )
                else:
                    pos = p.x
                node = XSLineParamNode(pos=pos, value=op(p.y))
                line.nodes.append(node)
        if len(line.nodes) == 0 or line.nodes[0].pos > left:
            bound = XSLineParamNode(pos=left, value=termination)
            line.nodes.insert(0, bound)
        if len(line.nodes) == 0 or line.nodes[-1].pos < right:
            bound = XSLineParamNode(pos=right, value=termination)
            line.nodes.append(bound)
        line.convert_to_param()
        return line
