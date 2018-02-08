def enum(**named_values):
    return type('Enum', (), named_values)

RoleType = enum(USER_ADMIN='UserAdmin', 
    SUPPLIER_ADMIN='SupplierAdmin',
    FUND_ADMIN='FundAdmin',
    COMMITTEE_ADMIN='CommitteeAdmin', 
    INCOME_ADMIN='IncomeAdmin',
    PROJECT_APPROVER='ProjectApprover',
    PAYMENT_ADMIN='PaymentAdmin')

#'User', 'Role'
#'Supplier', 'SupplierFund'
#'Fund'
#'Project', 'InternalTransfer', 'Pledge', 'Grant', 'Purchase'

role_types = [RoleType.USER_ADMIN, RoleType.SUPPLIER_ADMIN, RoleType.FUND_ADMIN, RoleType.COMMITTEE_ADMIN,
                RoleType.INCOME_ADMIN, RoleType.PROJECT_APPROVER]

def get_choices():
    choices = []
    for index in range(len(role_types)):
        type = role_types[index]
        choices.append((index, type))
    return choices     

def committee_matches(committee, role):
    if role.committee == "":
        return True
    return role.committee == committee
    
def get_types(roles, committee):
    type_set = set()
    for r in roles:
       type = role_types[r.type_index]
       if committee_matches(committee, r):
          type_set.add(type)
    return type_set