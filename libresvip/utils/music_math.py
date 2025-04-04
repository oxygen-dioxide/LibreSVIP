import dataclasses
import functools
import math
import re
from collections.abc import Callable
from typing import Concatenate

from more_itertools import pairwise
from typing_extensions import ParamSpec

from libresvip.core.constants import KEY_IN_OCTAVE
from libresvip.model.point import Point

P = ParamSpec("P")
NOTE_RE = re.compile(r"^(?P<note>[A-Ga-g])(?P<accidental>[#♯𝄪b!♭𝄫♮]*)(?P<octave>[+-]?\d+)?$")


def midi2note(midi: float) -> str:
    pitch_map = [
        "C",
        "C#",
        "D",
        "D#",
        "E",
        "F",
        "F#",
        "G",
        "G#",
        "A",
        "A#",
        "B",
    ]
    midi = round(midi)
    octave = (midi // KEY_IN_OCTAVE) - 1
    pitch = pitch_map[midi % KEY_IN_OCTAVE]
    return f"{pitch}{octave}"


def note2midi(note: str) -> int:
    pitch_map = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    acc_map = {
        "#": 1,
        "": 0,
        "b": -1,
        "!": -1,
        "♯": 1,
        "𝄪": 2,
        "♭": -1,
        "𝄫": -2,
        "♮": 0,
    }

    if (match := NOTE_RE.match(note)) is None:
        msg = f"Invalid note format: {note!r}"
        raise ValueError(msg)

    pitch = match["note"].upper()
    offset = sum(acc_map[o] for o in match["accidental"])
    octave = match["octave"]

    octave = int(octave) if octave else 0

    note_value = KEY_IN_OCTAVE * (octave + 1) + pitch_map[pitch] + offset

    return round(note_value)


def hz2midi(hz: float, a4_midi: int = 69, base_freq: float = 440.0) -> float:
    return a4_midi + KEY_IN_OCTAVE * math.log2(hz / base_freq)


def midi2hz(midi: float, a4_midi: int = 69, base_freq: float = 440.0) -> float:
    return base_freq * 2 ** ((midi - a4_midi) / KEY_IN_OCTAVE)


def clamp(
    x: float,
    lower: float | None = None,
    upper: float | None = None,
) -> float:
    """Limit a value to a given range.

    The returned value is guaranteed to be between *lower* and
    *upper*. Integers, floats, and other comparable types can be
    mixed.

    Similar to `numpy's clip`_ function.

    .. _numpy's clip: http://docs.scipy.org/doc/numpy/reference/generated/numpy.clip.html
    .. from boltons: https://boltons.readthedocs.io/en/latest/mathutils.html#boltons.mathutils.clamp

    """
    if lower is None:
        lower = float("-inf")
    if upper is None:
        upper = float("inf")
    if upper < lower:
        msg = f"expected upper bound ({upper!r}) >= lower bound ({lower!r})"
        raise ValueError(msg)
    return min(max(x, lower), upper)


def _transform_interpolation_args(
    func: Callable[Concatenate[float, P], float],
) -> Callable[[float, tuple[float, float], tuple[float, float]], float]:
    @functools.wraps(func, assigned=["__module__", "__name__", "__qualname__", "__doc__"])
    def inner(
        x: float,
        start: tuple[float, float],
        end: tuple[float, float],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> float:
        x0, y0 = start
        x1, y1 = end
        r = (x - x0) / (x1 - x0)
        return y0 + (y1 - y0) * func(r, *args, **kwargs)

    return inner


@_transform_interpolation_args
def linear_interpolation(r: float) -> float:
    return r


@_transform_interpolation_args
def cosine_easing_in_interpolation(r: float) -> float:
    return 1 - math.cos(r * math.pi / 2)


@_transform_interpolation_args
def cosine_easing_out_interpolation(r: float) -> float:
    return math.sin(r * math.pi / 2)


@_transform_interpolation_args
def cosine_easing_in_out_interpolation(r: float) -> float:
    return (1 - math.cos(r * math.pi)) / 2


@_transform_interpolation_args
def cubic_interpolation(r: float) -> float:
    return (3 - 2 * r) * r**2


@_transform_interpolation_args
def vocaloid_interpolation(r: float) -> float:
    return math.sin(r * math.pi) / 2 if r <= 0.5 else r


@_transform_interpolation_args
def sigmoid_interpolation(r: float, k: float) -> float:
    return 1 / (1 + math.exp(k * (-2 * r + 1)))


def _inner_interpolate(
    data: list[Point],
    sampling_interval_tick: int,
    mapping: Callable[[int, Point, Point], float],
) -> list[Point]:
    return (
        (
            [data[0]]
            + [
                Point(x=x, y=round(mapping(x, start, end)))
                for start, end in pairwise(data)
                for x in range(start.x + 1, end.x, sampling_interval_tick)
            ]
            + [data[-1]]
        )
        if data
        else data
    )


interpolate_linear = functools.partial(_inner_interpolate, mapping=linear_interpolation)
interpolate_cosine_ease_in_out = functools.partial(
    _inner_interpolate, mapping=cosine_easing_in_out_interpolation
)
interpolate_cosine_ease_in = functools.partial(
    _inner_interpolate, mapping=cosine_easing_in_interpolation
)
interpolate_cosine_ease_out = functools.partial(
    _inner_interpolate, mapping=cosine_easing_out_interpolation
)


@dataclasses.dataclass
class HermiteInterpolator:
    # from https://github.com/LiuYunPlayer/TuneLab/blob/master/TuneLab.Base/Science/HermiteInterpolation.cs

    points: list[tuple[float, float]]

    @staticmethod
    def f1(t1: float, t2: float) -> float:
        return (1 + 2 * t1) * t2**2

    @staticmethod
    def f3(t: float, d: float) -> float:
        return t**2 * d

    @staticmethod
    def slope(p1: tuple[float, float], p2: tuple[float, float]) -> float:
        return (p2[1] - p1[1]) / (p2[0] - p1[0]) if p2[0] != p1[0] else math.nan

    def slope_at(self, point_index: int) -> float:
        if point_index in [0, len(self.points) - 1]:
            return 0
        point = self.points[point_index]
        last_k = self.slope(point, self.points[point_index - 1])
        next_k = self.slope(point, self.points[point_index + 1])
        kk = last_k * next_k
        return 0 if kk <= 0 else 2 / (1 / last_k + 1 / next_k)

    def interpolate(self, xs: list[float]) -> list[float]:
        if len(self.points) < 2:
            return [self.points[0][1] if len(self.points) == 1 else 0] * len(xs)
        elif len(self.points) == 2:
            return [linear_interpolation(x, self.points[0], self.points[1]) for x in xs]
        point_index = 0
        ys = []
        for x in xs:
            while point_index < len(self.points) and self.points[point_index][0] < x:
                point_index += 1
            if point_index == 0:
                ys.append(self.points[0][1])
            elif point_index == len(self.points):
                ys.append(self.points[-1][1])
            else:
                last_point = self.points[point_index - 1]
                last_delta = self.slope_at(point_index - 1)
                next_point = self.points[point_index]
                next_delta = self.slope_at(point_index)
                delta_1 = x - last_point[0]
                delta_2 = x - next_point[0]
                t1 = delta_1 / (next_point[0] - last_point[0])
                t2 = delta_2 / (last_point[0] - next_point[0])
                ys.append(
                    self.f1(t1, t2) * last_point[1]
                    + self.f1(t2, t1) * next_point[1]
                    + self.f3(t2, delta_1) * last_delta
                    + self.f3(t1, delta_2) * next_delta
                )
        return ys


def db_to_float(db: float, using_amplitude: bool = True) -> float:
    """
    Converts the input db to a float, which represents the equivalent
    ratio in power.
    """
    return 10 ** (db / 20) if using_amplitude else 10 ** (db / 10)


def ratio_to_db(ratio: float, val2: float | None = None, using_amplitude: bool = True) -> float:
    """
    Converts the input float to db, which represents the equivalent
    to the ratio in power represented by the multiplier passed in.
    """

    # accept 2 values and use the ratio of val1 to val2
    if val2 is not None:
        ratio /= val2

    # special case for multiply-by-zero (convert to silence)
    if ratio == 0:
        return -float("inf")

    return 20 * math.log10(ratio) if using_amplitude else 10 * math.log10(ratio)
