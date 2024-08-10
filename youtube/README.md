Get recorded talks uploaded to YouTube
======================================

These tools were originally created in order to get the recorded talk of the [FOSS4G 2022] published on [YouTube]. Though some should also be generally useful for other conferences.

 - [foss4g-2022]: Scripts to generate the correct metadata for the FOSS4G 2022 videos.
 - [mdtoyt.py]: Tool and library to convert [Markdown] into a format that renders nicely as YouTube video description.
     You need to have [`mistune`] installed in order to use it. It's a command line utility as well as a library that exports `YouTubeRenderer` which can be used by `mistune`.
 - [get-token.py]: Tool to get a YouTube token in order to upload files. It requires a client secret JSON file. Detailed steps on how to generate such a file can be found at the top of the source file.
 - [upload-video.py]: Tool to upload a video to YouTube once you have a valid access token.
 - [pipe-each-line.py]: Tool to process a list of videos you'd like to upload.

For ease of use a `requirements.txt` is provided that install all dependencies that are needed for any of the scripts. So before you execute any of them you can create a virtualenv with everything you need:

```console
python -m venv venv
. ./venv/bin/activate
pip install --requirement requirements.txt
```

The code is licensed under the [MIT License](../LICENSE) unless otherwise noted.

[FOSS4G 2022]: https://2022.foss4g.org/
[YouTube]: https://youtube.com/
[foss4g-2022]: ./foss4g-2022
[mdtoyt.py]: ./mdtoyt.py
[get-token.py]: ./get-token.py
[upload-video.py]: ./upload-video.py
[pipe-each-line.py]: ./pipe-each-line.py
[Markdown]: https://en.wikipedia.org/wiki/Markdown
[`mistune`]: https://pypi.org/project/mistune/
