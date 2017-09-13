#import db
from dummy import db

def lookup_entity(url):
    key = db.createKey(url)
    return key.get()
        
def create_fund():
    return db.Fund()
    
def cap_fund_query():
    return db.Fund.query(ancestor=db.cap_key) # ugly query

def create_project(url):
    parent = db.createKey(url)
    return db.Project(parent=parent)
        
def list_projects(url):
    parent = db.createKey(url)
    return db.Project.query(ancestor=parent).fetch()
    
def create_grant(url):
    parent = db.createKey(url)
    project = parent.get()
    return db.Grant(parent=parent, dest_fund=project.dest_fund)
    
def list_grants(url):
    parent = db.createKey(url)
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
