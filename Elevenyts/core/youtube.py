# ==========================================================
# Copyright (c) 2026 MissShikhamusicbot
# All Rights Reserved.
#
# Project      : MissShikhamusicbot
# Powered By   : MissShikhamusicbot
# Type         : Telegram Music Bot
#
# Bot          : @MissShikhaMusicBot
#
# Unauthorized copying, modification, or redistribution
# of this source code without permission is prohibited.
# ==========================================================

import os
import re
import glob
import time
import yt_dlp
import random
import asyncio
import aiohttp
import shutil

from dataclasses import replace
from pathlib import Path
from typing import Optional, Union

from pyrogram import enums, types
from py_yt import Playlist, VideosSearch

from Elevenyts import config, logger
from Elevenyts.helpers import Track, utils


class YouTube:

    def __init__(self):
        """Initialize YouTube handler with configuration and caching."""

        self.base = "https://www.youtube.com/watch?v="

        self.cookies = []
        self.checked = False
        self.warned = False

        # ======================================================
        # API CONFIGURATION
        # ======================================================

        self.api_url = config.ARTISTBOTS_API_URL
        self.artistbots_key = config.ARTISTBOTS_KEY
        self.enable_api = config.ENABLE_API
        self.enable_cookies_fallback = config.ENABLE_COOKIES_FALLBACK
        self.api_timeout = config.API_TIMEOUT
        self.api_stream_timeout = config.API_STREAM_TIMEOUT

        # ======================================================
        # YOUTUBE URL REGEX
        # ======================================================

        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|live/|embed/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )

        # ======================================================
        # SEARCH CACHE
        # ======================================================

        self.search_cache = {}

        # Kept for compatibility with old download code.
        self._download_semaphore = asyncio.Semaphore(5)

        self._max_video_height = config.VIDEO_MAX_HEIGHT

        # ======================================================
        # DENO / YT-DLP JAVASCRIPT RUNTIME
        # ======================================================

        self.deno_path = self._find_deno()

        if self.deno_path:
            logger.info(
                f"🦕 Deno runtime detected: {self.deno_path}"
            )
        else:
            logger.warning(
                "⚠️ Deno runtime was not found. "
                "YouTube extraction may fail."
            )

        # ======================================================
        # LOGGING
        # ======================================================

        logger.info("=" * 50)
        logger.info("📹 YouTube Handler Initialized")

        logger.info(
            f"🎵 API Priority: "
            f"{'ENABLED' if self.enable_api else 'DISABLED'}"
        )

        if self.enable_api:

            logger.info(
                f"🔗 API URL: {self.api_url}"
            )

            if self.artistbots_key:

                masked_key = (
                    self.artistbots_key[:8] + "..."
                    if len(self.artistbots_key) > 8
                    else "***"
                )

                logger.info(
                    f"🔑 API Key: {masked_key}"
                )

            else:

                logger.warning(
                    "⚠️ No API Key configured!"
                )

        logger.info(
            f"🍪 Cookies Fallback: "
            f"{'ENABLED' if self.enable_cookies_fallback else 'DISABLED'}"
        )

        logger.info("=" * 50)

    # ==========================================================
    # DENO DETECTION
    # ==========================================================

    def _find_deno(self) -> Optional[str]:

        """
        Find Deno executable for yt-dlp JavaScript challenge solving.

        Priority:
        1. DENO_PATH environment variable
        2. PATH
        3. Common Windows WinGet installation
        """

        # ------------------------------------------------------
        # Environment variable
        # ------------------------------------------------------

        env_path = os.getenv("DENO_PATH")

        if env_path:

            env_path = os.path.expandvars(
                os.path.expanduser(env_path)
            )

            if os.path.isfile(env_path):

                return env_path

        # ------------------------------------------------------
        # PATH
        # ------------------------------------------------------

        path = shutil.which("deno")

        if path:

            return path

        # ------------------------------------------------------
        # Windows WinGet fallback
        # ------------------------------------------------------

        if os.name == "nt":

            local_app_data = os.getenv(
                "LOCALAPPDATA"
            )

            if local_app_data:

                winget_dir = os.path.join(
                    local_app_data,
                    "Microsoft",
                    "WinGet",
                    "Packages"
                )

                pattern = os.path.join(
                    winget_dir,
                    "DenoLand.Deno_*",
                    "deno.exe"
                )

                matches = glob.glob(
                    pattern
                )

                if matches:

                    return matches[0]

        return None

    # ==========================================================
    # YT-DLP OPTIONS
    # ==========================================================

    def _get_ydl_opts(self) -> dict:

        """
        Common yt-dlp configuration.

        Direct stream extraction does NOT download media.
        """

        options = {
            "quiet": True,
            "no_warnings": True,

            "noplaylist": True,

            "geo_bypass": True,
            "nocheckcertificate": True,

            "socket_timeout": 30,

            "retries": 3,
            "fragment_retries": 3,
            "extractor_retries": 5,

            "skip_download": True,

            "extractor_args": {
                "youtube": {
                    "player_client": [
                        "android",
                        "web"
                    ]
                }
            },
        }

        # ------------------------------------------------------
        # DENO
        # ------------------------------------------------------

        if self.deno_path:

            options["js_runtimes"] = {
                "deno": {
                    "path": self.deno_path
                }
            }

        else:

            # Deno is the default runtime in current yt-dlp.
            # Keeping this explicit allows yt-dlp to try it.
            options["js_runtimes"] = {
                "deno": {
                    "path": None
                }
            }

        return options

    # ==========================================================
    # EXISTING DOWNLOAD FILE LOCATOR
    # ==========================================================

    def _locate_download_file(
        self,
        video_id: str,
        video: bool = False
    ) -> Optional[str]:

        """Locate any completed download file for a video id."""

        pattern = f"downloads/{video_id}*"

        candidates = sorted(
            [
                path
                for path in glob.glob(pattern)
                if not path.endswith(
                    (
                        ".part",
                        ".ytdl",
                        ".info.json",
                        ".temp"
                    )
                )
            ]
        )

        video_exts = {
            ".mp4",
            ".mkv",
            ".webm",
            ".mov"
        }

        audio_exts = {
            ".m4a",
            ".webm",
            ".opus",
            ".mp3",
            ".ogg",
            ".wav",
            ".flac"
        }

        if video:

            for path in candidates:

                if os.path.isdir(path):
                    continue

                if Path(path).suffix.lower() in video_exts:
                    return path

        else:

            for path in candidates:

                if os.path.isdir(path):
                    continue

                if Path(path).suffix.lower() in audio_exts:
                    return path

        for path in candidates:

            if os.path.isdir(path):
                continue

            return path

        return None

    # ==========================================================
    # COOKIES
    # ==========================================================

    def get_cookies(self):

        """Get random cookie file from cookies directory."""

        if not self.checked:

            cookies_dir = "Elevenyts/cookies"

            if os.path.exists(cookies_dir):

                for file in os.listdir(cookies_dir):

                    if file.endswith(".txt"):

                        self.cookies.append(file)

            self.checked = True

        if not self.cookies:

            if not self.warned:

                self.warned = True

                logger.warning(
                    "🍪 Cookies are missing; "
                    "stream extraction might fail."
                )

            return None

        cookie_file = (
            f"Elevenyts/cookies/"
            f"{random.choice(self.cookies)}"
        )

        logger.debug(
            f"Using cookie file: {cookie_file}"
        )

        return cookie_file

    async def save_cookies(
        self,
        urls: list[str]
    ) -> None:

        """Save cookies from URLs to files."""

        logger.info(
            "🍪 Saving cookies from urls..."
        )

        saved_count = 0

        cookies_dir = Path(
            "Elevenyts/cookies"
        )

        cookies_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        for url in urls:

            try:

                path = (
                    cookies_dir /
                    f"cookie{random.randint(10000, 99999)}.txt"
                )

                if "pastebin.com" in url:

                    link = url.replace(
                        "pastebin.com",
                        "pastebin.com/raw"
                    )

                elif "batbin.me" in url:

                    link = url.replace(
                        "batbin.me",
                        "batbin.me/raw"
                    )

                else:

                    link = url

                async with aiohttp.ClientSession() as session:

                    async with session.get(
                        link,
                        timeout=aiohttp.ClientTimeout(
                            total=30
                        )
                    ) as resp:

                        if resp.status != 200:

                            logger.error(
                                f"❌ Cookie download failed: "
                                f"HTTP {resp.status} from {url}"
                            )

                            continue

                        content = await resp.read()

                        if (
                            not content
                            or len(content) < 50
                        ):

                            logger.error(
                                f"❌ Cookie file empty or invalid "
                                f"from {url}"
                            )

                            continue

                        with open(
                            path,
                            "wb"
                        ) as fw:

                            fw.write(content)

                        if (
                            path.exists()
                            and path.stat().st_size > 0
                        ):

                            saved_count += 1

                            cookie_filename = path.name

                            if (
                                cookie_filename
                                not in self.cookies
                            ):

                                self.cookies.append(
                                    cookie_filename
                                )

                            logger.info(
                                f"✅ Saved: "
                                f"{cookie_filename} "
                                f"({len(content)} bytes)"
                            )

            except asyncio.TimeoutError:

                logger.error(
                    f"❌ Cookie file download timeout "
                    f"from {url}"
                )

            except Exception as e:

                logger.error(
                    f"❌ Cookie file download error "
                    f"from {url}: {e}"
                )

        self.checked = True

        if saved_count > 0:

            logger.info(
                f"✅ Cookies saved successfully! "
                f"({saved_count} file(s))"
            )

        else:

            logger.error(
                "❌ No cookies saved! "
                "Check COOKIE_URL in .env."
            )

    # ==========================================================
    # DIRECT STREAM URL EXTRACTION
    # ==========================================================

    async def get_stream_url(
        self,
        video_id: str,
        is_live: bool = False,
        video: bool = False
    ) -> Optional[str]:

        """
        Extract a direct YouTube media URL.

        IMPORTANT:
        This method does NOT download MP3/MP4.

        It only extracts the temporary media URL
        and returns it to PyTgCalls / MediaStream.
        """

        if not video_id:

            logger.error(
                "❌ Cannot extract stream URL: "
                "video_id is empty."
            )

            return None

        url = self.base + video_id

        cookie = self.get_cookies()

        # ======================================================
        # YT-DLP OPTIONS
        # ======================================================

        ydl_opts = self._get_ydl_opts()

        # ------------------------------------------------------
        # Cookies
        # ------------------------------------------------------

        if cookie:

            ydl_opts["cookiefile"] = cookie

        # ======================================================
        # AUDIO STREAM
        # ======================================================

        if not video:

            ydl_opts["format"] = (
                "bestaudio[acodec!=none]/"
                "bestaudio/best"
            )

        # ======================================================
        # VIDEO STREAM
        # ======================================================

        else:

            height_filter = ""

            if (
                self._max_video_height
                and self._max_video_height > 0
            ):

                height_filter = (
                    f"[height<="
                    f"{self._max_video_height}]"
                )

            ydl_opts["format"] = (
                f"best[ext=mp4]"
                f"{height_filter}/"
                f"best"
                f"{height_filter}/"
                "best"
            )

        # ======================================================
        # SYNCHRONOUS YT-DLP EXTRACTION
        # ======================================================

        def _extract():

            try:

                with yt_dlp.YoutubeDL(
                    ydl_opts
                ) as ydl:

                    info = ydl.extract_info(
                        url,
                        download=False
                    )

                if not info:

                    return None

                # --------------------------------------------------
                # Direct URL
                # --------------------------------------------------

                direct_url = info.get("url")

                if direct_url:

                    return direct_url

                # --------------------------------------------------
                # Formats fallback
                # --------------------------------------------------

                formats = info.get(
                    "formats",
                    []
                )

                # Audio-only formats first.
                if not video:

                    for fmt in reversed(formats):

                        if (
                            fmt.get("acodec")
                            != "none"
                            and fmt.get("vcodec")
                            == "none"
                            and fmt.get("url")
                        ):

                            return fmt["url"]

                # Video/audio capable fallback.
                for fmt in reversed(formats):

                    if (
                        fmt.get("url")
                        and fmt.get("acodec")
                        != "none"
                    ):

                        return fmt["url"]

                # --------------------------------------------------
                # Manifest fallback
                # --------------------------------------------------

                manifest_url = info.get(
                    "manifest_url"
                )

                if manifest_url:

                    return manifest_url

                return None

            except Exception as e:

                logger.error(
                    f"❌ Direct stream extraction "
                    f"failed for {video_id}: {e}"
                )

                return None

        # ======================================================
        # RUN EXTRACTION WITHOUT BLOCKING BOT
        # ======================================================

        try:

            stream_url = await asyncio.wait_for(
                asyncio.to_thread(
                    _extract
                ),
                timeout=45
            )

            if stream_url:

                logger.info(
                    f"Direct stream URL extracted: "
                    f"{video_id}"
                )

            else:

                logger.error(
                    f"❌ No direct stream URL found: "
                    f"{video_id}"
                )

            return stream_url

        except asyncio.TimeoutError:

            logger.error(
                f"⏰ Stream URL extraction timed out: "
                f"{video_id}"
            )

            return None

        except Exception as e:

            logger.error(
                f"❌ Stream URL extraction error "
                f"for {video_id}: {e}"
            )

            return None

    # ==========================================================
    # OLD API DOWNLOAD METHOD
    # KEPT FOR COMPATIBILITY
    # ==========================================================

    async def download_via_api(
        self,
        link: str,
        video: bool = False
    ) -> Optional[str]:

        """
        Legacy API download method.

        This method is NOT used by the new direct-stream
        playback system.
        """

        if not self.enable_api:

            return None

        if not self.api_url:

            return None

        if "v=" in link:

            video_id = (
                link.split("v=")[-1]
                .split("&")[0]
            )

        elif "youtu.be" in link:

            video_id = (
                link.split("/")[-1]
                .split("?")[0]
            )

        else:

            video_id = link

        if not video_id:

            return None

        DOWNLOAD_DIR = "downloads"

        os.makedirs(
            DOWNLOAD_DIR,
            exist_ok=True
        )

        file_ext = (
            ".mp4"
            if video
            else ".mp3"
        )

        file_path = os.path.join(
            DOWNLOAD_DIR,
            f"{video_id}{file_ext}"
        )

        if os.path.exists(file_path):

            return file_path

        try:

            download_type = (
                "video"
                if video
                else "audio"
            )

            logger.info(
                f"🚀 [API] Downloading "
                f"{video_id}"
            )

            params = {
                "url": video_id,
                "type": download_type,
            }

            if self.artistbots_key:

                params["api_key"] = (
                    self.artistbots_key
                )

            else:

                return None

            async with aiohttp.ClientSession() as session:

                api_endpoint = (
                    f"{self.api_url.rstrip('/')}"
                    "/download"
                )

                async with session.get(
                    api_endpoint,
                    params=params,
                    timeout=aiohttp.ClientTimeout(
                        total=self.api_stream_timeout
                    ),
                ) as response:

                    if response.status != 200:

                        return None

                    with open(
                        file_path,
                        "wb"
                    ) as f:

                        async for chunk in response.content.iter_chunked(
                            65536
                        ):

                            f.write(chunk)

                    if (
                        os.path.exists(file_path)
                        and os.path.getsize(file_path) > 0
                    ):

                        return file_path

                    if os.path.exists(file_path):

                        os.remove(file_path)

                    return None

        except Exception as e:

            logger.error(
                f"❌ API download failed "
                f"for {video_id}: {e}"
            )

            return None

    # ==========================================================
    # OLD COOKIE DOWNLOAD METHOD
    # KEPT FOR COMPATIBILITY
    # ==========================================================

    async def download_via_cookies(
        self,
        video_id: str,
        video: bool = False
    ) -> Optional[str]:

        """
        Legacy cookie-based download method.

        New playback does NOT use this method.
        """

        if not self.enable_cookies_fallback:

            return None

        url = self.base + video_id

        filename_pattern = (
            f"downloads/{video_id}"
        )

        existing_files = [
            f
            for f in glob.glob(
                f"{filename_pattern}.*"
            )
            if not f.endswith(".part")
        ]

        if video:

            video_candidates = [
                f
                for f in existing_files
                if Path(f).suffix.lower()
                in {
                    ".mp4",
                    ".mkv",
                    ".webm",
                    ".mov"
                }
            ]

            if video_candidates:

                return video_candidates[0]

        else:

            audio_candidates = [
                f
                for f in existing_files
                if Path(f).suffix.lower()
                in {
                    ".m4a",
                    ".webm",
                    ".opus",
                    ".mp3",
                    ".ogg",
                    ".wav",
                    ".flac"
                }
            ]

            if audio_candidates:

                return audio_candidates[0]

        downloads_dir = Path(
            "downloads"
        )

        downloads_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        async with self._download_semaphore:

            cookie = self.get_cookies()

            base_opts = {
                "outtmpl":
                    "downloads/%(id)s.%(ext)s",

                "quiet": True,

                "noplaylist": True,

                "geo_bypass": True,

                "no_warnings": True,

                "overwrites": False,

                "nocheckcertificate": True,

                "continuedl": True,

                "noprogress": True,

                "socket_timeout": 30,

                "retries": 2,

                "fragment_retries": 2,

                "extractor_retries": 5,

                "extractor_args": {
                    "youtube": {
                        "player_client": [
                            "android",
                            "web"
                        ]
                    }
                },
            }

            # --------------------------------------------------
            # DENO
            # --------------------------------------------------

            if self.deno_path:

                base_opts["js_runtimes"] = {
                    "deno": {
                        "path": self.deno_path
                    }
                }

            else:

                base_opts["js_runtimes"] = {
                    "deno": {
                        "path": None
                    }
                }

            if video:

                height_filter = ""

                if (
                    self._max_video_height
                    and self._max_video_height > 0
                ):

                    height_filter = (
                        f"[height<="
                        f"{self._max_video_height}]"
                    )

                format_chain = (
                    f"bestvideo[ext=mp4]"
                    f"{height_filter}+"
                    "bestaudio[ext=m4a]/"
                    f"bestvideo{height_filter}+"
                    "bestaudio/"
                    "bestvideo+bestaudio/best"
                )

                ydl_opts = {
                    **base_opts,

                    "format": format_chain,

                    "merge_output_format": "mp4",
                }

            else:

                ydl_opts = {
                    **base_opts,

                    "format":
                        "bestaudio[ext=m4a]/"
                        "bestaudio[acodec=opus]/"
                        "bestaudio/best",
                }

            if cookie:

                ydl_opts["cookiefile"] = cookie

            def _download():

                try:

                    with yt_dlp.YoutubeDL(
                        ydl_opts
                    ) as ydl:

                        info = ydl.extract_info(
                            url,
                            download=True
                        )

                    if not info:

                        return None

                    time.sleep(0.5)

                    return self._locate_download_file(
                        video_id,
                        video=video
                    )

                except Exception as e:

                    logger.warning(
                        f"⚠️ Download error "
                        f"for {video_id}: {e}"
                    )

                    return self._locate_download_file(
                        video_id,
                        video=video
                    )

            return await asyncio.to_thread(
                _download
            )

    # ==========================================================
    # URL VALIDATION
    # ==========================================================

    def valid(
        self,
        url: str
    ) -> bool:

        if not url:

            return False

        return bool(
            re.match(
                self.regex,
                url
            )
        )

    # ==========================================================
    # EXTRACT YOUTUBE URL FROM MESSAGE
    # ==========================================================

    def url(
        self,
        message_1: types.Message
    ) -> Union[str, None]:

        messages = [
            message_1
        ]

        link = None

        if message_1.reply_to_message:

            messages.append(
                message_1.reply_to_message
            )

        for message in messages:

            text = (
                message.text
                or message.caption
                or ""
            )

            if message.entities:

                for entity in message.entities:

                    if (
                        entity.type
                        == enums.MessageEntityType.URL
                    ):

                        link = text[
                            entity.offset:
                            entity.offset
                            + entity.length
                        ]

                        break

            if message.caption_entities:

                for entity in message.caption_entities:

                    if (
                        entity.type
                        == enums.MessageEntityType.TEXT_LINK
                    ):

                        link = entity.url

                        break

        if link:

            return (
                link
                .split("&si")[0]
                .split("?si")[0]
            )

        return None

    # ==========================================================
    # YOUTUBE SEARCH
    # ==========================================================

    async def search(
        self,
        query: str,
        m_id: int
    ) -> Track | None:

        cache_key = query

        current_time = (
            asyncio.get_running_loop().time()
        )

        # ======================================================
        # CACHE
        # ======================================================

        if cache_key in self.search_cache:

            cached_result, cache_timestamp = (
                self.search_cache[cache_key]
            )

            if (
                current_time
                - cache_timestamp
                < 600
            ):

                fresh = replace(
                    cached_result
                )

                fresh.message_id = m_id
                fresh.file_path = None
                fresh.user = None
                fresh.time = 0
                fresh.video = False

                return fresh

        # ======================================================
        # SEARCH
        # ======================================================

        try:

            _search = VideosSearch(
                query,
                limit=1
            )

            results = await _search.next()

        except Exception as e:

            logger.warning(
                f"⚠️ YouTube search failed "
                f"for '{query}': {e}"
            )

            return None

        if results and results["result"]:

            data = results["result"][0]

            duration = data.get(
                "duration"
            )

            is_live = (
                duration is None
                or duration == "LIVE"
            )

            thumbnails = data.get(
                "thumbnails",
                []
            )

            thumbnail_url = ""

            if thumbnails:

                thumbnail_url = (
                    thumbnails[-1]
                    .get("url", "")
                    .split("?")[0]
                )

            title = data.get(
                "title",
                "Unknown"
            )

            if not title:

                title = "Unknown"

            track = Track(

                id=data.get(
                    "id"
                ),

                channel_name=data.get(
                    "channel",
                    {}
                ).get(
                    "name"
                ),

                duration=(
                    duration
                    if not is_live
                    else "LIVE"
                ),

                duration_sec=(
                    0
                    if is_live
                    else utils.to_seconds(
                        duration
                    )
                ),

                message_id=m_id,

                title=title[:25],

                thumbnail=thumbnail_url,

                url=data.get(
                    "link"
                ),

                view_count=(
                    data.get(
                        "viewCount",
                        {}
                    ).get(
                        "short"
                    )
                ),

                is_live=is_live,

                file_path=None,

            )

            # ==================================================
            # CACHE
            # ==================================================

            self.search_cache[
                cache_key
            ] = (
                track,
                current_time
            )

            if len(
                self.search_cache
            ) > 100:

                oldest_key = min(
                    self.search_cache.keys(),
                    key=lambda k:
                    self.search_cache[k][1]
                )

                del self.search_cache[
                    oldest_key
                ]

            return replace(
                track
            )

        return None

    # ==========================================================
    # PLAYLIST
    # ==========================================================

    async def playlist(
        self,
        limit: int,
        user: str,
        url: str
    ) -> list[Track]:

        try:

            plist = await Playlist.get(
                url
            )

            tracks = []

            if (
                not plist
                or "videos" not in plist
                or not plist["videos"]
            ):

                return []

            for data in plist[
                "videos"
            ][:limit]:

                try:

                    thumbnails = data.get(
                        "thumbnails",
                        []
                    )

                    thumbnail_url = ""

                    if thumbnails:

                        thumbnail_url = (
                            thumbnails[-1]
                            .get("url", "")
                            .split("?")[0]
                        )

                    link = data.get(
                        "link",
                        ""
                    )

                    if "&list=" in link:

                        link = link.split(
                            "&list="
                        )[0]

                    title = data.get(
                        "title",
                        "Unknown"
                    )

                    if not title:

                        title = "Unknown"

                    duration = data.get(
                        "duration",
                        "0:00"
                    )

                    track = Track(

                        id=data.get(
                            "id",
                            ""
                        ),

                        channel_name=data.get(
                            "channel",
                            {}
                        ).get(
                            "name",
                            ""
                        ),

                        duration=duration,

                        duration_sec=utils.to_seconds(
                            duration
                        ),

                        title=title[:25],

                        thumbnail=thumbnail_url,

                        url=link,

                        user=user,

                        view_count="",

                        file_path=None,

                    )

                    tracks.append(
                        track
                    )

                except Exception as e:

                    logger.warning(
                        f"Failed to parse "
                        f"playlist item: {e}"
                    )

                    continue

            return tracks

        except KeyError:

            raise Exception(
                "Failed to parse playlist. "
                "YouTube may have changed "
                "their structure."
            )

        except Exception as e:

            logger.error(
                f"Playlist extraction error: {e}"
            )

            raise

    # ==========================================================
    # LEGACY DOWNLOAD METHODS
    # ==========================================================

    async def _download_live(
        self,
        video_id: str
    ) -> Optional[str]:

        # Live playback now uses direct stream extraction.

        return await self.get_stream_url(
            video_id,
            is_live=True,
            video=False
        )

    async def _download_standard(
        self,
        video_id: str,
        video: bool
    ) -> Optional[str]:

        """
        Legacy compatibility method.

        New playback should use get_stream_url().

        This method is retained because other older parts
        of the project may still depend on it.
        """

        result = None

        if (
            self.enable_api
            and self.api_url
            and self.artistbots_key
        ):

            result = await self.download_via_api(
                self.base + video_id,
                video=video
            )

            if result:

                return result

        if self.enable_cookies_fallback:

            result = await self.download_via_cookies(
                video_id,
                video=video
            )

            if result:

                return result

        return result

    async def download(
        self,
        video_id: str,
        is_live: bool = False,
        video: bool = False
    ) -> Optional[str]:

        """
        Legacy compatibility method.

        IMPORTANT:
        New direct playback uses get_stream_url().

        This method is kept temporarily so older project
        components do not break.
        """

        if is_live:

            return await self._download_live(
                video_id
            )

        return await self._download_standard(
            video_id,
            video
        )


# ==========================================================
# GLOBAL YOUTUBE HANDLER
# ==========================================================

yt = YouTube()