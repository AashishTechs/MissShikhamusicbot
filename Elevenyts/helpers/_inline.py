# ==========================================================
# Copyright (c) 2026 ArtistBots
# All Rights Reserved.
#
# Project      : ArtistBots API Telegram Music Bot
# Powered By   : Artist
# Type         : API Based Telegram Music Bot
#
# Bot          : @ArtistApibot
# Channel      : https://t.me/artistbots
# GitHub       : https://github.com/elevenyts
#
# Unauthorized copying, modification, or redistribution
# of this source code without permission is prohibited.
# ==========================================================

from pyrogram import types
from pyrogram.enums import ButtonStyle

from Elevenyts import app, config, lang


class Inline:
    def __init__(self):
        self.ikm = types.InlineKeyboardMarkup
        self.ikb = types.InlineKeyboardButton

    # ======================================================
    # DOWNLOAD CANCEL BUTTON
    # ======================================================

    def cancel_dl(self, text) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text=text,
                        callback_data="cancel_dl",
                        style=ButtonStyle.PRIMARY,
                    )
                ]
            ]
        )

    # ======================================================
    # PREMIUM MUSIC PLAYER
    # ======================================================

    def controls(
        self,
        chat_id: int,
        status: str = None,
        timer: str = None,
        remove: bool = False,
    ) -> types.InlineKeyboardMarkup:

        keyboard = []

        # --------------------------------------------------
        # MUSIC PROGRESS
        # --------------------------------------------------

        if status:
            keyboard.append(
                [
                    self.ikb(
                        text=f"🎶  {status}",
                        callback_data=f"controls status {chat_id}",
                    )
                ]
            )

        elif timer:
            keyboard.append(
                [
                    self.ikb(
                        text=f"🎶  {timer}",
                        callback_data=f"controls status {chat_id}",
                    )
                ]
            )

        if not remove:

            # --------------------------------------------------
            # MAIN PLAYER CONTROL ROW
            # --------------------------------------------------

            keyboard.append(
                [
                    self.ikb(
                        text="⏪ 10",
                        callback_data=f"controls seek_back_10 {chat_id}",
                    ),
                    self.ikb(
                        text="⏸",
                        callback_data=f"controls pause {chat_id}",
                    ),
                    self.ikb(
                        text="⏩ 10",
                        callback_data=f"controls skip {chat_id}",
                    ),
                ]
            )

            # --------------------------------------------------
            # CLICK ME / SUPPORT
            # --------------------------------------------------

            keyboard.append(
                [
                    self.ikb(
                        text="✨ CLICK ME ↗",
                        url=config.SUPPORT_CHANNEL,
                    ),
                    self.ikb(
                        text="💬 SUPPORT ↗",
                        url=config.SUPPORT_CHAT,
                    ),
                ]
            )

            # --------------------------------------------------
            # CLOSE PLAYER
            # --------------------------------------------------

            keyboard.append(
                [
                    self.ikb(
                        text="✕ CLOSE",
                        callback_data=f"controls close {chat_id}",
                    )
                ]
            )

        return self.ikm(keyboard)

    # ======================================================
    # HELP MENU
    # ======================================================

    def help_markup(
        self,
        _lang: dict,
        back: bool = False,
    ) -> types.InlineKeyboardMarkup:

        if back:
            rows = [
                [
                    self.ikb(
                        text="BACK",
                        callback_data="help_main",
                        style=ButtonStyle.DANGER,
                    )
                ]
            ]
        else:
            rows = [
                [
                    self.ikb(text="ADMIN", callback_data="help_admin", style=ButtonStyle.PRIMARY),
                    self.ikb(text="AUTH", callback_data="help_auth", style=ButtonStyle.PRIMARY),
                    self.ikb(text="BLACKLIST", callback_data="help_blacklist", style=ButtonStyle.PRIMARY),
                ],
                [
                    self.ikb(text="BROADCAST", callback_data="help_broadcast", style=ButtonStyle.PRIMARY),
                    self.ikb(text="PING", callback_data="help_ping", style=ButtonStyle.PRIMARY),
                    self.ikb(text="PLAY", callback_data="help_play", style=ButtonStyle.PRIMARY),
                ],
                [
                    self.ikb(text="SUDO", callback_data="help_sudo", style=ButtonStyle.SUCCESS),
                    self.ikb(text="VIDEOCHATS", callback_data="help_videochats", style=ButtonStyle.SUCCESS),
                    self.ikb(text="START", callback_data="help_start", style=ButtonStyle.SUCCESS),
                ],
                [
                    self.ikb(text="AUTO PLAY", callback_data="help_autoplay", style=ButtonStyle.PRIMARY),
                ],
                [
                    self.ikb(text="BACK", callback_data="start", style=ButtonStyle.DANGER),
                ],
            ]

        return self.ikm(rows)

    # ======================================================
    # PING MENU
    # ======================================================

    def ping_markup(self, text: str) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text="📢 Channel",
                        url=config.SUPPORT_CHANNEL,
                        style=ButtonStyle.SUCCESS,
                    ),
                    self.ikb(
                        text="🆘 Support",
                        url=config.SUPPORT_CHAT,
                        style=ButtonStyle.SUCCESS,
                    ),
                ],
                [
                    self.ikb(
                        text="➕ Add Me to Your Group",
                        url=f"https://t.me/{app.username}?startgroup=true",
                        style=ButtonStyle.PRIMARY,
                    ),
                ],
            ]
        )

    # ======================================================
    # QUEUED MUSIC PLAYER
    # ======================================================

    def play_queued(
        self,
        chat_id: int,
        item_id: str,
        _text: str,
    ) -> types.InlineKeyboardMarkup:

        return self.ikm(
            [
                [
                    self.ikb(
                        text="⏪ 10",
                        callback_data=f"controls seek_back_10 {chat_id}",
                    ),
                    self.ikb(
                        text="⏸",
                        callback_data=f"controls pause {chat_id}",
                    ),
                    self.ikb(
                        text="⏩ 10",
                        callback_data=f"controls skip {chat_id}",
                    ),
                ],
                [
                    self.ikb(
                        text="✨ CLICK ME ↗",
                        url=config.SUPPORT_CHANNEL,
                    ),
                    self.ikb(
                        text="💬 SUPPORT ↗",
                        url=config.SUPPORT_CHAT,
                    ),
                ],
                [
                    self.ikb(
                        text="✕ CLOSE",
                        callback_data=f"controls close {chat_id}",
                    ),
                ],
            ]
        )

    # ======================================================
    # QUEUE BUTTON
    # ======================================================

    def queue_markup(
        self,
        chat_id: int,
        _text: str,
        playing: bool,
    ) -> types.InlineKeyboardMarkup:

        _action = "pause" if playing else "resume"

        return self.ikm(
            [
                [
                    self.ikb(
                        text=_text,
                        callback_data=f"controls {_action} {chat_id} q",
                        style=ButtonStyle.SUCCESS,
                    )
                ]
            ]
        )

    # ======================================================
    # SETTINGS
    # ======================================================

    def settings_markup(
        self,
        lang: dict,
        admin_only: bool,
        language: str,
        chat_id: int,
    ) -> types.InlineKeyboardMarkup:

        return self.ikm(
            [
                [
                    self.ikb(
                        text=lang["play_mode"] + " ➜",
                        callback_data=f"controls status {chat_id}",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text=admin_only,
                        callback_data="playmode",
                        style=ButtonStyle.SUCCESS,
                    ),
                ]
            ]
        )

    # ======================================================
    # START MENU
    # ======================================================

    def start_key(
        self,
        lang: dict,
        private: bool = False,
    ) -> types.InlineKeyboardMarkup:

        rows = [
            [
                self.ikb(
                    text="🚀 CREATE YOUR GROUP",
                    url=f"https://t.me/{app.username}?startgroup=true",
                    style=ButtonStyle.DANGER,
                )
            ],
            [
                self.ikb(
                    text="👤 OWNER",
                    url="https://t.me/Aashish_0fficial",
                    style=ButtonStyle.SUCCESS,
                ),
                self.ikb(
                    text="🌐 LANGUAGE",
                    callback_data="language",
                    style=ButtonStyle.SUCCESS,
                ),
            ],
            [
                self.ikb(
                    text="🤝 SUPPORT",
                    url="https://t.me/deep_emotions_01",
                    style=ButtonStyle.PRIMARY,
                ),
                self.ikb(
                    text="📢 UPDATES",
                    url="https://t.me/+cGoEVo7d8YtjOTI9",
                    style=ButtonStyle.PRIMARY,
                ),
            ],
            [
                self.ikb(
                    text="⚙️ HELP AND COMMANDS",
                    callback_data="help",
                    style=ButtonStyle.DANGER,
                )
            ],
        ]

        return self.ikm(rows)

    # ======================================================
    # YOUTUBE LINK MENU
    # ======================================================

    def yt_key(self, link: str) -> types.InlineKeyboardMarkup:

        return self.ikm(
            [
                [
                    self.ikb(
                        text="ᴄᴏᴘʏ ʟɪɴᴋ",
                        copy_text=link,
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="ᴏᴘᴇɴ ɪɴ ʏᴏᴜᴛᴜʙᴇ",
                        url=link,
                        style=ButtonStyle.PRIMARY,
                    ),
                ]
            ]
        )