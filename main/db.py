#_*_ coding: UTF-8 _*_

from google.appengine.ext import ndb
import json
import states

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

class EnumProperty(ndb.IntegerProperty):
    def __init__(self, enumArray, **kwargs):
        super(EnumProperty, self).__init__(**kwargs)
        self.enumArray = enumArray
        
    def _validate(self, enum):
         pass
       
    def _to_base_type(self, enum):
        return enum.index

    def _from_base_type(self, index):
        return self.enumArray[index]

class WorkBench(ndb.Model):
    last_ref_id = ndb.IntegerProperty(default=0)

class Supplier(ndb.Model):
    name = ndb.StringProperty()
    
class User(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()

# ancestor = Supplier or None   
class Fund(ndb.Model):
    name = ndb.StringProperty()
    description = ndb.StringProperty()
    committee = ndb.StringProperty()

# ancestor = Fund   
class InternalTransfer(ndb.Model):
    description = ndb.StringProperty()
    amount = MoneyProperty(default=Money())
    dest_fund = ndb.KeyProperty(kind=Fund)
    state = EnumProperty(states.transferStates, default=states.TRANSFER_PENDING)
    creator = ndb.KeyProperty(kind=User)

# ancestor = Fund   
class Project(ndb.Model):
    name = ndb.StringProperty()
    description = ndb.StringProperty()
    dest_fund = ndb.KeyProperty(kind=Fund)
    state = EnumProperty(states.projectStates, default=states.PROJECT_APPROVAL_PENDING)

# ancestor = Project   
class Grant(ndb.Model):
    description = ndb.StringProperty()
    amount = MoneyProperty(default=Money())
    state = EnumProperty(states.grantStates, default=states.GRANT_TRANSFER_PENDING)
    creator = ndb.KeyProperty(kind=User)

# ancestor = Project   
class Pledge(ndb.Model):
    amount = MoneyProperty(default=Money())
    ref_id = ndb.StringProperty()
    state = EnumProperty(states.pledgeStates, default=states.PLEDGE_PENDING)
    creator = ndb.KeyProperty(kind=User)
    
# ancestor = Project
class Purchase(ndb.Model):
    description = ndb.StringProperty()
    amount = MoneyProperty(default=Money())
    state = EnumProperty(states.purchaseStates, default=states.PURCHASE_APPROVING)
    po_number = ndb.StringProperty()
    creator = ndb.KeyProperty(kind=User)
