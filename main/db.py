from google.appengine.ext import ndb

def createKey(db_id):
    if db_id is None:
        return None
    return ndb.Key(urlsafe=db_id)
    
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

class Money(ndb.Model):
    currency = ndb.StringProperty(default='sterling')
    value = ndb.IntegerProperty()

# ancestor = Project   
class Grant(ndb.Model):
    amount = ndb.StructuredProperty(Money)
    state = ndb.StringProperty(default='transferPending')

# ancestor = Project   
class Pledge(ndb.Model):
    amount = ndb.StructuredProperty(Money)
    state = ndb.StringProperty(default='pending')
