#import db
from dummy import db

def lookup_entity(*key_pairs):
    key = db.createKey(key_pairs)
    return key.get()
        
def create_fund(*key_pairs):
    parent = db.createKey(key_pairs)
    return db.Fund(parent=parent)
    
def cap_fund_query():
    return db.Fund.query(ancestor=db.cap_key) # ugly query

def create_project(*key_pairs):
    parent = db.createKey(key_pairs)
    return db.Project(parent=parent)
        
def list_projects(*key_pairs):
    parent = db.createKey(key_pairs)
    return db.Project.query(ancestor=parent).fetch()
    
def create_grant(*key_pairs):
    parent = db.createKey(key_pairs)
    project = parent.get()
    return db.Grant(parent=parent, dest_fund=project.dest_fund)
    
def list_grants(*key_pairs):
    parent = db.createKey(key_pairs)
    return db.Grant.query(ancestor=parent).fetch()

def create_supplier():
    return db.Supplier()

def list_suppliers():
    return db.Supplier.query().fetch()
    
def is_action_allowed(action, entity):
    if action == 'approve':
        return entity.state == 'approvalPending'
    return True
    
def perform_action(action, entity):
    if action == 'approve':
        entity.state = 'approved'
