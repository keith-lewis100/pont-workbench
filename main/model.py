#import db
from dummy import db

def lookup_entity(*key_pairs):
    key = db.createKey(key_pairs)
    return key.get()
        
def create_fund(*key_pairs):
    parent = db.createKey(key_pairs)
    return db.Fund(parent=parent)
    
def fund_query(*key_pairs):
    parent = db.createKey(key_pairs)
    return db.Fund.query(ancestor=parent)

def create_project(*key_pairs):
    parent = db.createKey(key_pairs)
    return db.Project(parent=parent)
        
def list_projects(*key_pairs):
    parent = db.createKey(key_pairs)
    return db.Project.query(ancestor=parent).fetch()
    
def create_grant(*key_pairs):
    parent = db.createKey(key_pairs)
    return db.Grant(parent=parent)
    
def list_grants(*key_pairs):
    parent = db.createKey(key_pairs)
    return db.Grant.query(ancestor=parent).fetch()
