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

from pyrogram import filters
from pyrogram import types
from pyrogram.errors import (
    FloodWait,
    MessageIdInvalid,
    MessageDeleteForbidden,
    ChatSendPlainForbidden,
    ChatWriteForbidden,
)

from Elevenyts import tune, app, config, db, lang, queue, tg, yt
from Elevenyts.helpers import buttons, utils
from Elevenyts.helpers._play import checkUB

import asyncio
import logging


logger = logging.getLogger(__name__)


async def safe_edit(message, text, **kwargs):
    """
    Safely edit a Telegram message.
    """

    try:
        await message.edit_text(text, **kwargs)
        return True

    except FloodWait as e:
        await asyncio.sleep(e.value)

        try:
            await message.edit_text(text, **kwargs)
            return True
        except Exception:
            return False

    except (MessageIdInvalid, MessageDeleteForbidden):
        return False

    except Exception as e:
        logger.debug(f"Message edit failed: {e}")
        return False


async def safe_reply(message, text, **kwargs):
    """
    Safely send a reply message.
    """

    try:
        return await message.reply_text(text, **kwargs)

    except (ChatSendPlainForbidden, ChatWriteForbidden):
        logger.warning(
            f"Cannot send text in chat {message.chat.id}"
        )
        return None

    except Exception as e:
        logger.error(f"Failed to send reply: {e}")
        return None


def playlist_to_queue(chat_id: int, tracks: list) -> str:
    """
    Add playlist tracks to queue.
    """

    text = "<blockquote expandable>"

    for track in tracks:
        pos = queue.add(chat_id, track)
        text += f"<b>{pos}.</b> {track.title}\n"

    text = text[:1948] + "</blockquote>"

    return text


async def get_direct_stream(file):
    """
    Extract a direct streaming URL.

    IMPORTANT:
    This does NOT download MP3/MP4.

    The URL is generated only when the track is about to play,
    because YouTube stream URLs can expire.
    """

    try:
        stream_url = await yt.get_stream_url(
            file.id,
            is_live=file.is_live,
            video=getattr(file, "video", False),
        )

        if stream_url:
            file.file_path = stream_url
            return stream_url

        logger.error(
            f"Could not extract direct stream URL for: {file.id}"
        )

        return None

    except Exception as e:
        logger.error(
            f"Direct stream extraction failed for {file.id}: {e}"
        )
        return None


@app.on_message(
    filters.command(
        [
            "play",
            "playforce",
            "cplay",
            "cplayforce",
            "vplay",
            "vplayforce",
            "cvplay",
            "cvplayforce",
        ]
    )
    & filters.group
    & ~app.bl_users
)
@lang.language()
@checkUB
async def play_hndlr(
    _,
    m: types.Message,
    force: bool = False,
    url: str = None,
    cplay: bool = False,
    video: bool = False,
) -> None:

    # ------------------------------------------------------
    # Delete command message
    # ------------------------------------------------------

    try:
        await m.delete()
    except Exception:
        pass

    # ------------------------------------------------------
    # Chat IDs
    # ------------------------------------------------------

    chat_id = m.chat.id
    message_chat_id = m.chat.id

    # ------------------------------------------------------
    # Channel play mode
    # ------------------------------------------------------

    if cplay:

        channel_id = await db.get_cmode(m.chat.id)

        if channel_id is None:
            return await safe_reply(
                m,
                "<blockquote>❌ Channel play is not enabled.\n\n"
                "To enable for linked channel:\n"
                "`/channelplay linked`\n\n"
                "To enable for any channel:\n"
                "`/channelplay [channel_id]`</blockquote>",
            )

        try:
            chat = await app.get_chat(channel_id)
            chat_id = channel_id

        except Exception:

            await db.set_cmode(m.chat.id, None)

            return await safe_reply(
                m,
                "<blockquote>❌ Cannot find channel!\n\n"
                "Please make sure I'm admin in the channel "
                "and channel exists.</blockquote>",
            )

        # --------------------------------------------------
        # Assistant
        # --------------------------------------------------

        client = await db.get_client(channel_id)

        try:
            await app.get_chat_member(channel_id, client.id)

        except Exception:

            try:

                if chat.username:
                    invite_link = chat.username

                else:

                    try:
                        invite_link = chat.invite_link

                        if not invite_link:
                            invite_link = (
                                await app.export_chat_invite_link(
                                    channel_id
                                )
                            )

                    except Exception:

                        return await safe_reply(
                            m,
                            f"<blockquote>"
                            f"❌ Assistant cannot join channel!\n\n"
                            f"Please add "
                            f"@{client.username if client.username else client.mention} "
                            f"to the channel as an admin."
                            f"</blockquote>",
                        )

                join_msg = await safe_reply(
                    m,
                    "<blockquote>🔌 Joining assistant to channel...</blockquote>",
                )

                await client.join_chat(invite_link)

                await asyncio.sleep(1)

                try:
                    if join_msg:
                        await join_msg.delete()
                except Exception:
                    pass

            except Exception as e:

                return await safe_reply(
                    m,
                    f"<blockquote>"
                    f"❌ Failed to join assistant to channel!\n\n"
                    f"Please manually add "
                    f"@{client.username if client.username else client.mention} "
                    f"to the channel as an admin.\n\n"
                    f"Error: {e}"
                    f"</blockquote>",
                )

    # ------------------------------------------------------
    # Searching message
    # ------------------------------------------------------

    play_emoji = m.lang["play_emoji"]

    try:

        sent = await safe_reply(
            m,
            m.lang["play_searching"].format(play_emoji),
        )

    except Exception:
        return

    if not sent:
        return

    # ------------------------------------------------------
    # User / media
    # ------------------------------------------------------

    mention = m.from_user.mention

    media = (
        tg.get_media(m.reply_to_message)
        if m.reply_to_message
        else None
    )

    tracks = []
    file = None

    # ------------------------------------------------------
    # Telegram media
    # ------------------------------------------------------

    if media:

        setattr(sent, "lang", m.lang)

        file = await tg.download(
            m.reply_to_message,
            sent,
        )

    # ------------------------------------------------------
    # URL
    # ------------------------------------------------------

    elif url:

        # --------------------------------------------------
        # Playlist
        # --------------------------------------------------

        if "playlist" in url:

            await safe_edit(
                sent,
                m.lang["playlist_fetch"],
            )

            try:

                tracks = await yt.playlist(
                    config.PLAYLIST_LIMIT,
                    mention,
                    url,
                )

            except Exception as e:

                logger.error(
                    f"Playlist fetch error: {e}"
                )

                await safe_edit(
                    sent,
                    "<blockquote>"
                    "❌ Failed to fetch playlist.\n\n"
                    "YouTube playlists are currently "
                    "experiencing issues. "
                    "Please try a single track instead."
                    "</blockquote>",
                )

                return

            if not tracks:

                await safe_edit(
                    sent,
                    m.lang["playlist_error"],
                )

                return

            file = tracks[0]
            tracks.remove(file)

            file.message_id = sent.id

        # --------------------------------------------------
        # Single URL
        # --------------------------------------------------

        else:

            file = await yt.search(
                url,
                sent.id,
            )

        if not file:

            await safe_edit(
                sent,
                m.lang["play_not_found"].format(
                    config.SUPPORT_CHAT
                ),
            )

            return

    # ------------------------------------------------------
    # Search query
    # ------------------------------------------------------

    elif len(m.command) >= 2:

        query = " ".join(m.command[1:])

        file = await yt.search(
            query,
            sent.id,
        )

        if not file:

            await safe_edit(
                sent,
                m.lang["play_not_found"].format(
                    config.SUPPORT_CHAT
                ),
            )

            return

    # ------------------------------------------------------
    # No file
    # ------------------------------------------------------

    if not file:
        return

    # ------------------------------------------------------
    # Video flag
    # ------------------------------------------------------

    file.video = (
        getattr(file, "video", False)
        or video
    )

    if file.video:

        for track in tracks:
            track.video = True

    # ------------------------------------------------------
    # Duration check
    # ------------------------------------------------------

    if (
        not file.is_live
        and file.duration_sec > config.DURATION_LIMIT
    ):

        await safe_edit(
            sent,
            m.lang["play_duration_limit"].format(
                config.DURATION_LIMIT // 60
            ),
        )

        return

    # ------------------------------------------------------
    # Logger
    # ------------------------------------------------------

    if await db.is_logger():

        await utils.play_log(
            m,
            file.title,
            file.duration,
        )

    # ------------------------------------------------------
    # User
    # ------------------------------------------------------

    file.user = mention

    # ------------------------------------------------------
    # Add to queue
    # ------------------------------------------------------

    if force:

        queue.force_add(
            chat_id,
            file,
        )

    else:

        position = queue.add(
            chat_id,
            file,
        )

        # --------------------------------------------------
        # Call already active
        # --------------------------------------------------

        if await db.get_call(chat_id):

            queued_text = (
                f"<blockquote>➕ <b>QUEUED | #{position}</b>  ”</blockquote>\n\n"
                f"<blockquote>🟢 <b>SONG</b> : "
                f"<a href="{file.url}">{file.title}</a>  ”</blockquote>\n\n"
                f"<blockquote>⏱️ <b>LENGTH</b> : {file.duration} MIN  ”</blockquote>\n\n"
                f"<blockquote>👤 <b>USER</b> : {m.from_user.mention}  ”</blockquote>"
            )

            await safe_edit(
                sent,
                queued_text,
                reply_markup=buttons.play_queued(
                    chat_id,
                    file.id,
                    m.lang["play_now"],
                ),
            )

            # ------------------------------------------------
            # Add playlist tracks
            # ------------------------------------------------

            if tracks:

                added = playlist_to_queue(
                    chat_id,
                    tracks,
                )

                try:

                    await app.send_message(
                        chat_id=m.chat.id,
                        text=(
                            m.lang["playlist_queued"].format(
                                len(tracks)
                            )
                            + added
                        ),
                    )

                except Exception:
                    pass

            # ------------------------------------------------
            # Direct-stream architecture
            #
            # No download/preload.
            # URLs are extracted when playback starts.
            # ------------------------------------------------

            try:

                from Elevenyts import preload

                asyncio.create_task(
                    preload.start_preload(
                        chat_id,
                        count=2,
                    )
                )

            except Exception as e:

                logger.debug(
                    f"Preload manager skipped: {e}"
                )

            return

    # ------------------------------------------------------
    # DIRECT STREAM
    # ------------------------------------------------------

    if not file.file_path:

        await safe_edit(
            sent,
            "<blockquote>🔗 Preparing direct stream...</blockquote>",
        )

        stream_url = await get_direct_stream(
            file
        )

        if not stream_url:

            await safe_edit(
                sent,
                "<blockquote>"
                "❌ Failed to get direct stream.\n\n"
                "Possible reasons:\n"
                "• YouTube detected bot activity\n"
                "• Video is region-blocked or private\n"
                "• Age-restricted content\n"
                "• YouTube stream is temporarily unavailable\n\n"
                "Please update cookies in "
                "`Elevenyts/cookies/` if required."
                "</blockquote>",
            )

            return

    # ------------------------------------------------------
    # PLAY
    # ------------------------------------------------------

    try:

        await tune.play_media(
            chat_id=chat_id,
            message=sent,
            media=file,
            message_chat_id=(
                message_chat_id
                if chat_id != message_chat_id
                else None
            ),
        )

        # --------------------------------------------------
        # Reaction
        # --------------------------------------------------

        try:

            emoji = m.lang["play_emoji"]

            await m.react(
                emoji
            )

        except Exception:
            pass

    except Exception as e:

        error_msg = str(e)

        logger.error(
            f"Playback error: {error_msg}"
        )

        if (
            "bot" in error_msg.lower()
            or "sign in" in error_msg.lower()
            or "youtube" in error_msg.lower()
        ):

            await safe_edit(
                sent,
                "<blockquote>"
                "❌ YouTube stream could not be started.\n\n"
                "Possible solution:\n"
                "• Update YouTube cookies in "
                "`Elevenyts/cookies/`\n"
                "• Try the song again\n"
                "• Try another YouTube video\n\n"
                f"Support: {config.SUPPORT_CHAT}"
                "</blockquote>",
            )

        else:

            await safe_edit(
                sent,
                f"<blockquote>"
                f"❌ Playback error:\n"
                f"{error_msg}\n\n"
                f"Support: {config.SUPPORT_CHAT}"
                f"</blockquote>",
            )

        return

    # ------------------------------------------------------
    # Playlist queue
    # ------------------------------------------------------

    if not tracks:
        return

    added = playlist_to_queue(
        chat_id,
        tracks,
    )

    try:

        await app.send_message(
            chat_id=m.chat.id,
            text=(
                m.lang["playlist_queued"].format(
                    len(tracks)
                )
                + added
            ),
        )

    except Exception:
        pass