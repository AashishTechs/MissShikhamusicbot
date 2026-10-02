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
# Unauthorized copying, modification, or redistribution
# of this source code without permission is prohibited.
# ==========================================================

import asyncio
import logging

from ntgcalls import ConnectionNotFound, TelegramServerError
from pyrogram import enums, errors
from pyrogram.types import InputMediaPhoto, Message
from pytgcalls import PyTgCalls, exceptions, types
from pytgcalls.pytgcalls_session import PyTgCallsSession

from Elevenyts import app, config, db, lang, logger, preload, queue, userbot
from Elevenyts.core.youtube import yt
from Elevenyts.helpers import Media, Track, buttons, thumb


# ==========================================================
# Suppress harmless PyTgCalls errors
# ==========================================================

class PyTgCallsErrorFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()

        if "UpdateGroupCall" in message:
            return False

        if (
            "Connection with chat id" in message
            and "not found" in message
        ):
            return False

        return True


logging.getLogger("pyrogram.dispatcher").addFilter(
    PyTgCallsErrorFilter()
)


# ==========================================================
# Telegram Voice Chat Controller
# ==========================================================

class TgCall(PyTgCalls):

    def __init__(self):
        self.clients = []

        # Prevent multiple play_next() calls
        # from running simultaneously for the same chat.
        self._play_next_locks = {}

        # Prevent duplicate StreamEnded events.
        self._stream_end_cache = {}

    # ======================================================
    # Telegram message helpers
    # ======================================================

    async def _edit_media_with_retry(
        self,
        message: Message,
        media_obj: InputMediaPhoto,
        reply_markup,
    ):
        """Edit media with basic FloodWait handling."""

        try:
            return await message.edit_media(
                media=media_obj,
                reply_markup=reply_markup,
            )

        except errors.FloodWait as fw:
            await asyncio.sleep(fw.value + 1)

            try:
                return await message.edit_media(
                    media=media_obj,
                    reply_markup=reply_markup,
                )
            except Exception:
                return None

        except errors.MessageNotModified:
            return None

        except Exception:
            return None

    async def _send_photo_with_retry(
        self,
        chat_id: int,
        photo,
        caption: str,
        reply_markup,
    ):
        """Send photo with FloodWait handling."""

        try:
            return await app.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                reply_markup=reply_markup,
            )

        except errors.FloodWait as fw:
            await asyncio.sleep(fw.value + 1)

            try:
                return await app.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=caption,
                    reply_markup=reply_markup,
                )
            except Exception:
                return None

        except Exception:
            return None

    # ======================================================
    # Direct stream URL helper
    # ======================================================

    async def _get_stream_url(
        self,
        media: Media | Track,
    ) -> str | None:
        """
        Get a temporary direct streaming URL.

        IMPORTANT:
        This does NOT download MP3/MP4 files.

        YouTube direct URLs can expire, so the URL is generated
        immediately before playback.
        """

        try:
            stream_url = await yt.get_stream_url(
                media.id,
                is_live=getattr(media, "is_live", False),
                video=getattr(media, "video", False),
            )

            if stream_url:
                media.file_path = stream_url
                return stream_url

            logger.warning(
                f"Could not extract direct stream URL for {media.id}"
            )

            return None

        except Exception as e:
            logger.error(
                f"Direct stream extraction failed for {media.id}: {e}",
                exc_info=True,
            )
            return None

    # ======================================================
    # Pause
    # ======================================================

    async def pause(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)

        try:
            await client.pause(chat_id)

            await db.playing(
                chat_id,
                paused=True,
            )

            return True

        except (
            ConnectionNotFound,
            exceptions.NotInCallError,
        ):
            await db.playing(
                chat_id,
                paused=False,
            )

            await db.remove_call(chat_id)

            queue.clear(chat_id)

            logger.warning(
                f"Pause requested but assistant not in call "
                f"for {chat_id}, syncing state"
            )

            return False

        except Exception as e:
            await db.playing(
                chat_id,
                paused=False,
            )

            logger.error(
                f"Pause failed for {chat_id}: {e}"
            )

            return False

    # ======================================================
    # Resume
    # ======================================================

    async def resume(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)

        try:
            await client.resume(chat_id)

            await db.playing(
                chat_id,
                paused=False,
            )

            return True

        except (
            ConnectionNotFound,
            exceptions.NotInCallError,
        ):
            await db.playing(
                chat_id,
                paused=False,
            )

            await db.remove_call(chat_id)

            queue.clear(chat_id)

            logger.warning(
                f"Resume requested but assistant not in call "
                f"for {chat_id}, syncing state"
            )

            return False

        except Exception as e:
            logger.error(
                f"Resume failed for {chat_id}: {e}"
            )

            return False

    # ======================================================
    # Stop
    # ======================================================

    async def stop(self, chat_id: int) -> None:
        client = await db.get_assistant(chat_id)

        # Cancel preload manager.
        try:
            await preload.cancel_preload(chat_id)

        except Exception as e:
            logger.debug(
                f"Error cancelling preload for {chat_id}: {e}"
            )

        # Clear queue and database state.
        try:
            queue.clear(chat_id)
            await db.remove_call(chat_id)

        except Exception as e:
            logger.warning(
                f"Error clearing queue/call for {chat_id}: {e}"
            )

        # Leave voice chat.
        try:
            await client.leave_call(
                chat_id,
                close=False,
            )

            await asyncio.sleep(0.5)

        except (
            ConnectionNotFound,
            exceptions.NotInCallError,
        ):
            pass

        except Exception as e:
            error_msg = str(e).lower()

            ignored_errors = [
                "not in a call",
                "not in the group call",
                "groupcall_forbidden",
                "no active group call",
                "call was already stopped",
                "call already disconnected",
            ]

            if not any(
                ignore in error_msg
                for ignore in ignored_errors
            ):
                logger.warning(
                    f"Error leaving call for {chat_id}: {e}"
                )

    # ======================================================
    # Play media
    # ======================================================

    async def play_media(
        self,
        chat_id: int,
        message: Message | None,
        media: Media | Track,
        seek_time: int = 0,
        message_chat_id: int = None,
    ) -> None:

        """
        Play media in Telegram voice chat.

        media.file_path contains the direct stream URL.

        No MP3/MP4 file is downloaded by this method.
        """

        client = await db.get_assistant(chat_id)
        _lang = await lang.get_lang(chat_id)

        # --------------------------------------------------
        # Determine message destination.
        #
        # Channel play:
        #   Audio -> channel
        #   Messages -> linked group
        #
        # Normal group:
        #   Audio + messages -> same group
        # --------------------------------------------------

        target_chat_for_messages = (
            message_chat_id
            if message_chat_id
            else chat_id
        )

        # --------------------------------------------------
        # Thumbnail
        # --------------------------------------------------

        # Render the real song thumbnail into the Now Playing card.
        # This keeps the actual YouTube artwork while giving it the
        # rounded/cropped player-card look.
        if isinstance(media, Track):
            _thumb = await thumb.generate(media)
            if not _thumb or _thumb == config.DEFAULT_THUMB:
                _thumb = (
                    getattr(media, "thumbnail", None)
                    or f"https://i.ytimg.com/vi/{media.id}/hqdefault.jpg"
                )
        else:
            _thumb = config.DEFAULT_THUMB

        # --------------------------------------------------
        # Direct stream URL
        #
        # If file_path is empty, generate a fresh URL.
        # --------------------------------------------------

        if not media.file_path:

            stream_url = await self._get_stream_url(media)

            if not stream_url:

                if message:
                    try:
                        await message.edit_text(
                            _lang["error_no_file"].format(
                                config.SUPPORT_CHAT
                            )
                        )
                    except Exception:
                        pass

                else:
                    logger.error(
                        f"No direct stream URL for media in {chat_id}"
                    )

                return

        # --------------------------------------------------
        # Validate chat
        # --------------------------------------------------

        try:
            chat = await app.get_chat(chat_id)

            if chat.type not in [
                enums.ChatType.SUPERGROUP,
                enums.ChatType.GROUP,
                enums.ChatType.CHANNEL,
            ]:

                logger.error(
                    f"Invalid chat type for {chat_id}: "
                    f"{chat.type}"
                )

                if message:
                    await message.edit_text(
                        "❌ Can only play in groups/channels."
                    )

                return

            # ------------------------------------------------
            # Channel assistant validation
            # ------------------------------------------------

            if chat.type == enums.ChatType.CHANNEL:

                userbot_client = await db.get_client(
                    chat_id
                )

                if not userbot_client:

                    logger.error(
                        f"No userbot client available "
                        f"for {chat_id}"
                    )

                    if message:
                        await message.edit_text(
                            "❌ No assistant available."
                        )

                    return

                try:
                    assistant_member = (
                        await app.get_chat_member(
                            chat_id,
                            userbot_client.me.id,
                        )
                    )

                    if (
                        assistant_member.status
                        == enums.ChatMemberStatus.BANNED
                    ):

                        logger.error(
                            f"Assistant banned in channel "
                            f"{chat_id}"
                        )

                        if message:
                            await message.edit_text(
                                "❌ Assistant is banned "
                                "in this channel."
                            )

                        await db.set_cmode(
                            chat_id,
                            None,
                        )

                        return

                except errors.RPCError as e:

                    if (
                        "CHANNEL_INVALID" in str(e)
                        or "USER_NOT_PARTICIPANT" in str(e)
                    ):

                        logger.error(
                            f"Assistant not in channel "
                            f"{chat_id}: {e}"
                        )

                        if message:
                            await message.edit_text(
                                "❌ <b>Assistant not "
                                "in channel!</b>\n\n"
                                f"<blockquote>"
                                f"Please add "
                                f"@{userbot_client.me.username} "
                                f"to the channel as admin "
                                f"with voice chat permissions."
                                f"</blockquote>"
                            )

                        await db.set_cmode(
                            chat_id,
                            None,
                        )

                        return

        except errors.RPCError as e:

            if "CHANNEL_INVALID" in str(e):

                logger.error(
                    f"Invalid channel {chat_id}: {e}"
                )

                if message:
                    await message.edit_text(
                        "❌ Invalid channel. "
                        "Disabling channel play."
                    )

                await db.set_cmode(
                    chat_id,
                    None,
                )

                return

            raise

        # ==================================================
        # FFmpeg stream parameters
        # ==================================================

        if seek_time > 1:

            ffmpeg_params = (
                f"-ss {seek_time} "
                f"-probesize 10M "
                f"-analyzeduration 5M "
                f"-rtbufsize 5M "
                f"-fflags +genpts+igndts"
            )

        else:

            ffmpeg_params = (
                "-probesize 10M "
                "-analyzeduration 5M "
                "-rtbufsize 5M "
                "-fflags +genpts+igndts "
                "-sync ext"
            )

        # ==================================================
        # Audio / video flags
        # ==================================================

        is_video = getattr(
            media,
            "video",
            False,
        )

        video_flags = (
            types.MediaStream.Flags.AUTO_DETECT
            if is_video
            else types.MediaStream.Flags.IGNORE
        )

        # ==================================================
        # Create direct network MediaStream
        # ==================================================

        stream = types.MediaStream(
            media_path=media.file_path,
            audio_parameters=types.AudioQuality.STUDIO,
            audio_flags=types.MediaStream.Flags.REQUIRED,
            video_flags=video_flags,
            ffmpeg_parameters=ffmpeg_params,
        )

        # ==================================================
        # Make sure old call is disconnected
        # ==================================================

        try:

            call = await client.get_call(
                chat_id
            )

            if call:

                logger.debug(
                    f"Already connected to {chat_id}, "
                    f"leaving before reconnecting..."
                )

                await client.leave_call(
                    chat_id,
                    close=False,
                )

        except (
            ConnectionNotFound,
            exceptions.NotInCallError,
        ):
            pass

        except Exception as e:

            logger.debug(
                f"Error checking connection state "
                f"for {chat_id}: {e}"
            )

        # ==================================================
        # Start playback
        # ==================================================

        max_retries = 3
        retry_delay = 1

        try:

            for attempt in range(max_retries):

                try:

                    await client.play(
                        chat_id=chat_id,
                        stream=stream,
                        config=types.GroupCallConfig(
                            auto_start=True
                        ),
                    )

                    break

                except (
                    exceptions.NoActiveGroupCall,
                    errors.RPCError,
                ) as e:

                    error_msg = str(e)

                    if (
                        "GROUPCALL_INVALID"
                        in error_msg
                        or "GROUPCALL"
                        in error_msg
                        or isinstance(
                            e,
                            exceptions.NoActiveGroupCall,
                        )
                    ):

                        if attempt < max_retries - 1:

                            logger.debug(
                                f"Group call transitioning "
                                f"for {chat_id}, retrying in "
                                f"{retry_delay}s... "
                                f"(attempt "
                                f"{attempt + 1}/"
                                f"{max_retries})"
                            )

                            await asyncio.sleep(
                                retry_delay
                            )

                            continue

                        raise

                    raise

                except Exception as e:

                    error_msg = str(e).lower()

                    if (
                        "cannot be initialized "
                        "more than once"
                        in error_msg
                        or "connection"
                        in error_msg
                    ):

                        if attempt < max_retries - 1:

                            logger.debug(
                                f"Connection error for "
                                f"{chat_id}, leaving and "
                                f"retrying..."
                            )

                            try:
                                await client.leave_call(
                                    chat_id,
                                    close=False,
                                )

                                await asyncio.sleep(
                                    retry_delay
                                )

                            except Exception:
                                pass

                            continue

                        raise

                    raise

            # ==================================================
            # Voice command recording
            # ==================================================

            try:

                await client.record(
                    chat_id
                )

                logger.debug(
                    f"🎤 Started listening to VC audio "
                    f"for {chat_id}"
                )

            except Exception as e:

                logger.warning(
                    f"⚠️ Could not start voice-command "
                    f"listening for {chat_id}: {e}"
                )

            # ==================================================
            # Playback time
            # ==================================================

            if seek_time:
                media.time = seek_time
            else:
                media.time = 1

            # ==================================================
            # Send playback UI
            # ==================================================

            if not seek_time:

                await db.add_call(
                    chat_id
                )

                text = _lang["play_media"].format(
                    media.url,
                    media.title,
                    media.duration,
                    media.user,
                )

                # ------------------------------------------------
                # Progress bar
                # ------------------------------------------------

                if (
                    not media.is_live
                    and media.duration_sec
                ):

                    import time as time_module

                    played = media.time
                    duration = media.duration_sec

                    bar_length = 8

                    if duration == 0:
                        percentage = 0
                    else:
                        percentage = min(
                            (played / duration) * 100,
                            100,
                        )

                    filled = int(
                        round(
                            bar_length
                            * percentage
                            / 100
                        )
                    )

                    timer_bar = (
                        "—" * filled
                        + "●"
                        + "—"
                        * (
                            bar_length
                            - filled
                        )
                    )

                    if duration >= 3600:

                        played_time = (
                            time_module.strftime(
                                "%H:%M:%S",
                                time_module.gmtime(
                                    played
                                ),
                            )
                        )

                        total_time = (
                            time_module.strftime(
                                "%H:%M:%S",
                                time_module.gmtime(
                                    duration
                                ),
                            )
                        )

                    else:

                        played_time = (
                            time_module.strftime(
                                "%M:%S",
                                time_module.gmtime(
                                    played
                                ),
                            )
                        )

                        total_time = (
                            time_module.strftime(
                                "%M:%S",
                                time_module.gmtime(
                                    duration
                                ),
                            )
                        )

                    timer_text = (
                        f"{played_time} "
                        f"{timer_bar} "
                        f"{total_time}"
                    )

                    keyboard = buttons.controls(
                        chat_id,
                        timer=timer_text,
                    )

                else:

                    keyboard = buttons.controls(
                        chat_id
                    )

                # ------------------------------------------------
                # Delete command message
                # ------------------------------------------------

                if message:

                    try:
                        await message.delete()
                    except Exception:
                        pass

                # ------------------------------------------------
                # Send playback card
                # ------------------------------------------------

                sent_photo = (
                    await self._send_photo_with_retry(
                        chat_id=target_chat_for_messages,
                        photo=_thumb,
                        caption=text,
                        reply_markup=keyboard,
                    )
                )

                if sent_photo:
                    media.message_id = sent_photo.id

                # ------------------------------------------------
                # Start preload manager.
                #
                # Preload manager no longer downloads files.
                # ------------------------------------------------

                try:

                    asyncio.create_task(
                        preload.start_preload(
                            chat_id,
                            count=2,
                        )
                    )

                except Exception as e:

                    logger.debug(
                        f"Error starting preload "
                        f"for {chat_id}: {e}"
                    )

        # ======================================================
        # Errors
        # ======================================================

        except FileNotFoundError:

            if message:

                try:
                    await message.edit_text(
                        _lang["error_no_file"].format(
                            config.SUPPORT_CHAT
                        )
                    )
                except Exception:
                    pass

            await self.play_next(
                chat_id
            )

        except exceptions.NoActiveGroupCall:

            await self.stop(
                chat_id
            )

            if message:

                try:
                    await message.edit_text(
                        _lang["error_vc_disabled"]
                    )
                except Exception:
                    pass

        except errors.RPCError as e:

            error_str = str(e)

            if any(
                x in error_str
                for x in [
                    "CHAT_ADMIN_REQUIRED",
                    "phone.CreateGroupCall",
                    "GROUPCALL_FORBIDDEN",
                    "GROUPCALL_CREATE_FORBIDDEN",
                    "VOICE_MESSAGES_FORBIDDEN",
                ]
            ):

                await self.stop(
                    chat_id
                )

                if message:

                    try:
                        await message.edit_text(
                            _lang["error_vc_disabled"]
                        )
                    except Exception:
                        pass

            elif (
                "GROUPCALL_INVALID"
                in error_str
                or "GROUPCALL"
                in error_str
            ):

                await self.stop(
                    chat_id
                )

                if message:

                    try:
                        await message.edit_text(
                            _lang["error_no_call"]
                        )
                    except Exception:
                        pass

            else:

                logger.error(
                    f"RPC error in play_media "
                    f"for {chat_id}: {e}"
                )

                await self.stop(
                    chat_id
                )

        except exceptions.NoAudioSourceFound:

            if message:

                try:
                    await message.edit_text(
                        _lang["error_no_audio"]
                    )
                except Exception:
                    pass

            await self.play_next(
                chat_id
            )

        except (
            ConnectionNotFound,
            TelegramServerError,
        ):

            await self.stop(
                chat_id
            )

            if message:

                try:
                    await message.edit_text(
                        _lang["error_tg_server"]
                    )
                except Exception:
                    pass

        except TimeoutError as e:

            error_msg = str(e)

            logger.warning(
                f"⏱️ Timeout joining voice chat "
                f"{chat_id}: {error_msg}"
            )

            await self.stop(
                chat_id
            )

            if message:

                try:

                    await message.edit_text(
                        "⏱️ <b>Connection timed out!</b>\n\n"
                        "<blockquote>"
                        "Failed to join voice chat. "
                        "Please check your network "
                        "and try again."
                        "</blockquote>"
                    )

                except Exception:
                    pass

            await asyncio.sleep(2)

            await self.play_next(
                chat_id
            )

        except Exception as e:

            logger.error(
                f"Unexpected error in play_media "
                f"for {chat_id}: {e}",
                exc_info=True,
            )

            await self.stop(
                chat_id
            )

            if message:

                try:

                    await message.edit_text(
                        f"❌ Playback error: "
                        f"{str(e)[:100]}"
                    )

                except Exception:
                    pass

    # ======================================================
    # Replay
    # ======================================================

    async def replay(
        self,
        chat_id: int,
    ) -> None:

        try:

            if not await db.get_call(
                chat_id
            ):
                return

            message_chat_id = None

            try:

                chat = await app.get_chat(
                    chat_id
                )

                if chat.type == enums.ChatType.CHANNEL:

                    group_id = (
                        await db.get_group_for_channel(
                            chat_id
                        )
                    )

                    if group_id:
                        message_chat_id = group_id

            except Exception:
                pass

            media = queue.get_current(
                chat_id
            )

            if not media:
                return

            _lang = await lang.get_lang(
                chat_id
            )

            target_chat = (
                message_chat_id
                if message_chat_id
                else chat_id
            )

            msg = await app.send_message(
                chat_id=target_chat,
                text=_lang["play_again"],
            )

            # Direct URL may have expired.
            # Clear it so a fresh URL is extracted.
            media.file_path = None

            await self.play_media(
                chat_id,
                msg,
                media,
                message_chat_id=message_chat_id,
            )

        except Exception as e:

            logger.error(
                f"Error in replay for {chat_id}: {e}",
                exc_info=True,
            )

    # ======================================================
    # Seek
    # ======================================================

    async def seek_stream(
        self,
        chat_id: int,
        seconds: int,
    ) -> bool:

        """Seek to a specific position in the current stream."""

        try:

            if not await db.get_call(
                chat_id
            ):
                return False

            media = queue.get_current(
                chat_id
            )

            if not media or media.is_live:
                return False

            _lang = await lang.get_lang(
                chat_id
            )

            message_chat_id = None

            try:

                chat = await app.get_chat(
                    chat_id
                )

                if chat.type == enums.ChatType.CHANNEL:

                    group_id = (
                        await db.get_group_for_channel(
                            chat_id
                        )
                    )

                    if group_id:
                        message_chat_id = group_id

            except Exception:
                pass

            media.time = seconds

            # --------------------------------------------------
            # Direct stream URLs can expire.
            # Force a fresh URL before seeking.
            # --------------------------------------------------

            media.file_path = None

            target_chat = (
                message_chat_id
                if message_chat_id
                else chat_id
            )

            try:

                msg = await app.get_messages(
                    target_chat,
                    media.message_id,
                )

            except Exception:

                msg = None

            if not msg:

                msg = await app.send_message(
                    chat_id=target_chat,
                    text=_lang["seeking"],
                )

            await self.play_media(
                chat_id,
                msg,
                media,
                seek_time=seconds,
                message_chat_id=message_chat_id,
            )

            return True

        except Exception as e:

            logger.warning(
                f"Seek stream failed for "
                f"{chat_id}: {e}"
            )

            return False

    # ======================================================
    # Play next track
    # ======================================================

    async def play_next(
        self,
        chat_id: int,
    ) -> None:

        if chat_id not in self._play_next_locks:

            self._play_next_locks[
                chat_id
            ] = asyncio.Lock()

        lock = self._play_next_locks[
            chat_id
        ]

        if lock.locked():

            logger.info(
                f"play_next already running "
                f"for {chat_id}, skipping duplicate call"
            )

            return

        async with lock:

            try:

                if not await db.get_call(
                    chat_id
                ):
                    return

                # --------------------------------------------------
                # Message destination
                # --------------------------------------------------

                message_chat_id = None

                try:

                    chat = await app.get_chat(
                        chat_id
                    )

                    if (
                        chat.type
                        == enums.ChatType.CHANNEL
                    ):

                        group_id = (
                            await db.get_group_for_channel(
                                chat_id
                            )
                        )

                        if group_id:
                            message_chat_id = group_id

                except Exception:
                    pass

                target_chat = (
                    message_chat_id
                    if message_chat_id
                    else chat_id
                )

                # --------------------------------------------------
                # Loop mode
                # --------------------------------------------------

                loop_mode = await db.get_loop(
                    chat_id
                )

                # ==================================================
                # Loop current track
                # ==================================================

                if loop_mode == 1:

                    media = queue.get_current(
                        chat_id
                    )

                    if media:

                        _lang = await lang.get_lang(
                            chat_id
                        )

                        try:

                            msg = await app.send_message(
                                chat_id=target_chat,
                                text=_lang["play_again"],
                            )

                            # Direct URL may have expired.
                            media.file_path = None

                            await self.play_media(
                                chat_id,
                                msg,
                                media,
                                message_chat_id=message_chat_id,
                            )

                        except errors.ChannelPrivate:

                            logger.warning(
                                f"Bot removed from "
                                f"{chat_id}, cleaning up"
                            )

                            try:
                                await self.leave_call(
                                    chat_id
                                )

                            except Exception as leave_ex:

                                logger.debug(
                                    f"Could not leave call "
                                    f"for {chat_id}: "
                                    f"{leave_ex}"
                                )

                            await db.rm_chat(
                                chat_id
                            )

                    return

                # ==================================================
                # Queue loop mode
                # ==================================================

                media = queue.get_next(
                    chat_id
                )

                if (
                    not media
                    and loop_mode == 10
                ):

                    all_items = queue.get_all(
                        chat_id
                    )

                    if all_items:

                        first_track = all_items[0]

                        _lang = await lang.get_lang(
                            chat_id
                        )

                        try:

                            msg = await app.send_message(
                                chat_id=target_chat,
                                text="🔁 Looping queue...",
                            )

                            # ------------------------------------------------
                            # Direct streaming.
                            #
                            # NEVER download the track.
                            # Generate a fresh temporary stream URL.
                            # ------------------------------------------------

                            first_track.file_path = None

                            stream_url = (
                                await self._get_stream_url(
                                    first_track
                                )
                            )

                            if not stream_url:

                                logger.error(
                                    f"Could not get direct "
                                    f"stream URL for "
                                    f"{first_track.id}"
                                )

                                return

                            first_track.message_id = msg.id

                            await self.play_media(
                                chat_id,
                                msg,
                                first_track,
                                message_chat_id=message_chat_id,
                            )

                        except errors.ChannelPrivate:

                            logger.warning(
                                f"Bot removed from "
                                f"{chat_id}, cleaning up"
                            )

                            await self.leave_call(
                                chat_id
                            )

                            await db.rm_chat(
                                chat_id
                            )

                    return

                # ==================================================
                # Delete previous playback message
                # ==================================================

                try:

                    if (
                        media
                        and media.message_id
                    ):

                        await app.delete_messages(
                            chat_id=chat_id,
                            message_ids=media.message_id,
                            revoke=True,
                        )

                        media.message_id = 0

                except Exception as e:

                    logger.debug(
                        f"Could not delete previous "
                        f"message in {chat_id}: {e}"
                    )

                # ==================================================
                # Queue finished
                # ==================================================

                if not media:

                    if config.AUTO_END:

                        _lang = await lang.get_lang(
                            chat_id
                        )

                        try:

                            await app.send_message(
                                chat_id=chat_id,
                                text=_lang.get(
                                    "auto_end",
                                    "✅ Queue finished. "
                                    "Stream ended automatically.",
                                ),
                            )

                        except Exception as e:

                            logger.debug(
                                f"Could not send auto_end "
                                f"message in {chat_id}: {e}"
                            )

                    return await self.stop(
                        chat_id
                    )

                # ==================================================
                # Playback status message
                # ==================================================

                _lang = await lang.get_lang(
                    chat_id
                )

                msg = None

                # Send the lightweight transition message first.
                # Stream extraction can take several seconds and should
                # not block the user-facing state update.
                try:

                    msg = await app.send_message(
                        chat_id=target_chat,
                        text=_lang["play_next"],
                    )

                except errors.FloodWait as fw:

                    logger.warning(
                        f"FloodWait in play_next for "
                        f"{chat_id}: skipping status "
                        f"message ({fw.value}s)"
                    )

                    msg = None

                except errors.ChannelPrivate:

                    logger.warning(
                        f"Bot removed from "
                        f"{chat_id}, cleaning up"
                    )

                    await self.leave_call(
                        chat_id
                    )

                    await db.rm_chat(
                        chat_id
                    )

                    return

                except Exception as e:

                    logger.error(
                        f"Failed to send play_next "
                        f"message for {chat_id}: {e}"
                    )

                    msg = None

                # ==================================================
                # Save message ID
                # ==================================================

                media.message_id = (
                    msg.id
                    if msg
                    else 0
                )

                # ==================================================
                # Fresh direct stream URL
                # ==================================================

                # Reuse the background-preloaded URL when available.
                # If it is missing, extract it now. Direct URLs are
                # temporary, so replay/seek paths still force refreshes.
                if not media.file_path:
                    stream_url = await self._get_stream_url(media)

                    if not stream_url:
                        logger.error(
                            f"Could not get direct stream URL "
                            f"for next track {media.id}"
                        )

                        if msg:
                            try:
                                await msg.edit_text(
                                    "❌ Unable to prepare the next track."
                                )
                            except Exception:
                                pass

                        await self.stop(chat_id)
                        return

                # ==================================================
                # Start playback
                # ==================================================

                if msg:

                    await self.play_media(
                        chat_id,
                        msg,
                        media,
                        message_chat_id=message_chat_id,
                    )

                else:

                    logger.info(
                        f"Playing next track for "
                        f"{chat_id} without message update"
                    )

                    await self.play_media(
                        chat_id,
                        None,
                        media,
                        message_chat_id=message_chat_id,
                    )

                # ==================================================
                # Start no-download preload manager
                # ==================================================

                try:

                    asyncio.create_task(
                        preload.start_preload(
                            chat_id,
                            count=2,
                        )
                    )

                except Exception as e:

                    logger.debug(
                        f"Error starting preload "
                        f"after play_next for "
                        f"{chat_id}: {e}"
                    )

            except Exception as e:

                logger.error(
                    f"Error in play_next for "
                    f"{chat_id}: {e}",
                    exc_info=True,
                )

                try:

                    await self.stop(
                        chat_id
                    )

                except Exception:
                    pass

    # ======================================================
    # Ping
    # ======================================================

    async def ping(self) -> float:

        if not self.clients:
            return 0.0

        pings = [
            client.ping
            for client in self.clients
        ]

        return round(
            sum(pings) / len(pings),
            2,
        )

    # ======================================================
    # PyTgCalls event decorators
    # ======================================================

    async def decorators(
        self,
        client: PyTgCalls,
    ) -> None:

        for client in self.clients:

            @client.on_update()
            async def update_handler(
                _,
                update: types.Update,
            ) -> None:

                # ==============================================
                # Stream ended
                # ==============================================

                if isinstance(
                    update,
                    types.StreamEnded,
                ):

                    if (
                        update.stream_type
                        == types.StreamEnded.Type.AUDIO
                    ):

                        chat_id = update.chat_id

                        current_time = (
                            asyncio.get_event_loop().time()
                        )

                        # ------------------------------------------------
                        # Ignore duplicate StreamEnded events
                        # ------------------------------------------------

                        if (
                            chat_id
                            in self._stream_end_cache
                        ):

                            if (
                                current_time
                                - self._stream_end_cache[
                                    chat_id
                                ]
                                < 2.0
                            ):

                                return

                        self._stream_end_cache[
                            chat_id
                        ] = current_time

                        # ------------------------------------------------
                        # Clean old cache entries
                        # ------------------------------------------------

                        self._stream_end_cache = {
                            cid: timestamp
                            for cid, timestamp
                            in self._stream_end_cache.items()
                            if (
                                current_time
                                - timestamp
                                < 5.0
                            )
                        }

                        await self.play_next(
                            chat_id
                        )

                # ==============================================
                # Voice chat state updates
                # ==============================================

                elif isinstance(
                    update,
                    types.ChatUpdate,
                ):

                    if update.status in [
                        types.ChatUpdate.Status.KICKED,
                        types.ChatUpdate.Status.LEFT_GROUP,
                        types.ChatUpdate.Status.CLOSED_VOICE_CHAT,
                    ]:

                        await self.stop(
                            update.chat_id
                        )

    # ======================================================
    # Boot
    # ======================================================

    async def boot(self) -> None:

        PyTgCallsSession.notice_displayed = True

        from Elevenyts.core.voice_commands import (
            register_voice_listener
        )

        for ub in userbot.clients:

            client = PyTgCalls(
                ub,
                cache_duration=100,
            )

            await client.start()

            self.clients.append(
                client
            )

            await self.decorators(
                client
            )

            # ==============================================
            # Register VC voice command listener
            # ==============================================

            register_voice_listener(
                client
            )

        logger.info(
            "📞 PyTgCalls client(s) started."
        )