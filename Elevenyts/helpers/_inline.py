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
            rows = [[
                self.ikb(
                    text="ʙᴀᴄᴋ",
                    callback_data="help_main",
                    style=ButtonStyle.DANGER,
                )
            ]]
        else:
            rows = [
                # Row 1: red
                [
                    self.ikb(text="ᴀᴅᴍɪɴ", callback_data="help_admin", style=ButtonStyle.DANGER),
                    self.ikb(text="ᴀᴜᴛʜ", callback_data="help_auth", style=ButtonStyle.DANGER),
                    self.ikb(text="ʙʟᴀᴄᴋʟɪꜱᴛ", callback_data="help_blacklist", style=ButtonStyle.DANGER),
                ],
                # Row 2: blue / sky
                [
                    self.ikb(text="ʙʀᴏᴀᴅᴄᴀꜱᴛ", callback_data="help_broadcast", style=ButtonStyle.PRIMARY),
                    self.ikb(text="ᴘɪɴɢ", callback_data="help_ping", style=ButtonStyle.PRIMARY),
                    self.ikb(text="ᴘʟᴀʏ", callback_data="help_play", style=ButtonStyle.PRIMARY),
                ],
                # Row 3: green
                [
                    self.ikb(text="ᴠɪᴅᴇᴏᴄʜᴀᴛꜱ", callback_data="help_videochats", style=ButtonStyle.SUCCESS),
                    self.ikb(text="ꜱᴛᴀʀᴛ", callback_data="help_start", style=ButtonStyle.SUCCESS),
                    self.ikb(text="ᴀᴜᴛᴏ ᴘʟᴀʏ", callback_data="help_autoplay", style=ButtonStyle.SUCCESS),
                ],
                # Back: red
                [
                    self.ikb(text="ʙᴀᴄᴋ", callback_data="start", style=ButtonStyle.DANGER)
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
                    text="🌐 ʟᴀɴɢᴜᴀɢᴇ",
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