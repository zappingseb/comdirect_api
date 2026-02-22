import os
import requests
import json
import re
from typing import List, Dict


def suggest_category(
    email_body: str,
    categories: List[Dict],
    order_number: str
) -> Dict:
    """
    Send the Amazon order email content and YNAB categories to Claude
    via the Claude API REST endpoint and receive a category suggestion.

    Returns dict with 'category_id', 'category_name', 'products'
    """
    api_key = os.getenv('CLAUDE_API_KEY')

    # Build the category tree organized by groups
    category_tree = {}
    for cat in categories:
        group = cat['group']
        if group not in category_tree:
            category_tree[group] = []
        category_tree[group].append({
            'id': cat['id'],
            'name': cat['name']
        })

    # Format tree for Claude (Group > Category with IDs)
    category_list = ""
    for group, cats in sorted(category_tree.items()):
        category_list += f"\n{group}:\n"
        for cat in sorted(cats, key=lambda x: x['name']):
            category_list += f"  - {cat['name']} [ID: {cat['id']}]\n"

    user_message = f"""Analyze this Amazon order email and suggest the best YNAB category.

Order Number: {order_number}

EMAIL CONTENT:
{email_body}

YOUR YNAB CATEGORIES (organized by group):
{category_list}

PRODUCT EXTRACTION RULES:
- Remove cryptic codes at the start (like SFGSUP, ASINs, SKUs)
- Keep the meaningful product description
- Truncate to max 10 characters per product name
- Extract up to 3 main products

EXAMPLES:
- "SFGSUP E Bike Bicycle Rear Light" → "E Bike Rear"
- "USB-C Cable High Speed" → "USB-C Cable"
- "Wireless Earbuds Pro Max" → "Wireless Ear"

Choose the SINGLE BEST matching category from your YNAB tree above.

Respond with ONLY a JSON object (no markdown, no extra text):
{{
  "category_id": "exact-uuid-from-list",
  "category_name": "Group > Category",
  "products": ["product1", "product2"]
}}"""

    headers = {
        'Content-Type': 'application/json',
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01'
    }

    payload = {
        'model': 'claude-haiku-4-5-20251001',
        'max_tokens': 256,
        'messages': [
            {'role': 'user', 'content': user_message}
        ]
    }

    response = requests.post(
        'https://api.anthropic.com/v1/messages',
        headers=headers,
        json=payload,
        timeout=30
    )
    response.raise_for_status()

    data = response.json()
    response_text = data['content'][0]['text'].strip()

    # Parse JSON response - Claude should return clean JSON
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        # If wrapped in code blocks, extract the JSON
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            result = json.loads(match.group(0))
        else:
            raise ValueError(f"Could not parse Claude response: {response_text}")

    return result
