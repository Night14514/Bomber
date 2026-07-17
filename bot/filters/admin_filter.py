"""Admin authorization filter."""
from aiogram.filters import BaseFilter
from aiogram.types import Message

from bot.config.settings import settings


class AdminFilter(BaseFilter):
    """Filter to check if user is admin."""

    async def __call__(self, message: Message) -> bool:
        """Check if user is in admin list.

        Args:
            message: Telegram message.

        Returns:
            True if user is admin, False otherwise.
        """
        return message.from_user.id in settings.admin_ids
