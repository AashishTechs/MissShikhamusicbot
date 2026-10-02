# ==========================================================
# Copyright (c) 2026 Apple Music <<3
# All Rights Reserved.
#
# Project      : Apple Music Telegram Music Bot
# Powered By   : Apple Music <<3
# Type         : Telegram Music Bot
#
# Bot          : @AppleMusix_bot
# Channel      : https://t.me/deep_emotions_01
# GitHub       : https://github.com/AashishTechs/MissShikhamusicbot
#
# Unauthorized copying, modification,
# or redistribution of this source code without permission is prohibited.
# ==========================================================

from pyrogram import types
from pyrogram.enums import ButtonStyle

from Elevenyts import app, config, lang


class Inline:
    def __init__(self):
        self.ikm = types.InlineKeyboardMarkup
        self.ikb = types.InlineKeyboardButton

    def cancel_dl(self, text) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [[
                self.ikb(
                    text=text,
                    callback_data="cancel_dl",
                    style=ButtonStyle.PRIMARY,
                )
            ]]
        )

    def controls(
        self,
        chat_id: int,
        status: str = None,
        timer: str = None,
        remove: bool = False,
    ) -> types.InlineKeyboardMarkup:

        keyboard = []

        if status:
            keyboard.append([self.ikb(
                text=f"🎵  {status}",
                callback_data=f"controls status {chat_id}",
            )])

        if not remove:
            keyboard.append([
                self.ikb(
                    text="▷",
                    callback_data=f"controls resume {chat_id}",
                    style=ButtonStyle.SUCCESS,
                ),
                self.ikb(
                    text="Ⅱ",
                    callback_data=f"controls pause {chat_id}",
                    style=ButtonStyle.PRIMARY,
                ),
                self.ikb(
                    text="↻",
                    callback_data=f"controls loop {chat_id}",
                    style=ButtonStyle.PRIMARY,
                ),
                self.ikb(
                    text="⏭",
                    callback_data=f"controls skip {chat_id}",
                    style=ButtonStyle.PRIMARY,
                ),
                self.ikb(
                    text="□",
                    callback_data=f"controls close {chat_id}",
                    style=ButtonStyle.DANGER,
                ),
            ])

        if timer:
            keyboard.append([self.ikb(
                text=timer,
                callback_data=f"controls status {chat_id}",
            )])

        return self.ikm(keyboard)

    def help_markup(
        self,
        _lang: dict,
        back: bool = False,
    ) -> types.InlineKeyboardMarkup:

        if back:
            rows = [[self.ikb(
                text="ʙᴀᴄᴋ",
                callback_data="start",
                style=ButtonStyle.SUCCESS,
            )]]
        else:
            rows = [
                [
                    self.ikb(
                        text="/play",
                        callback_data="help_play",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="/queue",
                        callback_data="help_queue",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="/pause",
                        callback_data="help_pause",
                        style=ButtonStyle.PRIMARY,
                    ),
                ],
                [
                    self.ikb(
                        text="/resume",
                        callback_data="help_resume",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="/skip",
                        callback_data="help_skip",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="/stop",
                        callback_data="help_stop",
                        style=ButtonStyle.PRIMARY,
                    ),
                ],
                [
                    self.ikb(
                        text="/replay",
                        callback_data="help_replay",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="/shuffle",
                        callback_data="help_shuffle",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="/loop",
                        callback_data="help_loop",
                        style=ButtonStyle.PRIMARY,
                    ),
                ],
                [
                    self.ikb(
                        text="/seek",
                        callback_data="help_seek",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="/ping",
                        callback_data="help_ping",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="/stats",
                        callback_data="help_stats",
                        style=ButtonStyle.PRIMARY,
                    ),
                ],
                [
                    self.ikb(
                        text="/settings",
                        callback_data="help_settings",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="ᴀᴅᴍɪɴꜱ",
                        callback_data="help_admins",
                        style=ButtonStyle.PRIMARY,
                    ),
                ],
                [
                    self.ikb(
                        text="ʙʀᴏᴀᴅᴄᴀꜱᴛ",
                        callback_data="help_broadcast",
                        style=ButtonStyle.PRIMARY,
                    ),
                    self.ikb(
                        text="ɢ-ʙᴀɴ",
                        callback_data="help_gban",
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
                    )
                ],
            ]

        return self.ikm(rows)

    def ping_markup(self, text: str) -> types.InlineKeyboardMarkup:
        return self.ikm([
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
        ])

    def play_queued(
        self,
        chat_id: int,
        item_id: str,
        _text: str,
    ) -> types.InlineKeyboardMarkup:
        return self.ikm([[
            self.ikb(
                text="▷",
                callback_data=f"controls resume {chat_id}",
                style=ButtonStyle.SUCCESS,
            ),
            self.ikb(
                text="Ⅱ",
                callback_data=f"controls pause {chat_id}",
                style=ButtonStyle.PRIMARY,
            ),
            self.ikb(
                text="⏭",
                callback_data=f"controls skip {chat_id}",
                style=ButtonStyle.PRIMARY,
            ),
            self.ikb(
                text="□",
                callback_data=f"controls close {chat_id}",
                style=ButtonStyle.DANGER,
            ),
        ]])

    def queue_markup(
        self,
        chat_id: int,
        _text: str,
        playing: bool,
    ) -> types.InlineKeyboardMarkup:
        _action = "pause" if playing else "resume"
        return self.ikm([[
            self.ikb(
                text=_text,
                callback_data=f"controls {_action} {chat_id} q",
                style=ButtonStyle.SUCCESS,
            )
        ]])

    def settings_markup(
        self,
        lang: dict,
        admin_only: bool,
        language: str,
        chat_id: int,
    ) -> types.InlineKeyboardMarkup:
        return self.ikm([[
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
        ]])

    def start_key(
        self,
        lang: dict,
        private: bool = False,
        show_help: bool = False,
    ) -> types.InlineKeyboardMarkup:

        rows = [
            [
                self.ikb(
                    text="🚀 ᴄʀᴇᴀᴛᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ ↗",
                    url=f"https://t.me/{app.username}?startgroup=true",
                    style=ButtonStyle.DANGER,
                )
            ],
            [
                self.ikb(
                    text="👤 ᴏᴡɴᴇʀ",
                    url="https://t.me/Aashish_0fficial",
                    style=ButtonStyle.SUCCESS,
                ),
                self.ikb(
                    text="🌐 ʟᴀɴɢᴜᴀɢᴇ ↗",
                    callback_data="language",
                    style=ButtonStyle.SUCCESS,
                ),
            ],
            [
                self.ikb(
                    text="🤝 ꜱᴜᴘᴘᴏʀᴛ",
                    url=config.SUPPORT_CHAT,
                    style=ButtonStyle.PRIMARY,
                ),
                self.ikb(
                    text="📢 ᴜᴘᴅᴀᴛᴇꜱ",
                    url=config.SUPPORT_CHANNEL,
                    style=ButtonStyle.PRIMARY,
                ),
            ],
        ]

        if show_help:
            rows.append(
                [
                    self.ikb(
                        text="⚙️ ʜᴇʟᴘ ᴀɴᴅ ᴄᴏᴍᴍᴀɴᴅꜱ",
                        callback_data="help_main",
                        style=ButtonStyle.DANGER,
                    )
                ]
            )

        return self.ikm(rows)

    def yt_key(self, link: str) -> types.InlineKeyboardMarkup:
        return self.ikm([[
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
        ]])