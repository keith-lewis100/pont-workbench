#_*_ coding: UTF-8 _*_

class State:
    def __init__(self, index, display_name, *actions):
        self.index = index
        self.display_name = display_name
        self.actions = frozenset(actions)
        
    def is_allowed(self, action):
        return action in self.actions
        
    def __str__(self):
        return self.display_name
        
    def __repr__(self):
        return 'State(%s, %s)' % (self.index, self.display_name)
