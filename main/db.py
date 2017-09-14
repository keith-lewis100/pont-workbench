from google.appengine.ext import ndb

def createKey(urlsafe):
    if urlsafe is None:
        return None
    return ndb.Key(urlsafe=urlsafe)
    
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
    currency = ndb.StringProperty()
    value = ndb.IntegerProperty()

# ancestor = Project   
class Grant(ndb.Model):
    amount = ndb.StructuredProperty(Money)
    dest_fund = ndb.KeyProperty(kind=Fund)
    state = ndb.StringProperty()
