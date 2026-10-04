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
import os
import re
import asyncio
import aiohttp
import base64

from PIL import (
    Image,
    ImageDraw,
    ImageEnhance,
    ImageFilter,
    ImageFont,
    ImageOps
)

from Elevenyts import config
from Elevenyts.helpers import Track


PANEL_W, PANEL_H = 1030, 610
PANEL_X = (1280 - PANEL_W) // 2
PANEL_Y = 55

THUMB_W, THUMB_H = 930, 420
THUMB_X = PANEL_X + (PANEL_W - THUMB_W) // 2
THUMB_Y = PANEL_Y + 30

TITLE_X = THUMB_X + 5
TITLE_Y = THUMB_Y + THUMB_H + 25

META_Y = TITLE_Y + 58

BAR_X = THUMB_X + 5
BAR_Y = META_Y + 60

BAR_RED_LEN = 330
BAR_TOTAL_LEN = 920

ICONS_W, ICONS_H = 420, 45
ICONS_X = PANEL_X + (PANEL_W - ICONS_W) // 2
ICONS_Y = BAR_Y + 65

MAX_TITLE_WIDTH = 850

_f = "QXJ0aXN0Ym90cw=="


def _decode_f():
    decoded = base64.b64decode(_f).decode("utf-8")
    return f"✦ {decoded} ✦"


def trim_to_width(text: str, font, max_w: int) -> str:

    ellipsis = "…"

    if font.getlength(text) <= max_w:
        return text

    for i in range(len(text) - 1, 0, -1):

        if font.getlength(text[:i] + ellipsis) <= max_w:
            return text[:i] + ellipsis

    return ellipsis


class Thumbnail:

    def __init__(self):

        try:

            self.title_font = ImageFont.truetype(
                "Elevenyts/helpers/Raleway-Bold.ttf",
                42
            )

            self.regular_font = ImageFont.truetype(
                "Elevenyts/helpers/Inter-Light.ttf",
                24
            )

            self.signature_font = ImageFont.truetype(
                "Elevenyts/helpers/Raleway-Bold.ttf",
                28
            )

        except OSError:

            self.title_font = ImageFont.load_default()
            self.regular_font = ImageFont.load_default()
            self.signature_font = ImageFont.load_default()

    async def save_thumb(self, output_path: str, url: str):

        async with aiohttp.ClientSession() as session:

            async with session.get(url) as resp:

                with open(output_path, "wb") as f:
                    f.write(await resp.read())

        return output_path

    async def generate(self, song: Track, size=(1280, 720)) -> str:

        try:

            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}_full.png"

            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)

            return await asyncio.get_event_loop().run_in_executor(
                None,
                self._generate_sync,
                temp,
                output,
                song,
                size
            )

        except Exception:
            return config.DEFAULT_THUMB

    def _generate_sync(
        self,
        temp: str,
        output: str,
        song: Track,
        size=(1280, 720)
    ) -> str:

        try:
            # --------------------------------------------------
            # Reference-style music player card.
            # The source thumbnail is used as the album/video art
            # while the rest of the player UI is rendered locally.
            # --------------------------------------------------
            with Image.open(temp) as temp_img:
                source = temp_img.convert("RGB")
                # Keep the original thumbnail aspect ratio so the full
                # song image is visible without stretching or cropping.
                base = ImageOps.fit(source, size, method=Image.Resampling.LANCZOS)

            # Blurred background.
            bg = base.filter(ImageFilter.GaussianBlur(32))
            bg = ImageEnhance.Brightness(bg).enhance(0.32)
            bg = ImageEnhance.Contrast(bg).enhance(1.15)
            bg = bg.convert("RGBA")

            # Main rounded player surface.
            card = Image.new("RGBA", (1140, 610), (24, 35, 47, 238))
            mask = Image.new("L", card.size, 0)
            ImageDraw.Draw(mask).rounded_rectangle(
                (0, 0, 1139, 609),
                radius=34,
                fill=255,
            )
            bg.alpha_composite(card, (70, 55))

            draw = ImageDraw.Draw(bg)

            # Album/video art: preserve the complete source image.
            art_w, art_h = 500, 282
            art_x, art_y = 105, 145
            art = ImageOps.contain(
                source,
                (art_w, art_h),
                method=Image.Resampling.LANCZOS,
            )
            art_canvas = Image.new("RGB", (art_w, art_h), (18, 25, 34))
            art_canvas.paste(
                art,
                ((art_w - art.width) // 2, (art_h - art.height) // 2),
            )
            art_mask = Image.new("L", art_canvas.size, 0)
            ImageDraw.Draw(art_mask).rounded_rectangle(
                (0, 0, art_w - 1, art_h - 1),
                radius=26,
                fill=255,
            )
            bg.paste(art_canvas, (art_x, art_y), art_mask)

            # Fonts.
            title_font = self.title_font
            regular_font = self.regular_font
            icon_font = ImageFont.truetype(
                "Elevenyts/helpers/Raleway-Bold.ttf",
                34,
            )

            clean_title = re.sub(r"\s+", " ", song.title).strip()
            final_title = trim_to_width(
                clean_title,
                title_font,
                610,
            )

            # Right-side title and source.
            text_x = 575
            draw.text(
                (text_x + 2, 170 + 2),
                final_title,
                fill=(0, 0, 0, 180),
                font=title_font,
            )
            draw.text(
                (text_x, 170),
                final_title,
                fill=(255, 255, 255, 255),
                font=title_font,
            )

            draw.text(
                (text_x, 225),
                "NOW PLAYING",
                fill=(175, 190, 205, 255),
                font=regular_font,
            )

            # Progress bar.
            bar_x = text_x
            bar_y = 345
            bar_w = 470

            draw.rounded_rectangle(
                (bar_x, bar_y, bar_x + bar_w, bar_y + 7),
                radius=4,
                fill=(92, 105, 118, 255),
            )
            draw.rounded_rectangle(
                (bar_x, bar_y, bar_x + 95, bar_y + 7),
                radius=4,
                fill=(235, 238, 242, 255),
            )
            draw.ellipse(
                (bar_x + 87, bar_y - 5, bar_x + 101, bar_y + 9),
                fill=(255, 255, 255, 255),
            )

            draw.text(
                (bar_x, bar_y + 20),
                "0:00",
                fill=(190, 200, 210, 255),
                font=regular_font,
            )
            draw.text(
                (bar_x + bar_w - 65, bar_y + 20),
                song.duration,
                fill=(190, 200, 210, 255),
                font=regular_font,
            )

            # Player controls matching the reference image.
            controls = [
                ("|<<", 650),
                ("Ⅱ", 755),
                (">>|", 860),
            ]
            for label, x in controls:
                draw.text(
                    (x, 420),
                    label,
                    fill=(245, 248, 250, 255),
                    font=icon_font,
                )

            draw.text(
                (text_x, 485),
                "🔊",
                fill=(220, 230, 240, 255),
                font=regular_font,
            )
            draw.rounded_rectangle(
                (text_x + 45, 498, text_x + 540, 504),
                radius=3,
                fill=(95, 108, 120, 255),
            )

            # Small signature, matching the existing bot branding area.
            draw.text(
                (105, 92),
                "APPLE MUSIC <<3",
                fill=(255, 255, 255, 230),
                font=self.signature_font,
            )

            bg.convert("RGB").save(output, quality=95)

            try:
                os.remove(temp)
            except OSError:
                pass

            return output

        except Exception:
            return config.DEFAULT_THUMB
