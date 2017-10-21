# -*- coding: utf-8 -*-

from uuid import uuid4
from datetime import datetime
from dateutil.parser import parse

from rest_framework import serializers


class BasePlaceSerializer(serializers.Serializer):
    """
    Field mapping to our app.model.EventPlace
    Overrides in providers schema
    """
    provider = 'ww'
    place_id = serializers.SerializerMethodField()
    provider_id = serializers.SerializerMethodField()
    provider = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()
    geometry = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()

    email = serializers.SerializerMethodField()
    website = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()

    def get_place_id(self, obj):
        provider_id = self.get_provider_id(obj)
        if provider_id:
            return '%s_%s' % (self.provider, provider_id)

    def get_provider_id(self, obj):
        return obj.get('id', 0)

    def get_provider(self, obj):
        return self.provider

    def get_description(self, obj):
        return obj.get('description', '')


class BaseEventSerializer(serializers.Serializer):
    """
    Field mapping to our app.model.Event
    Overrides in providers schema
    """
    id = serializers.SerializerMethodField()
    provider_id = serializers.SerializerMethodField()
    provider = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()

    author = serializers.SerializerMethodField()
    collections = serializers.SerializerMethodField()
    place = BasePlaceSerializer(read_only=True)
    source_url = serializers.SerializerMethodField()

    category = serializers.SerializerMethodField()
    ticket_price = serializers.SerializerMethodField()
    ticket_url = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()

    images = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    schedules = serializers.SerializerMethodField()
    dates = serializers.SerializerMethodField()
    date_added = serializers.SerializerMethodField()
    deleted = serializers.SerializerMethodField()
    counters = serializers.SerializerMethodField()

    min_price = serializers.SerializerMethodField()
    max_price = serializers.SerializerMethodField()
    is_free = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    formatted_price = serializers.SerializerMethodField()

    def get_date_added(self, obj):
        return datetime.now()

    def get_dates(self, obj):
        dates = []
        now = datetime.now()
        schedules = self.get_schedules(obj) or []
        for schedule in schedules:
            actual = {}
            start = schedule.get('start_date', None)
            end = schedule.get('end_date', None)

            start = parse(start) if start else None
            end = parse(end) if end else None
            # start_time = parse(start_date).strftime('%H:%M')
            # end_time = parse(end_date).strftime('%H:%M')

            if end and end.date() >= now.date():
                actual['start_date'] = start.date() if start else None
                actual['start_time'] = start.strftime('%H:%M') if start else None
                actual['end_date'] = end.date()
                actual['end_time'] = end.strftime('%H:%M')
            elif start and start.date() >= now.date():
                actual['start_date'] = start.date()
                actual['start_time'] = start.strftime('%H:%M')
                actual['end_date'] = end.date() if end else None
                actual['end_time'] = end.strftime('%H:%M') if end else None
            if actual:
                dates.append(actual)
        return dates[:300]

    def get_provider(self, obj):
        return self.provider

    def get_provider_id(self, obj):
        return obj.get('provider_id', None)

    def get_id(self, obj):
        return '%s_%s' % (self.provider, obj['id'])

    def get_deleted(self, obj):
        return False

    def get_source_url(self, obj):
        return None

    def get_min_price(self, obj):
        pass

    def get_max_price(self, obj):
        pass

    def get_is_free(self, obj):
        pass

    def get_currency(self, obj):
        pass

    def get_formatted_price(self, obj):
        pass
