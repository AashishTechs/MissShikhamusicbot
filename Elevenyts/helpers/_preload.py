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

import asyncio
import logging
import time
from typing import Dict, Set


logger = logging.getLogger("Elevenyts")


class PreloadManager:
    """
    Direct-stream based preload manager.

    IMPORTANT:
    - MP3/MP4 download nahi karta.
    - YouTube stream URL advance me extract nahi karta.
    - Actual stream URL playback ke time generate hoga.
    - Existing preload API compatibility ke liye maintain ki gayi hai.
    """

    def __init__(self):
        """Initialize preload manager."""

        # {chat_id: {media_id: asyncio.Task}}
        self._tasks: Dict[int, Dict[str, asyncio.Task]] = {}

        # Direct streaming architecture me actual files
        # preload nahi hote, lekin compatibility state maintain hai.
        self._preloaded: Dict[int, Set[str]] = {}

    async def preload_next(self, chat_id: int, media) -> None:
        """
        Upcoming track ko preload karne ke naam par
        ab koi MP3/MP4 download nahi karta.
        """

        media_id = getattr(media, "id", None)

        if not media_id:
            return

        if chat_id not in self._tasks:
            self._tasks[chat_id] = {}

        if chat_id not in self._preloaded:
            self._preloaded[chat_id] = set()

        # Already marked as prepared
        if media_id in self._preloaded[chat_id]:
            logger.debug(
                f"Track {media_id} already prepared "
                f"for chat {chat_id}"
            )
            return

        # Existing task running
        existing = self._tasks[chat_id].get(media_id)

        if existing and not existing.done():
            return

        # Compatibility task
        task = asyncio.create_task(
            self._preload_task(chat_id, media)
        )

        self._tasks[chat_id][media_id] = task

    async def _preload_task(self, chat_id: int, media) -> None:
        """
        Compatibility method.

        OLD SYSTEM:
            yt.download() -> MP3/MP4 file

        NEW SYSTEM:
            No file download.
            Stream URL actual playback ke time generate hoga.
        """

        media_id = getattr(media, "id", None)
        title = getattr(media, "title", "Unknown")

        if not media_id:
            return

        try:
            # Pre-fetch the temporary direct stream URL for the
            # next queued track. This removes the URL-extraction
            # wait when the current song ends.
            from Elevenyts.core.youtube import yt

            stream_url = await yt.get_stream_url(
                media_id,
                is_live=getattr(media, "is_live", False),
                video=getattr(media, "video", False),
            )

            if not stream_url:
                logger.debug(
                    f"Could not prefetch stream URL for {chat_id}: {title}"
                )
                return

            media.file_path = stream_url
            media._stream_url_at = time.monotonic()

            self._preloaded.setdefault(
                chat_id,
                set()
            ).add(media_id)

            logger.debug(
                f"Stream URL prefetched for chat {chat_id}: {title}"
            )

        except asyncio.CancelledError:
            logger.debug(
                f"Preload cancelled for chat {chat_id}: "
                f"{title}"
            )
            raise

        except Exception as e:
            logger.error(
                f"Preload error for chat {chat_id}: {e}"
            )

        finally:
            media_tasks = self._tasks.get(chat_id)

            if media_tasks:
                media_tasks.pop(media_id, None)

                if not media_tasks:
                    self._tasks.pop(chat_id, None)

    async def cancel_preload(self, chat_id: int) -> None:
        """
        Chat ke active preload tasks cancel karta hai.
        """

        media_tasks = self._tasks.get(chat_id, {})

        if media_tasks:
            active_tasks = [
                task
                for task in media_tasks.values()
                if not task.done()
            ]

            for task in active_tasks:
                task.cancel()

            if active_tasks:
                await asyncio.gather(
                    *active_tasks,
                    return_exceptions=True
                )

            logger.debug(
                f"Cancelled preload for chat {chat_id}"
            )

        self._preloaded.pop(chat_id, None)
        self._tasks.pop(chat_id, None)

    def is_preloaded(
        self,
        chat_id: int,
        media_id: str
    ) -> bool:
        """
        Check karta hai ki track preparation state me hai ya nahi.
        """

        return media_id in self._preloaded.get(
            chat_id,
            set()
        )

    def clear(self, chat_id: int) -> None:
        """
        Chat ka preload state clear karta hai.
        """

        self._preloaded.pop(chat_id, None)
        self._tasks.pop(chat_id, None)

    async def start_preload(
        self,
        chat_id: int,
        count: int = 2
    ) -> None:
        """
        Queue ke upcoming tracks ko prepare karta hai.

        IMPORTANT:
        Direct streaming me actual files download nahi hoti.
        """

        try:
            # Import here to avoid circular dependency
            from Elevenyts import queue

            all_tracks = queue.get_queue(chat_id)

            if len(all_tracks) <= 1:
                return

            # Current track skip karke upcoming tracks
            upcoming = all_tracks[
                1:min(1 + count, len(all_tracks))
            ]

            for media in upcoming:

                media_id = getattr(media, "id", None)

                if not media_id:
                    continue

                # Keep a valid prefetched direct stream URL.
                # Clearing it here would defeat the whole preload
                # system and force play_next() to extract again.
                if getattr(media, "file_path", None):
                    try:
                        age = time.monotonic() - float(
                            getattr(media, "_stream_url_at", time.monotonic())
                        )
                        if age < 240:
                            continue
                    except Exception:
                        pass

                    media.file_path = None

                await self.preload_next(
                    chat_id,
                    media
                )

        except Exception as e:
            logger.debug(
                f"Error in start_preload for {chat_id}: {e}"
            )


preload = PreloadManager()