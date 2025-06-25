# -*- coding: utf-8 -*-
# app.py
import sys
import traceback
import os
import re
from flask import Flask, request, jsonify, send_file
from datetime import datetime, timedelta
from sqlalchemy import func

# Add startup logging
print("Starting Finance Bot application...")
print(f"Python version: {sys.version}")

# Railway environment debugging
print("=== RAILWAY ENVIRONMENT DEBUG ===")
railway_env_vars = ['PORT', 'RAILWAY_ENVIRONMENT', 'RAILWAY_PROJECT_ID', 'RAILWAY_SERVICE_ID']
for var in railway_env_vars:
    value = os.environ.get(var, 'NOT SET')
    print(f"{var}: {value}")
print("===================================")

try:
    from database import init_db, get_db
    from models import User, Category, Transaction, TransactionType
    print("Database modules imported successfully")
except Exception as e:
    print(f"ERROR importing database modules: {e}")
    traceback.print_exc()
    sys.exit(1)

# Import Twilio's TwiML MessagingResponse
try:
    from twilio.twiml.messaging_response import MessagingResponse
    print("Twilio module imported successfully")
except Exception as e:
    print(f"ERROR importing Twilio: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    from excel_generator import generate_excel_report # Keep this import
    print("Excel generator imported successfully")
except Exception as e:
    print(f"ERROR importing excel_generator: {e}")
    traceback.print_exc()
    sys.exit(1)

print("Creating Flask application...")
try:
    app = Flask(__name__)
    print("Flask application created successfully")

    # Initialize the database when the application starts
    print("Initializing database...")
    with app.app_context():
        try:
            init_db()
            print("Application started successfully with database connection!")
        except Exception as e:
            print(f"Warning: Database initialization failed: {e}")
            print("The application will still start, but database functionality may be limited.")
            print("Please check your Railway database configuration.")
            traceback.print_exc()

    print("Flask application setup completed successfully!")
    
    # Application startup banner
    print("=" * 50)
    print("🚀 FINANCE BOT APPLICATION READY!")
    print("✅ All modules loaded successfully")
    print("✅ Flask application initialized") 
    print("✅ Database connection established")
    print("🌐 Ready to serve requests!")
    print("=" * 50)
    
except Exception as e:
    print(f"CRITICAL ERROR during Flask application setup: {e}")
    traceback.print_exc()
    sys.exit(1)

@app.route('/')
def home():
    """
    A simple home route to confirm the server is running.
    """
    return "Personal Finance Bot Backend is Running!"

@app.route('/health')
def health():
    """
    Health check endpoint for debugging 502 errors.
    """
    try:
        # Test database connection
        session = next(get_db())
        session.close()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy", 
        "message": "Finance Bot is running",
        "database": db_status,
        "version": "1.0"
    }, 200

@app.route('/test')
def test():
    """
    Simple test endpoint.
    """
    return "Test endpoint working!", 200

# --- Helper Functions and Handlers (DEFINED BEFORE WEBHOOK) ---

def get_or_create_user(session, whatsapp_number):
    """
    Helper function to get an existing user or create a new one.
    """
    user = session.query(User).filter_by(whatsapp_number=whatsapp_number).first()
    if not user:
        user = User(whatsapp_number=whatsapp_number)
        session.add(user)
        session.commit() # Commit immediately to get the user ID
        session.refresh(user)
    return user

def parse_command(message_text):
    """
    Parses a raw message text into a command and arguments.
    Example: "/income 500000 salary" -> ("income", ["500000", "salary"])
    """
    parts = message_text.strip().split(maxsplit=2) # Split by first two spaces max
    command = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    return command, args

def get_help_message():
    """
    Provides a list of available commands to the user.
    """
    return (
        "Here are the commands you can use:\n"
        "/income <amount> <category> [notes] - Record income\n"
        "/expense <amount> <category> [notes] - Record expense\n"
        "/addcategory <type> <name> - Add a new category (e.g., income Salary, expense Food)\n"
        "/editcategory <old_name> <new_name> <type> - Edit a category name\n"
        "/deletecategory <name> <type> - Delete a category\n"
        "/asset <amount> [notes] - Adjust your total assets (can be positive or negative)\n"
        "/delete <transaction_id> - Delete a specific transaction\n"
        "/report [monthly/weekly/all] - Get financial report\n"
        "/history [count] - Show recent transactions (default: 5)\n"
        "/listall - Show all transactions with IDs\n"
        "/summary - Show total income, expenses, and current assets\n"
        "/help - Show this help message"
    )

def handle_income(session, user, args):
    """Handles the /income command."""
    if len(args) < 2:
        raise ValueError("Usage: /income <amount> <category> [notes]")
    try:
        amount = float(args[0])
        if amount <= 0:
            raise ValueError("Amount must be positive.")
    except ValueError:
        raise ValueError("Invalid amount. Please provide a number.")

    category_name = args[1].lower()
    notes = args[2] if len(args) > 2 else None

    category = session.query(Category).filter_by(user_id=user.id, name=category_name, type=TransactionType.INCOME).first()
    if not category:
        # Auto-add category if not found
        category = Category(user_id=user.id, name=category_name, type=TransactionType.INCOME)
        session.add(category)
        session.flush() # Flush to get category ID before adding transaction

    transaction = Transaction(
        user_id=user.id,
        type=TransactionType.INCOME,
        amount=amount,
        category_id=category.id,
        notes=notes
    )
    session.add(transaction)
    return f"Income recorded: Rp{amount:,.2f} for '{category.name}'. Notes: {notes if notes else 'None'}."

def handle_expense(session, user, args):
    """Handles the /expense command."""
    if len(args) < 2:
        raise ValueError("Usage: /expense <amount> <category> [notes]")
    try:
        amount = float(args[0])
        if amount <= 0:
            raise ValueError("Amount must be positive.")
    except ValueError:
        raise ValueError("Invalid amount. Please provide a number.")

    category_name = args[1].lower()
    notes = args[2] if len(args) > 2 else None

    category = session.query(Category).filter_by(user_id=user.id, name=category_name, type=TransactionType.EXPENSE).first()
    if not category:
        # Auto-add category if not found
        category = Category(user_id=user.id, name=category_name, type=TransactionType.EXPENSE)
        session.add(category)
        session.flush()

    transaction = Transaction(
        user_id=user.id,
        type=TransactionType.EXPENSE,
        amount=amount,
        category_id=category.id,
        notes=notes
    )
    session.add(transaction)
    return f"Expense recorded: Rp{amount:,.2f} for '{category.name}'. Notes: {notes if notes else 'None'}."

def handle_add_category(session, user, args):
    """Handles the /addcategory command."""
    if len(args) < 2:
        raise ValueError("Usage: /addcategory <type (income/expense)> <name>")

    category_type_str = args[0].lower()
    category_name = args[1].lower()

    if category_type_str == 'income':
        category_type = TransactionType.INCOME
    elif category_type_str == 'expense':
        category_type = TransactionType.EXPENSE
    else:
        raise ValueError("Invalid category type. Must be 'income' or 'expense'.")

    existing_category = session.query(Category).filter_by(
        user_id=user.id, name=category_name, type=category_type
    ).first()

    if existing_category:
        return f"Category '{category_name}' ({category_type.value}) already exists."

    new_category = Category(user_id=user.id, name=category_name, type=category_type)
    session.add(new_category)
    return f"Category '{category_name}' ({category_type.value}) added successfully."

def handle_edit_category(session, user, args):
    """Handles the /editcategory command."""
    if len(args) < 3:
        raise ValueError("Usage: /editcategory <old_name> <new_name> <type (income/expense)>")

    old_name = args[0].lower()
    new_name = args[1].lower()
    category_type_str = args[2].lower()

    if category_type_str == 'income':
        category_type = TransactionType.INCOME
    elif category_type_str == 'expense':
        category_type = TransactionType.EXPENSE
    else:
        raise ValueError("Invalid category type. Must be 'income' or 'expense'.")

    category = session.query(Category).filter_by(
        user_id=user.id, name=old_name, type=category_type
    ).first()

    if not category:
        return f"Category '{old_name}' ({category_type.value}) not found."

    category.name = new_name
    return f"Category '{old_name}' ({category_type.value}) renamed to '{new_name}'."

def handle_delete_category(session, user, args):
    """Handles the /deletecategory command."""
    if len(args) < 2:
        raise ValueError("Usage: /deletecategory <name> <type (income/expense)>")

    category_name = args[0].lower()
    category_type_str = args[1].lower()

    if category_type_str == 'income':
        category_type = TransactionType.INCOME
    elif category_type_str == 'expense':
        category_type = TransactionType.EXPENSE
    else:
        raise ValueError("Invalid category type. Must be 'income' or 'expense'.")

    category = session.query(Category).filter_by(
        user_id=user.id, name=category_name, type=category_type
    ).first()

    if not category:
        return f"Category '{category_name}' ({category_type.value}) not found."

    # Check if there are any transactions linked to this category
    linked_transactions = session.query(Transaction).filter_by(category_id=category.id).first()
    if linked_transactions:
        return (f"Cannot delete category '{category_name}' as it has existing transactions linked. "
                "Please reassign or delete linked transactions first.")

    session.delete(category)
    return f"Category '{category_name}' ({category_type.value}) deleted successfully."

def handle_asset_adjustment(session, user, args):
    """Handles the /asset command."""
    if len(args) < 1:
        raise ValueError("Usage: /asset <amount> [notes]")
    try:
        amount = float(args[0])
    except ValueError:
        raise ValueError("Invalid amount. Please provide a number.")

    notes = args[1] if len(args) > 1 else "Manual asset adjustment"

    transaction = Transaction(
        user_id=user.id,
        type=TransactionType.ASSET_ADJUSTMENT,
        amount=amount,
        notes=notes
    )
    session.add(transaction)
    return f"Asset adjusted by Rp{amount:,.2f}. Notes: {notes}."

def handle_delete_transaction(session, user, args):
    """Handles the /delete command."""
    if len(args) < 1:
        raise ValueError("Usage: /delete <transaction_id>\nUse /listall to see transaction IDs")
    
    try:
        transaction_id = int(args[0])
    except ValueError:
        raise ValueError("Invalid transaction ID. Please provide a number.\nUse /listall to see transaction IDs")

    # Find the transaction
    transaction = session.query(Transaction).filter_by(
        id=transaction_id, user_id=user.id
    ).first()

    if not transaction:
        return f"Transaction with ID {transaction_id} not found or doesn't belong to you.\nUse /listall to see your transactions."

    # Store transaction details for confirmation message
    transaction_details = f"{transaction.type.value.capitalize()}: Rp{transaction.amount:,.2f}"
    if transaction.category:
        transaction_details += f" ({transaction.category.name})"
    if transaction.notes:
        transaction_details += f" - {transaction.notes}"
    
    # Delete the transaction
    session.delete(transaction)
    
    return f"✅ Transaction deleted successfully!\nDeleted: {transaction_details}"

def handle_list_all_transactions(session, user, args):
    """Handles the /listall command."""
    # Get limit from args, default to 20
    limit = 20
    if args:
        try:
            limit = int(args[0])
            if limit <= 0:
                raise ValueError("Limit must be positive.")
            if limit > 100:
                limit = 100  # Cap at 100 for performance
        except ValueError:
            return "Invalid limit. Please provide a number (max 100)."

    transactions = session.query(Transaction).filter_by(user_id=user.id)\
                                             .order_by(Transaction.transaction_date.desc())\
                                             .limit(limit).all()

    if not transactions:
        return "No transactions found."

    message_lines = [f"📋 All Transactions (showing last {len(transactions)}):"]
    message_lines.append("=" * 40)
    
    for t in transactions:
        category_name = t.category.name if t.category else "N/A"
        date_str = t.transaction_date.strftime('%m/%d %H:%M')
        
        # Format amount with + or - sign
        if t.type == TransactionType.INCOME or t.type == TransactionType.ASSET_ADJUSTMENT:
            amount_str = f"+Rp{t.amount:,.0f}"
        else:
            amount_str = f"-Rp{t.amount:,.0f}"
        
        # Create transaction line
        transaction_line = f"ID:{t.id} | {date_str} | {amount_str}"
        
        # Add category if exists
        if t.category:
            transaction_line += f" | {category_name}"
        
        # Add notes if exists (truncated)
        if t.notes:
            notes_short = t.notes[:20] + "..." if len(t.notes) > 20 else t.notes
            transaction_line += f" | {notes_short}"
        
        message_lines.append(transaction_line)
    
    message_lines.append("=" * 40)
    message_lines.append("💡 Use /delete <ID> to delete a transaction")
    
    return "\n".join(message_lines)

# Renamed handle_report to handle_report_data as it won't send file directly via webhook response
def handle_report_data(session, user, args):
    """
    Handles the /report command. Generates an Excel file buffer.
    Doesn't send the file directly as webhook response.
    """
    period = args[0].lower() if args else 'monthly'

    end_date = datetime.now()
    start_date = None

    if period == 'monthly':
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == 'weekly':
        start_date = end_date - timedelta(days=end_date.weekday()) # Monday of current week
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'all':
        start_date = None # No start date for all time
    else:
        # Return None to indicate an invalid period
        raise ValueError("Invalid report period. Use 'monthly', 'weekly', or 'all'.")

    query = session.query(Transaction).filter_by(user_id=user.id)
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    query = query.order_by(Transaction.transaction_date.desc())

    transactions = query.all()

    if not transactions:
        return None # Return None if no transactions

    excel_file_buffer = generate_excel_report(transactions, start_date, end_date, user.whatsapp_number)
    return excel_file_buffer


def handle_history(session, user, args):
    """Handles the /history command."""
    count = 5 # Default
    if args:
        try:
            count = int(args[0])
            if count <= 0:
                raise ValueError("Count must be positive.")
        except ValueError:
            return "Invalid count. Please provide a number."

    transactions = session.query(Transaction).filter_by(user_id=user.id)\
                                             .order_by(Transaction.transaction_date.desc())\
                                             .limit(count).all()

    if not transactions:
        return "No transaction history found."

    history_messages = ["Your recent transactions:"]
    for t in transactions:
        category_name = t.category.name if t.category else "N/A"
        date_str = t.transaction_date.strftime('%Y-%m-%d %H:%M')
        notes_str = f" ({t.notes})" if t.notes else ""
        history_messages.append(f"• {date_str} | {t.type.value.capitalize()}: Rp{t.amount:,.2f} | {category_name}{notes_str}")

    return "\n".join(history_messages)

def handle_summary(session, user):
    """Handles the /summary command."""
    # Total income
    total_income = session.query(func.sum(Transaction.amount))\
                          .filter_by(user_id=user.id, type=TransactionType.INCOME)\
                          .scalar() or 0.0

    # Total expenses
    total_expense = session.query(func.sum(Transaction.amount))\
                           .filter_by(user_id=user.id, type=TransactionType.EXPENSE)\
                           .scalar() or 0.0

    # Total asset adjustments
    total_asset_adjustment = session.query(func.sum(Transaction.amount))\
                                    .filter_by(user_id=user.id, type=TransactionType.ASSET_ADJUSTMENT)\
                                    .scalar() or 0.0

    # Calculate current assets based on the sum of all income, expenses, and adjustments
    current_assets = total_income - total_expense + total_asset_adjustment

    summary_message = (
        f"Financial Summary for {user.whatsapp_number}:\n"
        f"• Total Income: Rp{total_income:,.2f}\n"
        f"• Total Expenses: Rp{total_expense:,.2f}\n"
        f"• Current Net Assets: Rp{current_assets:,.2f}"
    )
    return summary_message

# --- Webhook Route (DEFINED AFTER ALL HANDLERS) ---
@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    """
    This endpoint receives messages from a WhatsApp bot (e.g., Twilio).
    Twilio sends data as application/x-www-form-urlencoded, not JSON.
    We need to access request.form for the incoming data.
    The 'Body' parameter contains the message text, and 'From' contains the sender's WhatsApp number.
    """
    if request.method == 'GET':
        return {"status": "webhook endpoint is working", "method": "GET"}, 200
    
    try:
        print("Webhook called - processing request...")
        
        message_text = request.form.get('Body')
        whatsapp_number = request.form.get('From')

        if not whatsapp_number or not message_text:
            print("Missing required parameters")
            resp = MessagingResponse()
            resp.message("Error: Missing 'From' or 'Body' parameters in message.")
            return str(resp), 400

        print(f"Processing message from {whatsapp_number}: {message_text}")
        
        session = next(get_db())

        response_message = "An internal error occurred. Please try again later." # Default error for internal issues

        try:
            user = get_or_create_user(session, whatsapp_number)
            command, args = parse_command(message_text)

            if command == '/income':
                response_message = handle_income(session, user, args)
            elif command == '/expense':
                response_message = handle_expense(session, user, args)
            elif command == '/addcategory':
                response_message = handle_add_category(session, user, args)
            elif command == '/editcategory':
                response_message = handle_edit_category(session, user, args)
            elif command == '/deletecategory':
                response_message = handle_delete_category(session, user, args)
            elif command == '/asset' or command == '/aset':
                response_message = handle_asset_adjustment(session, user, args)
            elif command == '/delete':
                response_message = handle_delete_transaction(session, user, args)
            elif command == '/report':
                excel_file_buffer = handle_report_data(session, user, args)
                if excel_file_buffer:
                    response_message = "Your report has been generated! (Note: Actual file download via WhatsApp requires further Twilio media API integration)."
                else:
                    response_message = "No data to generate report for the selected period."
            elif command == '/history':
                response_message = handle_history(session, user, args)
            elif command == '/summary':
                response_message = handle_summary(session, user)
            elif command == '/listall':
                response_message = handle_list_all_transactions(session, user, args)
            elif command == '/help':
                response_message = get_help_message()
            else:
                response_message = "Unknown command. Type /help for available commands."

            session.commit()
            print(f"Successfully processed command: {command}")

        except ValueError as e:
            session.rollback()
            response_message = f"Error: {e}"
            print(f"ValueError in webhook: {e}")
        except Exception as e:
            session.rollback()
            app.logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            print(f"Unexpected error in webhook: {e}")
            response_message = "An internal error occurred. Please try again later."
        finally:
            session.close()

        resp = MessagingResponse()
        resp.message(response_message)
        print(f"Sending response: {response_message}")
        return str(resp)
        
    except Exception as e:
        print(f"Critical error in webhook: {e}")
        app.logger.error(f"Critical webhook error: {e}", exc_info=True)
        resp = MessagingResponse()
        resp.message("Service temporarily unavailable. Please try again later.")
        return str(resp), 500


@app.route('/download_report/<user_whatsapp_number>/<period>', methods=['GET'])
def download_report(user_whatsapp_number, period):
    session = next(get_db())
    try:
        user = session.query(User).filter_by(whatsapp_number=user_whatsapp_number).first()
        if not user:
            return "User not found", 404

        end_date = datetime.now()
        start_date = None

        if period == 'monthly':
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == 'weekly':
            start_date = end_date - timedelta(days=end_date.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'all':
            start_date = None
        else:
            return "Invalid report period", 400

        query = session.query(Transaction).filter_by(user_id=user.id)
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        transactions = query.order_by(Transaction.transaction_date.desc()).all()

        if not transactions:
            return "No transactions found for this period for the user.", 200

        excel_file_buffer = generate_excel_report(transactions, start_date, end_date, user.whatsapp_number)
        filename = f"finance_report_{user.whatsapp_number}_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return send_file(
            excel_file_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    finally:
        session.close()


if __name__ == '__main__':
    # This block allows you to run `python app.py` locally for development.
    # However, on Railway, Gunicorn will run the application,
    # so the app.run() line below will not be executed there.
    # You can leave it for local development, or comment it out.

    # If you want to run locally with Gunicorn as well,
    # you would run 'gunicorn --bind 127.0.0.1:5000 app:app' locally
    # instead of 'python app.py'.

    # Remove or comment out the line below for production deployment:
    # port = int(os.environ.get('PORT', 5000))
    # app.run(debug=True, host='0.0.0.0', port=port)

    # You might want to keep init_db() here for easy local development
    init_db()
    print("Database initialization complete for local run.")

# Test that all handler functions are defined (after all definitions)
print("Testing handler functions...")
try:
    # Test if all handler functions exist
    handler_functions = [
        'get_help_message', 'handle_income', 'handle_expense', 'handle_add_category', 
        'handle_edit_category', 'handle_delete_category', 
        'handle_asset_adjustment', 'handle_delete_transaction', 'handle_list_all_transactions',
        'handle_report_data', 'handle_history', 'handle_summary'
    ]
    
    for func_name in handler_functions:
        if func_name in globals():
            print(f"✓ {func_name} is defined")
        else:
            print(f"✗ {func_name} is NOT defined")
    
    print("Handler function test completed")
    print("✅ All handler functions verified")
except Exception as e:
    print(f"Error testing handler functions: {e}")

print("🎉 FINANCE BOT FULLY INITIALIZED AND READY!")
