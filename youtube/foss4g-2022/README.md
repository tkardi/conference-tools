Generate metadata for FOSS4G 2022 videos
========================================

The [`schedule-to-metadata.py` script] is specific to the FOSS4G 2022. It might still be an inspiration for other conferences on how to get the video files and the metadata from [pretalx] combined and processed in a YouTube friendly way.

The video files were the starting point, they were already organized by day, room and then sorted in the order the talks were given. For the metadata the `schedule.json` export from pretalx was used.

Here are the steps I've taken in order to generate the metadata files. I've also checked all files that are used as input, so that the final output can be reproduced (as some steps need special privileges not everyone has).

 - Download the schedules: the general track and the academic track were organized as if they were two separate conferences, hence there's a separate `schedule.json` for each of them.
     ```console
     wget https://talks.osgeo.org/foss4g-2022/schedule/export/schedule.json
     wget https://talks.osgeo.org/foss4g-2022-academic-track/schedule/export/schedule.json --output-document=schedule_academic.json
     ```
 - Generate a file list of all the videos. That list can also be used to verify that all videos are part of the final output:
     ```console
     ssh ownload.osgeo.org 'find /osgeo/foss4gvideos -type f | sort -V' > foss4gvideos.list
     ```
 - Generate the actual metadata for the videos. It will contain the path to the actual video file, a title and a description formatted suitable for YouTube descriptions. For easier sanity checking and development purpose it also contains the pretalx ID and the persons associated with the talk (according to pretalx).
     ```console
     python schedule-to-metadata.py schedule.json schedule_academic.json foss4gvideos.list > metadata.ndjson
     ```
     The output is JSON, where each line contains the entry for a single talk. It can be used with the [`video-upload.py` script].

[`schedule-to-metadata.py` script]: ./schedule-to-metadata.py
[pretalx]: https://pretalx.com/
[`video-upload.py` script]: ../video-upload.py
