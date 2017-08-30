from google.appengine.ext import ndb

def createKey(url):
    return ndb.Key(safeurl=url)
    
class Organisation(ndb.Model):
    name = ndb.StringProperty()

# ancestor = Organisation   
class Fund(ndb.Model):
    name = ndb.StringProperty()

# ancestor = Fund   
class Project(ndb.Model):
    name = ndb.StringProperty()

class Money(ndb.Model):
    currency = ndb.IntegerProperty()
    value = ndb.StringProperty()

# ancestor = Project   
class Grant(ndb.Model):
    state = ndb.IntegerProperty()
    amount = ndb.StructuredProperty(Money)
    dest_fund = ndb.KeyProperty(kind=Fund)
