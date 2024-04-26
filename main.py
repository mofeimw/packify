import requests
from urllib.parse import urlencode
import base64
import webbrowser
from datetime import datetime
import os

def main():
    # set up filesystem
    fs_setup()

    # create app in spotify developer dashboard for auth info
    # auth() with client_id & client_secret
    # token = auth(REDACTED, REDACTED)

    # extract data with obtained token
    extract(token)

def fs_setup():
    # make sure export dir does not exist and then create folder hierarchy
    if os.path.exists("export"):
        print("error: export directory exists already")
        exit(1)

    os.mkdir("export")
    os.mkdir("export/images")
    os.mkdir("export/playlists")

    fs_write("export/main.css", CSS)

def fs_write(file, content):
    f = open(file, "w")
    f.write(content)
    f.close()

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
        print("error: invalid auth code")
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
    index_html = TEMPLATE1 + TEMPLATE5 + "<link rel=\"stylesheet\" href=\"main.css\">"

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
            html = TEMPLATE1 + "<title>" + playlist["name"] + "</title>" + TEMPLATE2
            html += "<img id=\"art\" src=\"../images/" + str(i) + ".jpg" + "\">"
            html += "<div id=\"title-desc\">"
            html += "<h1>" + playlist["name"] + "</h1>"
            if (playlist["description"] != ""):
                html += "<h2>" + playlist["description"] + "</h2>"
                html += "<style>#header #title-desc { transform: translateY(-25px); }</style>"
            html += TEMPLATE3
            # download cover art
            dl_art(playlist["images"][0]["url"], i)

            index.append([playlist["name"], playlist["tracks"]["total"], playlist["description"], playlist["tracks"]["href"], html, i])
            index_html += "<li class=\"playlist\"><img src=\"images/" + str(i) + ".jpg" + "\"><a href=\"playlists/" + str(i) + ".html\">" + playlist["name"] + "</a></li>\n"

            i += 1

        cycle += 1
    # print("\n[i: " + str(i) + " // n (total): " + str(n) + "]")
    # print()

    index_html += TEMPLATE6
    fs_write("export/index.html", index_html)
    return index

def dl_art(url, i):
    data = requests.get(url).content
    f = open("export/images/" + str(i) + ".jpg", "wb")
    f.write(data)
    f.close()

def process_songs(headers, index):
    # [name, length, description, tracks_href, html, i]
    for playlist in index:
        # title
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
                song_html = "<ul class=\"song\">"
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

                # print to stdout
                print(name, end=" - ")
                print(album, end=" - ")
                print(artists, end=" - ")
                print(date_added)

                # and append to html
                song_html += "<li>" + name + "</li>"
                song_html += "<li>" + album + "</li>"
                song_html += "<li>" + artists + "</li>"
                song_html += "<li>" + date_added + "</li>"
                song_html += "</ul>\n"
                playlist[4] += song_html

                j += 1
            cycle += 1
        print()
        playlist[4] += TEMPLATE4
        fs_write("export/playlists/" + str(playlist[5]) + ".html", playlist[4])

TEMPLATE1 = """
<!DOCTYPE html>
<html>
    <head>
"""
# title goes here
TEMPLATE2 = """
        <link rel="stylesheet" href="../main.css">
    </head>
    <body>
        <div id="header">
"""
# cover art, and then title and description go here
TEMPLATE3 = """
            </div>
        </div>
        <div id="songs">
            <ul id="headers" class="song">
                <li>Title</li>
                <li>Artist</li>
                <li>Album</li>
                <li>Date</li>
            </ul>
"""
# songs go here
TEMPLATE4 = """
        </div>
    </body>
</html>
"""

# index.html
TEMPLATE5 = """
    </head>
    <body>
        <ul id="index">
"""
# list of playlists
TEMPLATE6 = """
        </ul>
    </body>
</html>
"""

CSS = """
body {
    font-family: helvetica, sans-serif;
    letter-spacing: 0.02rem;
    padding: 3rem 5rem;
    background-color: #CCCCFF;
    color: #1a1a2e;
}

#index li {
    list-style-type: none;
    margin: 0;
    padding: 0;
    margin-bottom: 2rem;
}

#index li:last-child {
    margin-bottom: 0;
}

#index a {
    transform: translateY(-30px);
    display: inline-block;
    color: #1a1a2e;
    font-weight: bold;
    font-size: 1.3rem;
    text-decoration: none;
}

#index a:visited, #index a:link {
    color: #1a1a2e;
}

#index img {
    width: 75px;
    height: 75px;
    margin-right: 1.5rem;
}

#art {
    display: inline-block;
    margin-right: 1rem;
    width: 150px;
    height: 150px;
}

#header #title-desc {
    display: inline-block;
    margin-left: 2rem;
    margin-bottom: 1rem;
    transform: translateY(-60px);
}

#header #title-desc h1 {
    font-size: 3rem;
    margin-bottom: 0.5rem;
}

#header #title-desc h2 {
    font-size: 1.3rem;
    margin-top: 0;
}

.song {
    padding: 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.song li {
    display: inline-block;
    margin-bottom: 1rem;
    margin-right: 4rem;
    font-size: 1rem;
    text-align: left;
    width: 50%;
}

.song li:nth-child(4) {
    width: 10%;
    margin-right: 0;
}

#headers li {
    font-weight: bold;
    font-size: 1.15rem;
}
"""

if __name__ == "__main__":
    main()
