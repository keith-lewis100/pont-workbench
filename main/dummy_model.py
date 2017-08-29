
grants = {}
nextid = 0

def getNextGrantId():
    global nextid
    nextid += 1
    return nextid
    
class Money:
    def __init__(self, currency, value):
        self.currency = currency
        self.value = value
        
    def __repr__(self):
        return 'Money(currency=%s,value=%s)' % (self.currency, self.value)

class Grant:
    def __init__(self, amount=None):
        self.key = None
        self.amount = amount
        
    def put(self):
        if self.key is None:
            self.key = getNextGrantId()
        grants[self.key] = self

    def __repr__(self):
        return 'Grant(key=%s,amount=%s)' % (self.key, self.amount)

def create_grant():
    return Grant(Money('sterling', None))
    
def list_grants():
    return grants.values()

