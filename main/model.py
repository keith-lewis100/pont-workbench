#_*_ coding: UTF-8 _*_

import db
#from dummy import db
import states

cap_key = db.Supplier.get_or_insert('mbale-cap', name='Mbale CAP').key

def lookup_entity(db_id):
    if db_id is None:
        return None
    key = db.createKey(db_id)
    return key.get()
        
def create_fund(parent):
    key = None
    pont = True
    if parent:
        key = parent.key
        pont = False
    return db.Fund(parent=key, pont=pont)
    
def list_funds(parent):
    key = None
    pont = True
    if parent:
        key = parent.key
        pont = False
    return db.Fund.query(ancestor=key).filter(
                    db.Fund.pont==pont).fetch()

def pont_fund_query():
    return db.Fund.query().filter(db.Fund.pont==True)
    
def cap_fund_query():
    return db.Fund.query(ancestor=cap_key) # ugly query

def create_project(parent):
    return db.Project(parent=parent.key)
        
def list_projects(parent):
    return db.Project.query(ancestor=parent.key).fetch()
    
def create_transfer(parent):
    return db.InternalTransfer(parent=parent.key)
        
def list_transfers(parent):
    return db.InternalTransfer.query(ancestor=parent.key).fetch()
    
def create_grant(parent):
    return db.Grant(parent=parent.key)
    
def list_grants(parent):
    return db.Grant.query(ancestor=parent.key).fetch()
    
def create_pledge(parent):
    return db.Pledge(parent=parent.key)
    
def list_pledges(parent):
    return db.Pledge.query(ancestor=parent.key).fetch()

def create_supplier():
    return db.Supplier()

def list_suppliers():
    return db.Supplier.query().fetch()

def is_action_allowed(action, entity): 
    if hasattr(entity, 'state') and not entity.state.isAllowed(action):
        return False
    return True

def perform_action(action_index, entity):
    kind = entity.key.kind()
    newState = states.getState(kind, action_index)
    if newState is None:
        raise BadAction
    entity.state = newState
    entity.put()

if cap_fund_query().count() == 0:
    db.Fund(parent=cap_key, name="Livelihoods").put()
    db.Fund(parent=cap_key, name="Churches").put()
