from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import requests
from youtubesearchpython import VideosSearch  # We'll reuse for search structure

if TYPE_CHECKING:
    from bot import Bot

from bot.config.models import ApModel
from bot.player.enums import TrackType
from bot.player.track import Track
from bot.services import Service as _Service
from bot import errors


class ApService(_Service):
    def __init__(self, bot: Bot, config: ApModel):
        self.bot = bot
        self.config = config
        self.name = "ap"
        self.hostnames = ["aparat.com", "www.aparat.com"]
        self.is_enabled = self.config.enabled
        self.error_message = ""
        self.warning_message = ""
        self.help = ""
        self.hidden = False

    def initialize(self):
        # Nothing to authenticate for now; just verify online if needed
        try:
            r = requests.get("https://www.aparat.com", timeout=5)
            if r.status_code != 200:
                raise errors.ServiceError("Aparat is unreachable")
        except Exception as e:
            logging.error(e)
            raise errors.ServiceError(e)

    def download(self, track: Track, file_path: str) -> None:
        url = track.url
        if not url:
            raise errors.ServiceError("No URL to download from")
        # For Aparat, just download file directly
        super().download(track, file_path)

    def get(
        self,
        url: str,
        extra_info: Optional[Dict[str, Any]] = None,
        process: bool = False,
    ) -> List[Track]:
        if not url:
            raise errors.InvalidArgumentError()
        try:
            # Extract video UID from URL
            video_id = url.rstrip("/").split("/")[-1]
            api_url = f"https://www.aparat.com/api/fa/v1/video/video/show/videohash/{video_id}?pr=1&mf=1&referer=direct"
            r = requests.get(api_url, timeout=5)
            if r.status_code != 200:
                raise errors.ServiceError("Failed to fetch Aparat video")
            data = r.json()["data"]["attributes"]["file_link_all"][0]
            video_url = data["urls"][0]
            quality = data.get("profile", "default")
            title = extra_info.get("title") if extra_info else f"Aparat video {video_id}"
            return [
                Track(
                    service=self.name,
                    url=video_url,
                    name=title,
                    format="mp4",
                    type=TrackType.Default,
                    extra_info={"quality": quality, "original_url": url},
                )
            ]
        except Exception as e:
            logging.error(e)
            raise errors.ServiceError(e)

    def search(self, query: str) -> List[Track]:
        try:
            r = requests.get(
                f"https://www.aparat.com/etc/api/videoBySearch/text/{query}/perpage/50", timeout=5
            )
            if r.status_code != 200:
                raise errors.ServiceError("Failed to search Aparat")
            data = r.json()
            tracks: List[Track] = []
            for t in data.get("videobysearch", []):
                tracks.append(
                    Track(
                        service=self.name,
                        url=f"https://www.aparat.com/v/{t['uid']}",
                        name=t["title"],
                        type=TrackType.Dynamic,
                        extra_info={"duration": t["duration"], "channel": t["sender_name"]},
                    )
                )
            if not tracks:
                raise errors.NothingFoundError()
            return tracks
        except Exception as e:
            logging.error(e)
            raise errors.ServiceError(e)
