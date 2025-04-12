from pathlib import Path, PurePath
import math
import time
import uuid
from typing import Any, Tuple, List

from librespot.metadata import TrackId
import ffmpy

from zotify.const import TRACKS, ALBUM, GENRES, NAME, ITEMS, DISC_NUMBER, TRACK_NUMBER, TOTAL_TRACKS, IS_PLAYABLE, ARTISTS, IMAGES, URL, \
    RELEASE_DATE, ID, TRACKS_URL, FOLLOWED_ARTISTS_URL, SAVED_TRACKS_URL, TRACK_STATS_URL, CODEC_MAP, EXT_MAP, DURATION_MS, \
    HREF, ARTISTS, WIDTH, COMPILATION, ALBUM_TYPE
from zotify.config import EXPORT_M3U8
from zotify.termoutput import Printer, PrintChannel
from zotify.utils import fix_filename, set_audio_tags, set_music_thumbnail, create_download_directory, add_to_m3u8, fetch_m3u8_songs, \
    get_directory_song_ids, add_to_directory_song_ids, get_previously_downloaded, add_to_archive, fmt_seconds
from zotify.zotify import Zotify
import traceback
from zotify.loader import Loader


def get_saved_tracks() -> list:
    """ Returns user's saved tracks """
    songs = []
    offset = 0
    limit = 50

    while True:
        resp = Zotify.invoke_url_with_params(
            SAVED_TRACKS_URL, limit=limit, offset=offset)
        offset += limit
        songs.extend(resp[ITEMS])
        if len(resp[ITEMS]) < limit:
            break

    return songs


def get_followed_artists() -> list:
    """ Returns user's followed artists """
    artists = []
    resp = Zotify.invoke_url(FOLLOWED_ARTISTS_URL)[1]
    for artist in resp[ARTISTS][ITEMS]:
        artists.append(artist)
    
    return artists


def get_song_info(song_id) -> Tuple[List[str], List[Any], str, str, Any, Any, Any, Any, Any, Any, Any, Any, Any, int]:
    """ Retrieves metadata for downloaded songs """
    with Loader(PrintChannel.PROGRESS_INFO, "Fetching track information..."):
        (raw, info) = Zotify.invoke_url(f'{TRACKS_URL}?ids={song_id}&market=from_token')
    
    if not TRACKS in info:
        raise ValueError(f'Invalid response from TRACKS_URL:\n{raw}')
    
    try:
        artists = []
        for data in info[TRACKS][0][ARTISTS]:
            artists.append(data[NAME])
        
        album_name = info[TRACKS][0][ALBUM][NAME]
        album_artist = info[TRACKS][0][ALBUM][ARTISTS][0][NAME]
        album_compilation = 1 if COMPILATION in info[TRACKS][0][ALBUM][ALBUM_TYPE] else 0
        name = info[TRACKS][0][NAME]
        release_year = info[TRACKS][0][ALBUM][RELEASE_DATE].split('-')[0]
        disc_number = info[TRACKS][0][DISC_NUMBER]
        track_number = info[TRACKS][0][TRACK_NUMBER]
        total_tracks = info[TRACKS][0][ALBUM][TOTAL_TRACKS]
        scraped_song_id = info[TRACKS][0][ID]
        is_playable = info[TRACKS][0][IS_PLAYABLE]
        duration_ms = info[TRACKS][0][DURATION_MS]
        
        image = info[TRACKS][0][ALBUM][IMAGES][0]
        for i in info[TRACKS][0][ALBUM][IMAGES]:
            if i[WIDTH] > image[WIDTH]:
                image = i
        image_url = image[URL]
        
        return artists, info[TRACKS][0][ARTISTS], album_name, album_artist, name, image_url, release_year, disc_number, track_number, total_tracks, album_compilation, scraped_song_id, is_playable, duration_ms
    except Exception as e:
        raise ValueError(f'Failed to parse TRACKS_URL response: {str(e)}\n{raw}')


def get_song_genres(rawartists: List[str], track_name: str) -> List[str]:
    if Zotify.CONFIG.get_save_genres():
        try:
            genres = []
            for data in rawartists:
                # query artist genres via href, which will be the api url
                with Loader(PrintChannel.PROGRESS_INFO, "Fetching artist information..."):
                    (raw, artistInfo) = Zotify.invoke_url(f'{data[HREF]}')
                if Zotify.CONFIG.get_all_genres() and len(artistInfo[GENRES]) > 0:
                    for genre in artistInfo[GENRES]:
                        genres.append(genre)
                elif len(artistInfo[GENRES]) > 0:
                    genres.append(artistInfo[GENRES][0])

            if len(genres) == 0:
                Printer.print(PrintChannel.WARNINGS, '###    No Genres found for song ' + track_name)
                genres.append('')

            return genres
        except Exception as e:
            raise ValueError(f'Failed to parse GENRES response: {str(e)}\n{raw}')
    else:
        return ['']


def get_song_lyrics(song_id: str) -> List[str]:
    raw, lyrics_dict = Zotify.invoke_url('https://spclient.wg.spot' + f'ify.com/color-lyrics/v2/track/{song_id}')
    if lyrics_dict:
        try:
            formatted_lyrics = lyrics_dict['lyrics']['lines']
        except KeyError:
            raise ValueError(f'Failed to fetch lyrics: {song_id}')
        
        if(lyrics_dict['lyrics']['syncType'] == "UNSYNCED"):
            lyrics = [line['words'] + '\n' for line in formatted_lyrics]
        elif(lyrics_dict['lyrics']['syncType'] == "LINE_SYNCED"):
            lyrics = []
            for line in formatted_lyrics:
                timestamp = int(line['startTimeMs'])
                ts_minutes = str(math.floor(timestamp / 60000)).zfill(2)
                ts_seconds = str(math.floor((timestamp % 60000) / 1000)).zfill(2)
                ts_millis = str(math.floor(timestamp % 1000))[:2].zfill(2)
                lyrics.append(f'[{ts_minutes}:{ts_seconds}.{ts_millis}]' + line['words'] + '\n')
        return lyrics
    raise ValueError(f'Failed to fetch lyrics: {song_id}')


def get_song_duration(song_id: str) -> float:
    """ Retrieves duration of song in second as is on spotify """

    (raw, resp) = Zotify.invoke_url(f'{TRACK_STATS_URL}{song_id}')

    # get duration in miliseconds
    ms_duration = resp['duration_ms']
    # convert to seconds
    duration = float(ms_duration)/1000

    return duration


def handle_lyrics(track_id: str, song_name: str, filedir: PurePath) -> List[str] | None:
    lyrics = None
    try:
        lyricdir = Zotify.CONFIG.get_lyrics_location()
        if lyricdir is None:
            lyricdir = filedir
        
        lyrics = get_song_lyrics(track_id)
        with open(lyricdir / f"{song_name}.lrc", 'w', encoding='utf-8') as file:
            file.writelines(lyrics)
        
    except ValueError:
        Printer.print(PrintChannel.SKIPS, "\n")
        Printer.print(PrintChannel.SKIPS, f'###   SKIPPING: LYRICS FOR "{song_name}" (LYRICS NOT AVAILABLE)   ###')
        Printer.print(PrintChannel.SKIPS, "\n")
    return lyrics


def download_track(mode: str, track_id: str, extra_keys: dict | None = None, wrapper_p_bars: list | None = None) -> None:
    """ Downloads raw song audio from Spotify """
    
    # recursive header for parent album download
    child_request_mode = mode
    child_request_id = track_id
    if Zotify.CONFIG.get_download_parent_album():
        if mode == "album" and "M3U8_bypass" in extra_keys and extra_keys["M3U8_bypass"] is not None:
            child_request_mode, child_request_id = extra_keys.pop("M3U8_bypass")
        else:
            album_id = total_tracks = None
            try:
                (raw, info) = Zotify.invoke_url(f'{TRACKS_URL}?ids={track_id}&market=from_token')
                album_id = info[TRACKS][0][ALBUM][ID]
                total_tracks = info[TRACKS][0][ALBUM][TOTAL_TRACKS]
            except:
                Printer.print(PrintChannel.ERRORS, f'###   FAILED TO FIND PARENT ALBUM FOR TRACK_ID: {track_id}   ###')
                Printer.print(PrintChannel.ERRORS, "\n")
            
            if album_id and total_tracks and int(total_tracks) > 1:
                from zotify.album import download_album
                # uses album OUTPUT template for filename formatting, but handle m3u8 as if only this track was downloaded
                return download_album(album_id, wrapper_p_bars, M3U8_bypass=(mode, track_id))
    
    if extra_keys is None:
        extra_keys = {}
    
    Printer.print(PrintChannel.PROGRESS_INFO, "\n")
    prepare_download_loader = Loader(PrintChannel.PROGRESS_INFO, "Preparing download...")
    prepare_download_loader.start()
    
    try:
        output_template = Zotify.CONFIG.get_output(mode)
        
        (artists, raw_artists, album_name, album_artist, name, image_url, release_year, disc_number,
         track_number, total_tracks, compilation, scraped_song_id, is_playable, duration_ms) = get_song_info(track_id)
        total_discs = None
        if "total_discs" in extra_keys:
            total_discs = extra_keys["total_discs"]
        
        song_name = fix_filename(artists[0]) + ' - ' + fix_filename(name)
        
        for k in extra_keys:
            output_template = output_template.replace("{"+k+"}", fix_filename(extra_keys[k]))
        
        ext = EXT_MAP.get(Zotify.CONFIG.get_download_format().lower())
        
        output_template = output_template.replace("{artist}", fix_filename(artists[0]))
        output_template = output_template.replace("{album_artist}", fix_filename(album_artist))
        output_template = output_template.replace("{album}", fix_filename(album_name))
        output_template = output_template.replace("{song_name}", fix_filename(name))
        output_template = output_template.replace("{release_year}", fix_filename(release_year))
        output_template = output_template.replace("{disc_number}", fix_filename(disc_number))
        output_template = output_template.replace("{track_number}", '{:02d}'.format(int(fix_filename(track_number))))
        output_template = output_template.replace("{total_tracks}", fix_filename(total_tracks))
        output_template = output_template.replace("{id}", fix_filename(scraped_song_id))
        output_template = output_template.replace("{track_id}", fix_filename(track_id))
        output_template += f".{ext}"
        
        filename = PurePath(Zotify.CONFIG.get_root_path()).joinpath(output_template)
        filedir = PurePath(filename).parent
        
        filename_temp = filename
        if Zotify.CONFIG.get_temp_download_dir() != '':
            filename_temp = PurePath(Zotify.CONFIG.get_temp_download_dir()).joinpath(f'zotify_{str(uuid.uuid4())}_{track_id}.{ext}')
        
        check_name = Path(filename).is_file() and Path(filename).stat().st_size
        check_local = scraped_song_id in get_directory_song_ids(filedir)
        check_all_time = scraped_song_id in get_previously_downloaded()
        if Zotify.CONFIG.get_disable_directory_archives():
            check_local = not Zotify.CONFIG.get_skip_existing() or not Zotify.CONFIG.get_skip_previously_downloaded()
            # avoids overwrite case only when both "safety switches" are on
        
        # same filename, not same song_id, rename the newcomer
        if not check_local and check_name:
            c = len([file for file in Path(filedir).iterdir() if file.match(filename.stem + "*")])
            filename = PurePath(filedir).joinpath(f'{filename.stem}_{c}{filename.suffix}')
        
        if Zotify.CONFIG.get_export_m3u8() and track_id == child_request_id:
            if child_request_mode == "liked" and Zotify.CONFIG.get_liked_songs_archive_m3u8():
                m3u_path = filedir / "Liked Songs.m3u8"
                songs_m3u = fetch_m3u8_songs(m3u_path)
            song_label = add_to_m3u8(child_request_mode, get_song_duration(track_id), song_name, filename)
            if child_request_mode == "liked" and Zotify.CONFIG.get_liked_songs_archive_m3u8():
                if songs_m3u is not None and song_label in songs_m3u[0]:
                    Zotify.CONFIG.Values[EXPORT_M3U8] = False
                    Path(filedir / (Zotify.datetime_launch + "_zotify.m3u8")).replace(m3u_path)
                    with open(m3u_path, 'a', encoding='utf-8') as file:
                        file.writelines(songs_m3u[3:])
        
        if Zotify.CONFIG.get_download_lyrics() and Zotify.CONFIG.get_always_check_lyrics():
            lyrics = handle_lyrics(track_id, song_name, filedir)
    
    except Exception as e:
        prepare_download_loader.stop()
        Printer.print(PrintChannel.ERRORS, f'###   SKIPPING SONG - FAILED TO QUERY METADATA - Track_ID: {str(track_id)}   ###')
        Printer.print(PrintChannel.ERRORS, "Extra_Keys {" + ", ".join(f'"{it[0]}": "{it[1]}"' for it in extra_keys.items()) + "}")
        Printer.print(PrintChannel.ERRORS, "\n")
        Printer.print(PrintChannel.ERRORS, "".join(traceback.TracebackException.from_exception(e).format()))
        Printer.print(PrintChannel.ERRORS, "\n\n")
    
    else:
        try:
            if not is_playable:
                prepare_download_loader.stop()
                Printer.print(PrintChannel.SKIPS, f'###   SKIPPING: "{song_name}" (SONG IS UNAVAILABLE)   ###')
                Printer.print(PrintChannel.SKIPS, "\n\n")
            else:
                if check_local and check_name and Zotify.CONFIG.get_skip_existing() and not Zotify.CONFIG.get_disable_directory_archives():
                    prepare_download_loader.stop()
                    Printer.print(PrintChannel.SKIPS, f'###   SKIPPING: "{song_name}" (SONG ALREADY EXISTS)   ###')
                    Printer.print(PrintChannel.SKIPS, "\n\n")
                
                elif check_all_time and Zotify.CONFIG.get_skip_previously_downloaded():
                    prepare_download_loader.stop()
                    Printer.print(PrintChannel.SKIPS, f'###   SKIPPING: "{song_name}" (SONG ALREADY DOWNLOADED ONCE)   ###')
                    Printer.print(PrintChannel.SKIPS, "\n\n")
                
                else:
                    if track_id != scraped_song_id:
                        track_id = scraped_song_id
                    track = TrackId.from_base62(track_id)
                    stream = Zotify.get_content_stream(track, Zotify.DOWNLOAD_QUALITY)
                    create_download_directory(filedir)
                    total_size = stream.input_stream.size
                    
                    prepare_download_loader.stop()
                    
                    time_start = time.time()
                    downloaded = 0
                    pos = 1
                    if wrapper_p_bars is not None:
                        pos = wrapper_p_bars[-1] if type(wrapper_p_bars[-1]) is int else -(wrapper_p_bars[-1].pos + 2)
                        for bar in wrapper_p_bars:
                            if type(bar) != int: bar.refresh()
                    with open(filename_temp, 'wb') as file, Printer.progress(
                            desc=song_name,
                            total=total_size,
                            unit='B',
                            unit_scale=True,
                            unit_divisor=1024,
                            disable=not Zotify.CONFIG.get_show_download_pbar(),
                            pos=pos
                    ) as p_bar:
                        b = 0
                        while b < 5:
                        #for _ in range(int(total_size / Zotify.CONFIG.get_chunk_size()) + 2):
                            data = stream.input_stream.stream().read(Zotify.CONFIG.get_chunk_size())
                            p_bar.update(file.write(data))
                            downloaded += len(data)
                            b += 1 if data == b'' else 0
                            if Zotify.CONFIG.get_download_real_time():
                                delta_real = time.time() - time_start
                                delta_want = (downloaded / total_size) * (duration_ms/1000)
                                if delta_want > delta_real:
                                    time.sleep(delta_want - delta_real)
                    
                    time_downloaded = time.time()
                    
                    genres = get_song_genres(raw_artists, name)
                    
                    if Zotify.CONFIG.get_download_lyrics() and not Zotify.CONFIG.get_always_check_lyrics():
                        lyrics = handle_lyrics(track_id, song_name, filedir)
                    
                    # no metadata is written to track prior to conversion
                    convert_audio_format(filename_temp)
                    
                    try:
                        set_audio_tags(filename_temp, artists, genres, name, album_name, album_artist, release_year, 
                                       disc_number, track_number, total_tracks, total_discs, compilation, lyrics)
                        set_music_thumbnail(filename_temp, image_url, mode)
                    except Exception:
                        Printer.print(PrintChannel.ERRORS, "\n")
                        Printer.print(PrintChannel.ERRORS, "Unable to write metadata, ensure FFMPEG is installed and added to your PATH.")
                        Printer.print(PrintChannel.ERRORS, "\n")
                    
                    if filename_temp != filename:
                        if Path(filename).exists():
                            Path(filename).unlink()
                        Path(filename_temp).rename(filename)
                    
                    time_finished = time.time()
                    
                    Printer.print(PrintChannel.DOWNLOADS, f'###   DOWNLOADED: "{song_name}" TO "{Path(filename).relative_to(Zotify.CONFIG.get_root_path())}" IN {fmt_seconds(time_downloaded - time_start)} (PLUS {fmt_seconds(time_finished - time_downloaded)} CONVERTING)   ###')
                    Printer.print(PrintChannel.DOWNLOADS, "\n\n")

                    # add song ID to global .song_archive file
                    if Zotify.CONFIG.get_skip_previously_downloaded() or Zotify.CONFIG.get_disable_directory_archives():
                        if not check_all_time:
                            add_to_archive(scraped_song_id, PurePath(filename).name, artists[0], name)
                    # add song ID to download directory's .song_ids file
                    if not check_local:
                        add_to_directory_song_ids(filedir, scraped_song_id, PurePath(filename).name, artists[0], name)

                    if Zotify.CONFIG.get_bulk_wait_time():
                        time.sleep(Zotify.CONFIG.get_bulk_wait_time())
            
            
            
        except Exception as e:
            Printer.print(PrintChannel.ERRORS, f'###   SKIPPING: {song_name} (GENERAL DOWNLOAD ERROR) - Track_ID: {str(track_id)}   ###')
            Printer.print(PrintChannel.ERRORS, "Extra_Keys {" + ", ".join(f'"{it[0]}": "{it[1]}"' for it in extra_keys.items()) + "}")
            Printer.print(PrintChannel.ERRORS, "\n")
            Printer.print(PrintChannel.ERRORS, "".join(traceback.TracebackException.from_exception(e).format()))
            Printer.print(PrintChannel.ERRORS, "\n\n")
            if Path(filename_temp).exists():
                Path(filename_temp).unlink()

    prepare_download_loader.stop()
    Printer.print(PrintChannel.ERRORS, "\n")





def convert_audio_format(filename) -> None:
    """ Converts raw audio into playable file """
    temp_filename = f'{PurePath(filename).parent}.tmp'
    Path(filename).replace(temp_filename)
    
    download_format = Zotify.CONFIG.get_download_format().lower()
    file_codec = CODEC_MAP.get(download_format, 'copy')
    bitrate = None
    if file_codec != 'copy':
        bitrate = Zotify.CONFIG.get_transcode_bitrate()
        if bitrate in {"auto", ""}:
            bitrates = {
                'auto': '0' if Zotify.check_premium() else '2',
                'normal': '3',
                'high': '2',
                'very_high': '0'
            }
            bitrate = bitrates[Zotify.CONFIG.get_download_quality()]
    
    output_params = ['-c:a', file_codec]
    if bitrate is not None:
        output_params += ['-q:a', bitrate]
    
    try:
        ff_m = ffmpy.FFmpeg(
            global_options=['-y', '-hide_banner', f'-loglevel {Zotify.CONFIG.get_ffmpeg_log_level()}'],
            inputs={temp_filename: None},
            outputs={filename: output_params}
        )
        with Loader(PrintChannel.PROGRESS_INFO, "Converting file..."):
            ff_m.run()
        
        if Path(temp_filename).exists():
            Path(temp_filename).unlink()
    
    except ffmpy.FFExecutableNotFoundError:
        Printer.print(PrintChannel.WARNINGS, f'###   SKIPPING {file_codec.upper()} CONVERSION - FFMPEG NOT FOUND   ###')
