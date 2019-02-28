
nextid = 0

def get_next_id():
    global nextid
    nextid += 1
    return nextid

datastore = {}

class Key:
  def __init__(self, kind, id, parent_key):
    self._kind = kind
    self._id = id
    self.parent_key = parent_key

  def kind(self):
    return self._kind

  def id(self):
    return self._id

  def get(self):
    return datastore.get(self._id)

  def parent(self):
    return self.parent_key

  def urlsafe(self):
      return self._kind + '-' + str(self._id)

class StringProperty:
    def __init__(self, default=None):
        pass

class IntegerProperty:
    def __init__(self, default=None):
        pass

class BooleanProperty:
    def __init__(self, default=None):
        pass

class KeyProperty:
   def __init__(self, kind=None):
       pass

class DateProperty:
   def __init__(self, auto_now_add=False):
       pass
   
class Query:
    def count(self):
        return 0

class Model:
    @staticmethod
    def get_or_insert(id):
        return None

    @staticmethod
    def query(*args):
        return Query()

    def __init__(self, parent=None):
        id = get_next_id()
        self.key = Key('kind', id, parent)

    def put(self):
        datastore[self.key.id()] = self
