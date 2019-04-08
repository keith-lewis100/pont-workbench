import unittest

from application import app
import db
import committees
import funds
import internal_transfers

class TestPurchases(unittest.TestCase):
    def test_transfer_list(self):
        fund = db.Fund(id=11)
        fund.committee = 'EDU'
        fund.name = 'myFund'
        fund.put()
        with app.test_request_context('/', method='GET'):
            internal_transfers.view_internaltransfer_list('Fund-11')
        self.assertTrue(True)

    def test_transfer(self):
        fund = db.Fund(id=11)
        fund.committee = 'EDU'
        fund.name = 'myFund'
        fund.put()
        transfer = db.InternalTransfer(id=12, parent=fund.key)
        transfer.put()
        with app.test_request_context('/', method='GET'):
            internal_transfers.view_internaltransfer('InternalTransfer-12')

if __name__ == '__main__':
   unittest.main()
