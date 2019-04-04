import unittest

from application import app
import db
import suppliers
import supplier_funds
import partners
import foreign_transfer

partners.add_rules(app)
supplier_funds.add_rules(app)

class TestSuppliers(unittest.TestCase):
    def test_view_supplier(self):
        supplier = db.Supplier(id=6)
        supplier.name = 'Sup1'
        supplier.receives_grants = True
        supplier.paid_in_sterling = False
        supplier.put()
        with app.test_request_context('/', method='GET'):
            suppliers.view_supplier('Supplier-6')

if __name__ == '__main__':
   unittest.main()
