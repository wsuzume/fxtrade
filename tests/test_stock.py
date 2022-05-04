import unittest

from fractions import Fraction

from fxtrade.stock import Stock, Rate


class TestStock(unittest.TestCase):
    def test_init(self):
        x1 = Stock('BTC', 15)
        x2 = Stock('BTC', '1/6')
        x3 = Stock('BTC', Fraction('1/3'))
        
        self.assertEqual(x1.q, Fraction('15'))
        self.assertEqual(x2.q, Fraction('1/6'))
        self.assertEqual(x3.q, Fraction('1/3'))
        
        with self.assertRaises(TypeError):
            x4 = Stock('BTC', 0.003)
        
        with self.assertRaises(TypeError):
            x5 = Stock(3, 4)
    
    def test_q(self):
        x = Stock('BTC', 15)
        
        with self.assertRaises(AttributeError):
            x.q = 5
    
    def test_comparison_operators(self):
        x = Stock('BTC', 2)
        y = Stock('BTC', 3)
        z = Stock('BTC', 2)
        w = Stock('BTC', 1)
        
        v = Stock('JPY', 2)
        
        self.assertTrue(x < y)
        self.assertTrue(x <= y)
        self.assertTrue(x <= z)
        self.assertTrue(x == z)
        self.assertTrue(x != y)
        self.assertTrue(x > w)
        self.assertTrue(x >= w)
        self.assertTrue(x >= z)
        
        self.assertFalse(x < w)
        self.assertFalse(x <= w)
        self.assertFalse(x == y)
        self.assertFalse(x != z)
        self.assertFalse(x > y)
        self.assertFalse(x >= y)
        
        with self.assertRaises(TypeError):
            self.assertTrue(x < v)
        with self.assertRaises(TypeError):
            self.assertTrue(x <= v)
        with self.assertRaises(TypeError):
            self.assertTrue(x <= v)
        with self.assertRaises(TypeError):
            self.assertTrue(x == v)
        with self.assertRaises(TypeError):
            self.assertTrue(x != v)
        with self.assertRaises(TypeError):
            self.assertTrue(x > v)
        with self.assertRaises(TypeError):
            self.assertTrue(x >= v)
        with self.assertRaises(TypeError):
            self.assertTrue(x >= v)
    
    def test_unary_operators(self):
        x = Stock('BTC', -2)
        
        self.assertEqual(abs(x), Stock('BTC', 2))
        self.assertEqual(+x, Stock('BTC', -2))
        self.assertEqual(-x, Stock('BTC', 2))
    
    def test_binary_operators(self):
        x = Stock('BTC', 3)
        y = Stock('BTC', 2)
        z = Stock('JPY', 100)
        a = Fraction('1/3')
        b = Fraction(2)
        
        self.assertEqual(x + y, Stock('BTC', 5))
        self.assertEqual(x + b, Stock('BTC', 5))
        self.assertEqual(b + x, Stock('BTC', 5))
        self.assertEqual(x - y, Stock('BTC', 1))
        self.assertEqual(x - b, Stock('BTC', 1))
        self.assertEqual(b - x, Stock('BTC', -1))
        
        self.assertEqual(x * a, Stock('BTC', 1))
        self.assertEqual(a * x, Stock('BTC', 1))
        
        self.assertEqual(x / a, Stock('BTC', 9))
        self.assertEqual(x // a, Stock('BTC', 9))
        self.assertEqual(x % a, Stock('BTC', 0))
        
        self.assertEqual(x ** 3, Stock('BTC', 27))
        
        with self.assertRaises(TypeError):
            x + z
        with self.assertRaises(TypeError):
            x - z
        with self.assertRaises(TypeError):
            x * y
        with self.assertRaises(TypeError):
            x * z
        with self.assertRaises(TypeError):
            x / y
        with self.assertRaises(TypeError):
            x / z
            
class TestRate(unittest.TestCase):
    def test_init(self):
        r1 = Rate('JPY', 'BTC', '1/3')
        r2 = Rate.from_stocks(Stock('JPY', 3), Stock('BTC', 1))
        
        self.assertEqual(r1.r, Fraction('1/3'))
        self.assertEqual(r2.from_code, 'JPY')
        self.assertEqual(r2.to_code, 'BTC')
        
    def test_equal(self):
        r1 = Rate('JPY', 'BTC', '1/3')
        r2 = Rate.from_stocks(Stock('JPY', 3), Stock('BTC', 1))
        r3 = Rate.from_stocks(Stock('JPY', 2), Stock('BTC', 1))
        r4 = Rate.from_stocks(Stock('USD', 3), Stock('BTC', 1))
        r5 = 5
        
        self.assertTrue(r1 == r2)
        self.assertTrue(r1 != r3)
        self.assertTrue(r1 != r4)
        
        self.assertFalse(r1 == r3)
        self.assertFalse(r1 == r4)
        self.assertFalse(r1 != r2)
        
        with self.assertRaises(TypeError):
            r1 == r5
            
    def test_unary_operators(self):
        r1 = Rate('JPY', 'BTC', '1/3')
        r2 = Rate('BTC', 'JPY', '3')
        
        self.assertEqual(~r1, r2)
    
    def test_binary_operators(self):
        r1 = Rate('JPY', 'BTC', '1/3')
        r2 = Rate('BTC', 'JPY', '6')
        r3 = Rate('JPY', 'JPY', 2)
        r4 = Rate('JPY', 'JPY', 8)
        r5 = Rate('JPY', 'BTC', 2)
        
        x1 = Stock('JPY', 300)
        x2 = Stock('BTC', 100)
        x3 = Stock('JPY', 50)
        
        self.assertEqual(r1 * r2, r3)
        self.assertEqual(r3 ** 3, r4)
        
        self.assertEqual(r1 * 6, r5)
        self.assertEqual(6 * r1, r5)
        
        self.assertEqual(r1 * x1, x2)
        self.assertEqual(x1 * r1, x2)
        
        self.assertEqual(2 / r1, r2)
        self.assertEqual(x2 / r5, x3)
        
        with self.assertRaises(TypeError):
            r1 * r3
        with self.assertRaises(TypeError):
            r1 ** r2
        with self.assertRaises(TypeError):
            6 ** r2


if __name__ == "__main__":
    unittest.main()