# Mortgage Calculator Web Application

A Flask web application for calculating mortgage payments and amortization schedules, ready for deployment on Render.com.

## Features

- Calculate mortgage payments based on principal, interest rate, and payment frequency
- Support for various payment frequencies:
  - Monthly
  - Bi-weekly
  - Weekly
  - Quarterly
  - Semi-annually
  - Annually
- Annual lump sum payment option with customizable month selection
- Complete amortization schedule with detailed payment breakdown
- Responsive design that works on desktop and mobile devices

## Screenshots

The application provides an intuitive interface for mortgage calculations:

- Input form for mortgage details
- Summary view with key mortgage statistics
- Detailed amortization table showing payment breakdown

## Local Development

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/mortgage_calculator.git
   cd mortgage_calculator
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the development server:
   ```
   flask --app app.py run
   ```

5. Open your browser and navigate to `http://127.0.0.1:5000`

## Deployment on Render.com

This application is configured for easy deployment to [Render.com](https://render.com/).

### Automatic Deployment

1. Fork or clone this repository to your GitHub account
2. Sign up for a Render account if you don't have one
3. In Render dashboard, click "New" and select "Web Service"
4. Connect your GitHub repository
5. Use the following settings:
   - **Name**: mortgage-calculator (or your preferred name)
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
6. Click "Create Web Service"

Render will automatically detect the configuration in `render.yaml` and deploy your application.

### Manual Configuration

If you prefer to configure manually:

1. In Render dashboard, click "New" and select "Web Service"
2. Connect your GitHub repository
3. Configure the service:
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Python Version**: 3.9 (or your preferred version)
4. Click "Create Web Service"

## Project Structure

```
mortgage_calculator/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── render.yaml             # Render.com deployment configuration
├── Procfile                # Process file for deployment
├── static/                 # Static assets
│   ├── css/
│   │   └── style.css       # Custom CSS styles
│   └── js/
│       └── script.js       # JavaScript for interactive UI
├── templates/              # HTML templates
│   ├── index.html          # Main calculator form
│   └── results.html        # Results page with amortization schedule
└── notebooks/              # Original Jupyter notebooks
    └── mortgage_calculator.ipynb  # Original calculator implementation
```

## Technical Details

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Deployment**: Render.com with Gunicorn WSGI server
- **Security Features**:
  - Content Security Policy (CSP) with flask-talisman
  - Cross-Origin Resource Sharing (CORS) protection
  - Rate limiting to prevent abuse
  - Secure cookies and session handling
  - HTTPS enforcement in production
  - Comprehensive error handling and logging
- **Dependencies**: 
  - flask: Web framework
  - python-dateutil: Date manipulation utilities
  - gunicorn: WSGI HTTP server for production
  - flask-talisman: Security headers and CSP
  - flask-cors: CORS protection
  - flask-limiter: Rate limiting

## License

MIT

## Acknowledgments

- Based on a Jupyter notebook implementation of a mortgage calculator
- Utilizes Bootstrap 5 for responsive design