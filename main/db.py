from google.appengine.ext import ndb

def createKey(pairs):
    return ndb.Key(pairs=pairs)
    
class Supplier(ndb.Model):
    name = ndb.StringProperty()

# ancestor = Organisation   
class Fund(ndb.Model):
    name = ndb.StringProperty()

# ancestor = Fund   
class Project(ndb.Model):
    name = ndb.StringProperty()
    dest_fund = ndb.KeyProperty(kind=Fund)
    state = ndb.StringProperty()

class Money(ndb.Model):
    currency = ndb.IntegerProperty()
    value = ndb.StringProperty()

# ancestor = Project   
class Grant(ndb.Model):
    amount = ndb.StructuredProperty(Money)
    dest_fund = ndb.KeyProperty(kind=Fund)
    state = ndb.IntegerProperty()

cap_key = Supplier.get_or_insert('mbale-cap', name='Mbale CAP').key
