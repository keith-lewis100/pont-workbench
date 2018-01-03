#_*_ coding: UTF-8 _*_

import db
#from dummy import db
import states

cap_key = db.Supplier.get_or_insert('mbale-cap', name='Mbale CAP').key
workbench = db.WorkBench.get_or_insert('main')
committee_labels=[
        ('PHC', 'PrimaryHealth'),
        ('EDU', 'SecondaryHealth'),
        ('LIV', 'Livelihoods'), 
        ('ENG', 'Engineering'),
        ('EDU', 'Education'), 
        ('CHU', 'Churches'), 
        ('WEC', 'Wildlife Centre')]

def lookup_entity(db_id):
    if db_id is None:
        return None
    key = db.createKey(db_id)
    return key.get()

def getParent(entity):
    parentKey = entity.key.parent()
    if parentKey is None:
        return None
    return parentKey.get()

def create_fund(parent):
    if parent:
        return db.Fund(parent=parent.key)
    return db.Fund()

def list_funds(parent):
    if parent:
        return db.Fund.query(ancestor=parent.key).fetch()
    return db.Fund.query().filter(db.Fund.committee != None).fetch()

def pont_fund_query():
    return db.Fund.query().filter(db.Fund.committee != None)
    
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

def create_purchase(parent):
    return db.Purchase(parent=parent.key)
    
def list_purchases(parent):
    return db.Purchase.query(ancestor=parent.key).fetch()

def _get_next_ref():
    ref = workbench.last_ref_id + 1
    workbench.last_ref_id = ref
    workbench.put()
    return ref

def create_supplier():
    return db.Supplier()

def list_suppliers():
    return db.Supplier.query().fetch()
    
def create_user():
    return db.User()

def list_users():
    return db.User.query().fetch()
    
def create_role(parent):
    return db.Role(parent=parent.key)
    
def list_roles(parent):
    return db.Role.query(ancestor=parent.key).fetch()

def user_by_email(email):
    return db.User.query().filter(db.User.email == email).get()

def is_action_allowed(action, entity, user): 
#    if user is None:
#        return False
    if hasattr(entity, 'state') and not entity.state.isAllowed(action):
        return False
    return True

def perform_create(kind, entity, user):
    if kind == 'Pledge':
        ref = _get_next_ref()
        entity.ref_id = 'PL%04d' % ref
    if hasattr(entity, 'creator'):
        entity.creator = user.key
    entity.put()

def perform_update(entity):
    entity.put()

def perform_state_change(index, entity):
    kind = entity.key.kind()
    newState = states.getState(kind, index)
    if newState is None:
        raise BadAction
    entity.state = newState
    if kind == 'Purchase' and newState == states.PURCHASE_APPROVED:
        ref = _get_next_ref()    
        entity.po_number = 'MB%04d' % ref
    entity.put()
