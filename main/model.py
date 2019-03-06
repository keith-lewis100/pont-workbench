#_*_ coding: UTF-8 _*_

import logging
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

def get_next_ref():
    ref = workbench.last_ref_id + 1
    workbench.last_ref_id = ref
    workbench.put()
    return ref

def lookup_entity(db_id):
    if db_id is None:
        return None
    key = db.create_key(db_id)
    return key.get()
    
def create_key(db_id):
    return db.create_key(db_id)

def get_parent(entity):
    parentKey = entity.key.parent()
    if parentKey is None:
        return None
    return parentKey.get()

def get_owning_committee(entity):
    while entity:
        if entity.key.kind() == 'Fund':
            return entity.committee
        entity = get_parent(entity)
    return None

def get_role_types(user, entity):
    if user.key is None:
       logger.debug("no user")
       return set()
    roles = db.Role.query(ancestor=user.key).fetch()
    committee = get_owning_committee(entity)
    return role_types.get_types(roles, committee)

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
    
class Action(object):
    def __init__(self, name, label, required_role, message=None):
        self.name = name
        self.label = label
        self.required_role = required_role
        self.message = message

    def is_allowed(self, entity, user):
        types = get_role_types(user, entity)
        if not self.required_role in types:
            return False
        return True
        
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
        
    def is_allowed(self, entity, user):
        if not super(StateAction, self).is_allowed(entity, user):
            return False
        state = entity.state_index
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
