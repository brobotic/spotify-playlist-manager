# spotify-playlist-manager
A simple Python application that automatically adds new releases from artists to playlists in your Spotify library. Note: this was built for my own needs, but it may work for you if you happen to use Spotify the same way I do. It was built around how my Spotify library is set up: each playlist is one artist's discography. If the script finds at least one new release for the artist, that does not already exist in the playlist, it will send an email report that includes a list of each release that was added to the library. This way, I stay up to date with all new releases from artists I listen to.

This came from not being satisifed with the way Spotify notified me of new releases. Say I'm following 3 artists, and they all release an album/single on the same day. I'll get an email saying "<artist 1> and more have released new music" (or something to that effect), and it includes a link to the Release Radar playlist that contains generally one track from each release. Basically, I got tired of chasing down new releases for the artists I listen to and I wanted better notifications regarding new releases.

# Usage

1. Edit config.py to include your Spotify API keys and email information(sender email, recipient email). I use one gmail account to send the alert, and my primary gmail account receives the alert.

2. pip install -r requirements.txt 

3. It's recommend to schedule the script however you prefer (i.e. Windows Task Scheduler or cron) to run check-spotify.py. For example, I run it every Friday at 9AM, since new music releases are generally released on Thursday nights/Friday mornings.
