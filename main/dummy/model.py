#_*_ coding: UTF-8 _*_

import logging

projects = {}
grants = {}
pledges = {}
nextid = 0

def get_next_id():
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
        result.append((self._kind, self._id))
        return result
        
    def id(self):
        return self._id
        
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

class Project:
    def __init__(self, parent):
        self.name = None
        self.key = Key(parent, 'Project', get_next_id())
        
    def put(self):
        logging.debug("storing project with key=" + str(self.key))
        projects[self.key] = self

    def __repr__(self):
        return 'Project(key=%s, name=%s)' % (self.key, self.name)

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

class Grant:
    def __init__(self, parent, amount):
        self.key = Key(parent, 'Grant', get_next_id())
        self.amount = amount
        
    def put(self):
        grants[self.key] = self

    def __repr__(self):
        return 'Grant(key=%s, amount=%s)' % (self.key, self.amount)


def create_project(*key_pairs):
    parent = createKey(key_pairs)
    return Project(parent=parent)
        
def list_projects(*key_pairs):
    return projects.values()

def lookup_project(*key_pairs):
    key = createKey(key_pairs)
    return projects[key]
    
def create_grant(*key_pairs):
    parent = createKey(key_pairs)
    return Grant(parent=parent, amount=Money())
    
def list_grants(*key_pairs):
    return grants.values()

def lookup_grant(*key_pairs):
    key = createKey(key_pairs)
    return grants[key]