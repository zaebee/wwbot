# -*- coding: utf-8 -*-

import re
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from uuid import uuid4
from datetime import datetime
from pytils.translit import slugify
from services.elastic.mixins import ElasticsearchMixin
from services.schema import BasePlaceSerializer, BaseEventSerializer


class PlaceSerializer(BasePlaceSerializer, ElasticsearchMixin):
    provider = 'afi'
    index = 'place-index'
    doc_type = 'places'

    id_pattern = re.compile(r'([a-zA-Z]+)([\d]+)')

    @classmethod
    def get_index_name(cls):
        return cls.index

    @classmethod
    def get_type_name(cls):
        return cls.doc_type

    @classmethod
    def get_document(cls, obj):
        return obj

    def get_place_id(self, obj):
        provider_id = obj.get('company-id', 0)
        category, provider_id = self.id_pattern.search(provider_id).groups()
        return '%s_%s' % (self.provider, provider_id)

    def get_provider_id(self, obj):
        return obj.get('company-id', 0)

    def get_slug(self, obj):
        title = self.get_title(obj)
        slug = slugify(title)
        if not slug:
            slug = slugify(uuid4())
        return slug

    def get_title(self, obj):
        return obj['name']['#text']

    def get_address(self, obj):
        address = obj.get('address', {})
        return address.get('#text', None)

    def get_city(self, obj):
        return obj.get('city', '')

    def get_lat(self, obj):
        coords = obj.get('coordinates', {})
        lat = coords.get('lat', 0)
        if lat:
            lat = float(lat)
        return lat

    def get_lng(self, obj):
        coords = obj.get('coordinates', {})
        lng = coords.get('lon', 0)
        if lng:
            lng = float(lng)
        return lng

    def get_geometry(self, obj):
        return {
            'lat': self.get_lat(obj),
            'lon': self.get_lng(obj),
        }

    def get_email(self, obj):
        return obj.get('email', None)

    def get_website(self, obj):
        return obj.get('add-url', None)

    def get_phone(self, obj):
        phones = obj.get('phone', [])
        if isinstance(phones, dict):
            return phones.get('number', None)
        elif isinstance(phones, list):
            return [phone['number'] for phone in phones if 'number' in phone]


class EventSerializer(BaseEventSerializer, ElasticsearchMixin):
    provider = 'afi'
    index = 'event-index'
    doc_type = 'events'

    id_pattern = re.compile(r'([a-zA-Z]+)([\d]+)')
    place = PlaceSerializer(required=False, allow_null=True)

    @classmethod
    def get_index_name(cls):
        return cls.index

    @classmethod
    def get_type_name(cls):
        return cls.doc_type

    @classmethod
    def get_document(cls, obj):
        return obj

    def get_id(self, obj):
        provider_id = obj.get('creation-id', 0)
        category, provider_id = self.id_pattern.search(provider_id).groups()
        return '%s_%s' % (self.provider, provider_id)

    def get_provider_id(self, obj):
        return obj.get('creation-id', 0)

    def get_title(self, obj):
        return obj['name']['#text']

    def get_description(self, obj):
        description = obj['description']
        editorial_comment = obj['editorial-comment']
        widget_description = obj['widget-description']
        synopsis = obj['synopsis']

        description = description.get('#text', None)
        description = editorial_comment.get('#text', description)
        return description or synopsis.get('#text', None)

    def get_slug(self, obj):
        title = self.get_title(obj)
        slug = slugify(title)
        if not slug:
            slug = slugify(uuid4())
        return slug

    def get_category(self, obj):
        provider_id = obj.get('creation-id', 0)
        category, provider_id = self.id_pattern.search(provider_id).groups()
        return {
            'title': category,
            'slug': category,
        }

    def get_images(self, obj):
        return [{
            'image': self.get_image(obj)
        }]

    def get_image(self, obj):
        thumbnail = obj.get('main-photo', None)
        if thumbnail:
            return thumbnail
        else:
            return False

    def get_schedules(self, obj):
        start = obj.get('begin', None)
        end = obj.get('end', None)
        if start and end:
            return [{
                'start_date': start,
                'end_date': end,
            }]

    def get_counters(self, obj):
        favorites_count = obj.get('rating', 0)
        return {
            'rating': favorites_count
        }

    def get_author(self, obj):
        contacts = obj.get('contacts', [])
        if contacts:
            return contacts[0]

    def get_collections(self, obj):
        pass

    def get_ticket_price(self, obj):
        return obj.get('status', None)

    def get_ticket_url(self, obj):
        pass

    def get_currency(self, obj):
        pass

    def get_video_url(self, obj):
        pass

    def source_url(self, obj):
        url = obj.get('url', None)
        return url
