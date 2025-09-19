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


