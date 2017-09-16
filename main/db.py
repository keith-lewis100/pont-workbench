#_*_ coding: UTF-8 _*_

from google.appengine.ext import ndb
import json

def createKey(db_id):
    if db_id is None:
        return None
    return ndb.Key(urlsafe=db_id)

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
            return str(self.value) + ' Ush'

class MoneyProperty(ndb.StringProperty):
    def _validate(self, value):
        if not isinstance(value, Money):
            raise TypeError('expected a Money value, got %s' % repr(value))

    def _to_base_type(self, value):
        money_dict = { 'c': value.currency, 'v': value.value }
        return json.dumps(money_dict)

    def _from_base_type(self, base):
        money_dict = json.loads(base)
        return Money(money_dict['c'], money_dict['v'])

class Supplier(ndb.Model):
    name = ndb.StringProperty()

# ancestor = Organisation   
class Fund(ndb.Model):
    name = ndb.StringProperty()

# ancestor = Fund   
class Project(ndb.Model):
    name = ndb.StringProperty()
    dest_fund = ndb.KeyProperty(kind=Fund)
    state = ndb.StringProperty(default='approvalPending')

# ancestor = Project   
class Grant(ndb.Model):
    amount = MoneyProperty()
    state = ndb.StringProperty(default='transferPending')

# ancestor = Project   
class Pledge(ndb.Model):
    amount = MoneyProperty()
    state = ndb.StringProperty(default='pending')
