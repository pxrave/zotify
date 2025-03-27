import json
from pathlib import Path
import datetime, time
import requests
from librespot.audio.decoders import VorbisOnlyAudioQuality

from zotify import OAuth, Session
from zotify.const import TYPE, \
    PREMIUM, USER_READ_EMAIL, OFFSET, LIMIT, \
    PLAYLIST_READ_PRIVATE, USER_LIBRARY_READ, USER_FOLLOW_READ
from zotify.config import Config

class Zotify:    
    SESSION: Session = None
    DOWNLOAD_QUALITY = None
    CONFIG: Config = Config()
    
    def __init__(self, args):
        Zotify.CONFIG.load(args)
        Zotify.login(args)
        Zotify.datetime_launch = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    @classmethod
    def login(cls, args):
        """ Authenticates with Spotify and saves credentials to a file """
    
        # Create session
        if args.username not in {None, ""} and args.token not in {None, ""}:
            oauth = OAuth(args.username)
            oauth.set_token(args.token, OAuth.RequestType.REFRESH)
            cls.SESSION = Session.from_oauth(
                oauth, cls.CONFIG.get_credentials_location(), cls.CONFIG.get_language()
            )
        elif cls.CONFIG.get_credentials_location() and Path(cls.CONFIG.get_credentials_location()).exists():
            cls.SESSION = Session.from_file(
                cls.CONFIG.get_credentials_location(),
                cls.CONFIG.get_language(),
            )
        else:
            username = args.username
            while username == "":
                username = input("Username: ")
            oauth = OAuth(username)
            auth_url = oauth.auth_interactive()
            print(f"\nClick on the following link to login:\n{auth_url}")
            cls.SESSION = Session.from_oauth(
                oauth, cls.CONFIG.get_credentials_location(), cls.CONFIG.get_language()
            )
    
    @classmethod
    def get_content_stream(cls, content_id, quality):
        return cls.SESSION.content_feeder().load(content_id, VorbisOnlyAudioQuality(quality), False, None)
    
    @classmethod
    def __get_auth_token(cls):
        return cls.SESSION.tokens().get_token(
            USER_READ_EMAIL, PLAYLIST_READ_PRIVATE, USER_LIBRARY_READ, USER_FOLLOW_READ
        ).access_token
    
    @classmethod
    def get_auth_header(cls):
        return {
            'Authorization': f'Bearer {cls.__get_auth_token()}',
            'Accept-Language': f'{cls.CONFIG.get_language()}',
            'Accept': 'application/json',
            'app-platform': 'WebPlayer',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0'
        }
    
    @classmethod
    def invoke_url_with_params(cls, url, limit, offset, **kwargs):
        headers = cls.get_auth_header()
        params = {LIMIT: limit, OFFSET: offset}
        params.update(kwargs)
        return requests.get(url, headers=headers, params=params).json()
    
    @classmethod
    def invoke_url(cls, url, tryCount=0):
        # we need to import that here, otherwise we will get circular imports!
        from zotify.termoutput import Printer, PrintChannel
        headers = cls.get_auth_header()
        response = requests.get(url, headers=headers)
        responsetext = response.text
        try:
            responsejson = response.json()
        except json.decoder.JSONDecodeError:
            responsejson = {"error": {"status": "unknown", "message": "received an empty response"}}
        
        if not responsejson or 'error' in responsejson:
            if tryCount < (cls.CONFIG.get_retry_attempts() - 1):
                Printer.print(PrintChannel.WARNINGS, f"Spotify API Error (try {tryCount + 1}) ({responsejson['error']['status']}): {responsejson['error']['message']}")
                time.sleep(5)
                return cls.invoke_url(url, tryCount + 1)
            
            Printer.print(PrintChannel.API_ERRORS, f"Spotify API Error ({responsejson['error']['status']}): {responsejson['error']['message']}")
        
        return responsetext, responsejson
    
    @classmethod
    def check_premium(cls) -> bool:
        """ If user has spotify premium return true """
        return (cls.SESSION.get_user_attribute(TYPE) == PREMIUM)
