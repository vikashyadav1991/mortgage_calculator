import unittest
from app import app, MortgageCalculator
from datetime import datetime

class TestMortgageCalculator(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.calculator = MortgageCalculator()
    
    def test_home_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_calculator_basic(self):
        result = self.calculator.calculate_payment_schedule(
            balance=300000,
            annual_interest_rate=0.05,
            regular_payment=2000,
            payment_frequency='monthly',
            full_schedule=False
        )
        
        self.assertNotIn('error', result)
        self.assertEqual(result['original_balance'], 300000)
        self.assertTrue(result['years_to_payoff'] > 0)
        self.assertTrue(result['total_interest_paid'] > 0)
    
    def test_low_payment(self):
        result = self.calculator.calculate_payment_schedule(
            balance=300000,
            annual_interest_rate=0.05,
            regular_payment=100,  # Too low to cover interest
            payment_frequency='monthly',
            full_schedule=False
        )
        
        self.assertIn('error', result)
        self.assertIn('minimum_payment_needed', result)
    
    def test_lump_sum_payment(self):
        result_without_lump = self.calculator.calculate_payment_schedule(
            balance=300000,
            annual_interest_rate=0.05,
            regular_payment=2000,
            payment_frequency='monthly',
            full_schedule=False
        )
        
        result_with_lump = self.calculator.calculate_payment_schedule(
            balance=300000,
            annual_interest_rate=0.05,
            regular_payment=2000,
            payment_frequency='monthly',
            lump_sum_payment=10000,
            lump_sum_month=1,
            full_schedule=False
        )
        
        # Mortgage should be paid off faster with lump sum payments
        self.assertLess(result_with_lump['years_to_payoff'], result_without_lump['years_to_payoff'])

if __name__ == '__main__':
    unittest.main()