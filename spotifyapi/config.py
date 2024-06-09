import os
import pathlib

"""
Defines application constants
"""

# Spotify application constants

# the unique id for the Spotify application used to read data
CLIENT_ID = "4b13aaeb2ffd402aaec34015c02d6a4e"
REDIRECT_URI = "http://localhost:8080/callback/"


# directory constants, not meant to be used directly by program
__dir_path = os.path.dirname(os.path.realpath(__file__))
__project_root = pathlib.Path(__dir_path).parent


SECRETS_CACHE = os.path.join(__dir_path, "cache/secrets.json")
