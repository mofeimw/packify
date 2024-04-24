import requests
from urllib.parse import urlencode
import base64
import webbrowser

# create app in spotify developer dashboard for auth info
# client_id & client_secret go here

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

# grab data
user_headers = {
    "Authorization": "Bearer " + token,
    "Content-Type": "application/json"
}
user_params = { "limit": 50, "offset": 0 } # apparently the limit is 100... but 50 for playlists? use offset to scroll thru

index = []
playlist_params = { "limit": 50, "offset": 0 }
playlists = requests.get("https://api.spotify.com/v1/me/playlists", params=playlist_params, headers=user_headers).json()
n = playlists["total"]
cycle = 0
i = 0
while i < n:
    playlist_params = { "limit": 50, "offset": 50*cycle }
    playlists = requests.get("https://api.spotify.com/v1/me/playlists", params=playlist_params, headers=user_headers).json()

    for playlist in playlists["items"]:
        # print(playlist["name"] + " [" + str(playlist["tracks"]["total"]) + "]")
        index.append([playlist["name"], playlist["tracks"]["total"], playlist["description"], playlist["tracks"]["href"]])
        i += 1

    cycle += 1

# print("\n[i: " + str(i) + " // n (total): " + str(n) + "]")
# print()

# songs
# [name, length, description, tracks href]
for playlist in index:
    print(playlist[0])
    if playlist[2] != "":
        print("~" + playlist[2] + "~")
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
        songs = requests.get(playlist[3], params=songs_params, headers=user_headers).json()
        for song in songs["items"]:
            print(song["track"]["name"], end=" - ")
            z = 0
            num_artists = len(song["track"]["artists"])
            while z < num_artists:
                print(song["track"]["artists"][z]["name"], end="")
                if (z != num_artists - 1):
                    print(", ", end="")
                z += 1
            print()
            j += 1
        cycle += 1
    print()
