#_*_ coding: UTF-8 _*_

import renderers
import readonly_fields
import views
import grants

payments_field_list = [
    grants.state_field,
    readonly_fields.ReadOnlyField('requestor'),
    readonly_fields.ReadOnlyField('amount'),
    grants.ExchangeCurrencyField('transferred_amount'),
    readonly_fields.ReadOnlyField('project_name'),
    readonly_fields.ReadOnlyField('partner', 'Implementing Partner'),
    readonly_fields.ReadOnlyField('source_fund'),
    readonly_fields.ReadOnlyField('dest_fund', 'Destination Fund')
]

class Payment:
    pass

def render_payments(grant_list):
    payments_list = []
    for grant in grant_list:
        p = Payment()
        p.key = grant.key
        p.state_index = grant.state_index
        p.requestor = grant.creator.get().name
        p.transfer = grant.transfer
        p.amount = grant.amount
        project = grant.project.get()
        p.project_name = project.name
        p.partner = None
        if project.partner != None:
          p.partner = project.partner.get().name
        p.source_fund = grant.key.parent().get().code
        p.dest_fund = grant.project.parent().get().name
        payments_list.append(p)
    return renderers.render_table(payments_list, views.url_for_entity, *payments_field_list)
