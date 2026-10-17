"""YouTube Data API v3 thin client — official API only, no scraping."""
import re
import requests

API = "https://www.googleapis.com/youtube/v3"


class YTClient:
    def __init__(self, api_key: str):
        self.key = api_key

    def _get(self, path, **params):
        params["key"] = self.key
        r = requests.get(f"{API}/{path}", params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def resolve_channel(self, url_or_id: str) -> dict:
        """Accept channel URL, handle, or raw ID -> channel resource."""
        url_or_id = url_or_id.strip()
        # raw channel id
        if re.fullmatch(r"UC[\w-]{22}", url_or_id):
            cid = url_or_id
        else:
            m = re.search(r"youtube\.com/(?:@([\w.\-]+)|channel/(UC[\w-]{22})|c/([\w.\-]+)|user/([\w.\-]+))", url_or_id)
            if not m:
                raise ValueError("Channel URL/handle/ID samajh nahi aaya: " + url_or_id)
            handle, cid, custom, user = m.groups()
            if cid:
                pass
            else:
                q = handle or custom or user
                # try handle lookup first
                try:
                    data = self._get("channels", part="id", forHandle=q)
                    cid = data["items"][0]["id"]
                except (IndexError, KeyError):
                    data = self._get("search", part="id", q=q, type="channel", maxResults=1)
                    cid = data["items"][0]["id"]["channelId"]
        data = self._get("channels", part="snippet,statistics,contentDetails", id=cid)
        return data["items"][0]

    def list_videos(self, channel: dict, max_results: int = 50) -> list:
        """Latest videos from the channel's uploads playlist, with stats."""
        uploads = channel["contentDetails"]["relatedPlaylists"]["uploads"]
        out, token = [], None
        while len(out) < max_results:
            pl = self._get("playlistItems", part="contentDetails",
                           playlistId=uploads, maxResults=min(50, max_results - len(out)),
                           pageToken=token or "")
            ids = [i["contentDetails"]["videoId"] for i in pl.get("items", [])]
            if not ids:
                break
            vids = self._get("videos", part="snippet,statistics,contentDetails",
                             id=",".join(ids))
            out.extend(vids.get("items", []))
            token = pl.get("nextPageToken")
            if not token:
                break
        return out[:max_results]
