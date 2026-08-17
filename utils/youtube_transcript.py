"""
YouTube transcript fetcher using youtube-transcript-api (v1.x).
Used as the primary method for YouTube URLs on Streamlit Cloud,
where yt-dlp audio downloads are blocked (403 Forbidden) by YouTube's
datacenter IP detection.
"""

import re
from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url: str) -> str:
    """Extract the YouTube video ID from various URL formats."""
    patterns = [
        r"(?:v=|\/v\/|youtu\.be\/|\/embed\/|\/shorts\/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {url}")


def fetch_youtube_transcript(url: str, preferred_langs: list = None) -> str:
    """
    Fetch the transcript/captions for a YouTube video.

    Uses the youtube-transcript-api v1.x instance-based API.
    Tries the simple .fetch() shortcut first with preferred languages,
    then falls back to listing all transcripts and translating if needed.

    Args:
        url: YouTube video URL.
        preferred_langs: Language codes to try, in order. Defaults to ["en"].

    Returns:
        The full transcript text.

    Raises:
        RuntimeError: If no transcript is available for the video.
    """
    if preferred_langs is None:
        preferred_langs = ["en"]

    video_id = extract_video_id(url)
    ytt_api = YouTubeTranscriptApi()

    # ── Attempt 1: Direct fetch with preferred languages ──
    try:
        fetched = ytt_api.fetch(video_id, languages=preferred_langs)
        text = " ".join(snippet.text for snippet in fetched)
        if text.strip():
            return text.strip()
    except Exception:
        pass

    # ── Attempt 2: List all transcripts, try manual then generated ──
    try:
        transcript_list = ytt_api.list(video_id)
    except Exception as e:
        raise RuntimeError(
            f"Could not retrieve transcript list for video '{video_id}'. "
            f"The video may not have captions enabled. Error: {e}"
        )

    transcript = None

    # Try manually created first
    for lang in preferred_langs:
        try:
            transcript = transcript_list.find_manually_created_transcript([lang])
            break
        except Exception:
            pass

    # Fall back to auto-generated
    if transcript is None:
        for lang in preferred_langs:
            try:
                transcript = transcript_list.find_generated_transcript([lang])
                break
            except Exception:
                pass

    # Last resort: translate any available transcript to English
    if transcript is None:
        try:
            available = list(transcript_list)
            if available:
                transcript = available[0].translate("en")
        except Exception:
            pass

    if transcript is None:
        raise RuntimeError(
            f"No captions (manual or auto-generated) found for video '{video_id}'. "
            "Please upload the audio/video file directly instead."
        )

    fetched = transcript.fetch()
    text = " ".join(snippet.text for snippet in fetched)
    return text.strip()
