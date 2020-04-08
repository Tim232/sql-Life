from datetime import datetime

from discord.ext import commands

from granitepy import objects


class GraniteTrack(objects.Track):

    def __init__(self, track_id: str, info: dict, ctx: commands.Context):
        super().__init__(track_id, info)

        self.ctx = ctx
        self.requester = ctx.author


class GranitePlaylist(objects.Playlist):

    def __init__(self, playlist_info: dict, tracks: list, ctx: commands.Context):
        super().__init__(playlist_info, tracks)

        self.ctx = ctx
        self.tracks = [GraniteTrack(track_id=track["track"], info=track["info"], ctx=self.ctx) for track in self.tracks_raw]


class SpotifyTrack:

    def __init__(self, ctx: commands.Context, title: str, uri: str, length: int):

        self.title = title
        self.uri = uri
        self.length = length

        self.ctx = ctx
        self.requester = ctx.author

    def __repr__(self):
        return f"<LifeSpotifyTrack title={self.title!r} uri=<{self.uri!r}> length={self.length}>"


class Playlist:

    def __init__(self, data: dict):
        self.data = data

        self.id = data.get("id")
        self.name = data.get("name")
        self.owner_id = data.get("owner_id")
        self.private = data.get("private")
        self.creation_date = datetime.strptime(data.get("creation_date"), "%d-%m-%Y: %H:%M")
        self.image_url = data.get("image_url")

        self.tracks = []

    def __repr__(self):
        return f"<LifePlaylist id={self.id!r} name={self.name!r} owner_id={self.owner_id!r}>"

    @property
    def track_ids(self):
        return [track.track_id for track in self.tracks]