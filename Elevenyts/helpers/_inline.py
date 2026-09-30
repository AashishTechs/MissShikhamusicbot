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

            # --------------------------------------------------
            # PRIMARY CONTROLS
            # --------------------------------------------------

            keyboard.append(
                [
                    self.ikb(
                        text="⏪ 10s",
                        callback_data=f"controls seek_back_10 {chat_id}",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="⏸",
                        callback_data=f"controls pause {chat_id}",
                        style=ButtonStyle.SUCCESS,
                    ),
                    self.ikb(
                        text="10s ⏩",
                        callback_data=f"controls seek_forward_10 {chat_id}",
                        style=ButtonStyle.PRIMARY,
                    ),
                ]
            )

            # --------------------------------------------------
            # SECONDARY PLAYER CONTROLS
            # --------------------------------------------------

            keyboard.append(
                [
                    self.ikb(
                        text="🔂 Loop",
                        callback_data=f"controls loop {chat_id}",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="🔀 Shuffle",
                        callback_data=f"controls shuffle {chat_id}",
                        style=ButtonStyle.PRIMARY,
                    ),
                ]
            )

            # --------------------------------------------------
            # SUPPORT
            # --------------------------------------------------

            keyboard.append(
                [
                    self.ikb(
                        text="✨ Channel ↗",
                        url=config.SUPPORT_CHANNEL,
                    ),
                    self.ikb(
                        text="💬 Support ↗",
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
                        text="✕ Close Player",
                        callback_data=f"controls close {chat_id}",
                        style=ButtonStyle.DANGER,
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
                        text="ʙᴀᴄᴋ",
                        callback_data="help_main",
                        style=ButtonStyle.SUCCESS,
                    )
                ]
            ]

        else:
            rows = [
                [
                    self.ikb(
                        text="ᴀᴅᴍɪɴꜱ",
                        callback_data="help_admins",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="ᴀᴜᴛʜ",
                        callback_data="help_auth",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="ʙʀᴏᴀᴅᴄᴀꜱᴛ",
                        callback_data="help_broadcast",
                        style=ButtonStyle.PRIMARY,
                    ),
                ],
                [
                    self.ikb(
                        text="ʙʟ-ᴄʜᴀᴛ",
                        callback_data="help_blchat",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="ʙʟ-ᴜꜱᴇʀ",
                        callback_data="help_bluser",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="ɢ-ʙᴀɴ",
                        callback_data="help_gban",
                        style=ButtonStyle.PRIMARY,
                    ),
                ],
                [
                    self.ikb(
                        text="ʟᴏᴏᴘ",
                        callback_data="help_loop",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="ᴘʟᴀʏ",
                        callback_data="help_play",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="ǫᴜᴇᴜᴇ",
                        callback_data="help_queue",
                        style=ButtonStyle.PRIMARY,
                    ),
                ],
                [
                    self.ikb(
                        text="ꜱᴇᴇᴋ",
                        callback_data="help_seek",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="ꜱʜᴜꜰꜰʟᴇ",
                        callback_data="help_shuffle",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="ᴘɪɴɢ",
                        callback_data="help_ping",
                        style=ButtonStyle.PRIMARY,
                    ),
                ],
                [
                    self.ikb(
                        text="ꜱᴛᴀᴛꜱ",
                        callback_data="help_stats",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="ꜱᴜᴅᴏ",
                        callback_data="help_sudo",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ",
                        callback_data="help_maintenance",
                        style=ButtonStyle.PRIMARY,
                    ),
                ],
                [
                    self.ikb(
                        text="ʙᴀᴄᴋ",
                        callback_data="start",
                        style=ButtonStyle.SUCCESS,
                    ),
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
                    text=lang["add_me"],
                    url=f"https://t.me/{app.username}?startgroup=true",
                    style=ButtonStyle.PRIMARY,
                )
            ],
            [
                self.ikb(
                    text=lang["help"],
                    callback_data="help",
                    style=ButtonStyle.SUCCESS,
                ),
                self.ikb(
                    text="ꜱᴏᴜʀᴄᴇ",
                    url="https://github.com/kalyan631/BlackMusic",
                    style=ButtonStyle.SUCCESS,
                ),
            ],
            [
                self.ikb(
                    text=lang["support"],
                    url=config.SUPPORT_CHAT,
                    style=ButtonStyle.PRIMARY,
                ),
                self.ikb(
                    text=lang["channel"],
                    url=config.SUPPORT_CHANNEL,
                    style=ButtonStyle.PRIMARY,
                ),
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