#_*_ coding: UTF-8 _*_

import logging
from google.appengine.api import users

import db
import role_types
import custom_fields
import renderers

logger = logging.getLogger('data_models')

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
    if db_id is None:
        return None
    if len(db_id) == 3:
        return lookup_committee(db_id)
    key = db.create_key(db_id)
    return key.get()
    
def create_key(db_id):
    return db.create_key(db_id)

def get_parent(entity):
    parentKey = entity.key.parent()
    if parentKey is not None:
        return parentKey.get()
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

def role_matches(role, role_type, committee):
    if role.type_index != role_type:
        return False
    return role.committee == "" or role.committee == committee
    
class Action(object):
    def __init__(self, name, label, required_role, message=None):
        self.name = name
        self.label = label
        self.required_role = required_role
        self.message = message

    def is_allowed(self, model):
        return model.user_has_role(self.required_role)

    def render(self, model):
        enabled = self.is_allowed(model)
        form = model.get_form(self.name)
        if form:
            return custom_fields.render_dialog_button(self.label, self.name, form, enabled)
        return renderers.render_submit_button(self.label, name='_action', value=self.name,
                disabled=not enabled)

    def apply_to(self, entity, user):
        entity.put()

    def audit(self, entity, user, **kwargs):
        audit = db.AuditRecord()
        audit.entity = entity.key
        audit.user = user.key
        audit.action = self.name
        message = '{action} performed'
        if self.message:
            message = self.message
        audit.message = message.format(action=self.name, kind=entity.key.kind(), **kwargs)
        return audit.put()

class StateAction(Action):
    def __init__(self, name, label, required_role, next_state, allowed_states):
        super(StateAction, self).__init__(name, label, required_role)
        self.next_state = next_state
        self.allowed_states = allowed_states
        
    def is_allowed(self, model):
        if not super(StateAction, self).is_allowed(model):
            return False
        state = model.entity.state_index
        return state in self.allowed_states
        
    def apply_to(self, entity, user):
        entity.state_index = self.next_state
        entity.put()

class CreateAction(Action):
    def __init__(self, required_role):
        super(CreateAction, self).__init__('create', 'New', required_role, message='Created')

    def apply_to(self, entity, user):
        if hasattr(entity, 'creator'):
            entity.creator = user.key
        entity.put()

class Model:
    def __init__(self, entity, committee=None):
        self.entity = entity
        self.committee = committee
        self.user = lookup_current_user()
        self.forms = {}

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
