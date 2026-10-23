import json

from urllib.parse import urlparse, parse_qs

def get_youtube_resource_type(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    if parsed_url.path == "/playlist" and "list" in query_params:
        return "playlist"

    if parsed_url.path == "/watch" and "v" in query_params:
        return "video"

    return "other"


def extract_embedded_json(soup, markers):
    decoder = json.JSONDecoder()

    for script in soup.find_all("script"):
        script_text = script.string or script.get_text()

        if not script_text:
            continue

        for marker in markers:
            marker_index = script_text.find(marker)

            if marker_index == -1:
                continue

            json_text = script_text[
                marker_index + len(marker):
            ].lstrip()

            try:
                data, _ = decoder.raw_decode(json_text)
                return data
            except json.JSONDecodeError:
                continue

    return None


def find_youtube_like_count(value):
    if isinstance(value, dict):
        if value.get("accessibilityId") == "id.video.like.button":
            accessibility_text = value.get("accessibilityText")

            if isinstance(accessibility_text, str):
                digits = "".join(
                    character
                    for character in accessibility_text
                    if character.isdigit()
                )

                if digits:
                    return int(digits)

        for child in value.values():
            like_count = find_youtube_like_count(child)

            if like_count is not None:
                return like_count

    elif isinstance(value, list):
        for child in value:
            like_count = find_youtube_like_count(child)

            if like_count is not None:
                return like_count

    return None


def extract_youtube_metadata(soup):
    player_response = extract_embedded_json(
        soup,
        [
            "var ytInitialPlayerResponse = ",
            "ytInitialPlayerResponse = ",
            'window["ytInitialPlayerResponse"] = ',
        ]
    )

    initial_data = extract_embedded_json(
        soup,
        [
            "var ytInitialData = ",
            "ytInitialData = ",
        ]
    )

    metadata = {
        "channel": None,
        "duration_seconds": None,
        "view_count": None,
        "upload_date": None,
        "like_count": None,
    }

    if player_response is not None:
        video_details = player_response.get("videoDetails", {})

        microformat = (
            player_response
            .get("microformat", {})
            .get("playerMicroformatRenderer", {})
        )

        duration = video_details.get("lengthSeconds")
        views = video_details.get("viewCount")

        metadata["channel"] = video_details.get("author")
        metadata["duration_seconds"] = int(duration) if duration else None
        metadata["view_count"] = int(views) if views else None
        metadata["upload_date"] = microformat.get("uploadDate")

    if initial_data is not None:
        metadata["like_count"] = find_youtube_like_count(initial_data)

    return metadata