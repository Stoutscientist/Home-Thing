#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os
import time
from datetime import timedelta

import schedule
import requests

from bs4 import BeautifulSoup

from spotifyapi.auth.utils import read_refresh_token
from spotifyapi.auth.crypto import exchange_refresh_token
from spotifyapi.auth.oauth import perform_authorization_code_flow

class SpotifyApi:

    # the HTML tags containing all lyric data on google
    lyric_container_scopes = {"jsname": "YS01Ge"}

    def __init__(self, clear=True, **kwargs):
        self.current_song = None
        self.clear_screen = clear

        # track the access and refresh tokens, used to access the user's spotify data
        self.access_token = None
        self.refresh_token = read_refresh_token()

        # if we have a cached refresh token, use it instead of OAuth
        if self.refresh_token:
            self.__exchange_refresh_token()

        # Otherwise, we must perfrom OAuth exchange, which requires prompting the user.
        # This is done with Spotify's client PKCE auth flow
        else:
            (
                self.access_token,
                self.refresh_token,
                token_duration,
            ) = perform_authorization_code_flow()

            # tracks the time until the token expires
            self.expires_at = time.time() + token_duration

        # run and update song info
        self.__update_song_info()

    def __exchange_refresh_token(self):
        """
        Exchanges the current refresh token for a new API key and refresh token.
        Used when the current API key is unknown or expired.
        """

        self.access_token, self.refresh_token, token_duration = exchange_refresh_token(
            self.refresh_token
        )

        self.expires_at = time.time() + token_duration

    def __get_song_metadata(self) -> dict:
        """
        Gets the api data for the song that the user is currently playing.

        Output
        ______
            api_data: json object
                A json object containing the data from the API endpoint
        """

        endpoint = "https://api.spotify.com/v1/me/player/currently-playing"

        api_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

        resp = requests.get(endpoint, headers=api_headers)
        return resp.json() if resp.text else None

    def __get_current_song(self) -> tuple:
        """
        Gets the title and artist of the song currently playing on the user's spotify account.
        If no song is currently playing, return None.

        Outputs
        _______

            song: str
                The song that is currently being played

            artist: str
                The artist of the current song
        """

        song_metadata = self.__get_song_metadata()
        song_title, artist, time = None, None, None

        # pass if API result is malformed (for example, if an ad is playing)
        try:
            song_title, artist, time = (
                song_metadata["item"]["name"],
                song_metadata["item"]["artists"][0]["name"],
                song_metadata["progress_ms"],
            )
        except (TypeError, KeyError):
            pass

        return (song_title, artist, time) if song_metadata else (None, None, None)

    def __pretty_print(self, song_title: str, artist: str, time: str,):
        """
        prints out the song title, artist, and lyrics
        """
        [os.system("cls") if os.name == "nt" else print("\033c", end="")]        song_header = song_title + " by " + artist
        print(song_header)
        print("-" * len(song_header))
        print(timedelta(seconds=round(time / 1000)))

    def __check_token_expiration(self):
        """
        Checks if the current API token has expired. if so, it is refreshed.
        """

        # refresh the token a minute before expiration so there are no errors.
        if time.time() + 60 > self.expires_at:
            self.__exchange_refresh_token()

    def __update_song_info(self):
        """
        Checks if the user has chenged songs. If the song has changed,
        then the lyrics of the new song are printed to the terminal.
        This can be considered the core function of the class.
        """

        song, artist, time = self.__get_current_song()

        self.current_song = song
        self.__pretty_print(song, artist, time)

    def serve_forever(self, interval: float = 0.1):
        """
        Checks every {interval} seconds if the user's song has changed or the token has expired on a permanent
        loop. This is the only public method in the class, and should be called after the constructor.

        Parameters
        _________

            interval: int
                The duration between requests. For example, if the interval is 10, then
                the program will wait 10 seconds before checking if the song has changed.
        """

        schedule.every(interval).seconds.do(self.__check_token_expiration)
        schedule.every(interval).seconds.do(self.__update_song_info)

        while True:
            schedule.run_pending()
            time.sleep(0.1)
