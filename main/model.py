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
    key = db.createKey(db_id)
    return key.get()

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
    if user is None:
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
    return db.User.query().filter(db.User.email == email).get()

class EntityModel:
    def __init__(self, name, update_role, parent_model=None, state_list=None):
        self.name = name
        self.update_role = update_role
        self.parent_model = parent_model
        self.state_list = state_list

    def is_action_allowed(self, action, entity, user):
        state = self.state_list[entity.state_index]
        types = get_role_types(user, entity)
        return state.is_action_allowed(action, types)

    def is_update_allowed(self, entity, user):
        types = get_role_types(user, entity)
        if not self.update_role in types:
            return False
        if not hasattr(entity, 'state_index'):
            return True
        state = self.state_list[entity.state_index]
        return state.is_update_allowed()

    def is_create_allowed(self, parent, user):
        types = get_role_types(user, parent)
        return self.update_role in types

    def perform_create(self, entity, user):
        if hasattr(entity, 'creator'):
            entity.creator = user.key
        entity.put()
