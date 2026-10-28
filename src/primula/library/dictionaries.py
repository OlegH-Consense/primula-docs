"""Built-in dictionaries of the standard library (sections 1, 3, 5, 6, 7).

The styles module extends and overrides them with ``currency(…)``,
``unit(…)``, ``month_names(…)``, ``typography(…)`` (library 1); the
settings are merged by layers in the style registry, and
:class:`primula.library.context.Library` merges them over these tables.
A call for a known code overrides only the given fields.

Currencies (library 3, decision 115): ``short`` — the symbol after the
number; ``units`` — forms by number (uk, ru: 1 / 2–4 / 5+; en: 1 / many);
``frac`` — genitive singular for fractional sums («12 500,50 гривні»);
``gender``; ``minor``, ``minor_gender``, ``minor_digits``.

Units (library 6): a quantity, the factor to the base unit of the quantity
and the symbols by language; temperatures also have an offset
(``value_in_K = value * factor + offset``).
"""

from __future__ import annotations

from decimal import Decimal

CURRENCIES: dict[str, dict[str, dict[str, object]]] = {
    "UAH": {
        "uk": {"short": "грн", "units": ("гривня", "гривні", "гривень"), "frac": "гривні", "gender": "f",
               "minor": ("копійка", "копійки", "копійок"), "minor_gender": "f", "minor_digits": 2},
        "ru": {"short": "грн", "units": ("гривна", "гривны", "гривен"), "frac": "гривны", "gender": "f",
               "minor": ("копейка", "копейки", "копеек"), "minor_gender": "f", "minor_digits": 2},
        "en": {"short": "UAH", "units": ("hryvnia", "hryvnias"), "gender": "f",
               "minor": ("kopiyka", "kopiykas"), "minor_gender": "f", "minor_digits": 2},
    },
    "USD": {
        "uk": {"short": "дол. США", "units": ("долар США", "долари США", "доларів США"), "frac": "долара США",
               "gender": "m", "minor": ("цент", "центи", "центів"), "minor_gender": "m", "minor_digits": 2},
        "ru": {"short": "долл. США", "units": ("доллар США", "доллара США", "долларов США"), "frac": "доллара США",
               "gender": "m", "minor": ("цент", "цента", "центов"), "minor_gender": "m", "minor_digits": 2},
        "en": {"short": "USD", "units": ("US dollar", "US dollars"), "gender": "m",
               "minor": ("cent", "cents"), "minor_gender": "m", "minor_digits": 2},
    },
    "EUR": {
        "uk": {"short": "євро", "units": ("євро", "євро", "євро"), "frac": "євро", "gender": "n",
               "minor": ("цент", "центи", "центів"), "minor_gender": "m", "minor_digits": 2},
        "ru": {"short": "евро", "units": ("евро", "евро", "евро"), "frac": "евро", "gender": "n",
               "minor": ("цент", "цента", "центов"), "minor_gender": "m", "minor_digits": 2},
        "en": {"short": "EUR", "units": ("euro", "euros"), "gender": "n",
               "minor": ("cent", "cents"), "minor_gender": "m", "minor_digits": 2},
    },
}

MONTHS: dict[str, dict[str, list[str]]] = {
    "uk": {
        "nom": ["січень", "лютий", "березень", "квітень", "травень", "червень", "липень", "серпень", "вересень",
                "жовтень", "листопад", "грудень"],
        "gen": ["січня", "лютого", "березня", "квітня", "травня", "червня", "липня", "серпня", "вересня",
                "жовтня", "листопада", "грудня"],
        "loc": ["січні", "лютому", "березні", "квітні", "травні", "червні", "липні", "серпні", "вересні",
                "жовтні", "листопаді", "грудні"],
    },
    "ru": {
        "nom": ["январь", "февраль", "март", "апрель", "май", "июнь", "июль", "август", "сентябрь", "октябрь",
                "ноябрь", "декабрь"],
        "gen": ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября",
                "ноября", "декабря"],
        "loc": ["январе", "феврале", "марте", "апреле", "мае", "июне", "июле", "августе", "сентябре", "октябре",
                "ноябре", "декабре"],
    },
    "en": {
        "nom": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
                "November", "December"],
    },
}

WEEKDAYS: dict[str, dict[str, list[str]]] = {
    "uk": {"nom": ["понеділок", "вівторок", "середа", "четвер", "п'ятниця", "субота", "неділя"],
           "acc": ["понеділок", "вівторок", "середу", "четвер", "п'ятницю", "суботу", "неділю"]},
    "ru": {"nom": ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"],
           "acc": ["понедельник", "вторник", "среду", "четверг", "пятницу", "субботу", "воскресенье"]},
    "en": {"nom": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
}

#: Calendar keys of weekdays (library 5): ``mon`` … ``sun``.
WEEKDAY_KEYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def _unit(quantity: str, factor: str, uk: str, ru: str, en: str, offset: str = "0") -> dict[str, object]:
    return {"quantity": quantity, "factor": Decimal(factor), "offset": Decimal(offset),
            "symbol": {"uk": uk, "ru": ru, "en": en}}


#: Units by code (library 6): SI symbols, Cyrillic for uk and ru.
UNITS: dict[str, dict[str, object]] = {
    "mV": _unit("voltage", "0.001", "мВ", "мВ", "mV"), "V": _unit("voltage", "1", "В", "В", "V"),
    "kV": _unit("voltage", "1000", "кВ", "кВ", "kV"),
    "mA": _unit("current", "0.001", "мА", "мА", "mA"), "A": _unit("current", "1", "А", "А", "A"),
    "W": _unit("power", "1", "Вт", "Вт", "W"), "kW": _unit("power", "1000", "кВт", "кВт", "kW"),
    "MW": _unit("power", "1000000", "МВт", "МВт", "MW"),
    "VA": _unit("apparent_power", "1", "В·А", "В·А", "VA"), "kVA": _unit("apparent_power", "1000", "кВ·А", "кВ·А", "kVA"),
    "Wh": _unit("energy", "1", "Вт·год", "Вт·ч", "Wh"), "kWh": _unit("energy", "1000", "кВт·год", "кВт·ч", "kWh"),
    "Hz": _unit("frequency", "1", "Гц", "Гц", "Hz"), "kHz": _unit("frequency", "1000", "кГц", "кГц", "kHz"),
    "MHz": _unit("frequency", "1000000", "МГц", "МГц", "MHz"),
    "Ohm": _unit("resistance", "1", "Ом", "Ом", "Ω"), "kOhm": _unit("resistance", "1000", "кОм", "кОм", "kΩ"),
    "MOhm": _unit("resistance", "1000000", "МОм", "МОм", "MΩ"),
    "mm": _unit("length", "0.001", "мм", "мм", "mm"), "cm": _unit("length", "0.01", "см", "см", "cm"),
    "m": _unit("length", "1", "м", "м", "m"), "km": _unit("length", "1000", "км", "км", "km"),
    "m2": _unit("area", "1", "м²", "м²", "m²"),
    "m3": _unit("volume", "1", "м³", "м³", "m³"), "l": _unit("volume", "0.001", "л", "л", "l"),
    "ml": _unit("volume", "0.000001", "мл", "мл", "ml"),
    "g": _unit("mass", "0.001", "г", "г", "g"), "kg": _unit("mass", "1", "кг", "кг", "kg"),
    "t": _unit("mass", "1000", "т", "т", "t"),
    "s": _unit("time", "1", "с", "с", "s"), "min": _unit("time", "60", "хв", "мин", "min"),
    "h": _unit("time", "3600", "год", "ч", "h"),
    "Pa": _unit("pressure", "1", "Па", "Па", "Pa"), "kPa": _unit("pressure", "1000", "кПа", "кПа", "kPa"),
    "MPa": _unit("pressure", "1000000", "МПа", "МПа", "MPa"), "bar": _unit("pressure", "100000", "бар", "бар", "bar"),
    "degC": _unit("temperature", "1", "°C", "°C", "°C", offset="273.15"), "K": _unit("temperature", "1", "К", "К", "K"),
    "%": _unit("fraction", "1", "%", "%", "%"),
}

#: Default typography settings (library 7).
TYPOGRAPHY: dict[str, object] = {"percent_space": True, "nbsp_short": False}
