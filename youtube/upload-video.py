#!/usr/bin/env python3

# SPDX-License-Identifier: MIT

# This script uploads a video to YouTube. It's set to private and subscribers
# are not notified.
# It's based on the [`upload_video.py` example from# `python-youtube`](https://github.com/sns-sdks/python-youtube/blob/280d8077c33c9920e0c5c4f9583e64e30b67f892/examples/clients/upload_video.py)
#
# It takes a single JSON object piped into the script as input. That object
# must have a `title`, `description` and `video_file` key. Additional keys are
# ignored.
#
# You also need to specify an access token in order to upload a video. Such a
# token can be retrieved with the `get-token.py` script from this repository.
# You need to specify it in an environment variable called
# `YOUTUBE_ACCESS_TOKEN`.
#
# And example invocation of this script might look like this:
#
#     YOUTUBE_ACCESS_TOKEN='ya29.a0AXooCgsMQcaKptaaOmy8ZmWu2ohKc85YS2l1l6D89AhIx9Qbz5sZqHZnM06qnfXRu71hxq-loEePjq3V-S2j6lT1pcrzTP_sFgH4AcbiEKB0OvQ656OJlUN2V0vIxjgpYN2LXel9j5LdyldPrYQNPcTtJBtplFeIcN0DaCgYKAXwSARESFQHGX2Mi6b7fvQFL09DLSvX1LyDpKA0171' echo '{"title": "vmx test video upload", "description": "This is a test from vmx if the upload script works", "video_file": "/tmp/video.mp4"}' | ./upload_video.py
#
# If you have a file that contains one of those JSON object per line, e.g. like
# the output from the FOSS4G 2022 `schedule-to-metadata.py` script, you can use
# `xargs` to process the whole file:
#
# cat metadata.ndjson | YOUTUBE_ACCESS_TOKEN='ya29.a0AXooCgsMQcaKptaaOmy8ZmWu2ohKc85YS2l1l6D89AhIx9Qbz5sZqHZnM06qnfXRu71hxq-loEePjq3V-S2j6lT1pcrzTP_sFgH4AcbiEKB0OvQ656OJlUN2V0vIxjgpYN2LXel9j5LdyldPrYQNPcTtJBtplFeIcN0DaCgYKAXwSARESFQHGX2Mi6b7fvQFL09DLSvX1LyDpKA0171' xargs --delimiter='\n' --replace={} sh -c "echo '{}' | ./upload_video.py"

import json, os, sys
from operator import itemgetter

from pyyoutube import Client
from pyyoutube.media import Media
from pyyoutube.models import Video, VideoSnippet, VideoStatus


def print_progress_bar(progress, total):
    """A simplistic progress bar"""
    print(f'\r{round((progress/total)*100,0)} %', end='\r')
    if progress == total:
        print()

def upload_video(token, title, description, file_path):
    """Uploads a video to YouTube."""
    print(
        f"Uploading ideo file `{file_path}`
    )
    cli = Client(access_token=token)

    body = Video(
        snippet=VideoSnippet(
            title=title.replace("&apos;", "'"),
            description=description.replace("&apos;", "'"),
        ),
        status=VideoStatus(
            privacyStatus="private",
            license="creativeCommon"
        ),
    )
    if os.path.exists(file_path) == False:
        # @tkardi 2.08.2024: maybe the filename has unescaped spaces
        file_path = r"" + file_path
    media = Media(filename=file_path)

    upload = cli.videos.insert(
        body=body,
        media=media,
        parts=["snippet", "status"],
        notify_subscribers=False,
    )

    response = None

    while response is None:
        #print(f"Uploading video...")
        status, response = upload.next_chunk()
        if status is not None:
#            print(f"Uploading video progress: {status.progress()}...")
            print_progress_bar(round(status.progress() * 100, 0), 100)

    video = Video.from_dict(response)

    print(
        f"\nVideo file `{file_path}` was successfully uploaded to https://youtu.be/{video.id}"
    )


def main(data=None):
    """The input `data` is a single JSON object consisting of the keys `title`,
    `description` and `video_file`.
    """
    if data is None:
        if sys.stdin.isatty():
            print(
                f'Usage: echo \'{{"title": …, "description": …, "video_file": …}}\' | upload_video.py'
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
        title, description, video_file = itemgetter(
            "title", "description", "video_file"
        )(parsed)
    except KeyError:
        print(
            "JSON object must contain the keys `title`, `description` and `video_file`."
        )
        return 4

    upload_video(token, title, description, video_file)


if __name__ == "__main__":
    sys.exit(main())
