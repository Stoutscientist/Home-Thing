import webbrowser
import socket

from .utils import parse_spotify_http_response
from .utils import StateTokenException

from .crypto import generate_client_PKCE
from .crypto import exchange_auth_code

from .http import OAuthServer


def perform_authorization_code_flow():
    """
    Performs spotify's Authorization Code Flow to retrive an API token.
    This uses the OAuth 2.0 protocol, which requires user input and consent.


    Output
    ______

        api_key: str
            a user's api key with prompted permissions

        refresh_token: str
            A refresh token used to retrive future api keys

        expires_in: int
            the time (in seconds) until the token expires
    """

    # create server that runs at the redirect URI. This is used to catch the
    # response sent from the OAuth authentication

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 1))  # connect() for UDP doesn't send packets
    ip = s.getsockname()[0]

    server = OAuthServer((ip, 8080))

    # generate a uri with the required Oauth headers and open it in a webbrowser
    auth_uri, code_verifier, state_token = generate_client_PKCE()
    webbrowser.open_new_tab(auth_uri)
    print("Go to " + auth_uri + " in your browser to authenticate.")

    # parse the spotify API's http response for the User's token
    raw_http_response = server.handle_auth().decode("utf-8")
    http_headers = parse_spotify_http_response(raw_http_response)

    # verify that state tokens match to prevent CSRF
    if state_token != http_headers["state"]:
        raise StateTokenException

    # exchange code for access token. The refresh token is automatically cached
    access_token, refresh_token, expires_in = exchange_auth_code(
        http_headers["code"], code_verifier
    )

    return access_token, refresh_token, expires_in
