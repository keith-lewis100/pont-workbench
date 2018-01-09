class RoleType:
    def __init__(self, display_name, *permissions):
        self.display_name = display_name
        self.permissions = frozenset(permissions)
    
    def has_permission(self, permission):
        return permission in self.permissions

class SuperUser(RoleType):
    def __init__(self):
        RoleType.__init__(self, 'SuperUser')

    def has_permission(self, permission):
        return True

role_types = [SuperUser(),
    RoleType('UserAdmin', (None, 'create', 'User'), ('User', 'update'), 
                             ('User', 'create', 'Role'), ('Role', 'update')),
    RoleType('FundAdmin', (None, 'create', 'Fund'), ('Fund', 'update'), 
                          ('InternalTransfer', 'state-change', 1),
                          ('Purchase', 'state-change', 2)),
    RoleType('CommitteeAdmin', ('Fund', 'create', 'Project'), ('Project', 'update'),
                        ('Fund', 'create', 'InternalTransfer'), ('InternalTransfer', 'update'),
                        ('Fund', 'create', 'Project'), ('Project', 'update'),
                        ('Project', 'create', 'Pledge'), ('Pledge', 'update'),
                        ('Project', 'create', 'Grant'), ('Grant', 'update'),
                        ('Project', 'create', 'Purchase'), ('Purchase', 'update'), ('Purchase', 'state-change', 3), 
                        ('Purchase', 'state-change', 4), ('Purchase', 'state-change', 5)),
    RoleType('IncomeAdmin', ('Pledge', 'state-change', 1))
    ]

def get_choices():
    choices = []
    for index in range(len(role_types)):
        type = role_types[index]
        choices.append((index, type.display_name))
    return choices     

def committee_matches(committee, role):
    if role.committee == "":
        return True
    return role.committee == committee
    
def has_permission(roles, kind, action, committee):
    if len(action) == 1:
        permission = (kind, action[0])
    else:
        permission = (kind, action[0], action[1])
    for r in roles:
       type = role_types[r.type_index]
       if committee_matches(committee, r) and type.has_permission(permission):
          return True
    return False