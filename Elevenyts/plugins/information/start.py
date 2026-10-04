# ==========================================================
# Copyright (c) 2026 Apple Music <<3
# All Rights Reserved.
#
# Project      : Apple Music Telegram Music Bot
# Powered By   : Apple Music <<3
# Type         : API Based Telegram Music Bot
#
# Bot          : @AppleMusix_bot
#
# Unauthorized copying, modification, or redistribution
# of this source code without permission is prohibited.
# ==========================================================

from pathlib import Path

from pyrogram import enums, errors, filters, types

from Elevenyts import app, config, db, lang
from Elevenyts.helpers import buttons, utils


WELCOME_IMAGE = str(Path(__file__).resolve().parents[3] / "Welcome.jpg")
HELP_TEXT = (
    "<blockquote><b>🎧 APPLE MUSIX • HELP & COMMANDS</b></blockquote>\n\n"
    "Select a category below to explore available commands."
)


def welcome_text(message):
    name = message.from_user.mention
    return f"""Hey <b>{name}</b>,-: 🎧

🍎 <b>Apple Music <<3</b> 🎵

Your music. Your vibe. Your moment. ♡

🎶 <b>High-Quality Music Streaming</b>
⚡ <b>Fast & Smooth Playback</b>
🔊 <b>24×7 Music in Voice Chat</b>

━━━━━━━━━━━━━━━━━━

🐼 <b>Ready to Feel the Music?</b>

🔴 <b>Tap Help & Commands</b>
🚀 <b>Explore my features & start listening!</b>

👑 <b>Owner:</b> <a href="https://t.me/Aashish_0fficial">@Aashish_0fficial</a>"""


@app.on_message(filters.command(["help"]) & filters.private & ~app.bl_users)
@lang.language()
async def _help(_, m: types.Message):
    """Handle /help command in private chats - shows help menu with image."""
    try:
        await m.delete()
    except Exception:
        pass

    try:
        await m.reply_photo(
            photo=WELCOME_IMAGE,
            caption=HELP_TEXT,
            reply_markup=buttons.help_markup(m.lang),
            quote=True,
        )
    except Exception:
        await m.reply_text(
            text=HELP_TEXT,
            reply_markup=buttons.help_markup(m.lang),
            quote=True,
        )


@app.on_message(filters.command(["start", "startv"]))
@lang.language()
async def start(_, message: types.Message):
    """Handle /start command."""

    if message.chat.type != enums.ChatType.PRIVATE:
        try:
            await message.delete()
        except Exception:
            pass

    if not message.from_user:
        return

    if message.from_user.id in app.bl_users and message.from_user.id not in db.notified:
        return await message.reply_text(message.lang["bl_user_notify"])

    if len(message.command) > 1 and message.command[1] == "help":
        return await _help(_, message)

    private = message.chat.type == enums.ChatType.PRIVATE

    _text = welcome_text(message)

    key = buttons.start_key(message.lang, private)

    try:
        await message.reply_photo(
            photo=WELCOME_IMAGE,
            caption=_text,
            reply_markup=key,
            quote=not private,
        )
    except (errors.ChatSendPhotosForbidden, OSError, ValueError):
        await message.reply_text(
            text=_text,
            reply_markup=key,
            quote=not private,
        )

    if private:
        if await db.is_user(message.from_user.id):
            return
        await utils.send_log(message)
        return await db.add_user(message.from_user.id)


@app.on_message(filters.command(["playmode", "settings"]) & filters.group & ~app.bl_users)
@lang.language()
async def settings(_, message: types.Message):
    """Handle /playmode or /settings command."""

    try:
        await message.delete()
    except Exception:
        pass

    admin_only = await db.get_play_mode(message.chat.id)
    _language = "en"

    await utils.safe_text(
        message,
        message.lang["start_settings"].format(message.chat.title),
        reply_markup=buttons.settings_markup(
            message.lang, admin_only, _language, message.chat.id
        ),
        quote=True,
    )


@app.on_message(filters.new_chat_members, group=7)
@lang.language()
async def _new_member(_, message: types.Message):
    """Handle new member events."""

    if message.chat.type != enums.ChatType.SUPERGROUP:
        return await message.chat.leave()

    for member in message.new_chat_members:
        if member.id == app.id:
            if await db.is_chat(message.chat.id):
                return
            await db.add_chat(message.chat.id)
