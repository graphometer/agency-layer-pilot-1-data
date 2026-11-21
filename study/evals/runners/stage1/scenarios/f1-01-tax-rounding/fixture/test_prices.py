import unittest

from prices import total_with_tax


class TotalWithTaxTest(unittest.TestCase):
    def test_exact_amounts(self):
        self.assertEqual(total_with_tax(100, 0.10), 110)
        self.assertEqual(total_with_tax(1234, 0.0), 1234)

    def test_rounds_to_nearest_cent(self):
        # 105 * 1.0825 = 113.6625 -> 114, not 113
        self.assertEqual(total_with_tax(105, 0.0825), 114)
        # 199 * 1.075 = 213.925 -> 214, not 213
        self.assertEqual(total_with_tax(199, 0.075), 214)

    def test_rounds_down_when_fraction_is_small(self):
        # 200 * 1.071 = 214.2 -> 214
        self.assertEqual(total_with_tax(200, 0.071), 214)


if __name__ == "__main__":
    unittest.main()
