from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)


def invite_keyboard(
    invite_code: str
):

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔗 Открыть приглашение",
                    url=(
                        f"https://t.me/"
                        f"{'YOUR_BOT_USERNAME'}"
                        f"?start={invite_code}"
                    )
                )
            ]
        ]
    )
