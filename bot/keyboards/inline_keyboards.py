"""Inline keyboards with Premium Emoji."""
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Get main menu keyboard.

    Returns:
        Inline keyboard with start attack button.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Начать атаку",
                    callback_data="start_attack",
                    icon_custom_emoji_id="5332752267978239415",
                )
            ]
        ]
    )
    return keyboard


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Get confirmation keyboard.

    Returns:
        Inline keyboard with confirm and cancel buttons.
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Запустить",
                    callback_data="confirm_attack",
                    icon_custom_emoji_id="5336916024023345490",
                ),
                InlineKeyboardButton(
                    text="Отмена",
                    callback_data="cancel_attack",
                    icon_custom_emoji_id="5339047410133919746",
                ),
            ]
        ]
    )
    return keyboard
