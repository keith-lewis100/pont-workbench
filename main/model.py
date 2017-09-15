#_*_ coding: UTF-8 _*_

import db
#from dummy import db

cap_key = db.Supplier.get_or_insert('mbale-cap', name='Mbale CAP').key

def lookup_entity(db_id):
    key = db.createKey(db_id)
    return key.get()
        
def create_fund():
    return db.Fund()
    
def cap_fund_query():
    return db.Fund.query(ancestor=cap_key) # ugly query

def create_project(db_id):
    parent = db.createKey(db_id)
    return db.Project(parent=parent)
        
def list_projects(db_id):
    parent = db.createKey(db_id)
    return db.Project.query(ancestor=parent).fetch()
    
def create_grant(db_id):
    parent = db.createKey(db_id)
    project = parent.get()
    return db.Grant(parent=parent, amount=db.Money())
    
def list_grants(db_id):
    parent = db.createKey(db_id)
    return db.Grant.query(ancestor=parent).fetch()
    
def create_pledge(db_id):
    parent = db.createKey(db_id)
    project = parent.get()
    return db.Pledge(parent=parent, amount=db.Money())
    
def list_pledges(db_id):
    parent = db.createKey(db_id)
    return db.Pledge.query(ancestor=parent).fetch()

def create_supplier():
    return db.Supplier()

def list_suppliers():
    return db.Supplier.query().fetch()
    
def is_action_allowed(action, entity):
    if action == 'approve':
        return entity.state == 'approvalPending'
    if action == 'fulfill':
        return entity.state == 'pending'
    return False
    
def perform_action(action, entity):
    if action == 'approve':
        entity.state = 'approved'
        entity.put()
        return
    if action == 'fulfill':
        entity.state = 'fulfilled'
        entity.put()
        return

if cap_fund_query().count() == 0:
    db.Fund(parent=cap_key, name="Livelihoods").put()
    db.Fund(parent=cap_key, name="Churches").put()
