class SpotifyService:
    def __init__(self, s_ctx):
        self.context = s_ctx

    # print("Initialized")

    def get_device_ids(self):
        return self.context.playback_devices()

    def get_currently_playing(self):
        current = self.context.playback_currently_playing()
        return current

    def get_song_uris_from_album(self, album_uri):
        tracks = self.context.album_tracks(album_id=album_uri, limit=50)
        track_ids = []
        for track in tracks.items:
            track_ids.append(track.uri)

        return track_ids

    def get_song_names_from_album(self, album_uri):
        tracks = self.context.album_tracks(album_id=album_uri, limit=50)
        track_names = []
        for track in tracks.items:
            track_names.append(track.name)

        return track_names

    def get_song_name_from_uri(self, song_uri):
        song_id = song_uri
        if song_uri.startswith('spotify:track:'):
            song_id = song_uri.split(':')[2]

        song = self.context.track(song_id)
        return song.name

    def get_song_uris_from_playlist(self, playlist_uri):
        playlist_items = self.context.playlist_items(playlist_uri).items
        playlist_uris = []
        for item in playlist_items:
            playlist_uris.append(item.track.uri)
        return playlist_uris

    def get_song_names_from_playlist(self, playlist_uri):
        playlist_items = self.context.playlist_items(playlist_uri).items
        track_names = []
        for item in playlist_items:
            track_names.append(item.track.name)
        return track_names

    def add_song_to_queue(self, track_uri, device_id=None):
        if device_id is None:
            device_id = self.get_device_ids()[0]

        self.context.playback_queue_add(track_uri, device_id)


# This class wraps SpotifyService and provides high level functions meant to be user tasks. This should have no
# usage of tekore, but instead only makes calls via SpotifyService

# TODO: add functions for getting and setting device id
class SpotifyWrapper:
    def __init__(self, spotifyService):
        self.service = spotifyService
        self.set_device()

    def handle(self, request):
        functions = {
            'queue': {
                'queue_track': self.add_song_to_queue,
                'queue_album': self.add_album_to_queue,
                'queue_playlist': self.add_playlist_to_queue,
            },
            'set_device': self.set_device,
        }

        # TODO: fix this shit
        if request['request_type'] in functions['queue']:
            song_names = functions['queue'][request['request_type']](request['data'])
            text_to_send = 'Thanks, {}, the following songs have been added to the queue:\n{}'.format(
                request["user"]["name"].split(" ")[0], "\n".join(song_names))
            return text_to_send
        else:
            text_to_send = functions[request['request_type']](request['data'])
            return text_to_send

    # End User Functions

    def add_song_to_queue(self, song_id):
        if song_id.startswith('spotify:track:'):
            uri = song_id
        else:
            uri = f'spotify:track:{song_id}'

        self.service.add_song_to_queue(uri, self.device_id)
        return [self.service.get_song_name_from_uri(uri)]

    def add_album_to_queue(self, album_id):
        song_uris = self.service.get_song_uris_from_album(album_id)
        song_names = self.service.get_song_names_from_album(album_id)
        for song in song_uris:
            song_names.append(self.add_song_to_queue(song))
        return song_names

    def add_playlist_to_queue(self, playlist_id):
        song_uris = self.service.get_song_uris_from_playlist(playlist_id)
        song_names = self.service.get_song_names_from_playlist(playlist_id)
        it = (x for x in song_uris)
        for i, item in enumerate(it):
            self.add_song_to_queue(item, iterator=i)
        return song_names

    def set_device(self, device_name='office_echo'):
        device_names = {
            'office_echo': 'Office Echo',
            'work_laptop': 'Web Player (Chrome)',
            'everywhere': '',
            'phone': ''
        }

        devices = self.service.get_device_ids()
        new_device = next((item for item in devices if item.name == device_names[device_name]), None)
        self.device_id = new_device.id

        return f'Device has been changed to: {new_device.name}'

    def _get_device_id(self):
        unfiltered_devices = self.service.get_device_ids()
        device_ids = []

        for i in range(len(unfiltered_devices)):
            if unfiltered_devices[i].is_active:
                device_ids.append(unfiltered_devices[i].id)

        if len(device_ids) > 1:
            print(
                'More than one device ID active. In the future, you\'ll be able to select which ID you want. For now, try again or ask sara?')
            return None
        elif len(device_ids) == 0:
            print('no devices? owo')
        # raise NoActiveDevices('No active devices were found')
        else:
            return device_ids[0]
