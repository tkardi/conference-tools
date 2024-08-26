Generate metadata for FOSS4G 2022 videos and uploading them
===========================================================

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
 - Upload the videos based on the metadata. The scripts for that are not conference specific, hence in the parent directory. Use [`video-upload.py`] in combination with the [`pipe-each-line.py` script]. You also need a valid YouTube Access Token, see the [`get-token.py` script] for more information on how to get one:
     ```console
     cat metadata.ndjson | YOUTUBE_ACCESS_TOKEN='<YOUR_TOKEN>' ./pipe-each-line.py python3 -u ./upload-video.py 2>&1 | tee ./upload.log
     ```
     The `upload.log` file will also contain the progress indicator, but a `cat` will show just the JSON output, which contains the YouTube ID of the uploaded video, which can be used for further processing. In case you e.g. want to add the YouTube ID to your metadata, you can combine the two files like that (after you've copied the output of `cat upload.log` into a file called `youtube_id.ndjson`):
     ```console
     jq -s 'group_by(.video_file) | map(reduce .[] as $x ({}; . * $x))' metadata.ndjson youtube_id.ndjson
     ```
     Credit for this `jq` one-liner goes to [this Stack Overflow answer].


[`schedule-to-metadata.py` script]: ./schedule-to-metadata.py
[pretalx]: https://pretalx.com/
[`video-upload.py`]: ../video-upload.py
[`pipe-each-line.py` script`]: ../pipe-each-line.py
[`get-token.py` script]: ../get-token.py
[this Stack Overflow answer]: https://stackoverflow.com/questions/49037956/how-to-merge-arrays-from-two-files-into-one-array-with-jq/49039053#49039053
