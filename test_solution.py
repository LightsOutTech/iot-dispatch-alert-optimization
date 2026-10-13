import unittest
from solution import load_data, is_flagged_s1, is_flagged_s2, is_flagged_s3

class TestSolution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_data('device_alerts.csv')
        cls.labeled = [r for r in cls.rows if r['is_valid_dispatch'] in ('0', '1')]

    def test_data_integrity(self):
        self.assertEqual(len(self.rows), 1140)
        self.assertEqual(len(self.labeled), 1091)
        unlabeled = [r for r in self.rows if r['is_valid_dispatch'] == '']
        self.assertEqual(len(unlabeled), 49)

    def test_baseline_and_s1(self):
        total_fa = sum(1 for r in self.labeled if r['is_valid_dispatch'] == '0')
        self.assertEqual(total_fa, 136)
        flagged = [r for r in self.labeled if is_flagged_s1(r)]
        caught_fa = sum(1 for r in flagged if r['is_valid_dispatch'] == '0')
        self.assertEqual(len(flagged), 279)
        self.assertEqual(caught_fa, 107)

    def test_strategy3_performance(self):
        flagged = [r for r in self.labeled if is_flagged_s3(r)]
        caught_fa = sum(1 for r in flagged if r['is_valid_dispatch'] == '0')
        self.assertEqual(len(flagged), 318)
        self.assertEqual(caught_fa, 119)
        base_cost = 136 * 90
        missed_fa = 136 - 119
        opt_cost = missed_fa * 90 + len(flagged) * 10
        saved = base_cost - opt_cost
        self.assertEqual(saved, 7530)
        self.assertAlmostEqual(saved / base_cost * 100, 61.52, places=2)

    def test_edge_cases(self):
        row_zero = {'drift_min': 0.0, 'signal_dbm': 20.0, 'retry_count': 10.0, 'plant_code': '西区涂装车间'}
        self.assertFalse(is_flagged_s1(row_zero))
        self.assertFalse(is_flagged_s2(row_zero))
        self.assertFalse(is_flagged_s3(row_zero))

        row_15 = {'drift_min': 15.0, 'signal_dbm': 20.0, 'retry_count': 10.0, 'plant_code': '西区涂装车间'}
        self.assertTrue(is_flagged_s1(row_15))
        self.assertTrue(is_flagged_s2(row_15))
        self.assertTrue(is_flagged_s3(row_15))

        row_plant1 = {'drift_min': 5.0, 'signal_dbm': 2.0, 'retry_count': 30.0, 'plant_code': '一号总装厂'}
        self.assertFalse(is_flagged_s1(row_plant1))
        self.assertFalse(is_flagged_s2(row_plant1))
        self.assertTrue(is_flagged_s3(row_plant1))

        row_plant2 = {'drift_min': 5.0, 'signal_dbm': 2.0, 'retry_count': 30.0, 'plant_code': '二号焊装厂'}
        self.assertFalse(is_flagged_s1(row_plant2))
        self.assertFalse(is_flagged_s2(row_plant2))
        self.assertFalse(is_flagged_s3(row_plant2))

if __name__ == '__main__':
    unittest.main()
