
class State:
    def __init__(self, index, display_name, *actions):
        self.index = index
        self.display_name = display_name
        self.actions = frozenset(actions)
        
    def isAllowed(self, action):
        return action in self.actions
        
    def __str__(self):
        return self.display_name
        
    def __repr__(self):
        return 'State(%s, %s)' % (self.index, self.display_name)
        
PROJECT_APPROVAL_PENDING = State(0, 'Approval Pending',
                ('state-change', 1), ('update',))
PROJECT_APPROVED = State(1, 'Approved', ('create', 'Grant'), ('create', 'Pledge'), ('update',))

GRANT_TRANSFER_PENDING = State(0, 'Transfer Pending', ('update',))
GRANT_TRANSFERED = State(1, 'Transfer Pending')

PLEDGE_PENDING = State(0, 'Pending', ('state-change', 1), ('update',))
PLEDGE_FULFILLED = State(1, 'Fulfilled')

projectStates = [PROJECT_APPROVAL_PENDING, PROJECT_APPROVED]
grantStates = [GRANT_TRANSFER_PENDING, GRANT_TRANSFERED]
pledgeStates = [PLEDGE_PENDING, PLEDGE_FULFILLED]

stateMap = {'Project': projectStates,
           'Grant': grantStates,
             'Pledge': pledgeStates}

def getState(kind, index):
    return stateMap[kind][index]
