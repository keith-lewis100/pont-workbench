class RoleType:
    def __init__(self, index, display_name, *permissions):
        self.index = index
        self.display_name = display_name
        self.permissions = frozenset(permissions)
    
    def has_permission(self, permission):
        return permission in self.permissions

class SuperUser(RoleType):
    def __init__(self, index):
        RoleType.__init__(self, index, 'SuperUser')

    def has_permission(self, permission):
        return True

role_types = [SuperUser(0)]

def get_choices():
    choices = []
    for type in role_types:
        choices.append((type.index, type.display_name))
    return choices     

def committee_matches(committee, role):
    if role.committee is None:
        return True
    return role.committee == committee
    
def has_permission(roles, permission, committee):
    for r in roles:
       type = role_types[r.type_index]
       if committee_matches(committee, r) and type.has_permission(permission):
          return True
    return False