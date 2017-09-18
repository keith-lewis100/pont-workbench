
class State:
    def __init__(self, index, display_name):
        self.index = index
        self.display_name = display_name
        
    def __str__(self):
        return self.display_name
        
    def __repr__(self):
        return 'State(%s, %s)' % (self.index, self.display_name)
        
PROJECT_APPROVAL_PENDING = State(0, 'Approval Pending')
PROJECT_APPROVED = State(1, 'Approved')

GRANT_TRANSFER_PENDING = State(0, 'Transfer Pending')
GRANT_TRANSFERED = State(1, 'Transfer Pending')

PLEDGE_PENDING = State(0, 'Pending')
PLEDGE_FULFILLED = State(1, 'Fulfilled')

projectStates = [PROJECT_APPROVAL_PENDING, PROJECT_APPROVED]
grantStates = [GRANT_TRANSFER_PENDING, GRANT_TRANSFERED]
pledgeStates = [PLEDGE_PENDING, PLEDGE_FULFILLED]
