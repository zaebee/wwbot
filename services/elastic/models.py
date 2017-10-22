# -*- coding: utf-8 -*-

from datetime import datetime
from django.utils import timezone
from django.conf import settings

from elasticsearch_dsl.connections import connections

from elasticsearch_dsl import (
    Q,
    DocType, Date, Nested, Boolean, Object,
    Long, Integer, String, GeoPoint, Float,
    InnerObjectWrapper, Completion, Keyword, Text
)

# configure default ES connection
connections.configure(default=settings.ELASTICSEARCH_CONNECTION_PARAMS)


class Schedule(InnerObjectWrapper):
    @property
    def age(self):
        if self.start_date.tzinfo:
            now = datetime.now(timezone.utc)
        else:
            now = datetime.now()
        return now - self.start_date


class Place(InnerObjectWrapper):
    def get_language(self, lang_code):
        return getattr(self, lang_code, None)


class Counter(InnerObjectWrapper):
    @property
    def total(self):
        as_dict = self.to_dict()
        return sum(as_dict.values())


class Locales(InnerObjectWrapper):
    def get_language(self, lang_code):
        return getattr(self, lang_code, None)


class Event(DocType):
    title = Text(multi=True, fields={
        'en': String(analyzer='english'),
        'ru': String(analyzer='russian'),
        # 'raw': String(analyzer='trigrams'),
        'raw': Keyword(),
        },
        analyzer='russian')
    title_localized = Object(
        doc_class=Locales,
        properties={
            'raw': String(analyzer='trigrams'),
            'en': String(analyzer='english'),
            'ru': String(analyzer='russian'),
            'de': String(analyzer='dutch'),
            'fr': String(analyzer='french'),
            'es': String(analyzer='spanish'),
        }
    )
    title_suggest = Completion()
    description = Text(analyzer='russian')
    description_localized = Object(
        doc_class=Locales,
        properties={
            'raw': String(analyzer='trigrams'),
            'en': String(analyzer='english'),
            'ru': String(analyzer='russian'),
            'de': String(analyzer='dutch'),
            'fr': String(analyzer='french'),
            'es': String(analyzer='spanish'),
        }
    )
    slug = Text(fields={'raw': Keyword()})
    provider = Text()
    provider_id = Text()
    ticket_price = Text()
    ticket_url = Text()
    video_url = Text()
    deleted = Boolean()
    image = Text()
    average_rate = Float()
    category = Object(
        properties={
            'title': Text(fields={'raw': Keyword()}, analyzer='russian'),
            'slug': Text(fields={'raw': Keyword()})
        }
    )
    place = Object(
        doc_class=Place,
        properties={
            'place_id': Text(fields={'raw': Keyword()}),
            'provider_id': Text(fields={'raw': Keyword()}),
            'slug': String(),
            'title': Text(fields={'raw': Keyword()}, analyzer='russian'),
            'title_localized': Object(
                doc_class=Locales,
                properties={
                    'raw': String(analyzer='trigrams'),
                    'en': String(analyzer='english'),
                    'ru': String(analyzer='russian'),
                    'de': String(analyzer='dutch'),
                    'fr': String(analyzer='french'),
                    'es': String(analyzer='spanish'),
                }
            ),
            'address': Text(fields={'raw': Keyword()}, analyzer='russian'),
            'address_localized': Object(
                doc_class=Locales,
                properties={
                    'raw': String(analyzer='trigrams'),
                    'en': String(analyzer='english'),
                    'ru': String(analyzer='russian'),
                    'de': String(analyzer='dutch'),
                    'fr': String(analyzer='french'),
                    'es': String(analyzer='spanish'),
                }
            ),
            'city': Text(fields={'raw': Keyword()}, analyzer='russian'),
            'description': Text(),
            'description_localized': Object(
                doc_class=Locales,
                properties={
                    'raw': String(analyzer='trigrams'),
                    'en': String(analyzer='english'),
                    'ru': String(analyzer='russian'),
                    'de': String(analyzer='dutch'),
                    'fr': String(analyzer='french'),
                    'es': String(analyzer='spanish'),
                }
            ),
            'lat': Float(),
            'lng': Float(),
            'geometry': GeoPoint(),
            'email': Text(),
            'website': Text(),
            'phone': Text()
        }
    )
    images = Nested(
        properties={
            'image': Text(),
        }
    )
    dates = Object(
        doc_class=Schedule,
        properties={
            'start_date': Date(
                format="YYYY-MM-dd||"
                "YYYY-MM-dd'T'HH:mm:ss"
            ),
            'end_date': Date(
                format="YYYY-MM-dd||"
                "YYYY-MM-dd'T'HH:mm:ss"
            )
        }
    )
    schedules = Object(
        doc_class=Schedule,
        properties={
            'start_date': Date(
                format="YYYY-MM-dd||"
                "YYYY-MM-dd'T'HH:mm:ss.SSS||"
                "YYYY-MM-dd'T'HH:mm:ss||"
                "YYYY-MM-dd'T'HH:mm:ssZ||"
                "dd.MM.YYYY'T'HH:mm:ss"
            ),
            'end_date': Date(
                format="YYYY-MM-dd||"
                "YYYY-MM-dd'T'HH:mm:ss.SSS||"
                "YYYY-MM-dd'T'HH:mm:ss||"
                "YYYY-MM-dd'T'HH:mm:ssZ||"
                "dd.MM.YYYY'T'HH:mm:ss"
            )
        }
    )
    date_added = Date()
    counters = Object(
        doc_class=Counter,
        properties={
            'favorites_count': Integer(),
            'interested_count': Integer(),
            'rating': Integer(),
        }
    )
    source_url = String()
    min_price = Integer()
    max_price = Integer()
    is_free = Boolean()
    currency = String()
    formatted_price = String()

    class Meta:
        doc_type = 'events'
        index = 'event-index'

    def save(self, **kwargs):
        if not self.date_added:
            self.date_added = datetime.now()
        return super(Event, self).save(**kwargs)

    def search_events(self, limit=100, **kwargs):
        """
        Build ES query fillter by `kwargs` params.
        kwargs = {
            'q': 'query string',
            'start_date': 'now'
            'end_date': 'now+7d',
            'radius': 0,
            'lat': 0.0,
            'lng': 0.0,
            'actual': False,
            ....
        }
        """
        search = self.search()
        search = search.exclude('term', deleted=True)

        observable = kwargs.get('observable', False)
        start_date = kwargs.get('start_date', None)
        end_date = kwargs.get('end_date', None)

        limit_from = kwargs.get('limit_from', 0)
        limit_to = kwargs.get('limit_to', 18)

        if not start_date:
            search = search.query(
                'range',
                **{'schedules.end_date': {
                    'lte': 'now+1y/d',
                    'gte': 'now/d'
                }}
            )

        if 'q' in kwargs and kwargs['q']:
            search = search.query(
                'multi_match',
                query=kwargs['q'],
                type='most_fields',
                minimum_should_match='75%',
                operator='and',
                tie_breaker=0.8,
                fields=['title^4', 'description',
                        'place.city', 'place.title^2', 'place.address']
            )

        if start_date and end_date:
            search = search.query(
                'range',
                **{'schedules.start_date': {
                    'gte': '{start_date}||/d'.format(**kwargs),
                    'lte': '{end_date}||/d'.format(**kwargs)
                }}
            )

        elif start_date:
            search = search.query(
                'range',
                **{'schedules.start_date': {
                    'gte': '{start_date}||/d'.format(**kwargs),
                    'lte': '{start_date}||/d'.format(**kwargs)
                }}
            )
        elif end_date:
            search = search.query(
                'range',
                **{'schedules.start_date': {
                    'gte': '{end_date}||/d'.format(**kwargs),
                    'lte': '{end_date}||/d'.format(**kwargs)
                }}
            )

        if 'radius' in kwargs and 'lat' in kwargs and 'lng' in kwargs:
            search = search.query('bool', filter=Q(
                'geo_distance',
                distance='{radius}m'.format(**kwargs),
                **{'place.geometry': {
                    'lat': kwargs['lat'], 'lon': kwargs['lng']
                }}
            ))

        search = search.sort('schedules.start_date')
        search = search[limit_from:limit_to]
        return search if observable else search.execute()


class Collection(DocType):
    title = Text(multi=True, fields={
        'en': String(analyzer='english'),
        'ru': String(analyzer='russian'),
        # 'raw': String(analyzer='trigrams'),
        'raw': Keyword(),
        },
        analyzer='russian')
    title_localized = Object(
        doc_class=Locales,
        properties={
            'raw': String(analyzer='trigrams'),
            'en': String(analyzer='english'),
            'ru': String(analyzer='russian'),
            'de': String(analyzer='dutch'),
            'fr': String(analyzer='french'),
            'es': String(analyzer='spanish'),
        }
    )
    slug = String()
    title_suggest = Completion()
    provider_id = Text(fields={'raw': Keyword()})
    description = Text(analyzer='russian')
    description_localized = Object(
        doc_class=Locales,
        properties={
            'raw': String(analyzer='trigrams'),
            'en': String(analyzer='english'),
            'ru': String(analyzer='russian'),
            'de': String(analyzer='dutch'),
            'fr': String(analyzer='french'),
            'es': String(analyzer='spanish'),
        }
    )
    public = Boolean()
    deleted = Boolean()
    events = String()
    events_count = Long()
    places = String()
    exclude_places = String()
    get_preview = Nested(
        properties={
            'image': Text(),
        }
    )
    date_added = Date()
    date_updated = Date()

    application_id = Keyword()
    source_url = String()
    limit_dates = Boolean()
    limit_date_from = Date()
    limit_date_to = Date()

    def remove_event(self, event_id):
        if self.events and event_id in self.events:
            self.events.remove(event_id)
            self.events_count = len(self.events)
            self.date_updated = datetime.now()

    class Meta:
        doc_type = 'collections'
        index = 'event-index'

    def save(self, **kwargs):
        update_date = kwargs.pop('update_date', False)
        if update_date:
            self.date_updated = datetime.now()
        if not self.date_added:
            self.date_added = datetime.now()
        return super(Collection, self).save(**kwargs)


class EventPlace(DocType):
    place_id = Text(fields={'raw': Keyword()})
    provider_id = Text(fields={'raw': Keyword()})
    provider = Text()
    date_added = Date()
    slug = String(fields={'raw': Keyword()})
    title = Text(fields={'raw': Keyword()}, analyzer='russian')
    address = Text(fields={'raw': Keyword()}, analyzer='russian')
    city = Text(fields={'raw': Keyword()}, analyzer='russian')
    description = Text()
    lat = Float()
    lng = Float()
    geometry = GeoPoint()
    email = Text()
    website = Text()
    phone = Text()

    class Meta:
        doc_type = 'places'
        index = 'place-index'

    def save(self, **kwargs):
        if not self.date_added:
            self.date_added = datetime.now()
        return super(EventPlace, self).save(**kwargs)
