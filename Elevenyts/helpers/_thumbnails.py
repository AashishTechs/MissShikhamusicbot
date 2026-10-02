# ==========================================================
# Copyright (c) 2026 Apple Music <<3
# All Rights Reserved.
# ==========================================================
import os
import asyncio
import aiohttp

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from Elevenyts import config
from Elevenyts.helpers import Track


class Thumbnail:
    def __init__(self):
        try:
            self.title_font = ImageFont.truetype(
                "Elevenyts/helpers/Raleway-Bold.ttf", 46
            )
            self.meta_font = ImageFont.truetype(
                "Elevenyts/helpers/Inter-Light.ttf", 25
            )
            self.small_font = ImageFont.truetype(
                "Elevenyts/helpers/Inter-Light.ttf", 18
            )
            self.icon_font = ImageFont.truetype(
                "Elevenyts/helpers/Raleway-Bold.ttf", 48
            )
        except OSError:
            self.title_font = ImageFont.load_default()
            self.meta_font = ImageFont.load_default()
            self.small_font = ImageFont.load_default()
            self.icon_font = ImageFont.load_default()

    async def save_thumb(self, output_path: str, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                with open(output_path, "wb") as f:
                    f.write(await resp.read())
        return output_path

    @staticmethod
    def _fit_cover(image: Image.Image, size):
        image = image.convert("RGB")
        src_w, src_h = image.size
        dst_w, dst_h = size
        scale = max(dst_w / src_w, dst_h / src_h)
        nw, nh = int(src_w * scale), int(src_h * scale)
        image = image.resize((nw, nh), Image.Resampling.LANCZOS)
        left = (nw - dst_w) // 2
        top = (nh - dst_h) // 2
        return image.crop((left, top, left + dst_w, top + dst_h))

    @staticmethod
    def _trim(text: str, font, max_width: int):
        if font.getlength(text) <= max_width:
            return text
        for i in range(len(text), 0, -1):
            value = text[:i].rstrip() + "…"
            if font.getlength(value) <= max_width:
                return value
        return "…"

    async def generate(self, song: Track, size=(1280, 720)) -> str:
        try:
            temp = f"cache/temp_{song.id}.jpg"
            # Versioned filename forces regeneration of old cached panels.
            output = f"cache/{song.id}_apple_v5.png"

            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)

            return await asyncio.get_event_loop().run_in_executor(
                None,
                self._generate_sync,
                temp,
                output,
                song,
                size,
            )
        except Exception:
            return config.DEFAULT_THUMB

    def _generate_sync(self, temp: str, output: str, song: Track, size=(1280, 720)) -> str:
        try:
            with Image.open(temp) as source:
                cover = self._fit_cover(source, (430, 430))

            base = cover.resize(size, Image.Resampling.LANCZOS).filter(
                ImageFilter.GaussianBlur(32)
            )
            base = ImageEnhance.Brightness(base).enhance(0.38)
            base = ImageEnhance.Saturation(base).enhance(1.15)

            draw = ImageDraw.Draw(base, "RGBA")

            # Dark translucent layer for the Apple-Music-style player card.
            draw.rounded_rectangle(
                (35, 35, size[0] - 35, size[1] - 35),
                radius=34,
                fill=(30, 10, 20, 145),
                outline=(80, 40, 55, 210),
                width=3,
            )

            # Full album artwork on the left.
            cover_box = (70, 90, 500, 520)
            mask = Image.new("L", (430, 430), 0)
            ImageDraw.Draw(mask).rounded_rectangle(
                (0, 0, 430, 430), radius=24, fill=255
            )
            base.paste(cover, (70, 90), mask)

            title = self._trim(
                str(song.title or "Unknown Track"),
                self.title_font,
                610,
            )
            artist = self._trim(
                str(song.channel_name or "YouTube"),
                self.meta_font,
                560,
            )

            # Track title and artist on the right.
            draw.text((555, 105), title, font=self.title_font, fill="white")
            draw.text((555, 160), artist, font=self.meta_font, fill=(220, 220, 220))

            # Progress bar.
            bar_x1, bar_x2, bar_y = 555, 1190, 245
            draw.rounded_rectangle(
                (bar_x1, bar_y, bar_x2, bar_y + 7),
                radius=5,
                fill=(205, 205, 205, 180),
            )
            draw.rounded_rectangle(
                (bar_x1, bar_y, bar_x1 + 135, bar_y + 7),
                radius=5,
                fill="white",
            )
            draw.ellipse(
                (bar_x1 + 123, bar_y - 7, bar_x1 + 137, bar_y + 7),
                fill="white",
            )
            draw.text((555, 260), "0:00", font=self.small_font, fill="white")
            end_time = "LIVE" if getattr(song, "is_live", False) else str(song.duration or "0:00")
            end_w = draw.textlength(end_time, font=self.small_font)
            draw.text((1190 - end_w, 260), end_time, font=self.small_font, fill="white")

            # Playback icons inside the artwork, matching the reference style.
            icon_y = 335
            draw.text((660, icon_y), "◀", font=self.icon_font, fill="white", anchor="mm")
            draw.text((805, icon_y), "Ⅱ", font=self.icon_font, fill="white", anchor="mm")
            draw.text((950, icon_y), "▶", font=self.icon_font, fill="white", anchor="mm")

            # Volume line + small utility icons.
            draw.text((555, 430), "♪", font=self.meta_font, fill="white")
            draw.rounded_rectangle(
                (605, 444, 1050, 449),
                radius=3,
                fill=(230, 230, 230, 220),
            )
            draw.text((690, 485), "▣", font=self.small_font, fill="white")
            draw.text((795, 485), "☷", font=self.small_font, fill="white")

            base.save(output)
            try:
                os.remove(temp)
            except OSError:
                pass

            return output
        except Exception:
            return config.DEFAULT_THUMB
