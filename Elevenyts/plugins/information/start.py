# ==========================================================
# Copyright (c) 2026 Apple Music <<3
# All Rights Reserved.
#
# Project      : Apple Music Telegram Music Bot
# Powered By   : Apple Music <<3
# Type         : Telegram Music Bot
#
# Bot          : @AppleMusix_bot
# 
# GitHub       : https://github.com/AashishTechs/MissShikhamusicbot
#
# Unauthorized copying, modification, or redistribution
# of this source code without permission is prohibited.
# ==========================================================

from pyrogram import enums, errors, filters, types

from Elevenyts import app, config, db, lang
from Elevenyts.helpers import buttons, utils


@app.on_message(filters.command(["help"]) & filters.private & ~app.bl_users)
@lang.language()
async def _help(_, m: types.Message):
    """Handle /help command in private chats - owner only."""
    if not m.from_user or not (
        m.from_user.id == config.OWNER_ID
        or (
            m.from_user.username
            and m.from_user.username.lower() == config.OWNER_USERNAME
        )
    ):
        return
    # Auto-delete command message
    try:
        await m.delete()
    except Exception:
        pass
    
    try:
        await m.reply_photo(
            photo=config.START_IMG,  # Use same image as start command
            caption=m.lang["help_menu"],
            reply_markup=buttons.help_markup(m.lang),
        )
    except Exception:
        # Fallback to text if photo fails
        await m.reply_text(
            text=m.lang["help_menu"],
            reply_markup=buttons.help_markup(m.lang),
        )


@app.on_message(filters.command(["start"]))
@lang.language()
async def start(_, message: types.Message):
    """
    Handle /start command - welcome message for users.

    - In private chat: Shows welcome message with inline buttons
    - In group chat: Shows short welcome message
    - Adds new users to database
    - Sends log to logger group for new users
    """
    # Auto-delete /start command so the welcome panel appears cleanly
    try:
        await message.delete()
    except Exception:
        pass
    
    # Skip if message from channel or anonymous admin
    if not message.from_user:
        return

    # Check if user is blacklisted
    if message.from_user.id in app.bl_users and message.from_user.id not in db.notified:
        return await message.reply_text(message.lang["bl_user_notify"])

    # If /start help, show help menu
    if len(message.command) > 1 and message.command[1] == "help":
        return await _help(_, message)

    # Determine if chat is private or group
    private = message.chat.type == enums.ChatType.PRIVATE

    # Choose appropriate welcome message
    _text = (
        message.lang["start_pm"].format(message.from_user.first_name, app.name, message.from_user.id)
        if private
        else message.lang["start_gp"].format(app.name)
    )

    key = buttons.start_key(
        message.lang,
        private,
        show_help=(
            message.from_user.id == config.OWNER_ID
            or (
                message.from_user.username
                and message.from_user.username.lower() == config.OWNER_USERNAME
            )
        ),
    )
    try:
        await message.reply_photo(
            photo=config.START_IMG,
            caption=_text,
            reply_markup=key,
        )
    except errors.ChatSendPhotosForbidden:
        # If photos are not allowed, send text only
        await message.reply_text(
            text=_text,
            reply_markup=key,
        )

    # For private chats, add user to database if new
    if private:
        if await db.is_user(message.from_user.id):
            return  # User already exists, no need to add
        # Log new user to logger group
        await utils.send_log(message)
        # Add user to database
        return await db.add_user(message.from_user.id)


@app.on_message(filters.command(["playmode", "settings"]) & filters.group & ~app.bl_users)
@lang.language()
async def settings(_, message: types.Message):
    """
    Handle /playmode or /settings command - show group settings.

    Displays:
    - Play mode (everyone or admin only)
    - Current language
    - Options to change settings
    """
    # Auto-delete command message
    try:
        await message.delete()
    except Exception:
        pass
    
    admin_only = await db.get_play_mode(message.chat.id)  # Get play mode setting
    _language = "en"
    await utils.safe_text(
        message,
        message.lang["start_settings"].format(message.chat.title),
        reply_markup=buttons.settings_markup(
            message.lang, admin_only, _language, message.chat.id
        ),
        )


@app.on_message(filters.new_chat_members, group=7)
@lang.language()
async def _new_member(_, message: types.Message):
    """
    Handle new member events - detect when bot is added to groups.

    - Leaves non-supergroup chats
    - Adds new groups to database
    """
    # Only work in supergroups (not basic groups)
    if message.chat.type != enums.ChatType.SUPERGROUP:
        return await message.chat.leave()

    # Check each new member
    for member in message.new_chat_members:
        if member.id == app.id:  # Bot itself was added
            if await db.is_chat(message.chat.id):
                return  # Chat already in database
            # Add chat to database (log is sent from new_chat.py with photo)
            await db.add_chat(message.chat.id)
