import os
import requests
from typing import List, Dict


YNAB_BASE_URL = "https://api.ynab.com/v1"


def get_categories() -> List[Dict]:
    """
    Fetch all budget categories from YNAB API.

    Endpoint: GET /v1/budgets/{budget_id}/categories

    Returns a flat list of category dicts with 'id', 'name',
    and 'category_group_name' for Claude's context.
    """
    token = os.getenv('YNAB_TOKEN')
    budget_id = os.getenv('YNAB_BUDGET_ID')

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    url = f"{YNAB_BASE_URL}/budgets/{budget_id}/categories"

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    data = response.json()

    flat_categories = []
    for group in data['data']['category_groups']:
        group_name = group['name']

        # Skip internal YNAB system groups
        if group_name in ('Internal Master Category', 'Credit Card Payments'):
            continue

        for category in group['categories']:
            # Skip hidden/deleted categories
            if category.get('hidden') or category.get('deleted'):
                continue

            flat_categories.append({
                'id': category['id'],
                'name': category['name'],
                'group': group_name,
                'full_name': f"{group_name} > {category['name']}"
            })

    return flat_categories
