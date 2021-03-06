#!/usr/bin/env python
# coding: utf-8
"""
instaLooter - Another API-less Instagram pictures and videos downloader

Usage:
    instaLooter <profile> [<directory>] [options]
    instaLooter hashtag <hashtag> [<directory>] [options]
    instaLooter post <post_token> [<directory>] [options]
    instaLooter (-h | --help | --version | --usage)

Arguments:
    <profile>                    The username of the profile to download
                                 videos and pictures from
    <hashtag>                    A hashtag to download pictures and videos
                                 from
    <post_token>                 Either the url or the code of a single post
                                 to download the picture or video from.

Options:
    -n NUM, --num-to-dl NUM      Maximum number of new files to download
    -j JOBS, --jobs JOBS         Number of parallel threads to use to
                                 download files [default: 16]
    -T TMPL, --template TMPL     A filename template to use to write the
                                 files (see *Template*). [default: {id}]
    -v, --get-videos             Get videos as well as photos
    -V, --videos-only            Get videos only
    -N, --new                    Only look for files newer than the ones
                                 in the destination directory (faster)
    -m, --add-metadata           Add date and caption metadata to downloaded
                                 pictures (requires PIL/Pillow and piexif)
    -q, --quiet                  Do not produce any output
    -t TIME, --time TIME         The time limit within which to download
                                 pictures and video (see *Time*)
    -h, --help                   Display this message and quit
    -c CRED, --credentials CRED  Credentials to login to Instagram with
                                 if needed [format: login[:password]]
    --version                    Show program version and quit
    -W WARNINGCTL                Change warning behaviour (same as python -W)
                                 [default: default]
    --traceback                  Print error traceback if any (debug).


Template:
    The default filename of the pictures and videos on Instagram doesn't show
    anything about the file you just downloaded. But using the -t argument
    allows you to give instaLooter a filename template, using the following
    format with brackets-enclosed ({}) variable names among:
    - ``id``* and ``code``² of the instagram id of the media
    - ``ownerid``*, ``username`` and ``fullname`` of the owner
    - ``datetime``*: the date and time of the post (YYYY-MM-DD hh:mm:ss)
    - ``date``*: the date of the post (YYYY-MM-DD)
    - ``width``* and ``height``*
    - ``likescount``* and ``commentscount``*

    *: use these only to quicken download, since fetching the others may take
    a tad longer (in particular in hashtag download mode).

    You are however to make sure that the generated filename is unique, so you
    should use at least id, code or datetime somewhere.
    Examples of acceptable values:
        - {username}.{datetime}
        - {username}-{likescount}-{width}x{height}.{id}

Time:
    The --time parameter can be given either a combination of start and stop
    date in ISO format (e.g. 2016-12-21:2016-12-18, 2015-03-07:, :2016-08-02)
    or a special value among: "thisday", "thisweek", "thismonth", "thisyear".

    Edges are included in the time frame, so if using the following value:
    `--time 2016-05-10:2016-04-03`, then all medias will be downloaded
    including the ones posted the 10th of May 2016 and the 3rd of April 2016.
"""
from __future__ import (
    absolute_import,
    unicode_literals,
)

import docopt
import os
import sys
import getpass
import hues
import warnings
import traceback

from . import __version__
from .core import InstaLooter
from .utils import get_times_from_cli, console, wrap_warnings

WARNING_ACTIONS = {'error', 'ignore', 'always', 'default', 'module', 'once'}

@wrap_warnings
def main(argv=sys.argv[1:]):
    """Run from the command line interface.
    """
    args = docopt.docopt(__doc__, argv, version='instaLooter {}'.format(__version__))

    if args['-W'] not in WARNING_ACTIONS:
        print("Unknown warning action: {}".format(args['-W']))
        print("   available action: {}".format(', '.join(WARNING_ACTIONS)))
        return 1

    with warnings.catch_warnings():
        warnings.simplefilter(args['-W'])

        # if args['<hashtag>'] and not args['--credentials']:
        #    warnings.warn("#hashtag downloading requires an Instagram account.")
        #    return 1

        if args['<post_token>'] is not None:
            args['--get-videos'] = True

        looter = InstaLooter(
            directory=os.path.expanduser(args.get('<directory>') or os.getcwd()),
            profile=args['<profile>'],hashtag=args['<hashtag>'],
            add_metadata=args['--add-metadata'], get_videos=args['--get-videos'],
            videos_only=args['--videos-only'], jobs=int(args['--jobs']),
            template=args['--template']
        )

        try:

            if args['--credentials']:
                credentials = args['--credentials'].split(':', 1)
                login = credentials[0]
                password = credentials[1] if len(credentials) > 1 else getpass.getpass()
                looter.login(login, password)
                if not args['--quiet']:
                    hues.success('Logged in.')

            if args['--time']:
                timeframe = get_times_from_cli(args['--time'])
            else:
                timeframe = None

        except ValueError as ve:
            console.error(ve)
            if args["--traceback"]:
               traceback.print_exc()
            return 1

        try:
            post_token = args['<post_token>']
            if post_token is None:
                media_count = int(args['--num-to-dl']) if args['--num-to-dl'] else None
                looter.download(
                    media_count=media_count,
                    with_pbar=not args['--quiet'], timeframe=timeframe,
                    new_only=args['--new'],
                )
            else:
                if 'insta' in post_token:
                    post_token = looter._extract_code_from_url(post_token)
                looter.download_post(post_token)

        except Exception as e:
            console.error(e)
            if args["--traceback"]:
               traceback.print_exc()
            looter.__del__()
            return 1

        except KeyboardInterrupt:
            looter.__del__()
            return 1

        else:
            return 0


if __name__ == "__main__":
    main()
