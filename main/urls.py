#_*_ coding: UTF-8 _*_

from flask import url_for

def url_for_entity(entity, external=False):
    key = entity.key
    endpoint = 'view_%s' % key.kind().lower()
    return url_for(endpoint, db_id=key.urlsafe(), _external=external)

def url_for_list(kind, parent, **query_params):
    endpoint = 'view_%s_list' % kind.lower()
    if parent is None:
        return url_for(endpoint, **query_params)
    return url_for(endpoint, db_id=parent.key.urlsafe(), **query_params)
