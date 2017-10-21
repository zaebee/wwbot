# -*- coding: utf-8 -*-

from uuid import uuid4
from elasticsearch import Elasticsearch, TransportError

from django.conf import settings
from . exceptions import MissingObjectError


class ElasticsearchMixin(object):

    @classmethod
    def get_es(cls):
        if not hasattr(cls, '_es'):
            cls._es = Elasticsearch(**cls.get_es_connection_settings())
        return cls._es

    @classmethod
    def get_es_connection_settings(cls):
        return settings.ELASTICSEARCH_CONNECTION_PARAMS

    @classmethod
    def get_index_name(cls):
        raise NotImplementedError

    @classmethod
    def get_type_name(cls):
        raise NotImplementedError

    @classmethod
    def get_document(cls, obj):
        # TODO if Event `deleted=True` disallow for indexing
        raise NotImplementedError

    @classmethod
    def get_document_id(cls, obj):
        if not obj:
            raise MissingObjectError
        provider = obj.get('provider', 'ww')
        provider_id = obj.get('provider_id', uuid4())
        return '%s_%s' % (provider, provider_id)

    @classmethod
    def get_request_params(cls, obj):
        return {}

    @classmethod
    def should_index(cls, obj):
        return True

    @classmethod
    def bulk_index(cls, es=None, index_name='', queryset=None, refresh=True):
        es = es or cls.get_es()

        tmp = []

        if not queryset:
            return

        for obj in queryset:
            delete = not cls.should_index(obj)

            doc = {}
            if not delete:
                # allow for the case where a document cannot be indexed;
                # the implementation of `get_document()` should return a
                # falsy value.
                doc = cls.get_document(obj)
                if not doc:
                    continue

            data = {
                '_index': index_name or cls.get_index_name(),
                '_type': cls.get_type_name(),
                '_id': cls.get_document_id(obj)
            }
            data.update(cls.get_request_params(obj))
            data = {'delete' if delete else 'update': data}

            # bulk operation instructions/details
            tmp.append(data)

            # only append bulk operation data if it's not a delete operation
            if not delete:
                tmp.append({'doc': doc, 'doc_as_upsert': True})

        if tmp:
            es.bulk(tmp, refresh=refresh)

    @classmethod
    def index_add(cls, obj, index_name=''):
        if obj and cls.should_index(obj):
            doc = cls.get_document(obj)
            if not doc:
                return False

            instance = cls.get_es().index(
                index_name or cls.get_index_name(),
                cls.get_type_name(),
                doc,
                cls.get_document_id(obj),
                refresh=True,
                **cls.get_request_params(obj)
            )
            return instance
        return False

    @classmethod
    def index_update(cls, obj, index_name=''):
        if obj and cls.should_index(obj):
            doc = cls.get_document(obj)
            if not doc:
                return False

            body = {'doc': doc}
            instance = cls.get_es().update(
                index_name or cls.get_index_name(),
                cls.get_type_name(),
                cls.get_document_id(obj),
                body,
                refresh=True,
                **cls.get_request_params(obj)
            )
            return instance
        return False

    @classmethod
    def index_delete(cls, obj, index_name=''):
        if obj:
            try:
                cls.get_es().delete(
                    index_name or cls.get_index_name(),
                    cls.get_type_name(),
                    cls.get_document_id(obj),
                    **cls.get_request_params(obj)
                )
            except TransportError as e:
                if e.status_code != 404:
                    raise
            return True
        return False

    @classmethod
    def index_add_or_delete(cls, obj, index_name=''):
        if obj:
            if cls.should_index(obj):
                return cls.index_add(obj, index_name)
            else:
                return cls.index_delete(obj, index_name)
        return False
