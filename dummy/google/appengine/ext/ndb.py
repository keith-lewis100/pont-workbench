
nextid = 0

def get_next_id():
    global nextid
    nextid += 1
    return nextid

repo = {}

class Key:
  def __init__(self, kind=None, id=None, parent=None, urlsafe=None):
    self._kind = kind
    self._id = str(id)
    self.parent_key = parent
    if urlsafe:
      index = urlsafe.rfind(':')
      if index > 0:
        self.parent_key = Key(urlsafe[0:index])
        urlsafe = urlsafe[index+1:]
      pair = urlsafe.split('-', 1)
      self._kind = pair[0]
      self._id = pair[1]

  def kind(self):
    return self._kind

  def id(self):
    return self._id

  def get(self):
    store = repo.setdefault(self._kind, {})
    return store.get(self._id)

  def parent(self):
    return self.parent_key

  def urlsafe(self):
    result = ""
    if self.parent_key:
       result = self.parent_key.urlsafe() + ':'
    return self._kind + '-' + str(self._id)

  def __cmp__(self, other):
      if not hasattr(other, '_id'):
          return False
      return cmp(self._id, other._id)

class StringProperty:
  def __init__(self, default=None):
    self.default = default

class IntegerProperty:
  def __init__(self, default=None):
    self.default = default

class BooleanProperty:
  def __init__(self, default=None):
    self.default = default

class KeyProperty:
  def __init__(self, kind=None, default=None):
    self.default = default

class DateProperty:
   def __init__(self, auto_now_add=False):
       self.default = None

class DateTimeProperty:
   def __init__(self, auto_now_add=False):
       self.default = None

   def __neg__(self):
       return self

class StructuredProperty:
    def __init__(self, cls):
       self.default = None

class Query:
    def __init__(self, kind, ancestor=None):
        self.kind = kind
        self.ancestor = ancestor

    def count(self):
        return 0

    def get(self):
        store = repo.setdefault(self.kind, {})
        if len(store) > 0:
            return store.itervalues().next()
        return None

    def fetch(self):
        store = repo.setdefault(self.kind, {})
        if self.ancestor is None:
            return store.values()
        return [e for e in store.values() if e.key.parent() == self.ancestor]

    def order(self, *args):
        return self

    def iter(self, **kwargs):
        return []

class Model(object):
    @classmethod
    def get_or_insert(cls, id):
        kind = cls.__name__
        key = Key(kind, id)
        obj = key.get()
        if obj:
            return obj
        obj = cls(id=id)
        obj.put()
        return obj

    @classmethod
    def query(cls, *args, **kwargs):
        return Query(cls.__name__, **kwargs)

    def __init__(self, id=None, parent=None):
        kind = type(self).__name__
        if not id:
            id = get_next_id()
        self.key = Key(kind, id, parent)
        for attr_name, attr in type(self).__dict__.iteritems():
            if hasattr(attr, 'default'):
                setattr(self, attr_name, getattr(attr, 'default'))

    def put(self):
        store = repo.setdefault(self.key._kind, {})
        store[self.key._id] = self
