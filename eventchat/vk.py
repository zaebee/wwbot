import logging
import rx
import apiai
import aiovk
import ujson

import requests
import aiohttp
import asyncio
import async_timeout

from geopy.geocoders import Nominatim

from aiovk import TokenSession, API
from aiovk.longpoll import LongPoll

logger = logging.getLogger(__name__)
geolocator = Nominatim()

# TODO remove hard coded tokens
VK_ACCESS_TOKEN = '861765b84b9a76c19ddb6d9fbfca27e1d5fb20201ffb33f121cb35e0895f3ddbc87f4b692a71129ec5484'
AI_ACCESS_TOKEN = '490d6a1fb84141cda768a766ab1173a8'
PEER_ID = -155406641


def get_bits(n):
    b = []
    while n:
        b = [n & 1] + b
        n >>= 1
    return b or [0]


def get_flags(mask):
    flags = [
        'UNREAD',
        'OUTBOX',
        'REPLIED',
        'IMPORTANT',
        'CHAT',
        'FRIENDS',
        'SPAM',
        'DELЕTЕD',
        'FIXED',
        'MEDIA',
        'HIDDEN',
    ]
    bits = get_bits(mask)
    result = map(lambda x, y: (x, y), flags[::-1][-len(bits):], bits)
    return dict(result)


class VKChat:

    def __init__(self, *args, **kwargs):
        self.loop = asyncio.get_event_loop()
        self.vk_token = kwargs.get('vk_token', VK_ACCESS_TOKEN)
        self.ai_token = kwargs.get('ai_token', AI_ACCESS_TOKEN)
        self.peer_id = kwargs.get('peer_id', PEER_ID)

        self.session = aiovk.TokenSession(access_token=self.vk_token)
        self.vk = aiovk.API(self.session)
        self.ai = apiai.ApiAI(self.ai_token)

    @asyncio.coroutine
    def get_answer(self, user_id, message):
        request = self.ai.text_request()
        request.query = message
        request.session_id = user_id
        response = request.getresponse()
        data = ujson.loads(response.read())
        return data

    @asyncio.coroutine
    def send_answer(self, user_id, answer):
        result = answer['result']
        params = result['parameters']
        message = result['fulfillment']['speech']

        # send `welcome` message
        message = yield from self.send_message(user_id, message)
        events = yield from self.search_events(**params)

        if events and events.hits.total:
            for event in events:
                place = event.place
                if event.image:
                    # TODO upload photo to vk server
                    image = requests.get(event.image, stream=True)
                    files = {'photo': ('photo.jpg', image.content)}
                    server = yield from self.vk(
                        'photos.getMessagesUploadServer',
                        peer_id=user_id
                    )
                    print(server)
                    image_response = requests.post(
                        server['upload_url'],
                        files=files
                    )
                    image_response_json = image_response.json()
                    response = yield from self.vk(
                        'photos.saveMessagesPhoto',
                        hash=image_response_json['hash'],
                        photo=image_response_json['photo'],
                        server=image_response_json['server'],
                    )
                    print(response)
                    ###
                    images = response
                    if images:
                        image = images[0]
                        attach_photo = 'photo%s_%s'
                        attach_photo = attach_photo % (image['owner_id'], image['id'])

                kwargs = {
                    'lat': str(place.lat),
                    'lng': str(place.lon),
                    'attachment': attach_photo
                }

                text = '%s \n Даты:%s' % (
                    event.title, event.schedules
                )
                yield from self.send_message(
                    user_id,
                    text,
                    **kwargs
                )
        return events

    @asyncio.coroutine
    def search_events(self, **kwargs):
        if any(kwargs.values()):
            geocode = geolocator.geocode(kwargs.get('geo-city', ''))
            lat = geocode.raw.get('lat', None) if geocode else None
            lng = geocode.raw.get('lon', None) if geocode else None
            date = kwargs.get('date', [])
            query = kwargs.get('genre', '')
            params = {
                'start_date': date[0] if len(date) == 1 else None,
                'end_date': date[1] if len(date) == 2 else None,
                'query': query,
            }
            if lat and lng:
                params['lat'] = lat  # profile.get('lat', None),
                params['lng'] = lng  # profile.get('lng', None),
                params['radius'] = 1000  # profile.get('radius', 80000),

            events = Event.search_events(**params)
            return events

    @asyncio.coroutine
    def parse_message_updates(self, code, *args):
        user_id = None
        message = ''
        print('code', code, args)
        if code in [1, 2, 3, 4]:
            # `message_id` as first argument
            message_id = args[0]
            if code == 4:
                flags = get_flags(args[1])
                # got NOT outbox messages
                if not flags.get('OUTBOX', 0):
                    print('INBOX message_id', message_id)
                    user_id, timestamp, _, message, attachments = args[2:]
        return user_id, message

    @asyncio.coroutine
    def send_message(self, user_id, message, **kwargs):
        return self.vk(
            'messages.send',
            user_id=user_id,
            message=message,
            domain='whatwhere.world',
            peer_id=self.peer_id,
            **kwargs
        )

    @asyncio.coroutine
    def wait_user_input(self):
        # listen long poll user chat session
        longpoll = LongPoll(self.vk, mode=2)
        while True:
            result = yield from longpoll.wait()
            for update in result.get('updates', []):
                user_id, message = yield from self.parse_message_updates(*update)
                if user_id and message:
                    answer = yield from self.get_answer(user_id, message)
                    print('answer: %s' % answer)
                    events = yield from self.send_answer(user_id, answer)
            print('result: %s' % result)

    @asyncio.coroutine
    def observe_chat(self):
        task = self.loop.create_task(self.wait_user_input())
        # obs = rx.Observable.from_iterable(task)
        return self.loop.run_until_complete(task)
