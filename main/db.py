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
        
class Supplier(ndb.Model):
    name = ndb.StringProperty()

# ancestor = Organisation   
class Fund(ndb.Model):
    name = ndb.StringProperty()

# ancestor = Fund   
class Project(ndb.Model):
    name = ndb.StringProperty()
    dest_fund = ndb.KeyProperty(kind=Fund)
    state = EnumProperty(states.projectStates, default=states.PROJECT_APPROVAL_PENDING, required=True)

# ancestor = Project   
class Grant(ndb.Model):
    amount = MoneyProperty()
    state = EnumProperty(states.grantStates, default=states.GRANT_TRANSFER_PENDING, required=True)

# ancestor = Project   
class Pledge(ndb.Model):
    amount = MoneyProperty()
    state = EnumProperty(states.pledgeStates, default=states.PLEDGE_PENDING, required=True)
