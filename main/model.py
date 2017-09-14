#_*_ coding: UTF-8 _*_

import db
#from dummy import db

cap_key = db.Supplier.get_or_insert('mbale-cap', name='Mbale CAP').key

def lookup_entity(url):
    key = db.createKey(url)
    return key.get()
        
def create_fund():
    return db.Fund()
    
def cap_fund_query():
    return db.Fund.query(ancestor=cap_key) # ugly query

def create_project(url):
    parent = db.createKey(url)
    return db.Project(parent=parent, state='approvalPending')
        
def list_projects(url):
    parent = db.createKey(url)
    return db.Project.query(ancestor=parent).fetch()
    
def create_grant(url):
    parent = db.createKey(url)
    project = parent.get()
    return db.Grant(parent=parent, amount=db.Money(),
                    dest_fund=project.dest_fund,
                    state='transferPending')
    
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
        entity.put()

if cap_fund_query().count() == 0:
    db.Fund(parent=cap_key, name="Livelihoods").put()
    db.Fund(parent=cap_key, name="Churches").put()
