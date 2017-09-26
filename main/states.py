#_*_ coding: UTF-8 _*_

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
PROJECT_APPROVED = State(1, 'Approved', ('create', 'Purchase'), ('create', 'Grant'), ('create', 'Pledge'), ('update',))

GRANT_TRANSFER_PENDING = State(0, 'Transfer Pending', ('update',))
GRANT_TRANSFERED = State(1, 'Transferred')

PLEDGE_PENDING = State(0, 'Pending', ('state-change', 1), ('update',))
PLEDGE_FULFILLED = State(1, 'Fulfilled')

TRANSFER_PENDING = State(0, 'Pending', ('state-change', 1), ('update',))
TRANSFER_COMPLETE = State(1, 'Transferred')

PURCHASE_AUTHORISING = State(0, 'Authorising', ('state-change', 1), ('state-change', 5), ('update',))
PURCHASE_APPROVING = State(1, 'Approving', ('state-change', 2), ('state-change', 5), ('update',))
PURCHASE_APPROVED = State(2, 'Approved', ('state-change', 3), ('state-change', 5))
PURCHASE_ORDERED = State(3, 'Ordered', ('state-change', 4))
PURCHASE_FULFILLED = State(4, 'Fulfilled', ('state-change', 5))
PURCHASE_CLOSED = State(5, 'Closed')

projectStates = [PROJECT_APPROVAL_PENDING, PROJECT_APPROVED]
grantStates = [GRANT_TRANSFER_PENDING, GRANT_TRANSFERED]
pledgeStates = [PLEDGE_PENDING, PLEDGE_FULFILLED]
transferStates = [TRANSFER_PENDING, TRANSFER_COMPLETE]
purchaseStates = [PURCHASE_AUTHORISING, PURCHASE_APPROVING, PURCHASE_APPROVED, PURCHASE_ORDERED,
                  PURCHASE_FULFILLED, PURCHASE_CLOSED]

stateMap = {'Project': projectStates,
            'Grant': grantStates,
            'Pledge': pledgeStates,
            'InternalTransfer': transferStates,
            'Purchase': purchaseStates}

def getState(kind, index):
    return stateMap[kind][index]
