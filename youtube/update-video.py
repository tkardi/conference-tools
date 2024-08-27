#!/usr/bin/env python3

# SPDX-License-Identifier: MIT

# This script updates a video on YouTube. During the development of the
# `upload-video.py` script, things changed quite a bit and videos where
# uploaded with different versions. This script was created in order to unify
# all videos. Usually you shouldn't need this script, it's only included in
# this repository in case you ever need to update a video for some reason.
# It's based on the [`upload_video.py` example from# `python-youtube`](https://github.com/sns-sdks/python-youtube/blob/280d8077c33c9920e0c5c4f9583e64e30b67f892/examples/clients/upload_video.py)
#
# This script needs (as opposed to the `upload-video.py` script) the OAuth
# scope `https://www.googleapis.com/auth/youtube`.
#
# It takes a single JSON object piped into the script as input. That object
# must have a `title`, `description`, `youtube_id` and `date` key. Additional
# keys are ignored.
#
#
# You also need to specify an access token in order to upload a video. Such a
# token can be retrieved with the `get-token.py` script from this repository.
# You need to specify it in an environment variable called
# `YOUTUBE_ACCESS_TOKEN`.
#
# And example invocation of this script might look like this:
#
#     YOUTUBE_ACCESS_TOKEN='ya29.a0AXooCgsMQcaKptaaOmy8ZmWu2ohKc85YS2l1l6D89AhIx9Qbz5sZqHZnM06qnfXRu71hxq-loEePjq3V-S2j6lT1pcrzTP_sFgH4AcbiEKB0OvQ656OJlUN2V0vIxjgpYN2LXel9j5LdyldPrYQNPcTtJBtplFeIcN0DaCgYKAXwSARESFQHGX2Mi6b7fvQFL09DLSvX1LyDpKA0171'
#     echo '{"title": "vmx test video update", "description": "This is a test from vmx if the update script works", "youtube_id": "S9HdPi9Ikhk", "date": "2024-08-25"}' | ./upload-video.py
#
# If you have a file that contains one of those JSON object per line, e.g. like
# the output from the FOSS4G 2022 `schedule-to-metadata.py` script, you can use
# `./pipe-each-line.py` to process the whole file:
#
#     cat metadata.ndjson | YOUTUBE_ACCESS_TOKEN='ya29.a0AXooCgsMQcaKptaaOmy8ZmWu2ohKc85YS2l1l6D89AhIx9Qbz5sZqHZnM06qnfXRu71hxq-loEePjq3V-S2j6lT1pcrzTP_sFgH4AcbiEKB0OvQ656OJlUN2V0vIxjgpYN2LXel9j5LdyldPrYQNPcTtJBtplFeIcN0DaCgYKAXwSARESFQHGX2Mi6b7fvQFL09DLSvX1LyDpKA0171' ./pipe-each-line.py ./update-video.py
#
# If you want to see the progress and have the results piped into a file, use
# `tee` and unbuffered Python:
#
#     cat metadata.ndjson | YOUTUBE_ACCESS_TOKEN='ya29.a0AXooCgsMQcaKptaaOmy8ZmWu2ohKc85YS2l1l6D89AhIx9Qbz5sZqHZnM06qnfXRu71hxq-loEePjq3V-S2j6lT1pcrzTP_sFgH4AcbiEKB0OvQ656OJlUN2V0vIxjgpYN2LXel9j5LdyldPrYQNPcTtJBtplFeIcN0DaCgYKAXwSARESFQHGX2Mi6b7fvQFL09DLSvX1LyDpKA0171' ./pipe-each-line.py python3 -u ./update-video.py 2>&1 | tee /tmp/update.log

import json, os, sys
from operator import itemgetter

from pyyoutube import Client
from pyyoutube.media import Media
from pyyoutube.models import (
    Video,
    VideoRecordingDetails,
    VideoSnippet,
    VideoStatus,
)

YOUTUBE_MAX_TITLE_LENGTH = 100
YOUTUBE_MAX_DESCRIPTION_LENGTH = 5000

CATEGORY_ID_EDUCATION = 27

def upload_video(token, title, description, youtube_id, date):
    """Updates a video on YouTube."""
    cli = Client(access_token=token)

    body = Video(
        id=youtube_id,
        snippet=VideoSnippet(
            title=title,
            description=description,
            defaultLanguage="en",
            defaultAudioLanguage="en",
            categoryId = str(CATEGORY_ID_EDUCATION),
        ),
        status=VideoStatus(
            privacyStatus="private",
            license="creativeCommon",
            selfDeclaredMadeForKids=False,
            embeddable=True,
            publicStatsViewable=True,
        ),
        recordingDetails=VideoRecordingDetails(recordingDate=date),
    )
    response = cli.videos.update(
        body=body,
        parts=["snippet", "status", "recordingDetails"],
        return_json=True,
    )

    print(response)


def main(data=None):
    """The input `data` is a single JSON object that contains the keys `title`,
    `description`, `youtube_id` and `date`.
    """
    if data is None:
        if sys.stdin.isatty():
            print(
                f'Usage: echo \'{{"title": …, "description": …, "youtube_id": …, "date": …}}\' | upload-video.py'
            )
            return 1
        else:
            data = sys.stdin.read()

    try:
        token = os.environ["YOUTUBE_ACCESS_TOKEN"]
    except KeyError:
        print(
            "The `YOUTUBE_ACCESS_TOKEN` environment variable must be set. "
            "Retrieve it via the `get_token.py` script."
        )
        return 2

    parsed = json.loads(data)
    try:
        parsed = json.loads(data)
    except:
        print("Cannot parse JSON input.")
        return 3

    try:
        title, description, youtube_id, date = itemgetter(
            "title",
            "description",
            "youtube_id",
            "date",
        )(parsed)
    except KeyError:
        print(
            "JSON object must contain the keys `title`, `description`, `youtube_id` and `date`."
        )
        return 4

    if len(title) > YOUTUBE_MAX_TITLE_LENGTH:
        print(
            f"Title must be less than {YOUTUBE_MAX_TITLE_LENGTH} characters long, it was {len(title)} characters long."
        )
        return 5

    if len(description) > YOUTUBE_MAX_DESCRIPTION_LENGTH:
        print(
            f"Description must be less than {YOUTUBE_MAX_DESCRIPTION_LENGTH} characters long, it was {len(description)} characters long."
        )
        return 6

    upload_video(token, title, description, youtube_id, date)


if __name__ == "__main__":
    sys.exit(main())
