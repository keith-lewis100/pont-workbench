#_*_ coding: UTF-8 _*_
import model

class State:
    def __init__(self, display_name, can_update=False, can_create_children=True, role_map={}):
        self.display_name = display_name
        self.can_update = can_update
        self.role_map = role_map
        self.can_create_children = can_create_children

    def is_transition_allowed(self, index, roles):
        required_role = self.role_map.get(index)
        return required_role in roles
    
    def is_child_create_allowed(self):
        return self.can_create_children

    def is_update_allowed(self):
        return self.can_update

    def find_transition_user(self, index):
        role_type = self.role_map.get(index)
        if role_type is None:
            return None
        return model.lookup_user_with_role(role_type)

    def __str__(self):
        return self.display_name
        
    def __repr__(self):
        return 'State(%s)' % (self.display_name)
