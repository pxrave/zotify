from pathlib import PurePath, Path
import time

from librespot.metadata import EpisodeId

from zotify.const import ERROR, ID, ITEMS, NAME, SHOW, DURATION_MS
from zotify.termoutput import PrintChannel, Printer
from zotify.utils import create_download_directory, fix_filename, wait_between_downloads
from zotify.zotify import Zotify
from zotify.loader import Loader


EPISODE_INFO_URL = 'https://api.spot'+'ify.com/v1/episodes'
SHOWS_URL = 'https://api.spot'+'ify.com/v1/shows'
PARTNER_URL = 'https://api-partner.spot'+'ify.com/pathfinder/v1/query?operationName=getEpisode&variables={"uri":"spotify:episode:'
PERSISTED_QUERY = '{"persistedQuery":{"version":1,"sha256Hash":"224ba0fd89fcfdfb3a15fa2d82a6112d3f4e2ac88fba5c6713de04d1b72cf482"}}'


def get_episode_info(episode_id_str) -> tuple[str | None, str | None, str | None]:
    with Loader(PrintChannel.PROGRESS_INFO, "Fetching episode information..."):
        (raw, info) = Zotify.invoke_url(f'{EPISODE_INFO_URL}/{episode_id_str}')
    if not info:
        Printer.print(PrintChannel.ERRORS, "###   INVALID EPISODE ID   ###")
    if ERROR in info:
        return None, None, None
    duration_ms = info[DURATION_MS]
    return fix_filename(info[SHOW][NAME]), duration_ms, fix_filename(info[NAME])


def get_show_episodes(show_id_str) -> list:
    episodes = []
    offset = 0
    limit = 50

    with Loader(PrintChannel.PROGRESS_INFO, "Fetching episodes..."):
        while True:
            resp = Zotify.invoke_url_with_params(
                f'{SHOWS_URL}/{show_id_str}/episodes', limit=limit, offset=offset)
            offset += limit
            for episode in resp[ITEMS]:
                episodes.append(episode[ID])
            if len(resp[ITEMS]) < limit:
                break

    return episodes


def download_podcast_directly(url, filename):
    import functools
    import shutil
    import requests
    from tqdm.auto import tqdm
    
    r = requests.get(url, stream=True, allow_redirects=True)
    if r.status_code != 200:
        r.raise_for_status()  # Will only raise for 4xx codes, so...
        raise RuntimeError(
            f"Request to {url} returned status code {r.status_code}")
    file_size = int(r.headers.get('Content-Length', 0))
    
    path = Path(filename).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    
    desc = "(Unknown total file size)" if file_size == 0 else ""
    r.raw.read = functools.partial(
        r.raw.read, decode_content=True)  # Decompress if needed
    with tqdm.wrapattr(r.raw, "read", total=file_size, desc=desc) as r_raw:
        with path.open("wb") as f:
            shutil.copyfileobj(r_raw, f)
    
    return path


def download_show(show_id, wrapper_p_bars: list | None = None):
    episodes = get_show_episodes(show_id)
    
    pos = 3
    if wrapper_p_bars is not None:
        pos = wrapper_p_bars[-1] if type(wrapper_p_bars[-1]) is int else -(wrapper_p_bars[-1].pos + 2)
    else:
        wrapper_p_bars = []
    p_bar = Printer.progress(episodes, unit='episodes', total=len(episodes), unit_scale=True,
                             disable=not Zotify.CONFIG.get_show_playlist_pbar(), pos=pos)
    wrapper_p_bars.append(p_bar if Zotify.CONFIG.get_show_playlist_pbar() else pos)
    
    for episode in p_bar:
        download_episode(episode, wrapper_p_bars)
        p_bar.set_description(get_episode_info(episode)[2])
        for bar in wrapper_p_bars:
            if type(bar) != int: bar.refresh()


def download_episode(episode_id, wrapper_p_bars: list | None = None) -> None:
    podcast_name, duration_ms, episode_name = get_episode_info(episode_id)
    
    Printer.print(PrintChannel.PROGRESS_INFO, "\n")
    prepare_download_loader = Loader(PrintChannel.PROGRESS_INFO, "Preparing download...")
    prepare_download_loader.start()
    
    if podcast_name is None or episode_name is None or duration_ms is None:
        prepare_download_loader.stop()
        Printer.print(PrintChannel.ERRORS, f'###   SKIPPING EPISODE - FAILED TO QUERY METADATA - Episode_ID: {str(episode_id)}   ###')
        Printer.print(PrintChannel.SKIPS, "\n\n")
    else:
        filename = podcast_name + ' - ' + episode_name
        extra_paths = podcast_name + '/'
        
        resp = Zotify.invoke_url(
            PARTNER_URL + episode_id + '"}&extensions=' + PERSISTED_QUERY)[1]["data"]["episode"]
        direct_download_url = resp["audio"]["items"][-1]["url"]
        
        download_directory = PurePath(Zotify.CONFIG.get_root_podcast_path()).joinpath(extra_paths)
        create_download_directory(download_directory)
        
        if "anon-podcast.scdn.co" in direct_download_url or "audio_preview_url" not in resp:
            episode_id = EpisodeId.from_base62(episode_id)
            stream = Zotify.get_content_stream(episode_id, Zotify.DOWNLOAD_QUALITY)
            
            if stream is None:
                Printer.print(PrintChannel.ERRORS, f'###   SKIPPING EPISODE - FAILED TO GET CONTENT STREAM - Episode_ID: {str(episode_id)}   ###')
                Printer.print(PrintChannel.SKIPS, "\n\n")
            else:
                total_size = stream.input_stream.size

                filepath = PurePath(download_directory).joinpath(f"{filename}.ogg")
                if (Path(filepath).is_file()
                    and Path(filepath).stat().st_size == total_size
                    and Zotify.CONFIG.get_skip_existing()
                ):
                    prepare_download_loader.stop()
                    Printer.print(PrintChannel.SKIPS, f'###   SKIPPING: "{podcast_name} - {episode_name}" (EPISODE ALREADY EXISTS)   ###')
                    Printer.print(PrintChannel.SKIPS, "\n\n")
                    return

                prepare_download_loader.stop()
                time_start = time.time()
                downloaded = 0
                pos = 1
                if wrapper_p_bars is not None:
                    pos = wrapper_p_bars[-1] if type(wrapper_p_bars[-1]) is int else -(wrapper_p_bars[-1].pos + 2)
                    for bar in wrapper_p_bars:
                        if type(bar) != int: bar.refresh()
                with open(filepath, 'wb') as file, Printer.progress(
                    desc=filename,
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                    disable=not Zotify.CONFIG.get_show_download_pbar(),
                    pos=pos
                ) as p_bar:
                    prepare_download_loader.stop()
                    while True:
                    #for _ in range(int(total_size / Zotify.CONFIG.get_chunk_size()) + 2):
                        data = stream.input_stream.stream().read(Zotify.CONFIG.get_chunk_size())
                        p_bar.update(file.write(data))
                        downloaded += len(data)
                        if data == b'':
                            break
                        if Zotify.CONFIG.get_download_real_time():
                            delta_real = time.time() - time_start
                            delta_want = (downloaded / total_size) * (int(duration_ms)/1000)
                            if delta_want > delta_real:
                                time.sleep(delta_want - delta_real)
                                
                
                wait_between_downloads()
        else:
            filepath = PurePath(download_directory).joinpath(f"{filename}.mp3")
            download_podcast_directly(direct_download_url, filepath)
            
            wait_between_downloads()
    
    prepare_download_loader.stop()
    Printer.print(PrintChannel.ERRORS, "\n")
