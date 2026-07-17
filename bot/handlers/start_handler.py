"""Start command handler."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config.settings import settings
from bot.keyboards.inline_keyboards import get_main_menu_keyboard

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    """Handle /start command.

    Args:
        message: Telegram message.
    """
    caption = (
        "<tg-emoji emoji-id=\"5334617288807048693\">🌟</tg-emoji> <b>Добро пожаловать!</b>\n\n"
        "<tg-emoji emoji-id=\"5332572076920298887\">🌟</tg-emoji> Это мощный смс-бомбер с более чем 330+ сервисами!\n\n"
        "<tg-emoji emoji-id=\"5332289648460853008\">🌟</tg-emoji> Нажимай кнопку ниже для начала атаки."
    )

    if settings.bot_image:
        await message.answer_photo(
            settings.bot_image,
            caption=caption,
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(),
        )
    else:
        await message.answer(
            caption,
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(),
        )
