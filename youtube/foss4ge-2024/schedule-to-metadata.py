#!/usr/bin/env python3

# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Volker Mische <volker.mische@gmail.com>

import json, os, sys, unicodedata
from collections import defaultdict
from pathlib import PurePath
from urllib import parse, request
import re
import argparse


import mistune
# Make sure the `mdtoyt` can be found in the parent directory.
sys.path.insert(1, os.path.join(sys.path[0], '..'))
from mdtoyt import YouTubeRenderer

TITLE_PREFIX = 'FOSS4GE 2024'
CONF_HASHTAG = '#foss4ge2024'
ACADEMICTRACK_NAME = "Academic track"
# The keys match the conference acronym of the schedule.
TYPE_HASHTAG = {
    'foss4g-europe-2024': '#generaltrack',
}
# List of that talks that were not recorded or presented.
TALKS_MISSING = [

]
# List of files that should be ignored.
IGNORE_FILES = [
    # File with better audio is available.
]
# List of talks where the actual speaker isn't the one mentioned in pretalx
ADDITIONAL_PERSONS = {

}
# Mapping between the room in the schedule.json and the uploaded files.
ROOM_MAPPING = {
    'Destination Earth (Van46 ring)': 'Destination_Earth',
    'GEOCAT (301)': 'GEOCAT',
    'LAStools (327)': 'LAStools',
    'QFieldCloud (246)': 'QFieldCloud',
    'Omicum': 'Omicum',
}

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
    '''Removes all whitespace and prepends a hash.

    Additionally turns the outbound hashtag to CamelCase
    '''
    if data is None:
        return ''
    else:
        return '#' + ''.join(x for x in data.title() if not x.isspace() and x.isalnum())

def process_file_list(video_files_list):
    '''Convert a list of files into a nested dictionary.'''
    result = defaultdict(lambda: defaultdict(dict))
    with open(video_files_list) as video_files:
        for row in video_files:
            # Extract the day and the room from the file path.
            pretalx_link, video_file = row.split(';')
            pretalx_id = PurePath(pretalx_link).parts[-1]
            day, room = PurePath(video_file).parts[-3:-1]
            result[day][room][pretalx_id] = video_file.strip()
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
            talk_id = talk['url'].split('/')[-2]
            slug = talk['slug'].removeprefix(f'{conf_prefix}-')

            # There are thing scheduled (like a group photo) which isn't a
            # talk. Those don't have a persons associated with it.
            # Make an exception for the OSGeo AGM (XMJZGY).
#            if not talk['persons'] and not talk_id == 'XMJZGY':
#                talk_offset += 1
#                continue

            # @tkardi 1.08.2024: For FOSS4GE2024 we keep only track of the
            # do_not_record == False
            if talk['do_not_record'] == True:
                continue

#            if talk_id in TALKS_MISSING:
#                talk_offset += 1
#                continue

            try:
                video_file = videos[date][room_name][talk_id]
            except KeyError as ke:
                video_file = 'ERROR: no video file found'

            title = f'{TITLE_PREFIX} | {talk["title"]}'

            persons_list = unique([person['public_name'] for person in talk['persons']])
            if talk_id in ADDITIONAL_PERSONS:
                persons_list.insert(0, ADDITIONAL_PERSONS[talk_id])
            persons = '\\n'.join(persons_list)

            markdown_renderer = mistune.create_markdown(renderer=YouTubeRenderer())
            abstract = markdown_renderer(talk['abstract']).strip()

            pretalx_link = ensure_https(talk['url'])

            try:
                if talk['track'] == ACADEMICTRACK_NAME:
                    type_hashtag = ''
                else:
                    type_hashtag = TYPE_HASHTAG[conf_prefix]
            except NameError:
                pass

            hashtags_list = [CONF_HASHTAG, type_hashtag, to_hashtag(talk['track'])]
            hashtags = '\\n'.join(hashtags_list)



            description = f'{abstract}\\n\\n{persons}\\n\\n{pretalx_link}\\n\\nRoom: {room} @ {talk["date"]}\\n\\n{hashtags}'

            metadata = {
                'video_file': video_file,
                'persons': ', '.join(persons_list),
                'pretalx_id': talk_id,
                'title': title,
                'description': description,
            }

            print(json.dumps(metadata))


def main(**kwargs):

    videos = process_file_list(kwargs['videofiles_list'])
    print (videos)
    for schedule_filename in kwargs['schedule']:
        if not os.path.exists(schedule_filename):
            assert schedule_filename.startswith('http://') or schedule_filename.startswith('https://'), \
                f'Did not os.path find schedule {schedule_filename}, nor it is an URL'
            with request.urlopen(schedule_filename) as r:
                schedule_json = json.loads(r.read())
            if kwargs['cache_schedule'] == True:
                path = os.path.dirname(os.path.abspath(__file__))
                p = PurePath(schedule_filename).parts[-2]
                with open(os.path.join(path, f'{p}.json'), 'w') as fp:
                    fp.write(json.dumps(schedule_json))

        else:
            with open(schedule_filename, 'r') as schedule_file:
                schedule_json = json.load(schedule_file)

        conf_prefix = schedule_json['schedule']['conference']['acronym']
        schedule_days = schedule_json['schedule']['conference']['days']
        for schedule_day in schedule_days:
            process_day(schedule_day, conf_prefix, videos)

        #print(conference_day1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog=__file__)
    parser.add_argument(
        "-s", "--schedule",
        help="Schedule filename. If many provide as many as needed separated by space.",
        nargs="+",
        required=True
    )
    parser.add_argument(
        "-v", "--videofiles-list",
        help="Path to preformatted list of videofiles.",
        required=True
    )
    parser.add_argument(
        "-c", "--cache-schedule",
        help="Save the schedule file locally", action=argparse.BooleanOptionalAction,
        default=False
    )

    args = parser.parse_args()
    kwargs = args.__dict__

    sys.exit(main(**kwargs))