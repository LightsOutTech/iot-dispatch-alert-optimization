import unittest
from solution import load_data, evaluate_policy

class TestDeviceAlertsSolution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_data('device_alerts.csv')
        cls.labeled = [r for r in cls.rows if r['is_valid_dispatch'] in ('0', '1')]
        cls.unlabeled = [r for r in cls.rows if r['is_valid_dispatch'] == '']

    def test_data_integrity(self):
        self.assertEqual(len(self.rows), 1140)
        self.assertEqual(len(self.labeled), 1091)
        self.assertEqual(len(self.unlabeled), 49)
        fa_count = sum(1 for r in self.labeled if r['is_valid_dispatch'] == '0')
        valid_count = sum(1 for r in self.labeled if r['is_valid_dispatch'] == '1')
        self.assertEqual(fa_count, 136)
        self.assertEqual(valid_count, 955)

    def test_drift_calculation(self):
        for r in self.rows:
            self.assertGreaterEqual(r['drift_min'], 0.0)
            self.assertLessEqual(r['drift_min'], 65.0)
            self.assertGreaterEqual(r['signal_dbm'], 0.0)
            self.assertLessEqual(r['signal_dbm'], 30.0)
            self.assertGreaterEqual(r['retry_count'], 0.0)
            self.assertLessEqual(r['retry_count'], 120.0)

    def test_baseline_and_strategies(self):
        base_cost, s1, s2, s3 = evaluate_policy(self.rows)
        self.assertEqual(base_cost, 12240)
        
        # Strategy 1 verification
        self.assertEqual(s1['deferred'], 279)
        self.assertEqual(s1['caught'], 107)
        self.assertEqual(s1['cost'], 5400)
        self.assertEqual(s1['saved'], 6840)
        self.assertAlmostEqual(s1['saved'] / base_cost * 100, 55.88, places=1)

        # Strategy 2 verification
        self.assertEqual(s2['deferred'], 300)
        self.assertEqual(s2['caught'], 110)
        self.assertEqual(s2['cost'], 5340)
        self.assertEqual(s2['saved'], 6900)
        self.assertAlmostEqual(s2['saved'] / base_cost * 100, 56.37, places=1)

        # Strategy 3 verification
        self.assertEqual(s3['deferred'], 318)
        self.assertEqual(s3['caught'], 119)
        self.assertEqual(s3['cost'], 4710)
        self.assertEqual(s3['saved'], 7530)
        self.assertAlmostEqual(s3['saved'] / base_cost * 100, 61.52, places=1)

if __name__ == '__main__':
    unittest.main()
