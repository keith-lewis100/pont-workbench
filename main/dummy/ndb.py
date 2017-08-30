#_*_ coding: UTF-8 _*_

dbstore = {}
nextid = 0

def get_next_id():
    global nextid
    nextid += 1
    return nextid

class Key:
    def __init__(self, safeurl=None):
        pass

class Query:
    def __init__(self, kind):
        self.kind = kind
        if not dbstore.has_key(kind):
            dbstore[kind] = {}

    def fetch(self):
        return dbstore[self.kind].values()

class Model:
    def __init__(self, parent=None, **kwargs):
        self.key = None
        
    def put(self):
        if self.key is None:
            self.key = get_next_id()
        kind = self.__class__.__name__
        if not dbstore.has_key(kind):
            dbstore[kind] = {}
        entities = dbstore[kind]
        entities[self.key] = self

    @classmethod
    def query(cls, ancestor):
        return Query(cls.__name__)
    
    @classmethod
    def get_or_insert(cls, key_name, parent=None, **constructor_args):
        pass

class StringProperty:
    pass
    
class StructuredProperty:
    def __init__(self, klass):
        pass
    
class KeyProperty:
    def __init__(self, **kwargs):
        pass

class IntegerProperty:
    pass
