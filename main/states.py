#_*_ coding: UTF-8 _*_
import model

class State:
    def __init__(self, display_name, can_update=False, role_map={}):
        self.display_name = display_name
        self.can_update = can_update
        self.role_map = role_map

    def is_action_allowed(self, action, roles):
        required_role = self.role_map.get(action)
        return required_role in roles

    def is_update_allowed(self):
        return self.can_update

    def __str__(self):
        return self.display_name
        
    def __repr__(self):
        return 'State(%s)' % (self.display_name)
