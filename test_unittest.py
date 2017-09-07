import unittest

import tushare_proxy as tsp


class TestTrading(unittest.TestCase):
    def set_data(self):
        self.code = '150118'
        self.start = '2014-11-03'
        self.end = '2014-11-07'

    def test_tickData(self):
        self.set_data()
        hist = tsp.get_h_data(self.code, index=True)
        print(hist)

    # def test_trade_cal(self):
    #     hist = tsp.trade_cal()
    #     print(hist)

    # def test_clear_cache(self):
    #     tushare_proxy.clear_cache()


    # def test_histData(self):
    #     self.set_data()
    #     td.get_hist_data(self.code, start=self.start, end=self.end)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
