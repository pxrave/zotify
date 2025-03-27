import datetime
import math
import os
import platform
import re
import subprocess
from pathlib import Path, PurePath
from typing import List, Tuple

import music_tag
import requests

from zotify.const import ARTIST, GENRE, TRACKTITLE, ALBUM, YEAR, DISCNUMBER, TRACKNUMBER, ARTWORK, \
    WINDOWS_SYSTEM, ALBUMARTIST, TOTALTRACKS, TOTALDISCS, EXT_MAP, LYRICS, COMPILATION
from zotify.zotify import Zotify


def create_download_directory(download_path: str) -> None:
    """ Create directory and add a hidden file with song ids """
    Path(download_path).mkdir(parents=True, exist_ok=True)

    # add hidden file with song ids
    hidden_file_path = PurePath(download_path).joinpath('.song_ids')
    if Zotify.CONFIG.get_disable_directory_archives():
        return
    if not Path(hidden_file_path).is_file():
        with open(hidden_file_path, 'w', encoding='utf-8') as f:
            pass


def get_previously_downloaded() -> List[str]:
    """ Returns list of all time downloaded songs """

    ids = []
    archive_path = Zotify.CONFIG.get_song_archive_location()

    if Path(archive_path).exists():
        with open(archive_path, 'r', encoding='utf-8') as f:
            ids = [line.strip().split('\t')[0] for line in f.readlines()]

    return ids


def add_to_archive(song_id: str, filename: str, author_name: str, song_name: str) -> None:
    """ Adds song id to all time installed songs archive """
    
    archive_path = Zotify.CONFIG.get_song_archive_location()
    
    if Path(archive_path).exists():
        with open(archive_path, 'a', encoding='utf-8') as file:
            file.write(f'{song_id}\t{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\t{author_name}\t{song_name}\t{filename}\n')
    else:
        with open(archive_path, 'w', encoding='utf-8') as file:
            file.write(f'{song_id}\t{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\t{author_name}\t{song_name}\t{filename}\n')


def add_to_m3u8(mode: str, song_duration: float, song_name: str, song_filename: PurePath, m3u_dir: PurePath | None = None) -> str | None:
    """ Adds song to a .m3u8 playlist, returning the song label in m3u8 format"""
    
    if m3u_dir is None:
        m3u_dir = Zotify.CONFIG.get_root_path()
    
    if mode == "liked" and Zotify.CONFIG.get_liked_songs_archive_m3u8() and \
    (not Path(m3u_dir / "Liked Songs.m3u8").exists() or "justCreatedLikedSongsM3U8" in globals()):
        m3u_path = m3u_dir / "Liked Songs.m3u8"
        global justCreatedLikedSongsM3U8; justCreatedLikedSongsM3U8 = True # hacky, terrible, truly awful: too bad!
    else:
        m3u_path = m3u_dir / (Zotify.datetime_launch + "_zotify.m3u8")
    
    if not Path(m3u_path).exists():
        with open(m3u_path, 'w', encoding='utf-8') as file:
            file.write("#EXTM3U\n\n")
    
    song_label_m3u = None
    with open(m3u_path, 'a', encoding='utf-8') as file:
        song_label_m3u = f"#EXTINF:{int(song_duration)}, {song_name}\n"
        file.write(song_label_m3u)
        file.write(f"{song_filename}\n\n")
    return song_label_m3u


def fetch_m3u8_songs(m3u_path: PurePath) -> list[str] | None:
    """ Fetches the songs and associated file paths in an .m3u8 playlist"""
    
    if not Path(m3u_path).exists():
        return
    
    with open(m3u_path, 'r', encoding='utf-8') as file:
        linesraw = file.readlines()[2:-1]
        # group by song and filepath
        # songsgrouped = []
        # for i in range(len(linesraw)//3):
        #     songsgrouped.append(linesraw[3*i:3*i+3])
    return linesraw


def get_directory_song_ids(download_path: str) -> List[str]:
    """ Gets song ids of songs in directory """
    
    song_ids = []
    
    hidden_file_path = PurePath(download_path).joinpath('.song_ids')
    
    if Path(hidden_file_path).is_file() and not Zotify.CONFIG.get_disable_directory_archives():
        with open(hidden_file_path, 'r', encoding='utf-8') as file:
            song_ids.extend([line.strip().split('\t')[0] for line in file.readlines()])
    
    return song_ids


def add_to_directory_song_ids(download_path: str, song_id: str, filename: str, author_name: str, song_name: str) -> None:
    """ Appends song_id to .song_ids file in directory """
    
    hidden_file_path = PurePath(download_path).joinpath('.song_ids')
    if Zotify.CONFIG.get_disable_directory_archives():
        return
    # not checking if file exists because we need an exception
    # to be raised if something is wrong
    with open(hidden_file_path, 'a', encoding='utf-8') as file:
        file.write(f'{song_id}\t{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\t{author_name}\t{song_name}\t{filename}\n')


def get_downloaded_song_duration(filename: str) -> float:
    """ Returns the downloaded file's duration in seconds """
    
    command = ['ffprobe', '-show_entries', 'format=duration', '-i', f'{filename}']
    output = subprocess.run(command, capture_output=True)
    
    duration = re.search(r'[\D]=([\d\.]*)', str(output.stdout)).groups()[0]
    duration = float(duration)
    
    return duration


def split_input(selection) -> List[str]:
    """ Returns a list of inputted strings """
    inputs = []
    if '-' in selection:
        for number in range(int(selection.split('-')[0]), int(selection.split('-')[1]) + 1):
            inputs.append(number)
    else:
        selections = selection.split(',')
        for i in selections:
            inputs.append(i.strip())
    return inputs


def splash() -> str:
    """ Displays splash screen """
    return """
███████╗ ██████╗ ████████╗██╗███████╗██╗   ██╗
╚══███╔╝██╔═══██╗╚══██╔══╝██║██╔════╝╚██╗ ██╔╝
  ███╔╝ ██║   ██║   ██║   ██║█████╗   ╚████╔╝ 
 ███╔╝  ██║   ██║   ██║   ██║██╔══╝    ╚██╔╝  
███████╗╚██████╔╝   ██║   ██║██║        ██║   
╚══════╝ ╚═════╝    ╚═╝   ╚═╝╚═╝        ╚═╝   
    """


def clear() -> None:
    """ Clear the console window """
    if platform.system() == WINDOWS_SYSTEM:
        os.system('cls')
    else:
        os.system('clear')


def set_audio_tags(filename, artists: List[str], genres: List[str], name, album_name, album_artist, release_year, disc_number, track_number, total_tracks, total_discs, compilation: int, lyrics: List[str] | None) -> None:
    """ sets music_tag metadata """
    tags = music_tag.load_file(filename)
    tags[ALBUMARTIST] = album_artist
    tags[ARTIST] = conv_artist_format(artists)
    tags[GENRE] = conv_genre_format(genres)
    tags[TRACKTITLE] = name
    tags[ALBUM] = album_name
    tags[YEAR] = release_year
    tags[DISCNUMBER] = disc_number
    tags[TRACKNUMBER] = track_number
    
    if compilation:
        tags[COMPILATION] = compilation
    
    if Zotify.CONFIG.get_disc_track_totals():
        tags[TOTALTRACKS] = total_tracks
        if total_discs is not None:
            tags[TOTALDISCS] = total_discs
    
    ext = EXT_MAP[Zotify.CONFIG.get_download_format().lower()]
    if ext == "mp3" and not Zotify.CONFIG.get_disc_track_totals():
        # music_tag python library writes DISCNUMBER and TRACKNUMBER as X/Y instead of X for mp3
        # this method bypasses all internal formatting, probably not resilient against arbitrary inputs
        tags.set_raw("mp3", "TPOS", str(disc_number))
        tags.set_raw("mp3", "TRCK", str(track_number))
    
    if lyrics and Zotify.CONFIG.get_save_lyrics_tags():
        tags[LYRICS] = "".join(lyrics)
    
    tags.save()


def conv_artist_format(artists: List[str]) -> List[str] | str:
    """ Returns converted artist format """
    if Zotify.CONFIG.get_artist_delimiter() == "":
        return artists
    else:
        return Zotify.CONFIG.get_artist_delimiter().join(artists)


def conv_genre_format(genres: List[str]) -> List[str] | str:
    """ Returns converted genre format """
    if not Zotify.CONFIG.get_all_genres():
        return genres[0]

    if Zotify.CONFIG.get_genre_delimiter() == "":
        return genres
    else:
        return Zotify.CONFIG.get_genre_delimiter().join(genres)


def set_music_thumbnail(filename: PurePath, image_url, mode: str) -> None:
    """ Fetch an album cover image, set album cover tag, and save to file if desired """
    
    # jpeg format expected from request
    img = requests.get(image_url).content
    set_music_thumbnail_tag(filename, img)
    
    if not Zotify.CONFIG.get_album_art_jpg_file():
        return
    
    jpg_filename = 'cover.jpg' if '{album}' in Zotify.CONFIG.get_output(mode) else filename.stem + '.jpg'
    jpg_path = Path(filename).parent.joinpath(jpg_filename)
    
    if not jpg_path.exists():
        with open(jpg_path, 'wb') as jpg_file:
            jpg_file.write(img)


def set_music_thumbnail_tag(filename, img: bytes) -> None:
    """ Sets an image as a music file's cover artwork """
    
    tags = music_tag.load_file(filename)
    tags[ARTWORK] = img
    tags.save()


def regex_input_for_urls(search_input) -> Tuple[str, str, str, str, str, str]:
    """ Since many kinds of search may be passed at the command line, process them all here. """
    track_uri_search = re.search(
        r'^spotify:track:(?P<TrackID>[0-9a-zA-Z]{22})$', search_input)
    track_url_search = re.search(
        r'^(https?://)?open\.spotify\.com(?:/intl-\w+)?/track/(?P<TrackID>[0-9a-zA-Z]{22})(\?si=.+?)?$',
        search_input,
    )

    album_uri_search = re.search(
        r'^spotify:album:(?P<AlbumID>[0-9a-zA-Z]{22})$', search_input)
    album_url_search = re.search(
        r'^(https?://)?open\.spotify\.com(?:/intl-\w+)?/album/(?P<AlbumID>[0-9a-zA-Z]{22})(\?si=.+?)?$',
        search_input,
    )

    playlist_uri_search = re.search(
        r'^spotify:playlist:(?P<PlaylistID>[0-9a-zA-Z]{22})$', search_input)
    playlist_url_search = re.search(
        r'^(https?://)?open\.spotify\.com(?:/intl-\w+)?/playlist/(?P<PlaylistID>[0-9a-zA-Z]{22})(\?si=.+?)?$',
        search_input,
    )

    episode_uri_search = re.search(
        r'^spotify:episode:(?P<EpisodeID>[0-9a-zA-Z]{22})$', search_input)
    episode_url_search = re.search(
        r'^(https?://)?open\.spotify\.com(?:/intl-\w+)?/episode/(?P<EpisodeID>[0-9a-zA-Z]{22})(\?si=.+?)?$',
        search_input,
    )

    show_uri_search = re.search(
        r'^spotify:show:(?P<ShowID>[0-9a-zA-Z]{22})$', search_input)
    show_url_search = re.search(
        r'^(https?://)?open\.spotify\.com(?:/intl-\w+)?/show/(?P<ShowID>[0-9a-zA-Z]{22})(\?si=.+?)?$',
        search_input,
    )

    artist_uri_search = re.search(
        r'^spotify:artist:(?P<ArtistID>[0-9a-zA-Z]{22})$', search_input)
    artist_url_search = re.search(
        r'^(https?://)?open\.spotify\.com(?:/intl-\w+)?/artist/(?P<ArtistID>[0-9a-zA-Z]{22})(\?si=.+?)?$',
        search_input,
    )

    if track_uri_search is not None or track_url_search is not None:
        track_id_str = (track_uri_search
                        if track_uri_search is not None else
                        track_url_search).group('TrackID')
    else:
        track_id_str = None

    if album_uri_search is not None or album_url_search is not None:
        album_id_str = (album_uri_search
                        if album_uri_search is not None else
                        album_url_search).group('AlbumID')
    else:
        album_id_str = None

    if playlist_uri_search is not None or playlist_url_search is not None:
        playlist_id_str = (playlist_uri_search
                           if playlist_uri_search is not None else
                           playlist_url_search).group('PlaylistID')
    else:
        playlist_id_str = None

    if episode_uri_search is not None or episode_url_search is not None:
        episode_id_str = (episode_uri_search
                          if episode_uri_search is not None else
                          episode_url_search).group('EpisodeID')
    else:
        episode_id_str = None

    if show_uri_search is not None or show_url_search is not None:
        show_id_str = (show_uri_search
                       if show_uri_search is not None else
                       show_url_search).group('ShowID')
    else:
        show_id_str = None

    if artist_uri_search is not None or artist_url_search is not None:
        artist_id_str = (artist_uri_search
                         if artist_uri_search is not None else
                         artist_url_search).group('ArtistID')
    else:
        artist_id_str = None

    return track_id_str, album_id_str, playlist_id_str, episode_id_str, show_id_str, artist_id_str


def fix_filename(name):
    """
    Replace invalid characters on Linux/Windows/MacOS with underscores.
    List from https://stackoverflow.com/a/31976060/819417
    Trailing spaces & periods are ignored on Windows.
    >>> fix_filename("  COM1  ")
    '_ COM1 _'
    >>> fix_filename("COM10")
    'COM10'
    >>> fix_filename("COM1,")
    'COM1,'
    >>> fix_filename("COM1.txt")
    '_.txt'
    >>> all('_' == fix_filename(chr(i)) for i in list(range(32)))
    True
    """
    name = re.sub(r'[/\\:|<>"?*\0-\x1f]|^(AUX|COM[1-9]|CON|LPT[1-9]|NUL|PRN)(?![^.])|^\s|[\s.]$', "_", str(name), flags=re.IGNORECASE)
    
    maxlen = Zotify.CONFIG.get_max_filename_length()
    if maxlen and len(name) > maxlen:
        name = name[:maxlen]
    
    return name


def fmt_seconds(secs: float) -> str:
    val = math.floor(secs)
    
    s = math.floor(val % 60)
    val -= s
    val /= 60
    
    m = math.floor(val % 60)
    val -= m
    val /= 60
    
    h = math.floor(val)
    
    if h == 0 and m == 0 and s == 0:
        return "0s"
    elif h == 0 and m == 0:
        return f'{s}s'.zfill(2)
    elif h == 0:
        return f'{m}'.zfill(2) + ':' + f'{s}'.zfill(2)
    else:
        return f'{h}'.zfill(2) + ':' + f'{m}'.zfill(2) + ':' + f'{s}'.zfill(2)


def strptime_utc(dtstr) -> datetime.datetime:
    return datetime.datetime.strptime(dtstr[:-1], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc)
