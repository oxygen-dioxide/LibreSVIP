import dataclasses

from libresvip.core.constants import DEFAULT_CHINESE_LYRIC, TICKS_IN_BEAT
from libresvip.model.base import Note, Project, SingingTrack, SongTempo, TimeSignature
from libresvip.utils import note2midi

from .models.mxml2 import ScorePartwise
from .options import InputOptions


@dataclasses.dataclass
class MusicXMLParser:
    options: InputOptions

    def parse_project(self, mxml: ScorePartwise) -> Project:
        part_nodes = mxml.part

        mater_track = next((part for part in part_nodes if part.measure), None)
        (
            time_signatures,
            tempos,
            measure_borders,
            import_tick_rate,
        ) = self.parse_master_track(mater_track)
        time_signatures = time_signatures or [TimeSignature()]
        tempos = tempos or [SongTempo()]

        tracks = [
            self.parse_track(index, part, measure_borders, import_tick_rate)
            for index, part in enumerate(part_nodes)
        ]

        return Project(
            track_list=tracks,
            time_signature_list=time_signatures,
            song_tempo_list=tempos,
        )

    def parse_master_track(self, part_node: ScorePartwise.Part):
        measure_nodes = part_node.measure
        divisions = int(measure_nodes[0].attributes[0].divisions)
        import_tick_rate = TICKS_IN_BEAT / divisions
        tempos = []
        time_signatures = []
        measure_borders = [0]
        tick_position = 0
        current_time_signature = TimeSignature()
        for measure_node in measure_nodes:
            if (
                len(measure_node.attributes)
                and len(measure_node.attributes[0].time)
                and (time_signature_node := measure_node.attributes[0].time[0])
            ):
                numerator = int(time_signature_node.beats[0])
                denominator = int(time_signature_node.beat_type[0])
                current_time_signature = TimeSignature(
                    numerator=numerator, denominator=denominator
                )
                time_signatures.append(current_time_signature)

            sound_nodes = measure_node.sound
            if len(sound_nodes) and (sound_node := sound_nodes[0]).tempo:
                tempo = SongTempo(
                    position=tick_position,
                    bpm=float(sound_node.tempo),
                )
                tempos.append(tempo)

            tick_position += current_time_signature.bar_length()
            measure_borders.append(tick_position)
        return time_signatures, tempos, measure_borders, import_tick_rate

    def parse_track(
        self,
        track_index,
        part_node: ScorePartwise.Part,
        measure_borders: list[tuple[int, int]],
        import_tick_rate: float,
    ) -> SingingTrack:
        track_name = f"Track {track_index + 1}"
        notes = []
        is_inside_note = False
        import_tick_rate = import_tick_rate
        measure_nodes = part_node.measure
        for index, measure_node in enumerate(measure_nodes):
            tick_position = measure_borders[index]
            note_nodes = measure_node.note
            for note_node in note_nodes:
                duration_nodes = note_node.duration
                duration = (
                    int(duration_nodes[0]) * import_tick_rate
                    if len(duration_nodes)
                    else None
                )
                if not duration:
                    if note_node.grace:
                        continue
                    else:
                        msg = "Duration not found"
                        raise ValueError(msg)

                rest_nodes = note_node.rest
                if rest_nodes:
                    tick_position += duration
                    continue

                pitch_node = note_node.pitch[0]
                step = pitch_node.step
                alter_node = pitch_node.alter
                alter = int(alter_node) if alter_node else 0
                octave = int(pitch_node.octave) + 1
                key = note2midi(f"{step.value}{octave}") + alter

                lyric_nodes = note_node.lyric
                lyric = (
                    lyric_nodes[0].text[0].value
                    if len(lyric_nodes)
                    else DEFAULT_CHINESE_LYRIC
                )

                if not is_inside_note:
                    note = Note(
                        key_number=key,
                        lyric=lyric,
                        start_pos=tick_position,
                        length=duration,
                    )
                    notes.append(note)
                else:
                    notes[-1] = notes[-1].model_copy(
                        update={
                            "length": notes[-1].length + duration,
                        }
                    )

                tick_position += duration

                tie_nodes = note_node.tie
                if (
                    len(tie_nodes)
                    and (tie_node := tie_nodes[0])
                    and tie_node.type_value
                ):
                    if tie_node.type_value == "start":
                        is_inside_note = True
                    elif tie_node.type_value == "stop":
                        is_inside_note = False

        return SingingTrack(
            title=track_name,
            note_list=notes,
        )