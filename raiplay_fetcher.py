#!/usr/bin/env python3

"""
            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
                    Version 2, December 2004

 Copyright (C) 2017 Giuseppe Crinò <giuscri@gmail.com>

 Everyone is permitted to copy and distribute verbatim or modified
 copies of this license document, and changing it is allowed as long
 as the name is changed.

            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

  0. You just DO WHAT THE FUCK YOU WANT TO.
"""

from requests import get
from sys import argv, exit
from re import match
from math import ceil
from subprocess import run
from uuid import uuid4

URL_FMT = '[http://|https://].*[^/]$'

def fetch_index(page_url, hd=True):
    """
    Fetch the video index, where all the URL
    are stored - that's how the legit player does.
    """

    assert match(URL_FMT, base_url), '{}...'.format(base_url[:10])

    r = get(page_url, params='json')
    if not r.ok: fail(b'')

    master_url = r.json()['video']['contentUrl']
    r = get(master_url)
    if not r.ok: fail(b'')

    master_index = tuple(filter(lambda l: not l.startswith('#'), r.text.strip().split('\n')))

    index_url = master_index[0]
    if len(master_index) > 1 and hd: index_url = master_index[1]

    r = get(index_url)
    if not r.ok: fail(b'')

    lines = r.text.strip().split('\n')
    return tuple(filter(lambda l: not l.startswith('#'), lines))

def fail(blob):
    """
    Write the retrieved blob to a file, and exit.
    Mostly for debugging purpose, depending when
    that happens.
    """

    random_fname = str(uuid4())
    with open('/tmp/{}'.format(random_fname), 'wb') as f:
        f.write(blob)

    print('\n*** :(, Written current blob to /tmp/{}'.format(random_fname))

    exit(-1)

def draw_progress_bar(i, n, w=60):
    progress = ceil(i / n * w)
    loading_fmt = '*** Getting segment #{{:0{}}} of {{}} ['.format(len(str(n)))

    print(loading_fmt.format(i, n), end='')
    print('>' * progress, end='')
    print('.' * (w - progress), end='')
    print(']', end='\r')

if __name__ == '__main__':
    from argparse import ArgumentParser

    help = {
        'url': 'URL of the official video page, http://www.raiplay.it/video/*',
        'file': 'Where to store the download',
        'nohd': "If you don't want high definition content",
    }

    argument_parser = ArgumentParser(description='Download videos from raiplay.it')
    argument_parser.add_argument('url', help=help['url'])
    argument_parser.add_argument('file', help=help['file'])
    argument_parser.add_argument('--nohd', help=help['nohd'], action='store_true')
    args = argument_parser.parse_args()

    base_url, output_fname, hd = args.url, args.file, not args.nohd

    index = fetch_index(base_url, hd=hd)
    n = len(index)
    blob = b''

    for i, url in enumerate(index, start=1):
        draw_progress_bar(i, n)

        r = get(url)
        if not r.ok: fail(blob)
        blob += r.content

    # Try to run the ffmpeg conversion
    cmd = 'ffmpeg -i - -c copy {} 2>/dev/null'.format(output_fname)
    process = run(cmd, shell=True, input=blob)
    if process.returncode != 0: fail(blob)

    print('\n*** :)')
