"""FSM states for attack flow."""
from aiogram.fsm.state import State, StatesGroup


class AttackStates(StatesGroup):
    """FSM states for attack flow."""

    waiting_phone = State()
    waiting_repeats = State()
    confirmation = State()
