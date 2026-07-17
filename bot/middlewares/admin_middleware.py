"""Admin authorization middleware."""
from aiogram import BaseMiddleware
from aiogram.types import Message

from bot.config.settings import settings


class AdminMiddleware(BaseMiddleware):
    """Middleware to check admin access."""

    async def __call__(
        self,
        handler,
        event: Message,
        data: dict,
    ) -> None:
        """Check if user is admin before processing handler.

        Args:
            handler: Next handler in chain.
            event: Telegram message event.
            data: Middleware data.
        """
        if event.from_user.id not in settings.admin_ids:
            await event.answer(
                "<tg-emoji emoji-id=\"5330273431898318607\">🌟</tg-emoji> Доступ закрыт.\n\n"
                "Для получения доступа обратитесь к\n"
                "<a href=\"https://t.me/enotdev\">@enotdev</a>",
                parse_mode="HTML",
            )
            return

        await handler(event, data)
