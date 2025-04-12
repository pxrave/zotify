import json
import sys
from pathlib import Path, PurePath
from typing import Any


ROOT_PATH = 'ROOT_PATH'
ROOT_PODCAST_PATH = 'ROOT_PODCAST_PATH'
SKIP_EXISTING = 'SKIP_EXISTING'
SKIP_PREVIOUSLY_DOWNLOADED = 'SKIP_PREVIOUSLY_DOWNLOADED'
DOWNLOAD_FORMAT = 'DOWNLOAD_FORMAT'
BULK_WAIT_TIME = 'BULK_WAIT_TIME'
OVERRIDE_AUTO_WAIT = 'OVERRIDE_AUTO_WAIT'
CHUNK_SIZE = 'CHUNK_SIZE'
SPLIT_ALBUM_DISCS = 'SPLIT_ALBUM_DISCS'
DOWNLOAD_REAL_TIME = 'DOWNLOAD_REAL_TIME'
LANGUAGE = 'LANGUAGE'
DOWNLOAD_QUALITY = 'DOWNLOAD_QUALITY'
TRANSCODE_BITRATE = 'TRANSCODE_BITRATE'
SONG_ARCHIVE_LOCATION = 'SONG_ARCHIVE_LOCATION'
SAVE_CREDENTIALS = 'SAVE_CREDENTIALS'
CREDENTIALS_LOCATION = 'CREDENTIALS_LOCATION'
OUTPUT = 'OUTPUT'
PRINT_SPLASH = 'PRINT_SPLASH'
PRINT_SKIPS = 'PRINT_SKIPS'
PRINT_DOWNLOAD_PROGRESS = 'PRINT_DOWNLOAD_PROGRESS'
PRINT_ERRORS = 'PRINT_ERRORS'
PRINT_DOWNLOADS = 'PRINT_DOWNLOADS'
PRINT_API_ERRORS = 'PRINT_API_ERRORS'
TEMP_DOWNLOAD_DIR = 'TEMP_DOWNLOAD_DIR'
MD_DISC_TRACK_TOTALS = "MD_DISC_TRACK_TOTALS"
MD_SAVE_GENRES = 'MD_SAVE_GENRES'
MD_ALLGENRES = 'MD_ALLGENRES'
MD_GENREDELIMITER = 'MD_GENREDELIMITER'
MD_ARTISTDELIMITER = 'MD_ARTISTDELIMITER'
MD_SAVE_LYRICS = 'MD_SAVE_LYRICS'
PRINT_PROGRESS_INFO = 'PRINT_PROGRESS_INFO'
PRINT_WARNINGS = 'PRINT_WARNINGS'
RETRY_ATTEMPTS = 'RETRY_ATTEMPTS'
CONFIG_VERSION = 'CONFIG_VERSION'
DOWNLOAD_LYRICS = 'DOWNLOAD_LYRICS'
OUTPUT_PLAYLIST = 'OUTPUT_PLAYLIST'
OUTPUT_PLAYLIST_EXT = 'OUTPUT_PLAYLIST_EXT'
OUTPUT_LIKED_SONGS = 'OUTPUT_LIKED_SONGS'
OUTPUT_SINGLE = 'OUTPUT_SINGLE'
OUTPUT_ALBUM = 'OUTPUT_ALBUM'
DISABLE_DIRECTORY_ARCHIVES = 'DISABLE_DIRECTORY_ARCHIVES'
LYRICS_LOCATION = 'LYRICS_LOCATION'
FFMPEG_LOG_LEVEL = 'FFMPEG_LOG_LEVEL'
PRINT_URL_PROGRESS = 'PRINT_URL_PROGRESS'
PRINT_ALBUM_PROGRESS = 'PRINT_ALBUM_PROGRESS'
PRINT_ARTIST_PROGRESS = 'PRINT_ARTIST_PROGRESS'
PRINT_PLAYLIST_PROGRESS = 'PRINT_PLAYLIST_PROGRESS'
EXPORT_M3U8 = 'EXPORT_M3U8'
LIKED_SONGS_ARCHIVE_M3U8 = 'LIKED_SONGS_ARCHIVE_M3U8'
ALBUM_ART_JPG_FILE = 'ALBUM_ART_JPG_FILE'
MAX_FILENAME_LENGTH = 'MAX_FILENAME_LENGTH'
ALWAYS_CHECK_LYRICS = 'ALWAYS_CHECK_LYRICS'
M3U8_LOCATION = 'M3U8_LOCATION'
M3U8_REL_PATHS = 'M3U8_REL_PATHS'
DOWNLOAD_PARENT_ALBUM = 'DOWNLOAD_PARENT_ALBUM'


CONFIG_VALUES = {
    ROOT_PATH:                  { 'default': '~/Music/Zotify Music',    'type': str,    'arg': ('-rp', '--root-path'                     ,) },
    SAVE_CREDENTIALS:           { 'default': 'True',                    'type': bool,   'arg': ('--save-credentials'                     ,) },
    CREDENTIALS_LOCATION:       { 'default': '',                        'type': str,    'arg': ('--creds', '--credentials-location'      ,) },
    OUTPUT:                     { 'default': '',                        'type': str,    'arg': ('--output'                               ,) },
    OUTPUT_PLAYLIST:            { 'default': '{playlist}/{artist}_{song_name}',
                                  'type': str, 
                                  'arg': ('-op', '--output-playlist' ,) },
    OUTPUT_PLAYLIST_EXT:        { 'default': '{playlist}/{playlist_num}_{artist}_{song_name}',
                                  'type': str,  
                                  'arg': ('-oe', '--output-ext-playlist' ,) },
    OUTPUT_LIKED_SONGS:         { 'default': 'Liked Songs/{artist}_{song_name}',
                                  'type': str,
                                  'arg': ('-ol', '--output-liked-songs' ,) },
    OUTPUT_SINGLE:              { 'default': '{artist}/{album}/{artist} - {song_name}',
                                  'type': str,
                                  'arg': ('-os', '--output-single' ,) },
    OUTPUT_ALBUM:               { 'default': '{artist}/{album}/{album_num} - {artist} - {song_name}',
                                  'type': str,
                                  'arg': ('-oa', '--output-album' ,) },
    MAX_FILENAME_LENGTH:        { 'default': '0',                       'type': int,    'arg': ('--max-filename-length'                  ,) },
    EXPORT_M3U8:                { 'default': 'False',                   'type': bool,   'arg': ('-e, --export-m3u8'                      ,) },
    M3U8_LOCATION:              { 'default': '',                        'type': str,    'arg': ('--m3u8-location'                        ,) },
    M3U8_REL_PATHS:             { 'default': 'True',                    'type': bool,   'arg': ('--m3u8-relative-paths'                  ,) },
    LIKED_SONGS_ARCHIVE_M3U8:   { 'default': 'True',                    'type': bool,   'arg': ('--liked-songs-archive-m3u8'             ,) },
    ROOT_PODCAST_PATH:          { 'default': '~/Music/Zotify Podcasts', 'type': str,    'arg': ('-rpp', '--root-podcast-path'            ,) },
    TEMP_DOWNLOAD_DIR:          { 'default': '',                        'type': str,    'arg': ('-td', '--temp-download-dir'             ,) },
    DOWNLOAD_FORMAT:            { 'default': 'mp3',                    'type': str,    'arg': ('--codec', '--download-format'           ,) },
    DOWNLOAD_QUALITY:           { 'default': 'auto',                    'type': str,    'arg': ('-q', '--download-quality'               ,) },
    TRANSCODE_BITRATE:          { 'default': '2',                    'type': str,    'arg': ('-b', '--bitrate', '--transcode-bitrate' ,) },
    ALBUM_ART_JPG_FILE:         { 'default': 'False',                   'type': bool,   'arg': ('--album-art-jpg-file'                   ,) },
    SONG_ARCHIVE_LOCATION:      { 'default': '',                        'type': str,    'arg': ('--song-archive-location'                ,) },
    DISABLE_DIRECTORY_ARCHIVES: { 'default': 'False',                   'type': bool,   'arg': ('--disable-directory-archives'           ,) },
    SPLIT_ALBUM_DISCS:          { 'default': 'False',                   'type': bool,   'arg': ('--split-album-discs'                    ,) },
    DOWNLOAD_LYRICS:            { 'default': 'True',                    'type': bool,   'arg': ('--download-lyrics'                      ,) },
    LYRICS_LOCATION:            { 'default': '',                        'type': str,    'arg': ('--lyrics-location'                      ,) },
    ALWAYS_CHECK_LYRICS:        { 'default': 'False',                   'type': bool,   'arg': ('--always-check-lyrics'                  ,) },
    MD_DISC_TRACK_TOTALS:       { 'default': 'True',                    'type': bool,   'arg': ('--md-disc-track-totals'                 ,) },
    MD_SAVE_GENRES:             { 'default': 'False',                   'type': bool,   'arg': ('--md-save-genres'                       ,) },
    MD_ALLGENRES:               { 'default': 'False',                   'type': bool,   'arg': ('--md-allgenres'                         ,) },
    MD_GENREDELIMITER:          { 'default': ', ',                      'type': str,    'arg': ('--md-genredelimiter'                    ,) },
    MD_ARTISTDELIMITER:         { 'default': ', ',                      'type': str,    'arg': ('--md-artistdelimiter'                   ,) },
    MD_SAVE_LYRICS:             { 'default': 'True',                    'type': bool,   'arg': ('--md-save-lyrics'                       ,) },
    SKIP_EXISTING:              { 'default': 'True',                    'type': bool,   'arg': ('-ie', '--skip-existing'                 ,) },
    SKIP_PREVIOUSLY_DOWNLOADED: { 'default': 'False',                   'type': bool,   'arg': ('-ip', '--skip-previously-downloaded'    ,) },
    DOWNLOAD_PARENT_ALBUM:      { 'default': 'False',                   'type': bool,   'arg': ('--download-parent-album'                ,) },
    RETRY_ATTEMPTS:             { 'default': '1',                       'type': int,    'arg': ('--retry-attempts'                       ,) },
    BULK_WAIT_TIME:             { 'default': '31',                       'type': int,    'arg': ('--bulk-wait-time'                       ,) },
    OVERRIDE_AUTO_WAIT:         { 'default': 'False',                   'type': bool,   'arg': ('--override-auto-wait'                   ,) },
    CHUNK_SIZE:                 { 'default': '20000',                   'type': int,    'arg': ('--chunk-size'                           ,) },
    DOWNLOAD_REAL_TIME:         { 'default': 'False',                   'type': bool,   'arg': ('-rt', '--download-real-time'            ,) },
    LANGUAGE:                   { 'default': 'en',                      'type': str,    'arg': ('--language'                             ,) },
    PRINT_SPLASH:               { 'default': 'False',                   'type': bool,   'arg': ('--print-splash'                         ,) },
    PRINT_SKIPS:                { 'default': 'True',                    'type': bool,   'arg': ('--print-skips'                          ,) },
    PRINT_DOWNLOAD_PROGRESS:    { 'default': 'True',                    'type': bool,   'arg': ('--print-download-progress'              ,) },
    PRINT_URL_PROGRESS:         { 'default': 'True',                    'type': bool,   'arg': ('--print-url-progress'                   ,) },
    PRINT_ALBUM_PROGRESS:       { 'default': 'True',                    'type': bool,   'arg': ('--print-album-progress'                 ,) },
    PRINT_ARTIST_PROGRESS:      { 'default': 'True',                    'type': bool,   'arg': ('--print-artist-progress'                ,) },
    PRINT_PLAYLIST_PROGRESS:    { 'default': 'True',                    'type': bool,   'arg': ('--print-playlist-progress'              ,) },
    PRINT_PROGRESS_INFO:        { 'default': 'True',                    'type': bool,   'arg': ('--print-progress-info'                  ,) },
    PRINT_DOWNLOADS:            { 'default': 'True',                    'type': bool,   'arg': ('--print-downloads'                      ,) },
    PRINT_WARNINGS:             { 'default': 'True',                    'type': bool,   'arg': ('--print-warnings'                       ,) },
    PRINT_ERRORS:               { 'default': 'True',                    'type': bool,   'arg': ('--print-errors'                         ,) },
    PRINT_API_ERRORS:           { 'default': 'True',                    'type': bool,   'arg': ('--print-api-errors'                     ,) },
    FFMPEG_LOG_LEVEL:           { 'default': 'error',                   'type': str,    'arg': ('--ffmpeg-log-level'                     ,) },
}  


class Config:
    Values = {}
    
    @classmethod
    def load(cls, args) -> None:
        system_paths = {
            'win32': Path.home() / 'AppData/Roaming/Zotify',
            'linux': Path.home() / '.config/zotify',
            'darwin': Path.home() / 'Library/Application Support/Zotify'
        }
        if sys.platform not in system_paths:
            config_fp = Path.cwd() / '.zotify/config.json'
        else:
            config_fp = system_paths[sys.platform] / 'config.json'
        if args.config_location:
            config_fp = Path(args.config_location) / 'config.json'
        
        true_config_file_path = Path(config_fp).expanduser()
        
        # Load config from zconfig.json
        Path(PurePath(true_config_file_path).parent).mkdir(parents=True, exist_ok=True)
        if not Path(true_config_file_path).exists():
            with open(true_config_file_path, 'w', encoding='utf-8') as config_file:
                json.dump(cls.get_default_json(), config_file, indent=4)
        with open(true_config_file_path, encoding='utf-8') as config_file:
            jsonvalues = json.load(config_file)
            cls.Values = {}
            for key in CONFIG_VALUES:
                if key in jsonvalues:
                    cls.Values[key] = cls.parse_arg_value(key, jsonvalues[key])
        
        # Add default values for missing keys
        
        for key in CONFIG_VALUES:
            if key not in cls.Values:
                cls.Values[key] = cls.parse_arg_value(key, CONFIG_VALUES[key]['default'])
        
        # Override config from commandline arguments
        
        for key in CONFIG_VALUES:
            if key.lower() in vars(args) and vars(args)[key.lower()] is not None:
                cls.Values[key] = cls.parse_arg_value(key, vars(args)[key.lower()])
        
        if args.no_splash:
            cls.Values[PRINT_SPLASH] = False
    
    @classmethod
    def get_default_json(cls) -> Any:
        r = {}
        for key in CONFIG_VALUES:
            r[key] = CONFIG_VALUES[key]['default']
        return r
    
    @classmethod
    def parse_arg_value(cls, key: str, value: Any) -> Any:
        if type(value) == CONFIG_VALUES[key]['type']:
            return value
        if CONFIG_VALUES[key]['type'] == str:
            return str(value)
        if CONFIG_VALUES[key]['type'] == int:
            return int(value)
        if CONFIG_VALUES[key]['type'] == bool:
            if str(value).lower() in ['yes', 'true', '1']:
                return True
            if str(value).lower() in ['no', 'false', '0']:
                return False
            raise ValueError("Not a boolean: " + value)
        raise ValueError("Unknown Type: " + value)
    
    @classmethod
    def get(cls, key: str) -> Any:
        return cls.Values.get(key)
    
    @classmethod
    def get_root_path(cls) -> PurePath:
        if cls.get(ROOT_PATH) == '':
            root_path = PurePath(Path.home() / 'Music/Zotify Music/')
        else:
            root_path = PurePath(Path(cls.get(ROOT_PATH)).expanduser())
        Path(root_path).mkdir(parents=True, exist_ok=True)
        return root_path
    
    @classmethod
    def get_root_podcast_path(cls) -> PurePath:
        if cls.get(ROOT_PODCAST_PATH) == '':
            root_podcast_path = PurePath(Path.home() / 'Music/Zotify Podcasts/')
        else:
            root_podcast_path:str = cls.get(ROOT_PODCAST_PATH)
            if root_podcast_path[0] == ".":
                root_podcast_path = cls.get_root_path() / PurePath(root_podcast_path).relative_to(".")
            root_podcast_path = PurePath(Path(root_podcast_path).expanduser())
        Path(root_podcast_path).mkdir(parents=True, exist_ok=True)
        return root_podcast_path
    
    @classmethod
    def get_skip_existing(cls) -> bool:
        return cls.get(SKIP_EXISTING)
    
    @classmethod
    def get_skip_previously_downloaded(cls) -> bool:
        return cls.get(SKIP_PREVIOUSLY_DOWNLOADED)
    
    @classmethod
    def get_split_album_discs(cls) -> bool:
        return cls.get(SPLIT_ALBUM_DISCS)
    
    @classmethod
    def get_chunk_size(cls) -> int:
        return cls.get(CHUNK_SIZE)
    
    @classmethod
    def get_override_auto_wait(cls) -> bool:
        return cls.get(OVERRIDE_AUTO_WAIT)
    
    @classmethod
    def get_download_format(cls) -> str:
        return cls.get(DOWNLOAD_FORMAT)
    
    @classmethod
    def get_download_lyrics(cls) -> bool:
        return cls.get(DOWNLOAD_LYRICS)
    
    @classmethod
    def get_bulk_wait_time(cls) -> int:
        return cls.get(BULK_WAIT_TIME)
    
    @classmethod
    def get_language(cls) -> str:
        return cls.get(LANGUAGE)
    
    @classmethod
    def get_download_real_time(cls) -> bool:
        return cls.get(DOWNLOAD_REAL_TIME)
    
    @classmethod
    def get_download_quality(cls) -> str:
        return cls.get(DOWNLOAD_QUALITY)
    
    @classmethod
    def get_transcode_bitrate(cls) -> str:
        return cls.get(TRANSCODE_BITRATE)
    
    @classmethod
    def get_song_archive_location(cls) -> PurePath:
        if cls.get(SONG_ARCHIVE_LOCATION) == '':
            system_paths = {
                'win32': Path.home() / 'AppData/Roaming/Zotify',
                'linux': Path.home() / '.local/share/zotify',
                'darwin': Path.home() / 'Library/Application Support/Zotify'
            }
            if sys.platform not in system_paths:
                song_archive =  PurePath(Path.cwd() / '.zotify/.song_archive')
            else:
                song_archive = PurePath(system_paths[sys.platform] / '.song_archive')
        else:
            song_archive_path: str = cls.get(SONG_ARCHIVE_LOCATION)
            if song_archive_path[0] == ".":
                song_archive_path = cls.get_root_path() / PurePath(song_archive_path).relative_to(".")
            song_archive = PurePath(Path(song_archive_path).expanduser() / ".song_archive")
        Path(song_archive.parent).mkdir(parents=True, exist_ok=True)
        return song_archive
    
    @classmethod
    def get_save_credentials(cls) -> bool:
        return cls.get(SAVE_CREDENTIALS)
    
    @classmethod
    def get_credentials_location(cls) -> PurePath:
        if cls.get(CREDENTIALS_LOCATION) == '':
            system_paths = {
                'win32': Path.home() / 'AppData/Roaming/Zotify',
                'linux': Path.home() / '.local/share/zotify',
                'darwin': Path.home() / 'Library/Application Support/Zotify'
            }
            if sys.platform not in system_paths:
                credentials = PurePath(Path.cwd() / '.zotify/credentials.json')
            else:
                credentials = PurePath(system_paths[sys.platform] / 'credentials.json')
        else:
            credentials_path: str = cls.get(CREDENTIALS_LOCATION)
            if credentials_path[0] == ".":
                credentials_path = cls.get_root_path() / PurePath(credentials_path).relative_to(".")
            credentials = PurePath(Path(credentials_path).expanduser() / 'credentials.json')
        Path(credentials.parent).mkdir(parents=True, exist_ok=True)
        return credentials
    
    @classmethod
    def get_temp_download_dir(cls) -> str | PurePath:
        if cls.get(TEMP_DOWNLOAD_DIR) == '':
            return ''
        temp_download_path:str = cls.get(TEMP_DOWNLOAD_DIR)
        if temp_download_path[0] == ".":
            temp_download_path = cls.get_root_path() / PurePath(temp_download_path).relative_to(".")
        return PurePath(Path(temp_download_path).expanduser())
    
    @classmethod
    def get_disc_track_totals(cls) -> bool:
        return cls.get(MD_DISC_TRACK_TOTALS)
    
    @classmethod
    def get_save_genres(cls) -> bool:
        return cls.get(MD_SAVE_GENRES)
    
    @classmethod
    def get_all_genres(cls) -> bool:
        return cls.get(MD_ALLGENRES)
    
    @classmethod
    def get_genre_delimiter(cls) -> str:
        return cls.get(MD_GENREDELIMITER)
    
    @classmethod
    def get_artist_delimiter(cls) -> str:
        return cls.get(MD_ARTISTDELIMITER)
    
    @classmethod
    def get_output(cls, mode: str) -> str:
        v = cls.get(OUTPUT)
        if v:
            return v
        
        if mode == 'playlist':
            v = cls.get(OUTPUT_PLAYLIST)
        elif mode == 'extplaylist':
            v = cls.get(OUTPUT_PLAYLIST_EXT)
        elif mode == 'liked':
            v = cls.get(OUTPUT_LIKED_SONGS)
        elif mode == 'single':
            v = cls.get(OUTPUT_SINGLE)
        elif mode == 'album':
            v = cls.get(OUTPUT_ALBUM)
        else:
            raise ValueError()
        
        if cls.get_split_album_discs():
            return str(PurePath(v).parent / 'Disc {disc_number}' / PurePath(v).name)
        return v
    
    @classmethod
    def get_retry_attempts(cls) -> int:
        return cls.get(RETRY_ATTEMPTS)
    
    @classmethod
    def get_disable_directory_archives(cls) -> bool:
        return cls.get(DISABLE_DIRECTORY_ARCHIVES)
    
    @classmethod
    def get_lyrics_location(cls) -> PurePath | None:
        if cls.get(LYRICS_LOCATION) == '':
            # Use OUTPUT path as default location
            return None
        else:
            lyrics_path = cls.get(LYRICS_LOCATION)
            if lyrics_path[0] == ".":
                lyrics_path = cls.get_root_path() / PurePath(lyrics_path).relative_to(".")
            lyrics_path = PurePath(Path(lyrics_path).expanduser())
        
        Path(lyrics_path).mkdir(parents=True, exist_ok=True)
        return lyrics_path
    
    @classmethod
    def get_ffmpeg_log_level(cls) -> str:
        level = cls.get(FFMPEG_LOG_LEVEL)
        if level not in {"trace", "verbose", "info", "warning", "error", "fatal", "panic", "quiet"}:
            raise ValueError()
        return level
    
    @classmethod
    def get_show_download_pbar(cls) -> bool:
        return cls.get(PRINT_DOWNLOAD_PROGRESS)
    
    @classmethod
    def get_show_url_pbar(cls) -> bool:
        return cls.get(PRINT_URL_PROGRESS)
    
    @classmethod
    def get_show_album_pbar(cls) -> bool:
        return cls.get(PRINT_ALBUM_PROGRESS)
    
    @classmethod
    def get_show_artist_pbar(cls) -> bool:
        return cls.get(PRINT_ARTIST_PROGRESS)
    
    @classmethod
    def get_show_playlist_pbar(cls) -> bool:
        return cls.get(PRINT_PLAYLIST_PROGRESS)
    
    @classmethod
    def get_show_any_progress(cls) -> bool:
        return cls.get(PRINT_DOWNLOAD_PROGRESS) or cls.get(PRINT_URL_PROGRESS) \
           or cls.get(PRINT_ALBUM_PROGRESS) or cls.get(PRINT_ARTIST_PROGRESS) \
        or cls.get(PRINT_PLAYLIST_PROGRESS)
    
    @classmethod
    def get_export_m3u8(cls) -> bool:
        return cls.get(EXPORT_M3U8)
    
    @classmethod
    def get_liked_songs_archive_m3u8(cls) -> bool:
        return cls.get(LIKED_SONGS_ARCHIVE_M3U8)
    
    @classmethod
    def get_album_art_jpg_file(cls) -> bool:
        return cls.get(ALBUM_ART_JPG_FILE)
    
    @classmethod
    def get_max_filename_length(cls) -> int:
        return cls.get(MAX_FILENAME_LENGTH)
    
    @classmethod
    def get_save_lyrics_tags(cls) -> bool:
        return cls.get(MD_SAVE_LYRICS)
    
    @classmethod
    def get_always_check_lyrics(cls) -> bool:
        return cls.get(ALWAYS_CHECK_LYRICS)
    
    @classmethod
    def get_m3u8_location(cls) -> PurePath | None:
        if cls.get(M3U8_LOCATION) == '':
            # Use OUTPUT path as default location
            return None
        else:
            m3u8_path = cls.get(M3U8_LOCATION)
            if m3u8_path[0] == ".":
                m3u8_path = cls.get_root_path() / PurePath(m3u8_path).relative_to(".")
            m3u8_path = PurePath(Path(m3u8_path).expanduser())
        
        Path(m3u8_path).mkdir(parents=True, exist_ok=True)
        return m3u8_path
    
    @classmethod
    def get_m3u8_relative_paths(cls) -> bool:
        return cls.get(M3U8_REL_PATHS)
    
    @classmethod
    def get_download_parent_album(cls) -> bool:
        return cls.get(DOWNLOAD_PARENT_ALBUM)
    