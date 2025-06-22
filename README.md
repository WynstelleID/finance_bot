Personal Finance Tracking WhatsApp Bot Backend
This is the backend Flask application for a personal finance tracking bot, designed to integrate with a WhatsApp bot API (like Twilio). It allows users to manage their income, expenses, assets, and generate financial reports directly via chat commands.

Table of Contents
Features

Tech Stack

Project Structure

Installation Guide

Prerequisites

Step 1: Clone the Repository

Step 2: Create and Activate a Virtual Environment

Step 3: Install Dependencies

Step 4: Initialize the Database

Step 5: Run the Flask Application

Step 6: Expose Your Local Server with ngrok

Step 7: Configure Twilio WhatsApp Sandbox

Usage / Bot Commands

Troubleshooting Common Issues

command not found: pip or python

Address already in use (Port 5000 is occupied)

ngrok: command not found

ngrok authentication failed

POST /webhook HTTP/1.1" 415

ModuleNotFoundError: No module named 'twilio'

NameError: name 'handle_income' is not defined

NameError: name 'openpyxl' is not defined

An internal error occurred. Please try again later.

Creator

Features
Income Recording: Easily log your income with amounts and categories.

Example: /income 5000000 Gaji bulanan

Expense Recording: Track your spending with amounts and categories.

Example: /expense 150000 Makan malam

Category Management: Add, edit, and delete custom categories for both income and expenses.

Example: /addcategory expense Transportasi

Example: /editcategory expense transportasi_lama transportasi_baru

Example: /deletecategory income side_hustle

Asset Tracking: Manually adjust your total assets.

Example: /asset 10000000 Tambahan deposito (for increasing assets)

Example: /asset -500000 Investasi merugi (for decreasing assets)

Custom Notes: Attach notes to any transaction for better context.

Transaction History: View a list of your most recent transactions.

Example: /history (shows last 5)

Example: /history 10 (shows last 10)

Financial Summaries: Get quick overviews of total income, expenses, and current assets.

Example: /summary

Excel Report Generation: Generate detailed reports (monthly, weekly, or all-time) in Excel format.

Example: /report monthly

(Note: Direct file download via WhatsApp requires further Twilio media API integration beyond this backend. The bot will confirm report generation, but you'd need to manually retrieve or extend the bot for direct download links.)

Multi-user Support: Data is securely stored per WhatsApp number, allowing multiple users to manage their finances independently.

Confirmations: The bot responds with confirmations after each successful entry.

Tech Stack
Backend: Python 3.11/3.12 (Flask framework)

Database: SQLite (for simplicity, file-based)

ORM: SQLAlchemy (for database interaction)

Excel Generation: openpyxl

WhatsApp Integration: Twilio (requires external setup and ngrok for local testing)

Project Structure
finance_bot/
├── app.py # Main Flask application, defines routes and command handlers
├── database.py # Database initialization and session management
├── models.py # SQLAlchemy database models (User, Category, Transaction)
├── excel_generator.py # Logic for generating Excel reports
└── requirements.txt # Python dependencies

Installation Guide
Follow these steps to set up and run the backend application.

Prerequisites
Python: Version 3.11 or 3.12 is highly recommended due to compatibility with SQLAlchemy 2.x. (Python 3.13 can cause issues).

macOS (Homebrew): brew install python@3.11 (or python@3.12)

Linux (Ubuntu/Debian): sudo apt install python3.11 python3.11-venv

Windows: Download installer from python.org/downloads/ and ensure "Add Python to PATH" is checked.

pip: Python's package installer (usually comes with Python).

ngrok: A tool to expose your local server to the internet for testing with Twilio.

Download from ngrok.com/download.

Unzip the executable and move it to a directory in your system's PATH (e.g., /usr/local/bin on macOS/Linux).

Sign up for a free ngrok account and link your authtoken using ngrok config add-authtoken <YOUR_AUTH_TOKEN>.

Twilio Account: A free trial account at twilio.com with WhatsApp Sandbox configured.

Step 1: Clone the Repository
If you're starting from scratch, create a directory for your project and add the files provided previously. If you have a Git repository, clone it:

git clone <your-repo-url>
cd finance_bot

If you copied the files manually, ensure you are in the finance_bot directory.

Step 2: Create and Activate a Virtual Environment
It's best practice to use a virtual environment to manage project dependencies.

# Use your specific Python version (e.g., python3.11, python3.12)

# On macOS/Linux:

python3.11 -m venv venv

# Activate the virtual environment

source venv/bin/activate

# On Windows (in Command Prompt):

# .venv\Scripts\activate

Your terminal prompt should now show (venv) indicating the environment is active.

Step 3: Install Dependencies
With the virtual environment activated, install the required Python packages:

pip install -r requirements.txt
pip install twilio # Twilio library is not in requirements.txt initially.

Step 4: Initialize the Database
This will create the finance.db SQLite file in your project directory.

python database.py

Step 5: Run the Flask Application
In one terminal window, start your Flask backend:

python app.py

You should see output indicating the Flask server is running, typically on http://127.0.0.1:5000/. Keep this terminal running.

Step 6: Expose Your Local Server with ngrok
In a separate terminal window, start ngrok to create a public URL for your Flask app:

ngrok http 5000

(If your Flask app is running on a different port, use that port number instead).

You will see output with a Forwarding HTTPS URL (e.g., https://your-random-subdomain.ngrok-free.app). Copy this URL. Keep this terminal running.

Step 7: Configure Twilio WhatsApp Sandbox
Log in to Twilio Console.

Navigate to Develop > Messaging > Try it out > Try WhatsApp.

Under "Sandbox Configuration":

In the "WHEN A MESSAGE COMES IN" field, paste your ngrok public HTTPS URL and append /webhook to it.

Example: https://your-random-subdomain.ngrok-free.app/webhook

Ensure the method is set to HTTP POST.

Click the "Save" button at the bottom.

Connect your WhatsApp number by sending the provided "join " message from your WhatsApp to the Twilio Sandbox number.

Usage / Bot Commands
Once everything is set up, send these commands to your Twilio Sandbox WhatsApp number:

/income <amount> <category> [notes] - Record income (e.g., /income 5000000 Gaji bulanan)

/expense <amount> <category> [notes] - Record expense (e.g., /expense 15000 Kopi)

/addcategory <type (income/expense)> <name> - Add a new category (e.g., /addcategory expense Transportasi)

/editcategory <old_name> <new_name> <type (income/expense)> - Edit a category name (e.g., /editcategory expense old_food new_cuisine)

/deletecategory <name> <type (income/expense)> - Delete a category (e.g., /deletecategory income bonus)

/asset <amount> [notes] - Adjust your total assets (e.g., /asset 10000000 Bonus or /asset -50000 Saham turun)

/report [monthly/weekly/all] - Get financial report (e.g., /report monthly). (Note: The bot will confirm generation; direct file sending requires more setup.)

/history [count] - Show recent transactions (default: 5) (e.g., /history 10)

/summary - Show total income, expenses, and current assets.

/help - Show available commands.

Troubleshooting Common Issues
Here are solutions to common problems you might encounter during setup:

command not found: pip or python
Problem: Your system cannot locate the pip or python executable.
Solution:

Verify Python Installation: Ensure Python 3.11 or 3.12 is installed.

Check with python3.11 --version or python3.12 --version.

If not installed, follow the Prerequisites section.

Use python3 / pip3: On some systems, python refers to Python 2. Try python3 and pip3 instead.

Check PATH: Ensure Python's installation directory is in your system's PATH. For Homebrew/apt, this is usually handled automatically.

Address already in use (Port 5000 is occupied)
Problem: Another program is already using the default port 5000.
Solution:

Find and Kill Process:

macOS/Linux: sudo lsof -i :5000 to find the PID, then kill <PID> (or kill -9 <PID> if stubborn).

Windows: netstat -ano | findstr :5000 to find PID, then taskkill /PID <PID> /F.

Disable AirPlay Receiver (macOS): Go to System Settings/Preferences > General > AirDrop & Handoff, and uncheck "AirPlay Receiver".

Change Flask Port: In app.py, change app.run(debug=True, host='0.0.0.0', port=5000) to a different port like port=5001. Remember to update your ngrok command if you do this.

ngrok: command not found
Problem: The ngrok executable is not in your system's PATH.
Solution:

Download and Unzip: Ensure you've downloaded ngrok and unzipped the executable.

Move to PATH: Move the ngrok executable to a directory in your PATH (e.g., /usr/local/bin on macOS/Linux).

sudo mv ~/Downloads/ngrok /usr/local/bin/ (adjust path to ngrok if different).

Make Executable: chmod +x /usr/local/bin/ngrok

ngrok authentication failed
Problem: Your ngrok client is not authenticated with your account.
Solution:

Sign Up: Go to https://dashboard.ngrok.com/signup and create a free account.

Get Authtoken: Log in, go to https://dashboard.ngrok.com/get-started/your-authtoken.

Add Authtoken: Copy the command provided on the ngrok dashboard (e.g., ngrok config add-authtoken <YOUR_TOKEN>) and paste it into your terminal.

POST /webhook HTTP/1.1" 415
Problem: Flask received a request but didn't like the Content-Type header (it expected JSON but got form-encoded data from Twilio).
Solution: This has been addressed in app.py by using request.form.get('Body') and request.form.get('From'). Ensure you have the latest version of app.py.

ModuleNotFoundError: No module named 'twilio'
Problem: The twilio Python library is not installed in your active virtual environment.
Solution:

Activate Virtual Environment: source venv/bin/activate

Install Twilio: pip install twilio

Restart Flask App: Stop and restart python app.py.

NameError: name 'handle*income' is not defined
Problem: Functions like handle_income were called before they were defined in app.py.
Solution: This has been addressed by reordering functions in app.py. Ensure all handle*\* and get_help_message functions are defined before the webhook function. Make sure you have the latest app.py content.

NameError: name 'openpyxl' is not defined
Problem: The openpyxl.styles module was referenced without being explicitly imported.
Solution: This has been addressed in excel_generator.py by adding import openpyxl.styles and from models import TransactionType. Ensure you have the latest excel_generator.py content.

An internal error occurred. Please try again later.
Problem: This is a generic message from your Flask app's error handling. The actual error is a Python traceback in your Flask app's terminal.
Solution:

Check Flask Terminal: Immediately look at the terminal running python app.py for a detailed Traceback (most recent call last):.

Identify the Cause: The traceback will pinpoint the exact line of code causing the issue. Refer to specific NameError, TypeError, etc., in the traceback to identify the underlying problem.

Creator
This backend application was created by Dandi Setiyawan.
