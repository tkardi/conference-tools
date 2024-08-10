#!/usr/bin/env python3

# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Volker Mische <volker.mische@gmail.com>

# This script takes piped files as input. Each line is then piped into the
# specified command.
#
# This can be used to upload several videos sequentially. For example:
#
#     cat metadata.ndjson | YOUTUBE_ACCESS_TOKEN='ya29.a0AXooCgsMQcaKptaaOmy8ZmWu2ohKc85YS2l1l6D89AhIx9Qbz5sZqHZnM06qnfXRu71hxq-loEePjq3V-S2j6lT1pcrzTP_sFgH4AcbiEKB0OvQ656OJlUN2V0vIxjgpYN2LXel9j5LdyldPrYQNPcTtJBtplFeIcN0DaCgYKAXwSARESFQHGX2Mi6b7fvQFL09DLSvX1LyDpKA0171' ./pipe-each-line.py ./upload-video.py

import subprocess, sys


def print_usage(command):
    print(
        "Usage: cat some-file.txt | {} program-to-run [args for the program]".format(
            command
        )
    )


def main(argv=None, data=None):
    """`data` needs to be an iterable that contains a string-like object."""
    if argv is None:
        argv = sys.argv

    if len(argv) < 2:
        print_usage()
        return 1

    if data is None:
        if sys.stdin.isatty():
            print_usage()
            return 2
        else:
            data = sys.stdin

    for line in data:
        command = argv[1:]
        subprocess.run(command, input=line.encode())


if __name__ == "__main__":
    sys.exit(main())
