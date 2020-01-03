#_*_ coding: UTF-8 _*_

import logging
from google.appengine.api import users
from google.appengine.ext import ndb

import db
import role_types

logger = logging.getLogger('model')

workbench = db.WorkBench.get_or_insert('main')
committee_labels=[
        ('AMB', 'Ambulance'),
        ('PHC', 'PrimaryHealth'),
        ('SEC', 'SecondaryHealth'),
        ('LIV', 'Livelihoods'),
        ('ENG', 'Engineering'),
        ('EDU', 'Education'),
        ('CHU', 'Churches'),
        ('WEC', 'Wildlife Centre'),
        ('GEN', 'General')]

if db.User.query().count() == 0:
    user = db.User();
    user.name = 'Keith'
    user.email = 'keith.lewis@pont-mbale.org.uk'
    key = user.put()
    
    role = db.Role(parent=key)
    role.type_index = 0
    role.committee = ''
    role.put()

class Committee:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.key = self
       
    def kind(self):
        return 'Committee'
        
    def urlsafe(self):
        return self.id
        
    def parent(self):
        return None

def get_committee_list():
    return [Committee(id, name) for id, name in committee_labels]
    
def lookup_committee(c_id):
    for id, name in committee_labels:
        if id == c_id:
            return Committee(id, name)
    return None

def get_next_ref():
    ref = workbench.last_ref_id + 1
    workbench.last_ref_id = ref
    workbench.put()
    return ref

def lookup_entity(db_id):
    key = create_key(db_id)
    return key.get()

def create_key(db_id):
    if db_id is None or db_id == "":
        return None
    return ndb.Key(urlsafe=db_id)

def get_parent(entity):
    parent_key = entity.key.parent()
    if parent_key is not None:
         return parent_key.get()
    if entity.key.kind() == 'Fund':
         return lookup_committee(entity.committee)
    return None

def get_owning_committee(entity):
    while entity:
        if entity.key.kind() == 'Fund':
            return entity.committee
        entity = get_parent(entity)
    return None

def lookup_user_with_role(type):
    roles = db.Role.query(type_index=type)
    for role in roles:
        user = role.key.parent
        return user
    return None

def lookup_user_by_email(email):
    user = db.User.query(db.User.email == email).get()
    if user is None:
        user = db.User()
        user.name = email
    return user

def lookup_current_user():
    email = users.get_current_user().email()
    return lookup_user_by_email(email)

def logout_url():
    return users.create_logout_url('/')

def role_matches(role, role_type, committee):
    if role.type_index != role_type:
        return False
    if role.committee is None or role.committee == "":
        return True
    return role.committee == committee

        
def calculate_transferred_amount(payment):
    if payment is None or payment.transfer is None:
        return ""
    transfer = payment.transfer.get()
    if transfer.exchange_rate is None:
        return ""
    requested_amount = payment.amount.value
    if payment.amount.currency == 'sterling':
        sterling = requested_amount
        shillings = int(requested_amount * transfer.exchange_rate)
    if payment.amount.currency == 'ugx':
        sterling = int(requested_amount / transfer.exchange_rate)
        shillings = requested_amount
    return u"£{:,}".format(sterling) + "/" + u"{:,}".format(shillings) + ' Ush'

STATE_CLOSED = 0

class Model(object):
    def __init__(self, entity, committee=None):
        self.entity = entity
        self.committee = committee
        self.user = lookup_current_user()
        self.forms = {}
        self.errors=[]
        self.next_entity = None
        self.entity_deleted = False

    def get_state(self):
        return self.entity.state_index

    def user_has_role(self, role_type):
        roles = db.Role.query(ancestor=self.user.key).fetch()
        for r in roles:
            if role_matches(r, role_type, self.committee):
                return True
        return False

    def add_form(self, action_name, form):
        self.forms[action_name] = form

    def get_form(self, action_name):
        return self.forms.get(action_name)

    def perform_create(self, action_name):
        form = self.get_form(action_name)
        if not form.validate():
            return False
        entity = self.entity
        form.populate_obj(entity)
        if hasattr(entity, 'creator'):
            entity.creator = self.user.key
        entity.put()
        self.audit(action_name, "Create performed")
        return True

    def perform_update(self, action_name):
        form = self.get_form(action_name)
        if not form.validate():
            return False
        form.populate_obj(self.entity)
        self.entity.put()
        self.audit(action_name, "Update performed")
        return True

    def perform_close(self, action_name):
        self.entity.state_index = STATE_CLOSED
        self.entity.put()
        self.audit(action_name, "%s performed" % action_name.title())
        return True

    def add_error(self, error_text):
            self.errors.append(error_text)

    def audit(self, action_name, message, entity=None):
        if not entity:
            entity = self.entity
        audit = db.AuditRecord()
        audit.entity = entity.key
        audit.user = self.user.key
        audit.action = action_name
        audit.message = message
        return audit.put()

    def __repr__(self):
        return 'Model(%s, %s)' % (repr(self.entity), self.committee) 
