#_*_ coding: UTF-8 _*_

import logging
import db
import role_types
from google.appengine.api import users

logger = logging.getLogger('model')

cap_key = db.Supplier.get_or_insert('mbale-cap', name='Mbale CAP').key
workbench = db.WorkBench.get_or_insert('main')
committee_labels=[
        ('PHC', 'PrimaryHealth'),
        ('SEC', 'SecondaryHealth'),
        ('LIV', 'Livelihoods'), 
        ('ENG', 'Engineering'),
        ('EDU', 'Education'), 
        ('CHU', 'Churches'), 
        ('WEC', 'Wildlife Centre')]

if db.User.query().count() == 0:
    user = db.User();
    user.name = 'Admin'
    user.email = 'admin@pont-mbale.org.uk'
    key = user.put()
    
    role = db.Role(parent=key)
    role.type_index = 0
    role.committee = ''
    role.put()
 
def lookup_entity(db_id):
    if db_id is None:
        return None
    key = db.createKey(db_id)
    return key.get()

def get_parent(entity):
    parentKey = entity.key.parent()
    if parentKey is None:
        return None
    return parentKey.get()

def create_fund():
    return db.Fund()

def list_funds():
    return db.Fund.query().fetch()

def create_supplier_fund(parent):
    return db.SupplierFund(parent=parent.key)
    
def list_supplier_funds(parent):
    return db.SupplierFund.query(ancestor=parent.key).fetch()

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
    
def get_owning_committee(entity):
    while entity:
        if entity.key.kind() == 'Fund':
            return entity.committee
        entity = get_parent(entity)
    return None

def is_user_allowed_action(action, entity): 
    email = users.get_current_user().email()
    user = user_by_email(email)
    if user is None:
       logger.debug("no user")
       return False
    roles = list_roles(user)
    committee = get_owning_committee(entity)
    kind = None
    if entity:
        kind = entity.key.kind()
    if not role_types.has_permission(roles, kind, action, committee):
       return False
    logger.debug("no permission")
    return True

def perform_create(kind, entity):
    if kind == 'Pledge':
        ref = _get_next_ref()
        entity.ref_id = 'PL%04d' % ref
    if hasattr(entity, 'creator'):
        email = users.get_current_user().email()
        user = user_by_email(email)
        entity.creator = user.key
    entity.put()

def perform_update(entity):
    entity.put()

def perform_state_change(entity, state_index):
    entity.state_index = state_index
#    if kind == 'Purchase' and newState == states.PURCHASE_APPROVED:
#        ref = _get_next_ref()    
#        entity.po_number = 'MB%04d' % ref
    entity.put()

def perform_delete(entity):
    entity.key.delete()