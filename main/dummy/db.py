#_*_ coding: UTF-8 _*_

import logging

nextid = 0

models = {}

def get_next_id():
    global nextid
    nextid += 1
    return nextid

def lookup_model(kind):
    return models[kind]

class Key:
    def __init__(self, parent, kind, id):
        self._parent = parent
        self._kind = kind
        self._id = id
        
    def pairs(self):
        result = []
        if self._parent:
            result = self._parent.pairs()
        result.append((self._kind, self._id))
        return result
        
    def urlsafe(self):
        return str(self._id)
    
    def get(self):
        model = lookup_model(self._kind)
        return model.store[self]

    def __hash__(self):
        return hash((self._parent, self._kind, self._id))
        
    def __eq__(self, other):
        return (self._parent, self._kind, self._id) == (other._parent, other._kind, other._id)

    def __repr__(self):
        return 'Key(parent=%s, kind=%s, id=%s)' % (self._parent, self._kind, self._id)

def createKey(pairs):
    key = None
    for kind, id in pairs:
        key = Key(key, kind, int(id))
    return key

class Query:
    def __init__(self, store, ancestor=None):
        self.store = store
        self.ancestor = ancestor
        
    def fetch(self):
        if self.ancestor is None:
            return self.store.values()
        result = []
        for key, value in self.store.items():
            if key._parent == self.ancestor:
                result.append(value)
        return result

class Model:
    @classmethod
    def query(cls, **kwargs):
        return Query(cls.store, **kwargs)
            
    def put(self):
        model = self.__class__
        model.store[self.key] = self
        return self.key
    
class Organisation(Model):        
    store = {}

    def __init__(self, name=None):
        self.key = Key(None, 'Organisation', get_next_id())
        self.name = name
                
    def __repr__(self):
        return 'Organisation(key=%s, name=%s)' % (self.key, self.name)

class Fund(Model):
    store = {}

    def __init__(self, parent, name=None):
        self.key = Key(parent, 'Fund', get_next_id())
        self.name = name
        
    def __repr__(self):
        return 'Fund(key=%s, name=%s)' % (self.key, self.name)

class Project(Model):
    store = {}
    
    def __init__(self, parent):
        self.key = Key(parent, 'Project', get_next_id())
        self.name = None
        self.dest_fund = None
        
    def __repr__(self):
        return 'Project(key=%s, name=%s, dest_fund=%s)' % (self.key, 
                            self.name, str(self.dest_fund))

class Money:
    def __init__(self, currency='sterling', value=None):
        self.currency = currency
        self.value = value
        
    def __repr__(self):
        return 'Money(currency=%s,value=%s)' % (self.currency, self.value)

    def __str__(self):
        if self.currency=='sterling':
            return u'£' + str(self.value)
        else:
            return str(self.value) + 'Ush'

class Grant(Model):
    store = {}
    
    def __init__(self, parent):
        self.key = Key(parent, 'Grant', get_next_id())
        self.amount = Money()
        self.dest_fund = None
        self.payment = None

    def __repr__(self):
        return 'Grant(key=%s, amount=%s)' % (self.key, self.amount)

class Payment(Model):
    store = {}
    
    def __init__(self, parent):
        self.key = Key(parent, 'Payment', get_next_id())
        self.rate = None

    def __repr__(self):
        return 'Grant(key=%s, rate=%s)' % (self.key, self.amount)

class Pledge(Model):
    store = {}

    def __init__(self, parent):
        self.key = Key(parent, 'Pledge', get_next_id())
        self.ref = None
        self.amount = None
        
    def __repr__(self):
        return 'Pledge(key=%s, amount=%s)' % (self.key, self.amount)

models['Organisation'] = Organisation        
models['Fund'] = Fund
models['Project'] = Project
models['Grant'] = Grant
models['Payment'] = Payment
models['Pledge'] = Pledge

cap_key = Organisation(name ='Mbale CAP').put()

Fund(cap_key, "Livelihoods").put()
Fund(cap_key, "Churches").put()
