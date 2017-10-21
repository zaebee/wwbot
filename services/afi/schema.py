# -*- coding: utf-8 -*-

import re
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from uuid import uuid4
from datetime import datetime
from pytils.translit import slugify
from services.schema import BasePlaceSerializer, BaseEventSerializer


class PlaceSerializer(BasePlaceSerializer):
    provider = 'afi'

    def get_place_id(self, obj):
        return '%s_%s' % (self.provider, self.get_provider_id(obj))

    def get_provider_id(self, obj):
        return obj.get('id', 0)

    def get_slug(self, obj):
        title = self.get_title(obj)
        slug = slugify(title)
        if not slug:
            slug = slugify(uuid4())
        return slug

    def get_title(self, obj):
        return obj.get('title', '')

    def get_address(self, obj):
        return obj.get('address', '')

    def get_city(self, obj):
        return obj.get('city', '')

    def get_lat(self, obj):
        lat = obj.get('latitude', None)
        if lat:
            return float(lat)

    def get_lng(self, obj):
        lng = obj.get('longitude', None)
        if lng:
            return float(lng)

    def get_geometry(self, obj):
        return {
            'lat': self.get_lat(obj),
            'lon': self.get_lng(obj),
        }

    def get_email(self, obj):
        return obj.get('email', None)

    def get_website(self, obj):
        return obj.get('site_url', None)

    def get_phone(self, obj):
        return obj.get('phone', None)


class EventSerializer(BaseEventSerializer):
    provider = 'afi'
    id_pattern = re.compile(r'([a-zA-Z]+)([\d]+)')
    place = PlaceSerializer(required=False, allow_null=True)

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
        return category

    def get_images(self, obj):
        return [{
            'image': self.get_image(obj)
        }]

    def get_image(self, obj):
        thumbnail = obj.get('main-photo', None)
        if thumbnail:
            return thumbnail

    def get_schedules(self, obj):
        start = obj.get('start_date', None)
        end = obj.get('finish_date', None)
        if start and end:
            start = datetime.fromtimestamp(start).isoformat()
            end = datetime.fromtimestamp(end).isoformat()
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
