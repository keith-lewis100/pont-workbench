#_*_ coding: UTF-8 _*_

from google.appengine.ext import ndb
import json
#import role_types

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
        money_dict = { 'currency': value.currency, 'value': value.value }
        return json.dumps(money_dict)

    def _from_base_type(self, base):
        money_dict = json.loads(base)
        return Money(money_dict['currency'], money_dict['value'])

class WorkBench(ndb.Model):
    last_ref_id = ndb.IntegerProperty(default=0)

class Supplier(ndb.Model):
    name = ndb.StringProperty()
    
# ancestor = Supplier  
class SupplierFund(ndb.Model):
    name = ndb.StringProperty()
    description = ndb.StringProperty()
    
class User(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()

# ancestor = User
class Role(ndb.Model):
    type_index = ndb.IntegerProperty()
    committee = ndb.StringProperty()

class Fund(ndb.Model):
    name = ndb.StringProperty()
    description = ndb.StringProperty()
    committee = ndb.StringProperty()

# ancestor = Fund   
class InternalTransfer(ndb.Model):
    description = ndb.StringProperty()
    amount = MoneyProperty(default=Money())
    dest_fund = ndb.KeyProperty(kind=Fund)
    state_index = ndb.IntegerProperty(default=0)
    creator = ndb.KeyProperty(kind=User)

# ancestor = Fund   
class Project(ndb.Model):
    name = ndb.StringProperty()
    description = ndb.StringProperty()
    dest_fund = ndb.KeyProperty(kind=SupplierFund)
    state_index = ndb.IntegerProperty(default=0)

# ancestor = Project   
class Grant(ndb.Model):
    description = ndb.StringProperty()
    amount = MoneyProperty(default=Money())
    state_index = ndb.IntegerProperty(default=0)
    creator = ndb.KeyProperty(kind=User)

# ancestor = Project   
class Pledge(ndb.Model):
    amount = MoneyProperty(default=Money())
    ref_id = ndb.StringProperty()
    state_index = ndb.IntegerProperty(default=0)
    creator = ndb.KeyProperty(kind=User)
    
# ancestor = Project
class Purchase(ndb.Model):
    description = ndb.StringProperty()
    amount = MoneyProperty(default=Money())
    state_index = ndb.IntegerProperty(default=0)
    po_number = ndb.StringProperty()
    supplier = ndb.KeyProperty(kind=Supplier)
    creator = ndb.KeyProperty(kind=User)
