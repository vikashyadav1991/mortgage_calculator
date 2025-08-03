from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import math
import os
import logging
from logging.handlers import RotatingFileHandler
import sys
from flask_talisman import Talisman
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# Set up rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
    storage_options={"expire": 3600}  # Expire keys after 1 hour to prevent memory growth
)

# Configure app for production
if os.environ.get('FLASK_ENV') == 'production':
    app.config.update(
        SECRET_KEY=os.environ.get('SECRET_KEY', os.urandom(24)),
        SESSION_COOKIE_SECURE=True,
        REMEMBER_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_HTTPONLY=True
    )
    
    # Set up Content Security Policy
    csp = {
        'default-src': '\'self\'',
        'style-src': ['\'self\'', 'https://cdn.jsdelivr.net'],
        'script-src': ['\'self\'', 'https://cdn.jsdelivr.net'],
        'img-src': ['\'self\'', 'data:'],
        'font-src': ['\'self\'', 'https://cdn.jsdelivr.net']
    }
    
    # Initialize Talisman for security headers including CSP
    # Use environment variable to control HTTPS enforcement
    # This allows local testing without HTTPS while enforcing it in production
    force_https = os.environ.get('FORCE_HTTPS', 'false').lower() == 'true'
    Talisman(app, content_security_policy=csp, force_https=force_https)
    
    # Configure CORS - allow requests from browsers but be more restrictive than wildcard
    # This allows the site to be accessed by anyone via browser while preventing malicious cross-origin requests
    CORS(app, resources={
        r"/*": {
            "origins": ["https://mortgage-calculator-35wi.onrender.com", "https://*.onrender.com"],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })
else:
    # Development environment - less strict settings
    Talisman(app, force_https=False, content_security_policy=None)
    CORS(app)

class MortgageCalculator:
    """Comprehensive mortgage payment calculator"""
    def __init__(self):
        self.payment_frequencies = {
            'monthly': 12,
            'bi-weekly': 26,
            'weekly': 52,
            'quarterly': 4,
            'semi-annually': 2,
            'annually': 1
        }
    
    def calculate_payment_schedule(self, balance, annual_interest_rate, regular_payment, payment_frequency='monthly', lump_sum_payment=0, start_date=None, lump_sum_month=None, full_schedule=False):
        if start_date is None:
            start_date = datetime.now()
        if payment_frequency not in self.payment_frequencies:
            raise ValueError(f'Invalid payment frequency. Must be one of: {list(self.payment_frequencies.keys())}')
        
        payments_per_year = self.payment_frequencies[payment_frequency]
        periodic_interest_rate = annual_interest_rate / payments_per_year
        current_balance = balance
        total_payments = 0
        total_interest = 0
        payment_count = 0
        current_date = start_date
        
        if payment_frequency == 'monthly':
            payment_delta = relativedelta(months=1)
        elif payment_frequency == 'bi-weekly':
            payment_delta = timedelta(weeks=2)
        elif payment_frequency == 'weekly':
            payment_delta = timedelta(weeks=1)
        elif payment_frequency == 'quarterly':
            payment_delta = relativedelta(months=3)
        elif payment_frequency == 'semi-annually':
            payment_delta = relativedelta(months=6)
        elif payment_frequency == 'annually':
            payment_delta = relativedelta(years=1)
        
        payment_history = []
        
        while current_balance > 0.01:
            interest_payment = current_balance * periodic_interest_rate
            principal_payment = min(regular_payment - interest_payment, current_balance)
            
            if principal_payment <= 0:
                return {
                    'error': 'Regular payment is too low to cover interest. Mortgage will never be paid off.',
                    'minimum_payment_needed': interest_payment + 1
                }
            
            current_balance -= principal_payment
            total_payments += regular_payment
            total_interest += interest_payment
            payment_count += 1
            
            lump_sum_applied = 0
            # Apply lump sum annually in the selected month regardless of payment frequency
            if lump_sum_payment > 0 and current_date.month == lump_sum_month and (
                # For first year, apply it when we reach the selected month
                (payment_count <= payments_per_year and current_date.month == lump_sum_month) or
                # For subsequent years, make sure we're at the anniversary of the start date (same month and day)
                (payment_count > payments_per_year and current_date.month == lump_sum_month and 
                 (current_date.month != start_date.month or current_date.day >= start_date.day))
            ):
                lump_sum_applied = min(lump_sum_payment, current_balance)
                current_balance -= lump_sum_applied
                total_payments += lump_sum_applied
            
            payment_history.append({
                'payment_number': payment_count,
                'date': current_date.strftime('%Y-%m-%d'),
                'regular_payment': regular_payment,
                'lump_sum': lump_sum_applied,
                'interest': interest_payment,
                'principal': principal_payment + lump_sum_applied,
                'balance': current_balance
            })
            
            current_date += payment_delta
            
            if payment_count > 10000:
                return {
                    'error': 'Calculation exceeded maximum iterations. Please check your inputs.',
                    'payments_calculated': payment_count
                }
        
        payoff_date = current_date - payment_delta
        
        # Limit the payment history size to prevent excessive memory usage
        # For very long mortgages, we'll only keep the first 12, last 12, and some middle payments
        if full_schedule and len(payment_history) > 300:
            # Keep first year, last year, and some samples in between
            first_payments = payment_history[:12]
            last_payments = payment_history[-12:]
            
            # Take some samples from the middle (one payment per year)
            middle_samples = []
            step = max(1, (len(payment_history) - 24) // 10)
            for i in range(12, len(payment_history) - 12, step):
                middle_samples.append(payment_history[i])
            
            # Add a note about sampling
            truncated_history = first_payments + middle_samples + last_payments
            for i, payment in enumerate(truncated_history):
                if i > 0 and payment['payment_number'] - truncated_history[i-1]['payment_number'] > 1:
                    payment['note'] = f"Showing sample payment (skipped {payment['payment_number'] - truncated_history[i-1]['payment_number'] - 1} payments)"
            
            payment_history = truncated_history
        
        return {
            'original_balance': balance,
            'payoff_date': payoff_date.strftime('%Y-%m-%d'),
            'total_payments': payment_count,
            'years_to_payoff': payment_count / payments_per_year,
            'total_amount_paid': total_payments,
            'total_interest_paid': total_interest,
            'interest_savings_from_lump_sum': self._calculate_interest_savings(balance, annual_interest_rate, regular_payment, payment_frequency, lump_sum_payment),
            'payment_history': payment_history if full_schedule else (payment_history[-10:] if len(payment_history) > 10 else payment_history)
        }
    
    def _calculate_interest_savings(self, balance, annual_rate, regular_payment, frequency, lump_sum):
        """Calculate interest savings from lump sum payments without storing full payment history"""
        if lump_sum == 0:
            return 0
            
        # Use a simplified calculation to avoid recursive full calculation
        # This estimates the interest savings without generating the full payment history
        payments_per_year = self.payment_frequencies[frequency]
        periodic_rate = annual_rate / payments_per_year
        
        # Simplified calculation based on time value of money
        # Each lump sum payment saves approximately this much interest over the life of the loan
        estimated_years = balance / (regular_payment * payments_per_year) * 0.7  # 0.7 factor accounts for principal reduction
        avg_balance_reduction = lump_sum / 2  # Average balance reduction over time
        
        # Estimate interest savings: reduced balance * rate * estimated remaining years
        interest_savings = avg_balance_reduction * annual_rate * estimated_years
        
        return interest_savings

# Initialize calculator
mortgage_calc = MortgageCalculator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'version': '1.0.0'})

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/calculate', methods=['POST'])
@limiter.limit("20 per minute")
def calculate():
    try:
        app.logger.info(f"Calculate request from {request.remote_addr}")
        data = request.form
        
        # Input validation constants
        MAX_MORTGAGE_AMOUNT = 50_000_000  # $50M reasonable upper limit
        MAX_INTEREST_RATE = 30.0  # 30% maximum interest rate
        MAX_PAYMENT = 1_000_000  # $1M maximum payment
        MAX_LUMP_SUM = 10_000_000  # $10M maximum lump sum
        
        balance = float(data.get('balance', 0))
        annual_rate = float(data.get('interest_rate', 0)) / 100
        regular_payment = float(data.get('payment', 0))
        frequency = data.get('frequency', 'monthly')
        lump_sum = float(data.get('lump_sum', 0))
        lump_sum_month = int(data.get('lump_sum_month', 1))
        
        # Enhanced input validation
        if balance <= 0:
            return render_template('error.html', 
                                  error_title='Invalid Input', 
                                  error_message='Mortgage balance must be positive')
        if balance > MAX_MORTGAGE_AMOUNT:
            return render_template('error.html', 
                                  error_title='Invalid Input', 
                                  error_message=f'Mortgage amount exceeds maximum allowed (${MAX_MORTGAGE_AMOUNT:,.2f})')
        if annual_rate < 0:
            return render_template('error.html', 
                                  error_title='Invalid Input', 
                                  error_message='Interest rate cannot be negative')
        if annual_rate > MAX_INTEREST_RATE / 100:
            return render_template('error.html', 
                                  error_title='Invalid Input', 
                                  error_message=f'Interest rate exceeds maximum allowed ({MAX_INTEREST_RATE}%)')
        if regular_payment <= 0:
            return render_template('error.html', 
                                  error_title='Invalid Input', 
                                  error_message='Regular payment must be positive')
        if regular_payment > MAX_PAYMENT:
            return render_template('error.html', 
                                  error_title='Invalid Input', 
                                  error_message=f'Payment amount exceeds maximum allowed (${MAX_PAYMENT:,.2f})')
        if lump_sum < 0:
            return render_template('error.html', 
                                  error_title='Invalid Input', 
                                  error_message='Lump sum payment cannot be negative')
        if lump_sum > MAX_LUMP_SUM:
            return render_template('error.html', 
                                  error_title='Invalid Input', 
                                  error_message=f'Lump sum exceeds maximum allowed (${MAX_LUMP_SUM:,.2f})')
        if lump_sum_month < 1 or lump_sum_month > 12:
            return render_template('error.html', 
                                  error_title='Invalid Input', 
                                  error_message='Lump sum month must be between 1 and 12')
        
        results = mortgage_calc.calculate_payment_schedule(
            balance=balance, 
            annual_interest_rate=annual_rate, 
            regular_payment=regular_payment, 
            payment_frequency=frequency, 
            lump_sum_payment=lump_sum, 
            lump_sum_month=lump_sum_month, 
            full_schedule=True
        )
        
        if 'error' in results:
            return render_template('error.html', 
                                  error_title='Calculation Error', 
                                  error_message=results['error'],
                                  minimum_payment=results.get('minimum_payment_needed', 0))
        
        return render_template('results.html', results=results)
    
    except ValueError as e:
        app.logger.error(f"Input validation error in calculate: {str(e)}")
        return render_template('error.html', 
                              error_title='Invalid Input', 
                              error_message='Please check your input values and try again.')
    except Exception as e:
        app.logger.error(f"Error in calculate: {str(e)}")
        return render_template('error.html', 
                              error_title='System Error', 
                              error_message='A system error occurred. Please try again.')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', 
                          error_title='Page Not Found', 
                          error_message='The page you requested does not exist.'), 404

# Configure logging
def setup_logging(app):
    if os.environ.get('FLASK_ENV') == 'production':
        # In production, log to file with rotation
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler('logs/mortgage_calculator.log', maxBytes=10485760, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        # Also log to stderr
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Mortgage Calculator startup')
    else:
        # In development, just log to console
        app.logger.setLevel(logging.DEBUG)

# Set up logging
setup_logging(app)

# Add startup logging
app.logger.info(f"Flask app initialized. Environment: {os.environ.get('FLASK_ENV', 'development')}")
app.logger.info(f"App name: {app.name}")
app.logger.info(f"App instance path: {app.instance_path}")

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)