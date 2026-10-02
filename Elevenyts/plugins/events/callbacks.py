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

    _text = query.lang["start_pm"].format(
        query.from_user.first_name,
        app.name,
        query.from_user.id,
    )

    key = buttons.start_key(
        query.lang,
        True,
        show_help=query.from_user.id == config.OWNER_ID,
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

    if action == "close":
        await query.answer()

        try:
            await query.message.delete()
        except Exception:
            pass

        return

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

    if not await db.get_call(chat_id):
        return await query.answer(
            query.lang["not_playing"],
            show_alert=True
        )

    if action == "status":
        return await query.answer()

    if action.startswith("seek_"):
        return await handle_seek(
            query,
            chat_id,
            action,
            user
        )

    if action == "loop":
        return await handle_loop(
            query,
            chat_id,
            user
        )

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

    elif action == "skip":

        await tune.play_next(chat_id)

        status = query.lang["skipped"]
        reply = query.lang["play_skipped"].format(user)

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
        m_id = current.message_id if current else None

        queue.force_add(
            chat_id,
            media,
            remove=pos
        )

        try:
            await app.delete_messages(
                chat_id=chat_id,
                message_ids=[m_id, media.message_id],
                revoke=True
            )
            media.message_id = None
        except Exception:
            pass

        msg = await app.send_message(
            chat_id=chat_id,
            text=query.lang["play_next"]
        )

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

    elif action == "replay":

        media = queue.get_current(chat_id)
        media.user = user

        await tune.replay(chat_id)

        status = query.lang["replayed"]
        reply = query.lang["play_replayed"].format(user)

    elif action == "stop":

        await tune.stop(chat_id)

        status = query.lang["stopped"]
        reply = query.lang["play_stopped"].format(user)

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

        updated_text = f"{mtext}\n\n<blockquote>{reply}</blockquote>"

        try:
            await query.edit_message_caption(
                caption=updated_text,
                reply_markup=keyboard,
            )
        except Exception:
            await query.edit_message_text(
                updated_text,
                reply_markup=keyboard,
            )

    except FloodWait as e:

        await asyncio.sleep(e.value)

        try:
            try:
                await query.edit_message_caption(
                    caption=updated_text,
                    reply_markup=keyboard,
                )
            except Exception:
                await query.edit_message_text(
                    updated_text,
                    reply_markup=keyboard,
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

    current_time = getattr(media, "time", 0)

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

    if current_loop == 0:
        new_loop = 1
        text = "🔂 Loop: Single Track"
        message = "🔂 Loop mode set to <b>Single Track</b>"
    elif current_loop == 1:
        new_loop = 10
        text = "🔁 Loop: Queue"
        message = "🔁 Loop mode set to <b>Queue</b>"
    else:
        new_loop = 0
        text = "➡️ Loop: Off"
        message = "➡️ Loop mode <b>Disabled</b>"

    await db.set_loop(chat_id, new_loop)

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

    current = items[0] if items else None
    remaining = items[1:] if len(items) > 1 else []

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
@safe_callback
async def _help(_, query: types.CallbackQuery):
    """Show the complete Apple Musix command help center - owner only."""

    if not query.from_user or query.from_user.id != config.OWNER_ID:
        return await query.answer(
            "⛔ This Help Center is available to the owner only.",
            show_alert=True,
        )

    await query.answer()

    help_menu = """🎧 <b>APPLE MUSIX • HELP CENTER</b>

<b>🎵 MUSIC & PLAYBACK</b>
/play — Play a song, YouTube link, or playlist.
/queue — Show the current queue.
/pause — Pause the current track.
/resume — Resume playback.
/skip — Skip to the next track.
/stop — Stop playback and clear the call.
/replay — Replay the current track.
/shuffle — Shuffle the waiting queue.
/loop — Toggle loop mode.
/seek — Seek forward/backward in the current track.

<b>ℹ️ INFORMATION</b>
/help — Open this Help Center.
/start — Open the bot welcome panel.
/ping — Check bot response time. (/alive)
/stats — Show bot statistics.
/activevc — Show active voice chats. (sudo)

<b>⚙️ SETTINGS</b>
/settings — Open playback settings.
/playmode — Change playback mode.
/auth — Authorize a user for music controls.
/unauth — Remove an authorized user.
/authlist — Show authorized users.
/admincache — Refresh admin cache. (/reload)
/channelplay — Configure channel playback.

<b>🛡️ CHAT / BLACKLIST</b>
/blacklistchat — Blacklist a chat. (sudo)
/whitelistchat — Whitelist a chat. (/unblacklistchat)
/blacklistedchat — Show blacklisted chats. (/blchats)
/block — Block a user. (sudo)
/unblock — Unblock a user. (sudo)
/blockedusers — Show blocked users. (/blusers)

<b>👑 SUDO / ADMIN</b>
/broadcast — Broadcast a message. (sudo)
/stop_gcast — Stop an active broadcast. (sudo)
/gban — Globally ban a user. (sudo)
/ungban — Remove a global ban. (/unglobalban)
/gbanlist — Show globally banned users. (/gbannedusers)
/leave — Make the bot leave a chat. (sudo)
/leaveall — Leave all eligible chats. (sudo)
/maintenance — Toggle maintenance mode. (sudo)
/addsudo — Add a sudo user.
/delsudo — Remove a sudo user. (/rmsudo)
/listsudo — Show sudo users. (/sudolist)
/autoleave — Configure automatic leaving.
/logs — View bot logs. (sudo)
/logger — Logger controls. (sudo)
/restart — Restart the bot. (sudo)
/update — Update the bot. (sudo)

<b>🔧 OWNER / DEVELOPER</b>
/eval — Execute owner evaluation code.
/exec — Execute owner evaluation code.

<b>🎬 VIDEO PLAYBACK</b>
/vplay — Play video in the voice chat.
/vplayforce — Force video playback.

<b>🎛️ PLAY COMMAND VARIANTS</b>
/playforce — Force play a track.
/cplay — Cached play mode.
/cplayforce — Force cached play.
/cvplay — Cached video play.
/cvplayforce — Force cached video play.

<i>Use /help anytime to open this command reference.</i>"""

    category = query.data.replace("help_", "")

    help_texts = {
        "play": "🎵 <b>/play</b>\n\nPlay a song, YouTube link, or playlist in the voice chat.\n\n<b>Aliases:</b> /playforce /cplay /cplayforce /vplay /vplayforce /cvplay /cvplayforce",
        "queue": "📋 <b>/queue</b>\n\nShow the current playing track and queued songs.\n\n<b>Aliases:</b> /playing /cqueue /cplaying",
        "pause": "⏸️ <b>/pause</b>\n\nPause the current track.\n\n<b>Alias:</b> /cpause",
        "resume": "▶️ <b>/resume</b>\n\nResume a paused track.\n\n<b>Alias:</b> /cresume",
        "skip": "⏭️ <b>/skip</b>\n\nSkip the current track and continue with the next queued track.\n\n<b>Aliases:</b> /next /cskip /cnext",
        "stop": "⏹️ <b>/stop</b>\n\nStop playback and clear the current voice session.\n\n<b>Aliases:</b> /end /cend /cstop",
        "replay": "🔄 <b>/replay</b>\n\nReplay the currently playing track.",
        "shuffle": "🔀 <b>/shuffle</b>\n\nRandomize the remaining queue.\n\n<b>Alias:</b> /cshuffle",
        "loop": "🔁 <b>/loop</b>\n\nToggle loop mode between off, single-track, and queue loop.\n\n<b>Alias:</b> /cloop",
        "seek": "⏩ <b>/seek</b>\n\nSeek within the current track.\n\n<b>Aliases:</b> /seekback /cseek /cseekback",
        "ping": "🏓 <b>/ping</b>\n\nCheck the bot response time.\n\n<b>Alias:</b> /alive",
        "stats": "📊 <b>/stats</b>\n\nShow bot statistics and system information.",
        "settings": "⚙️ <b>/settings</b>\n\nOpen playback settings.\n\n<b>Alias:</b> /playmode",
        "admins": "👮 <b>ADMIN COMMANDS</b>\n\nUse /auth, /unauth, /authlist, /admincache and /channelplay to manage authorized playback and chat settings.",
        "sudo": "👑 <b>SUDO COMMANDS</b>\n\nSudo tools include /broadcast, /gban, /ungban, /gbanlist, /leave, /leaveall, /maintenance, /addsudo, /delsudo and /listsudo.",
        "broadcast": "📢 <b>/broadcast</b>\n\nSend a broadcast message to the bot's configured chats. Sudo only.\n\n<b>Stop:</b> /stop_gcast",
        "gban": "🚫 <b>/gban</b>\n\nGlobally ban a user. Sudo only.\n\n<b>Related:</b> /ungban /unglobalban /gbanlist /gbannedusers",
        "maintenance": "🛠️ <b>/maintenance</b>\n\nEnable or disable maintenance mode. Sudo only.",
        "auth": "🔐 <b>/auth</b>\n\nAuthorize a user to use music controls in the group.\n\n<b>Related:</b> /unauth /authlist",
        "blchat": "🚫 <b>CHAT BLACKLIST</b>\n\nManage blocked chats with /blacklistchat, /whitelistchat and /blacklistedchat. Sudo only.",
        "bluser": "🚫 <b>USER BLOCKLIST</b>\n\nManage blocked users with /block, /unblock and /blockedusers. Sudo only.",
    }

    if query.data in ("help", "help_main"):
        help_text = help_menu
        markup = buttons.help_markup({})

        # Telegram captions are limited to 1024 characters.  The complete
        # Help Center is intentionally longer, so never try to put it in a
        # photo caption.  Convert the welcome photo into a normal text
        # message, then all category/back callbacks can safely edit text.
        try:
            if query.message and query.message.photo:
                sent = await query.message.reply_text(
                    help_text,
                    reply_markup=markup,
                    quote=False,
                )
                try:
                    await query.message.delete()
                except Exception:
                    pass
                return

            await query.edit_message_text(
                text=help_text,
                reply_markup=markup,
            )
            return

        except Exception as e:
            logger.error(
                f"Help Center main message update failed: {e}",
                exc_info=True,
            )

            # If editing fails for any reason, send a fresh text message.
            try:
                sent = await app.send_message(
                    chat_id=query.message.chat.id,
                    text=help_text,
                    reply_markup=markup,
                    reply_to_message_id=query.message.id,
                )
                try:
                    await query.message.delete()
                except Exception:
                    pass
                return
            except Exception:
                raise

    help_text = help_texts.get(category, help_menu)
    markup = buttons.help_markup({}, True)

    # Category descriptions are short enough for a Telegram caption, but
    # support both media and text messages so the Back button is reliable.
    try:
        if query.message and query.message.photo:
            await query.edit_message_caption(
                caption=help_text,
                reply_markup=markup,
            )
        else:
            await query.edit_message_text(
                text=help_text,
                reply_markup=markup,
            )
    except Exception as e:
        logger.error(
            f"Help Center category update failed for {query.data}: {e}",
            exc_info=True,
        )

        # Last-resort recovery: create a text Help Center message instead
        # of silently swallowing the error.
        try:
            await app.send_message(
                chat_id=query.message.chat.id,
                text=help_text,
                reply_markup=markup,
                reply_to_message_id=query.message.id,
            )
            try:
                await query.message.delete()
            except Exception:
                pass
        except Exception:
            raise


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
