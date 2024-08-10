#!/usr/bin/env python3

# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Volker Mische <volker.mische@gmail.com>

import json, os, sys, unicodedata
from collections import defaultdict
from pathlib import PurePath
from urllib import parse
import textwrap

import mistune
# Make sure the `mdtoyt` can be found in the parent directory.
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from mdtoyt import YouTubeRenderer

TITLE_PREFIX = 'FOSS4G 2022'
CONF_HASHTAG = '#foss4g2022'
# The keys match the conference acronym of the schedule.
TYPE_HASHTAG = {
    'foss4g-2022': '#generaltrack',
    'foss4g-2022-academic-track': '#academictrack',
}
# List of that talks that were not recorded or presented.
TALKS_MISSING = ['GURC7K', 'BWTAEY', '79KBL9', 'GYAWLJ', 'WFLJKB', 'JAERFJ']
# List of files that should be ignored.
IGNORE_FILES = [
    # File with better audio is available.
    '/osgeo/foss4gvideos/2022-08-26/Room_6/14 Sini P\u00f6yt\u00e4niemi - VIDEO ORIGINALE HA BUCHI DI AUDIO.mp4',
    '/osgeo/foss4gvideos/2022-08-26/Room_6/14 nota.txt',
    '/osgeo/foss4gvideos/2022-08-26/Room_9/5 non presente.txt',
    '/osgeo/foss4gvideos/2022-08-24/Room_Hall_3A/6 no speaker.txt',
]
# List of talks where the actual speaker isn't the one mentioned in pretalx
ADDITIONAL_PERSONS = {
    'SDG9K7': 'JulienOsman',
    'JDGNJD': 'Anca Anghelea',
    'XPCXBQ': 'Lorenzo Natali',
    'XHUGFC': 'Antoine Drabble',
}

YOUTUBE_MAX_TITLE_LENGTH = 100
YOUTUBE_MAX_DESCRIPTION_LENGTH = 5000

# From https://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-normalize-in-a-python-unicode-string/518232#518232
def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

# From https://stackoverflow.com/questions/12897374/get-unique-values-from-a-list-in-python/37163210#37163210
def unique(data):
    '''Returns a new list with the same order, but only unique items.'''
    return list(dict.fromkeys(data))

def ensure_https(url):
    '''Make sure that URL is HTTP and not HTTPS.'''
    parsed = parse.urlparse(url)
    https = parse.ParseResult('https', *parsed[1:])
    return https.geturl()

def to_hashtag(data):
    '''Removes all whitespace, replaces ampersands and prepends a hash.'''
    if data is None:
        return ''
    else:
        return '#' + ''.join(data.split()).replace('&', 'And')

def replace_illegal_characters(data):
    '''Replaces all characters that are not legal in YouTube titles or
    descriptions.'''
    return data.replace('<', '＜').replace('>', '＞')


# Mapping between the room in the schedule.json and the uploaded files.
ROOM_MAPPING = {
    'Auditorium': 'Auditorium',
    'Room 4': 'Room_4',
    'Modulo 0': 'Room_6',
    'Room 9' : 'Room_9',
    'Room Hall 3A': 'Room_Hall_3A',
    'Room Limonaia': 'Room_Limonaia',
    'Room Modulo 3': 'Room_Modulo_3A',
    'Room Onice': 'Room_Onice',
    'Room Verde': 'Room_Verde',
}

def process_file_list(video_files_list):
    '''Convert a list of files into a nested dictionary.'''
    result = defaultdict(lambda: defaultdict(list))
    with open(video_files_list) as video_files:
        for video_file in video_files:
            # Extract the day and the room from the file path.
            day, room = PurePath(video_file).parts[-3:-1]
            result[day][room].append(video_file.strip())
    return result

def process_day(day, conf_prefix, videos):
    date = day['date']
    for room in day['rooms']:
        if room in ['General online', 'Academic online']:
            continue

        room_name = ROOM_MAPPING[room]

        # An offset for the case that a talk wasn't recorded or the file is not
        # found.
        talk_offset = 0
        for talk_counter, talk in enumerate(day['rooms'][room]):
            talk_id = talk['url'].split('/')[5]
            slug = talk['slug'].removeprefix(f'{conf_prefix}-')

            # There are thing scheduled (like a group photo) which isn't a
            # talk. Those don't have a persons associated with it.
            # Make an exception for the OSGeo AGM (XMJZGY).
            if not talk['persons'] and not talk_id == 'XMJZGY':
                talk_offset += 1
                continue


            if talk_id in TALKS_MISSING:
                talk_offset += 1
                continue

            try:
                while True:
                    video_file = videos[date][room_name][talk_counter - talk_offset]
                    if video_file in IGNORE_FILES:
                        talk_offset -= 1
                    else:
                        break
            except:
                video_file = 'ERROR: no video file found'

            title = replace_illegal_characters(f'{TITLE_PREFIX} | {talk["title"]}')
            # If the title is longer than the maximum size, preserve the
            # original title, so that it can be put into the description. That
            # should enable folks to find the viceo if they search for the full
            # title.
            if len(title) > YOUTUBE_MAX_TITLE_LENGTH:
                title = textwrap.shorten(title, width=YOUTUBE_MAX_TITLE_LENGTH, placeholder='…')
                maybe_full_title = talk["title"]
            else:
                maybe_full_title = None

            persons_list = unique([person['public_name'] for person in talk['persons']])
            if talk_id in ADDITIONAL_PERSONS:
                persons_list.insert(0, ADDITIONAL_PERSONS[talk_id])
            persons = '\n'.join(persons_list)

            markdown_renderer = mistune.create_markdown(renderer=YouTubeRenderer())
            abstract = markdown_renderer(talk['abstract']).strip()

            pretalx_link = ensure_https(talk['url'])

            hashtags_list = [CONF_HASHTAG, TYPE_HASHTAG[conf_prefix], to_hashtag(talk['track'])]
            hashtags = '\n'.join(hashtags_list)

            description_list = [
                maybe_full_title,
                abstract,
                persons,
                pretalx_link,
                hashtags
            ]
            # The full title may not be set, hence filter it out.
            description = '\n\n'.join(filter(None, description_list))
            description = replace_illegal_characters(description)
            # If the description is too long, then shorten the abstract, but
            # keep the rest the same.
            if len(description) > YOUTUBE_MAX_DESCRIPTION_LENGTH:
                max_abstract_len = YOUTUBE_MAX_DESCRIPTION_LENGTH - (len(description) - len(abstract))
                abstract = textwrap.shorten(description, width=max_abstract_len, placeholder='…')
                description_list = [
                    maybe_full_title,
                    abstract,
                    persons,
                    pretalx_link,
                    hashtags
                ]
                # The full title may not be set, hence filter it out.
                description = '\n\n'.join(filter(None, description_list))

            metadata = {
                'video_file': video_file,
                'persons': ', '.join(persons_list),
                'pretalx_id': talk_id,
                'title': title,
                'description': description,
            }

            print(json.dumps(metadata))


def main(argv=None):
    if argv is None:
        argv = sys.argv

    if len(argv) != 4:
        print("Usage: {} schedule.json schedule_academic.json video-files.list".format(argv[0]))
        sys.exit(1)

    schedule_filename = argv[1]
    schedule_academic_filename = argv[2]
    video_files_list = argv[3]

    videos = process_file_list(video_files_list)

    with open(schedule_filename, 'r') as schedule_file:
        schedule_json = json.load(schedule_file)
        conf_prefix = schedule_json['schedule']['conference']['acronym']
        # First day of the talks is the third day of the conference
        process_day(schedule_json['schedule']['conference']['days'][2], conf_prefix, videos)
        process_day(schedule_json['schedule']['conference']['days'][3], conf_prefix, videos)
        process_day(schedule_json['schedule']['conference']['days'][4], conf_prefix, videos)

    with open(schedule_academic_filename, 'r') as schedule_academic_file:
        schedule_academic_json = json.load(schedule_academic_file)
        conf_prefix = schedule_academic_json['schedule']['conference']['acronym']
        # First day of the talks is the third day of the conference
        process_day(schedule_academic_json['schedule']['conference']['days'][2], conf_prefix, videos)
        process_day(schedule_academic_json['schedule']['conference']['days'][3], conf_prefix, videos)
        process_day(schedule_academic_json['schedule']['conference']['days'][4], conf_prefix, videos)
        #print(conference_day1)

if __name__ == '__main__':
    sys.exit(main())
