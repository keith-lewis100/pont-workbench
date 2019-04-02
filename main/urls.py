#_*_ coding: UTF-8 _*_

def url_for_entity(entity):
    key = entity.key
    return '/%s/%s' % (key.kind().lower(), key.urlsafe())

def url_for_list(kind, parent):
    url = '/%s_list' % kind.lower()
    if parent is None:
        return url
    return url + '/' + parent.key.urlsafe()
