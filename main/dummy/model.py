#_*_ coding: UTF-8 _*_

grants = {}
nextid = 0

def getNextGrantId():
    global nextid
    nextid += 1
    return nextid

class Key:
    def __init__(self, parent, kind, id):
        self._parent = parent
        self._kind = kind
        self._id = id
        
    def pairs(self):
        result = []
        if self._parent:
            result = self._parent.pairs()
        return result.append((self._kind, self._id))
        
    def id(self):
        return self._id

def createKey(pairs):
    key = None
    for kind, id in pairs:
        key = Key(key, kind, id)
    return key

class Project:
    def __init__(self, name):
        self.name = name
        self.key = Key(None, 'Project', getNextGrantId())

class Money:
    def __init__(self, currency, value):
        self.currency = currency
        self.value = value
        
    def __repr__(self):
        return 'Money(currency=%s,value=%s)' % (self.currency, self.value)

    def __str__(self):
        if self.currency=='sterling':
            return u'£' + str(self.value)
        else:
            return str(self.value) + 'Ush'

class Grant:
    def __init__(self, parent, amount):
        self.key = Key(parent, 'Grant', getNextGrantId())
        self.amount = amount
        
    def put(self):
        grants[self.key] = self

    def __repr__(self):
        return 'Grant(key=%s, amount=%s)' % (self.key, self.amount)
        
def list_projects(*key_pairs):
    return [Project("OVC01")]

def lookup_project(*key_pairs):
    return Project("OVC01")

def create_grant(*key_pairs):
    parent = createKey(key_pairs)
    return Grant(parent=parent, amount=Money('sterling', None))
    
def list_grants(*key_pairs):
    return grants.values()

def lookup_grant(*key_pairs):
    key = createKey(key_pairs)
    return grants[key]