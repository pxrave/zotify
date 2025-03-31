#! /usr/bin/env python3

"""
Zotify
It's like youtube-dl, but for that other music platform.
"""

import argparse

from zotify.app import client
from zotify.config import CONFIG_VALUES

def main():
    parser = argparse.ArgumentParser(prog='zotify',
        description='A music and podcast downloader needing only Python and FFMPEG.')
    
    parser.add_argument('-ns', '--no-splash',
                        action='store_true',
                        help='Suppress the splash screen when loading')
    parser.add_argument('-c', '--config', '--config-location',
                        type=str,
                        dest='config_location',
                        help='Specify a directory containing a Zotify `config.json` file to load settings')
    parser.add_argument('-u', '--username',
                        type=str,
                        dest='username',
                        help='Account username')
    parser.add_argument('--token',
                        type=str,
                        dest='token',
                        help='Authentication token')
    
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('urls',
                       type=str,
                       # action='extend',
                       default='',
                       nargs='*',
                       help='Download track(s), album(s), playlist(s), podcast episode(s), or artist(s) specified by the URL(s) passed as a command line argument(s). If an artist\'s URL is given, all albums by the specified artist will be downloaded. Can take multiple URLs as multiple arguments.')
    group.add_argument('-l', '--liked',
                       dest='liked_songs',
                       action='store_true',
                       help='Download all Liked Songs on your account')
    group.add_argument('-f', '--followed',
                       dest='followed_artists',
                       action='store_true',
                       help='Download all songs by all followed artists')
    group.add_argument('-p', '--playlist',
                       action='store_true',
                       help='Download playlist(s) saved by your account (interactive)')
    group.add_argument('-s', '--search',
                       type=str,
                       nargs='?',
                       const=' ',
                       help='Search tracks/albums/artists/playlists based on argument (interactive)')
    group.add_argument('-d', '--download',
                       type=str,
                       help='Download all tracks/albums/episodes/playlists URLs within the file passed as argument')
    
    for configkey in CONFIG_VALUES:
        parser.add_argument(*CONFIG_VALUES[configkey]['arg'],
                            type=CONFIG_VALUES[configkey]['type'],
                            dest=configkey.lower(),
                            default=None,
                            # help='Specify the value of the ['+configkey+'] config value'
                            )
    
    parser.set_defaults(func=client)
    
    args = parser.parse_args()
    args.func(args)
    print("\n")


if __name__ == '__main__':
    main()
