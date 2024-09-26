from enum import Enum
from typing import Final

VELOCITY_CONSTANT: Final[float] = 1.75
EXPRESSION_CONSTANT: Final[float] = 2.0
PITCH_MAX_VALUE: Final[int] = 8191
BORDER_APPEND_RADIUS: Final[int] = 5
MIN_BREAK_LENGTH_BETWEEN_PITCH_SECTIONS: Final[int] = 480


class ControlChange(Enum):
    BANK_SELECT = 0
    MODULATION = 1
    BREATH = 2
    FOOT = 4
    PORTAMENTO_TIME = 5
    DATA_ENTRY = 6
    VOLUME = 7
    BALANCE = 8
    PAN = 10
    EXPRESSION = 11
    EFFECT_1 = 12
    EFFECT_2 = 13
    GENERAL_1 = 16
    GENERAL_2 = 17
    GENERAL_3 = 18
    GENERAL_4 = 19
    BANK_SELECT_L = 32
    MODULATION_L = 33
    BREATH_L = 34
    FOOT_L = 36
    PORTAMENTO_TIME_L = 37
    DATA_ENTRY_L = 38
    VOLUME_L = 39
    BALANCE_L = 40
    PAN_L = 42
    EXPRESSION_L = 43
    EFFECT_1_L = 44
    EFFECT_2_L = 45
    GENERAL_1_L = 48
    GENERAL_2_L = 49
    GENERAL_3_L = 50
    GENERAL_4_L = 51
    HOLD = 64
    PORTAMENTO = 65
    SUSTENUTO = 66
    SOFT_PEDAL = 67
    LEGATO_FOOTSWITCH = 68
    HOLD_2 = 69
    SOUND_VARIATION = 70
    SOUND_TIMBRE = 71
    SOUND_RELEASE_TIME = 72
    SOUND_ATTACK_TIME = 73
    SOUND_BRIGHTNESS = 74
    SOUND_CONTROL_6 = 75
    SOUND_CONTROL_7 = 76
    SOUND_CONTROL_8 = 77
    SOUND_CONTROL_9 = 78
    SOUND_CONTROL_10 = 79
    GENERAL_5 = 80
    GENERAL_6 = 81
    GENERAL_7 = 82
    GENERAL_8 = 83
    PORTAMENTO_CONTROL = 84
    EFFECTS_DEPTH_1 = 91
    EFFECTS_DEPTH_2 = 92
    EFFECTS_DEPTH_3 = 93
    EFFECTS_DEPTH_4 = 94
    EFFECTS_DEPTH_5 = 95
    DATA_INCREMENT = 96
    DATA_DECREMENT = 97
    NRPN_LSB = 98
    NRPN_MSB = 99
    RPN_LSB = 100
    RPN_MSB = 101
    ALL_SOUND_OFF = 120
    RESET_ALL_CONTROLLERS = 121
    LOCAL_CONTROL = 122
    ALL_NOTES_OFF = 123
    OMNI_MODE_OFF = 124
    OMNI_MODE_ON = 125
    MONO_MODE_ON = 126
    POLY_MODE_ON = 127
