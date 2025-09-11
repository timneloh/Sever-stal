from aiogram.fsm.state import State, StatesGroup

class TestStates(StatesGroup):
    CHOOSE_TEST = State()
    SERIOUS_TEST = State()
    FUN_TEST = State()

class Day2States(StatesGroup):
    CHOOSE_CARD = State()

class Day3States(StatesGroup):
    CHOOSE_HERO = State()
    COMICS_PROGRESS = State()
    QUIZ = State()

class Day4States(StatesGroup):
    WATCHING_VIDEO = State()
    QUIZ = State()

class Day5States(StatesGroup):
    QUIZ = State()
    REFLECTION = State()

SERIOUS_INTRO = (
    "Сегодня проверим твой стиль коммуникации на работе!\n\n"
    "Это короткий тест по международной методике DiSC. "
    "Отвечай спонтанно, не обдумывай слишком долго — так результат будет яснее и полезнее.\n\n"
    "В финале тебя ждёт твой коммуникационный профиль и 3 полезных совета 💡"
)
