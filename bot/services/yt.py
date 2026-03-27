from __future__ import annotations
import logging
import os
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from bot import Bot

from yt_dlp import YoutubeDL
from yt_dlp.downloader import get_suitable_downloader
from youtubesearchpython import VideosSearch

from bot.config.models import YtModel
from bot.player.enums import TrackType
from bot.player.track import Track
from bot.services import Service as _Service
from bot import errors


class YtService(_Service):
    def __init__(self, bot: Bot, config: YtModel):
        self.bot = bot
        self.config = config
        self.name = "yt"
        self.hostnames = []
        self.is_enabled = self.config.enabled
        self.error_message = ""
        self.warning_message = ""
        self.help = ""
        self.hidden = False

    def initialize(self):
        self._ydl_config = {
            "skip_download": True,
            "format": "m4a/bestaudio/best[protocol!=m3u8_native]/best",
            "socket_timeout": 5,
            "logger": logging.getLogger("root"),
        }

        if self.config.cookiefile_path and os.path.isfile(self.config.cookiefile_path):
            self._ydl_config |= {"cookiefile": self.config.cookiefile_path}

    def download(self, track: Track, file_path: str) -> None:
        info = track.extra_info
        if not info:
            super().download(track, file_path)
            return
        with YoutubeDL(self._ydl_config) as ydl:
            dl = get_suitable_downloader(info)(ydl, self._ydl_config)
            dl.download(file_path, info)

    def get(
        self,
        url: str,
        extra_info: Optional[Dict[str, Any]] = None,
        process: bool = False,
    ) -> List[Track]:
        if not (url or extra_info):
            raise errors.InvalidArgumentError()
        with YoutubeDL(self._ydl_config) as ydl:
            info = extra_info or ydl.extract_info(url, process=False)
            info_type = info.get("_type", None)

            if info_type == "url" and not info.get("ie_key"):
                return self.get(info["url"], process=False)

            elif info_type == "playlist":
                tracks: List[Track] = []
                for entry in info.get("entries", []):
                    tracks += self.get("", extra_info=entry, process=False)
                return tracks

            if not process:
                track_name = info.get("title") or "Unknown"
                uploader = info.get("uploader")
                if uploader:
                    track_name += f" - {uploader}"
                return [
                    Track(service=self.name, extra_info=info, name=track_name, type=TrackType.Dynamic)
                ]

            try:
                stream = ydl.process_ie_result(info)
            except Exception:
                raise errors.ServiceError()

            url = stream.get("url")
            if not url:
                raise errors.ServiceError()

            title = stream.get("title") or "Unknown"
            uploader = stream.get("uploader")
            if uploader:
                title += f" - {uploader}"

            format = stream.get("ext") or "mp3"
            type = TrackType.Live if stream.get("is_live") else TrackType.Default

            return [
                Track(
                    service=self.name,
                    url=url,
                    name=title,
                    format=format,
                    type=type,
                    extra_info=stream
                )
            ]

    def search(self, query: str) -> List[Track]:
        search = VideosSearch(query, limit=300).result()
        if search.get("result"):
            tracks: List[Track] = []
            for video in search["result"]:
                tracks.append(
                    Track(service=self.name, url=video.get("link") or "", type=TrackType.Dynamic)
                )
            return tracks
        else:
            raise errors.NothingFoundError("")
