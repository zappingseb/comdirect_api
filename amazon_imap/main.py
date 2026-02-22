import os
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from services.imap_service import extract_order_number, search_amazon_email
from services.ynab_service import get_categories
from services.claude_service import suggest_category

# Load .env from same directory as main.py
load_dotenv()

app = Flask(__name__)

API_SECRET = os.getenv('API_SECRET')


def _validate_secret(req) -> bool:
    """
    Optional bearer/header auth.
    If API_SECRET is not set in .env, auth is skipped (for local dev).
    """
    if not API_SECRET:
        return True
    secret = req.headers.get('X-API-Secret')
    return secret == API_SECRET


@app.route('/health', methods=['GET'])
def health():
    """Simple health check for Docker and monitoring."""
    return jsonify({'status': 'ok'}), 200


@app.route('/categorize', methods=['POST'])
def categorize():
    """
    POST /categorize

    Request body (JSON):
    {
        "transaction": "AMAZON PAYMENTS 306-6340477-5787538"
    }

    Response (JSON):
    {
        "order_number": "306-6340477-5787538",
        "category_id": "uuid",
        "category_name": "Shopping > Online Shopping",
        "products": ["Item 1", "Item 2"]
    }
    """
    if not _validate_secret(request):
        return jsonify({'error': 'Unauthorized'}), 401

    body = request.get_json(silent=True)
    if not body or 'transaction' not in body:
        return jsonify({'error': 'Request body must include "transaction" field'}), 400

    transaction_string = body['transaction']

    # Step 1: Extract order number from transaction string
    order_number = extract_order_number(transaction_string)
    if not order_number:
        return jsonify({
            'error': 'Could not extract Amazon order number from transaction string',
            'input': transaction_string,
            'hint': 'Expected format: digits-digits-digits like 306-6340477-5787538'
        }), 400

    # Step 2: Search IMAP mailbox for matching email
    try:
        email_body = search_amazon_email(order_number)
    except RuntimeError as e:
        return jsonify({'error': f'IMAP error: {str(e)}'}), 500

    if not email_body:
        return jsonify({
            'error': 'No Amazon order email found for this order number',
            'order_number': order_number
        }), 404

    # Step 3: Fetch YNAB categories
    try:
        categories = get_categories()
    except Exception as e:
        return jsonify({'error': f'YNAB API error: {str(e)}'}), 500

    # Step 4: Ask Claude to suggest a category
    try:
        suggestion = suggest_category(email_body, categories, order_number)
    except Exception as e:
        return jsonify({'error': f'Claude API error: {str(e)}'}), 500

    # Step 5: Return the result
    return jsonify({
        'order_number': order_number,
        **suggestion
    }), 200


if __name__ == '__main__':
    # Development only - gunicorn is used in Docker
    app.run(host='0.0.0.0', port=5000, debug=False)
