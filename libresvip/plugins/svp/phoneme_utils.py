import re
from collections.abc import Iterable
from importlib.resources import files

from bidict import bidict
from ko_pron.ko_pron import romanise

from libresvip.core.compat import json
from libresvip.core.constants import DEFAULT_PHONEME
from libresvip.core.lyric_phoneme.chinese import get_pinyin_series
from libresvip.core.lyric_phoneme.japanese import to_romaji
from libresvip.utils.text import LATIN_ALPHABET

from .constants import DEFAULT_DURATIONS, DEFAULT_PHONE_RATIO

resource_dir = files("libresvip.plugins.svp")
phoneme_categories_by_language = json.loads(
    (resource_dir / "phoneme_categories.json").read_text(encoding="utf-8")
)
phoneme_dictionary = {
    language: bidict(xsampa_dict) if language in ["mandarin", "cantonese"] else xsampa_dict
    for language, xsampa_dict in json.loads(
        (resource_dir / "phoneme_dictionary.json").read_text(encoding="utf-8")
    ).items()
}


def sv_g2p_one(buffer: list[str], language: str | None) -> Iterable[str]:
    if language == "japanese":
        return (to_romaji(part) for part in buffer)
    elif language == "korean":
        return (phoneme_dictionary["korean"].get(romanise(part, "rr"), "l 6") for part in buffer)
    else:
        return get_pinyin_series(buffer, filter_non_chinese=False)


def sv_g2p(lyrics: Iterable[str], languages: Iterable[str]) -> list[str]:
    phoneme_list: list[str] = []
    builder: list[str] = []
    language = None
    for lyric, language in zip(lyrics, languages):
        if LATIN_ALPHABET.match(lyric) is not None:
            if builder:
                phoneme_list.extend(sv_g2p_one(builder, language))
                builder.clear()
            phoneme_list.append(lyric)
        else:
            builder.append(lyric)
    if builder:
        phoneme_list.extend(sv_g2p_one(builder, language))
    return phoneme_list


def xsampa2pinyin(xsampa: str, language: str) -> str:
    xsampa = re.sub(r"\s+", " ", xsampa).strip()
    return phoneme_dictionary[language].inverse.get(xsampa, DEFAULT_PHONEME)


def get_phoneme_categories(phoneme_parts: list[str], language: str) -> list[str]:
    if language in phoneme_categories_by_language:
        phoneme_categories = [
            phoneme_categories_by_language[language].get(phoneme) for phoneme in phoneme_parts
        ]
        if all(phoneme_category is not None for phoneme_category in phoneme_categories):
            return phoneme_categories
    return []


def number_of_phones(phoneme: str, language: str) -> int:
    phoneme_parts = phoneme.split()
    phoneme_categories = get_phoneme_categories(phoneme_parts, language)
    return len(phoneme_categories) if phoneme_categories else 2


def default_phone_marks(phoneme: str, language: str) -> list[float]:
    phoneme_parts = phoneme.split()
    res_len = max(len(phoneme_parts), 2)
    res = [0.0] * res_len
    if phoneme == "-":
        return res
    elif phoneme_categories := get_phoneme_categories(phoneme_parts, language):
        index = 0
        if phoneme_categories[index] in {"vowel", "diphthong"}:
            res[index] = getattr(DEFAULT_DURATIONS, phoneme_categories[index])
            index += 1
        if res_len > index:
            res[index:res_len] = [DEFAULT_PHONE_RATIO if index < res_len else 0.0] * (
                res_len - index
            )
    return res
