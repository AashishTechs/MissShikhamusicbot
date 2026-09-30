<div align="center">

<img src="./Welcome.jpg" alt="Miss Shikha Music" width="420"/>

# 🎧 Miss Shikha Music

**Fast • Clean • Direct Voice-Chat Music**

A Telegram music bot focused on low-latency VC playback, a clean now-playing panel, queue controls, and direct YouTube streaming.

</div>

---

## ✨ Highlights

- ⚡ **Low-latency VC playback** with direct stream URLs
- 🚀 **Background next-track preparation** for smoother queue transitions
- 🎛️ **Systematic player panel** with seek, pause/resume, loop and shuffle
- 🎵 **YouTube search, links and playlists**
- 📋 **Queue management** with force play and playback controls
- 🎤 **Voice-command support**
- 📺 **Group and channel playback**
- 🖼️ **Dynamic thumbnails** with a clean now-playing layout

## 🎚️ Player Controls

The player panel is organized into four sections:

1. **Progress** — current playback position
2. **Primary controls** — 10s rewind, pause/resume, 10s forward
3. **Secondary controls** — loop and shuffle
4. **Support / Close** — quick links and player cleanup

## ⚡ Playback Architecture

The bot uses temporary direct YouTube stream URLs instead of downloading every track before playback.

For queued tracks, the bot can extract upcoming stream URLs in the background. When the next song starts, an already-prepared URL can be reused instead of waiting for another extraction.

## 🛠️ Run Locally

```bash
python -m Elevenyts
```

Configure the required environment variables from `sample.env` before starting.

## 🔐 Security

Keep tokens, MongoDB credentials, sessions, and YouTube cookies outside Git. The repository's MIT license and required upstream attribution are preserved.

---

<div align="center">

**🎶 Miss Shikha Music — Music beyond the wait.**

</div>
