"""Configuration settings using python-dotenv."""
from dataclasses import dataclass
from os import getenv
from typing import Set

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True, slots=True)
class Settings:
    """Application settings."""

    bot_token: str
    admin_ids: Set[int]
    bot_image: str

    @classmethod
    def from_env(cls) -> "Settings":
        """Create settings from environment variables."""
        bot_token = getenv("BOT_TOKEN", "")
        if not bot_token:
            raise ValueError("BOT_TOKEN is required")

        admin_ids_str = getenv("ADMIN_IDS", "")
        admin_ids = {
            int(id_.strip()) for id_ in admin_ids_str.split(",") if id_.strip()
        }

        bot_image = getenv("BOT_IMAGE", "")

        return cls(
            bot_token=bot_token,
            admin_ids=admin_ids,
            bot_image=bot_image,
        )


settings = Settings.from_env()
