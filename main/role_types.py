class RoleType:
    USER_ADMIN=0
    SUPPLIER_ADMIN=1
    FUND_ADMIN=2
    COMMITTEE_ADMIN=3
    INCOME_ADMIN=4
    PROJECT_APPROVER=5
    PAYMENT_ADMIN=6
    PROJECT_CREATOR=7

role_names = ['UserAdmin', 'SupplierAdmin', 'FundAdmin', 'CommitteeAdmin',
                'IncomeAdmin', 'ProjectApprover', 'PaymentAdmin',
                'ProjectCreator']

def get_choices():
    return list(enumerate(role_names))

def committee_matches(committee, role):
    if role.committee == "":
        return True
    return role.committee == committee.id

def get_types(roles, committee):
    types = [r.type_index for r in roles if committee_matches(committee, r)]
    return set(types)
