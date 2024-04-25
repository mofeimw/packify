import requests
from urllib.parse import urlencode
import base64
import webbrowser
from datetime import datetime

def main():
    # create app in spotify developer dashboard for auth info
    # auth() with client_id & client_secret
    # token = auth(REDACTED, REDACTED)

    # extract data with obtained token
    extract(token)

def auth(client_id, client_secret):
    auth_headers = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": "http://localhost:7777/callback",
        # "scope": "user-library-read"
        "scope": "playlist-read-private"
    }

    # apparently this (temporary) auth code expires every run
    webbrowser.open("https://accounts.spotify.com/authorize?" + urlencode(auth_headers))
    code = input("Auth Code: ")
    print()

    # obtain auth token (diff from auth code)
    encoded_credentials = base64.b64encode(client_id.encode() + b':' + client_secret.encode()).decode("utf-8")

    token_headers = {
        "Authorization": "Basic " + encoded_credentials,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://localhost:7777/callback"
    }

    r = requests.post("https://accounts.spotify.com/api/token", data=token_data, headers=token_headers)
    try:
        token = r.json()["access_token"]
    except:
        print("Invalid Auth Code")
        exit(1)

    return token

def extract(token):
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json"
    }

    index = index_playlists(headers)
    process_songs(headers, index)

def index_playlists(headers):
    index = []
    playlist_params = { "limit": 50, "offset": 0 } # apparently the limit is 100... but 50 for playlists? use offset to scroll thru
    playlists = requests.get("https://api.spotify.com/v1/me/playlists", params=playlist_params, headers=headers).json()
    n = playlists["total"]
    cycle = 0
    i = 0
    while i < n:
        playlist_params = { "limit": 50, "offset": 50*cycle }
        playlists = requests.get("https://api.spotify.com/v1/me/playlists", params=playlist_params, headers=headers).json()

        for playlist in playlists["items"]:
            # print(playlist["name"] + " [" + str(playlist["tracks"]["total"]) + "]")
            index.append([playlist["name"], playlist["tracks"]["total"], playlist["description"], playlist["tracks"]["href"]])
            i += 1

        cycle += 1
    # print("\n[i: " + str(i) + " // n (total): " + str(n) + "]")
    # print()

    return index

def process_songs(headers, index):
    # [name, length, description, tracks href]
    for playlist in index:
        #title
        print(playlist[0])
        # description
        if playlist[2] != "":
            print("~" + playlist[2] + "~")
        # ------
        z = 0
        while z < len(playlist[0]):
            print("-", end="")
            z += 1
        print()

        songs_params = { "limit": 50, "offset": 0 }
        j = 0
        cycle = 0
        while j < playlist[1]:
            songs_params = { "limit": 50, "offset": 50*cycle }
            songs = requests.get(playlist[3], params=songs_params, headers=headers).json()
            for song in songs["items"]:
                name = song["track"]["name"]
                album = song["track"]["album"]["name"]
                added_at = song["added_at"]
                artists = ""
                # cycle through artists
                z = 0
                num_artists = len(song["track"]["artists"])
                while z < num_artists:
                    artists += song["track"]["artists"][z]["name"]
                    if (z != num_artists - 1):
                        artists += ", "
                    z += 1
                # process date
                date_object = datetime.strptime(added_at, "%Y-%m-%dT%H:%M:%SZ")
                date_added = date_object.strftime("%-m/%d/%y")

                print(name, end=" - ")
                print(album, end=" - ")
                print(artists, end=" - ")
                print(date_added)

                j += 1
            cycle += 1
        print()

if __name__ == "__main__":
    main()
