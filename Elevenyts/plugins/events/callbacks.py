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

import re
import asyncio
from functools import wraps

from pyrogram import filters, types
from pyrogram.errors import FloodWait, QueryIdInvalid

from Elevenyts import tune, app, config, db, lang, logger, queue, tg, yt
from Elevenyts.helpers import admin_check, buttons, can_manage_vc


def safe_callback(func):
    """Decorator to handle exceptions in callback handlers."""

    @wraps(func)
    async def wrapper(client, query: types.CallbackQuery):
        try:
            return await func(client, query)

        except QueryIdInvalid:
            return

        except Exception as e:
            logger.error(
                f"Error in callback {func.__name__}: {e}",
                exc_info=True
            )

            try:
                await query.answer(
                    "❌ An error occurred. Please try again.",
                    show_alert=True
                )
            except Exception:
                pass

    return wrapper


async def get_direct_stream(media):
    """
    Get a fresh direct streaming URL.

    IMPORTANT:
    Direct YouTube URLs expire, therefore URL ko
    playback ke time fresh generate kiya jata hai.
    """

    try:
        media.file_path = None

        stream_url = await yt.get_stream_url(
            media.id,
            is_live=getattr(media, "is_live", False),
            video=getattr(media, "video", False),
        )

        if stream_url:
            media.file_path = stream_url
            return stream_url

        return None

    except Exception as e:
        logger.error(
            f"Failed to get direct stream for "
            f"{getattr(media, 'id', 'unknown')}: {e}",
            exc_info=True
        )
        return None


@app.on_callback_query(filters.regex("^start$") & ~app.bl_users)
@lang.language()
@safe_callback
async def _start_callback(_, query: types.CallbackQuery):
    """Handle start button callback - return to start message."""

    await query.answer()

    name = query.from_user.mention
    _text = f"""Hey <b>{name}</b>,-: 🎧

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

    key = buttons.start_key(
        query.lang,
        True
    )

    try:
        await query.edit_message_caption(
            caption=_text,
            reply_markup=key,
        )

    except Exception:
        try:
            await query.edit_message_text(
                text=_text,
                reply_markup=key,
            )
        except Exception:
            pass


@app.on_callback_query(filters.regex("^language$") & ~app.bl_users)
@lang.language()
@safe_callback
async def _language_callback(_, query: types.CallbackQuery):
    await query.answer(
        "🌐 Language: English",
        show_alert=True
    )


@app.on_callback_query(filters.regex("cancel_dl") & ~app.bl_users)
@lang.language()
@safe_callback
async def cancel_dl(_, query: types.CallbackQuery):

    await query.answer()

    await tg.cancel(query)


@app.on_callback_query(filters.regex("controls") & ~app.bl_users)
@lang.language()
@safe_callback
async def _controls(_, query: types.CallbackQuery):

    args = query.data.split()

    action = args[1]
    chat_id = int(args[2])

    qaction = len(args) == 4
    user = query.from_user.mention

    # ------------------------------------------------------
    # CLOSE
    # ------------------------------------------------------

    if action == "close":

        await query.answer()

        try:
            await query.message.delete()
        except Exception:
            pass

        return

    # ------------------------------------------------------
    # PERMISSION CHECK
    # ------------------------------------------------------

    user_id = query.from_user.id

    has_permission = False

    if user_id in app.sudoers:
        has_permission = True

    elif await db.is_auth(chat_id, user_id):
        has_permission = True

    else:
        admins = await db.get_admins(chat_id)

        if user_id in admins:
            has_permission = True

    if not has_permission:
        return await query.answer(
            "⚠️ You don't have permission to use this.",
            show_alert=True
        )

    # ------------------------------------------------------
    # CALL CHECK
    # ------------------------------------------------------

    if not await db.get_call(chat_id):
        return await query.answer(
            query.lang["not_playing"],
            show_alert=True
        )

    # ------------------------------------------------------
    # STATUS
    # ------------------------------------------------------

    if action == "status":
        return await query.answer()

    # ------------------------------------------------------
    # SEEK
    # ------------------------------------------------------

    if action.startswith("seek_"):

        return await handle_seek(
            query,
            chat_id,
            action,
            user
        )

    # ------------------------------------------------------
    # LOOP
    # ------------------------------------------------------

    if action == "loop":

        return await handle_loop(
            query,
            chat_id,
            user
        )

    # ------------------------------------------------------
    # SHUFFLE
    # ------------------------------------------------------

    if action == "shuffle":

        return await handle_shuffle(
            query,
            chat_id,
            user
        )

    await query.answer(
        query.lang["processing"],
        show_alert=True
    )

    # ------------------------------------------------------
    # PAUSE
    # ------------------------------------------------------

    if action == "pause":

        if not await db.playing(chat_id):

            return await query.answer(
                query.lang["play_already_paused"],
                show_alert=True
            )

        if not await tune.pause(chat_id):

            return await query.answer(
                query.lang["not_playing"],
                show_alert=True
            )

        if qaction:

            return await query.edit_message_reply_markup(
                reply_markup=buttons.queue_markup(
                    chat_id,
                    query.lang["paused"],
                    False
                )
            )

        status = query.lang["paused"]

        reply = query.lang["play_paused"].format(user)

    # ------------------------------------------------------
    # RESUME
    # ------------------------------------------------------

    elif action == "resume":

        status = query.lang["playing"]

        if await db.playing(chat_id):

            return await query.answer(
                query.lang["play_not_paused"],
                show_alert=True
            )

        if not await tune.resume(chat_id):

            return await query.answer(
                query.lang["not_playing"],
                show_alert=True
            )

        if qaction:

            return await query.edit_message_reply_markup(
                reply_markup=buttons.queue_markup(
                    chat_id,
                    query.lang["playing"],
                    True
                )
            )

        reply = query.lang["play_resumed"].format(user)

    # ------------------------------------------------------
    # SKIP
    # ------------------------------------------------------

    elif action == "skip":

        await tune.play_next(chat_id)

        status = query.lang["skipped"]

        reply = query.lang["play_skipped"].format(user)

    # ------------------------------------------------------
    # FORCE PLAY
    # ------------------------------------------------------

    elif action == "force":

        pos, media = queue.check_item(
            chat_id,
            args[3]
        )

        if not media or pos == -1:

            return await query.edit_message_text(
                query.lang["play_expired"]
            )

        current = queue.get_current(chat_id)

        m_id = (
            current.message_id
            if current
            else None
        )

        queue.force_add(
            chat_id,
            media,
            remove=pos
        )

        try:

            await app.delete_messages(
                chat_id=chat_id,
                message_ids=[
                    m_id,
                    media.message_id
                ],
                revoke=True
            )

            media.message_id = None

        except Exception:
            pass

        msg = await app.send_message(
            chat_id=chat_id,
            text=query.lang["play_next"]
        )

        # --------------------------------------------------
        # DIRECT STREAM
        # --------------------------------------------------
        # OLD:
        # media.file_path = await yt.download(...)
        #
        # NEW:
        # Fresh direct stream URL.
        # --------------------------------------------------

        stream_url = await get_direct_stream(media)

        if not stream_url:

            try:
                await msg.edit_text(
                    "❌ Unable to get direct stream for this track."
                )
            except Exception:
                pass

            return

        media.message_id = msg.id

        return await tune.play_media(
            chat_id,
            msg,
            media
        )

    # ------------------------------------------------------
    # REPLAY
    # ------------------------------------------------------

    elif action == "replay":

        media = queue.get_current(chat_id)

        media.user = user

        await tune.replay(chat_id)

        status = query.lang["replayed"]

        reply = query.lang["play_replayed"].format(user)

    # ------------------------------------------------------
    # STOP
    # ------------------------------------------------------

    elif action == "stop":

        await tune.stop(chat_id)

        status = query.lang["stopped"]

        reply = query.lang["play_stopped"].format(user)

    # ------------------------------------------------------
    # MESSAGE UPDATE
    # ------------------------------------------------------

    try:

        if action in ["skip", "replay", "stop"]:

            sent_msg = None

            try:

                sent_msg = await query.message.reply_text(
                    reply,
                    quote=False
                )

            except FloodWait as e:

                await asyncio.sleep(e.value)

                try:

                    sent_msg = await query.message.reply_text(
                        reply,
                        quote=False
                    )

                except Exception:
                    pass

            except Exception:
                pass

            try:
                await query.message.delete()
            except Exception:
                pass

            # Auto-delete reply after 5 seconds
            if sent_msg:

                await asyncio.sleep(5)

                try:
                    await sent_msg.delete()
                except Exception:
                    pass

            return

        mtext = re.sub(
            r"\n\n<blockquote>.*?</blockquote>",
            "",
            query.message.caption.html
            or query.message.text.html,
            flags=re.DOTALL,
        )

        keyboard = buttons.controls(
            chat_id,
            status=status if action != "resume" else None
        )

        await query.edit_message_text(
            f"{mtext}\n\n<blockquote>{reply}</blockquote>",
            reply_markup=keyboard
        )

    except FloodWait as e:

        await asyncio.sleep(e.value)

        try:

            await query.edit_message_text(
                f"{mtext}\n\n<blockquote>{reply}</blockquote>",
                reply_markup=keyboard
            )

        except Exception:
            pass

    except Exception:
        pass


async def handle_seek(
    query: types.CallbackQuery,
    chat_id: int,
    action: str,
    user: str
):
    """Handle seek forward/backward actions."""

    media = queue.get_current(chat_id)

    if not media or media.is_live:

        return await query.answer(
            "⚠️ Cannot seek in live streams!",
            show_alert=True
        )

    if not media.duration_sec or media.duration_sec == 0:

        return await query.answer(
            "⚠️ Cannot seek in this track!",
            show_alert=True
        )

    # Determine seek amount
    if action == "seek_back_10":

        seconds = -10
        label = "« 10s"

    elif action == "seek_back_30":

        seconds = -30
        label = "« 30s"

    elif action == "seek_forward_10":

        seconds = 10
        label = "10s »"

    elif action == "seek_forward_30":

        seconds = 30
        label = "30s »"

    else:

        return await query.answer(
            "⚠️ Invalid seek action!",
            show_alert=True
        )

    current_time = getattr(
        media,
        "time",
        0
    )

    new_time = max(
        0,
        min(
            current_time + seconds,
            media.duration_sec - 5
        )
    )

    if new_time == 0 and seconds < 0:

        return await query.answer(
            "⏮️ Already at the beginning!",
            show_alert=True
        )

    if (
        new_time >= media.duration_sec - 5
        and seconds > 0
    ):

        return await query.answer(
            "⏭️ Too close to the end!",
            show_alert=True
        )

    success = await tune.seek_stream(
        chat_id,
        int(new_time)
    )

    if success:

        import time as time_module

        if media.duration_sec >= 3600:

            time_str = time_module.strftime(
                "%H:%M:%S",
                time_module.gmtime(new_time)
            )

        else:

            time_str = time_module.strftime(
                "%M:%S",
                time_module.gmtime(new_time)
            )

        await query.answer(
            f"✅ Seeked to {time_str}",
            show_alert=True
        )

        try:

            sent_msg = await query.message.reply_text(
                f"✅ Seeked to {time_str}\n\n"
                f"<blockquote>By {user}</blockquote>",
                quote=False
            )

            await asyncio.sleep(5)

            try:
                await sent_msg.delete()
            except Exception:
                pass

        except FloodWait:
            pass

        except Exception:
            pass


async def handle_loop(
    query: types.CallbackQuery,
    chat_id: int,
    user: str
):
    """Handle loop mode toggling."""

    current_loop = await db.get_loop(chat_id)

    # 0 -> 1 -> 10 -> 0
    if current_loop == 0:

        new_loop = 1

        text = "🔂 Loop: Single Track"

        message = (
            "🔂 Loop mode set to "
            "<b>Single Track</b>"
        )

    elif current_loop == 1:

        new_loop = 10

        text = "🔁 Loop: Queue"

        message = (
            "🔁 Loop mode set to "
            "<b>Queue</b>"
        )

    else:

        new_loop = 0

        text = "➡️ Loop: Off"

        message = (
            "➡️ Loop mode "
            "<b>Disabled</b>"
        )

    await db.set_loop(
        chat_id,
        new_loop
    )

    await query.answer(
        text,
        show_alert=False
    )

    await query.message.reply_text(
        message,
        quote=False
    )


async def handle_shuffle(
    query: types.CallbackQuery,
    chat_id: int,
    user: str
):
    """Handle queue shuffling."""

    import random

    items = queue.get_queue(chat_id)

    if not items or len(items) <= 1:

        return await query.answer(
            "⚠️ Queue is empty or has only one track!",
            show_alert=True
        )

    current = (
        items[0]
        if items
        else None
    )

    remaining = (
        items[1:]
        if len(items) > 1
        else []
    )

    if not remaining:

        return await query.answer(
            "⚠️ No tracks to shuffle!",
            show_alert=True
        )

    random.shuffle(remaining)

    queue.clear(chat_id)

    if current:
        queue.add(
            chat_id,
            current
        )

    for item in remaining:

        queue.add(
            chat_id,
            item
        )

    await query.answer(
        "🔀 Queue shuffled!",
        show_alert=False
    )

    await query.message.reply_text(
        f"🔀 Queue <b>shuffled</b> "
        f"({len(remaining)} tracks)",
        quote=False
    )


@app.on_callback_query(
    filters.regex(r"^help")
    & ~app.bl_users
)
@lang.language()
@safe_callback
async def _help(_, query: types.CallbackQuery):

    await query.answer()

    help_main = (
        "<blockquote><b>🎧 APPLE MUSIX • HELP & COMMANDS</b></blockquote>\n\n"
        "CHOOSE THE CATEGORY FOR WHICH YOU\n"
        "WANNA GET HELP.\n"
        "ASK YOUR DOUBTS AT <a href=\"https://t.me/Dosto_ki_Mehfil786\">SUPPORT CHAT</a>\n\n"
        "ALL COMMANDS CAN BE USED WITH : /"
    )

    help_texts = {
        "admin": (
            "<b>Admin Commands</b>\n\n"
            "Commands available only to administrators.\n\n"
            "<b>Playback</b>\n\n"
            "<pre>"
            "Command              Description\n"
            "────────────────────────────────────────────\n"
            "/pause               Pause the current\n"
            "                     playing stream.\n"
            "/resume              Resume the\n"
            "                     paused stream.\n"
            "/skip                Skip the current\n"
            "                     stream and play\n"
            "                     the next track in\n"
            "                     queue.\n"
            "/end or /stop        Stop playback and\n"
            "                     clear the queue.\n"
            "/queue               Show the current\n"
            "                     queue.\n"
            "/shuffle             Shuffle the queued\n"
            "                     tracks.\n"
            "/loop [1-10]         Repeat the current\n"
            "                     track for the\n"
            "                     specified number\n"
            "                     of times.\n"
            "/seek [time]         Seek to the given\n"
            "                     timestamp.\n"
            "/seekback [time]     Seek backward\n"
            "                     to the given\n"
            "                     timestamp."
            "</pre>\n\n"
            "<b>Notes</b>\n\n"
            "• Prefix commands with <b>c</b> to use them in linked channels.\n"
            "• Example: <code>/cpause</code>, <code>/cskip</code>, <code>/cqueue</code>"
        ),
        "play": (
            "<b>Play Module</b>\n\n"
            "Commands for playing music and videos.\n\n"
            "<b>Play Commands</b>\n\n"
            "• <b>c</b> stands for <b>Channel Play</b>.\n"
            "• <b>v</b> stands for <b>Video Play</b>.\n"
            "• <b>force</b> stands for <b>Force Play</b>.\n\n"
            "<pre>"
            "Command                    Description\n"
            "──────────────────────────────────────────────\n"
            "/play /vplay /cplay       Start streaming the\n"
            "                          requested track in\n"
            "                          the voice/video chat.\n"
            "/playforce /vplayforce    Stop the current\n"
            "/cplayforce               stream and immediately\n"
            "                          play the requested track.\n"
            "/channelplay [chat        Connect a channel to a\n"
            "username/id]              group for channel play.\n"
            "/channelplay disable      Disable channel play\n"
            "                          for the group."
            "</pre>"
        ),
        "auth": (
            "<b>Auth Module</b>\n\n"
            "Commands for managing authorized users.\n\n"
            "<pre>"
            "Command              Description\n"
            "────────────────────────────────────────\n"
            "/auth                 Authorize a user.\n"
            "/unauth               Remove authorization.\n"
            "/authlist             Show authorized users."
            "</pre>"
        ),
        "blacklist": (
            "<b>Blacklist Module</b>\n\n"
            "Commands for managing blocked users and chats.\n\n"
            "<pre>"
            "Command              Description\n"
            "────────────────────────────────────────\n"
            "/blacklistchat       Blacklist a chat.\n"
            "/whitelistchat       Remove chat blacklist.\n"
            "/blacklistedchat     List blacklisted chats.\n"
            "/block               Block a user.\n"
            "/unblock             Unblock a user.\n"
            "/blockedusers        List blocked users."
            "</pre>"
        ),
        "broadcast": (
            "<b>Broadcast Module</b>\n\n"
            "Commands for broadcasting messages.\n\n"
            "<pre>"
            "Command              Description\n"
            "────────────────────────────────────────\n"
            "/broadcast            Broadcast a message.\n"
            "/stop_broadcast       Stop broadcast.\n"
            "/stop_gcast           Stop broadcast."
            "</pre>"
        ),
        "ping": (
            "<b>Ping Module</b>\n\n"
            "Bot status and system information.\n\n"
            "<pre>"
            "Command              Description\n"
            "────────────────────────────────────────\n"
            "/ping                 Check bot status and\n"
            "                      system health."
            "</pre>"
        ),
        "sudo": (
            "<b>Sudo Module</b>\n\n"
            "Commands for managing sudo users.\n\n"
            "<pre>"
            "Command              Description\n"
            "────────────────────────────────────────\n"
            "/addsudo              Add sudo user.\n"
            "/delsudo              Remove sudo user.\n"
            "/listsudo             List sudo users."
            "</pre>"
        ),
        "videochats": (
            "<b>Video Chats</b>\n\n"
            "Commands for video chat playback.\n\n"
            "<pre>"
            "Command              Description\n"
            "────────────────────────────────────────\n"
            "/vplay                Start video playback.\n"
            "/vplayforce           Force video playback.\n"
            "/cvplay               Channel video playback.\n"
            "/cvplayforce          Force channel video playback."
            "</pre>"
        ),
        "start": (
            "<b>Start Module</b>\n\n"
            "Commands for opening the bot panels.\n\n"
            "<pre>"
            "Command              Description\n"
            "────────────────────────────────────────\n"
            "/start                Open the welcome panel.\n"
            "/help                 Open Help & Commands."
            "</pre>"
        ),
        "autoplay": (
            "<b>Auto Play</b>\n\n"
            "Automatic playback feature.\n\n"
            "<pre>"
            "Command              Description\n"
            "────────────────────────────────────────\n"
            "/autoplay             Enable automatic playback."
            "</pre>"
        ),
    }

    if query.data in ("help", "help_main"):
        text = help_main
        markup = buttons.help_markup(query.lang)

        # Text-only Help panel. Keep the existing button layout/colors.
        try:
            new_message = await query.message.reply_text(
                text=text,
                reply_markup=markup,
            )
            try:
                await query.message.delete()
            except Exception:
                pass
            return new_message
        except Exception:
            return

    category = query.data.removeprefix("help_")
    text = help_texts.get(category, help_main)
    markup = buttons.help_markup(query.lang, True)

    category_titles = {
        "admin": "ADMIN",
        "auth": "AUTH",
        "blacklist": "BLACKLIST",
        "broadcast": "BROADCAST",
        "ping": "PING",
        "play": "PLAY",
        "sudo": "SUDO",
        "videochats": "VIDEOCHATS",
        "start": "START",
        "autoplay": "AUTO PLAY",
    }
    title = category_titles.get(category, category.upper())
    if not text.startswith("<blockquote>"):
        text = (
            f"<blockquote><b>🎧 APPLE MUSIX • {title}</b></blockquote>\\n\\n"
            + text
        )

    # Text-only category panel. Keep the existing button layout/colors.
    try:
        new_message = await query.message.reply_text(
            text=text,
            reply_markup=markup,
        )
        try:
            await query.message.delete()
        except Exception:
            pass
        return new_message
    except Exception:
        return


@app.on_callback_query(
    filters.regex("playmode")
    & ~app.bl_users
)
@lang.language()
@admin_check
async def _playmode(_, query: types.CallbackQuery):

    await query.answer(
        query.lang["processing"],
        show_alert=True
    )

    chat_id = query.message.chat.id

    admin_only = await db.get_play_mode(
        chat_id
    )

    _language = "en"

    await db.set_play_mode(
        chat_id,
        admin_only
    )

    await query.edit_message_reply_markup(
        reply_markup=buttons.settings_markup(
            query.lang,
            not admin_only,
            _language,
            chat_id,
        )
    )