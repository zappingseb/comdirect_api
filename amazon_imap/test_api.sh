#!/bin/bash

# Test script for Amazon Categorizer API

API_URL="http://raspberrypidocker:5010"
SECRET="amazon_categorizer_secret_key"

echo "Testing Amazon Categorizer API"
echo "================================"
echo ""

# Test 1: Health check
echo "1. Health Check:"
curl -s -X GET "$API_URL/health" | jq . || echo "Failed"
echo ""

# Test 2: Categorize transaction
echo "2. Test Categorization (Order: 306-6340477-5787538):"
curl -s -X POST "$API_URL/categorize" \
  -H "Content-Type: application/json" \
  -H "X-API-Secret: $SECRET" \
  -d '{"transaction": "AMAZON PAYMENTS 306-6340477-5787538"}' | jq .
echo ""

# Test 3: Invalid transaction (should fail gracefully)
echo "3. Test Invalid Transaction:"
curl -s -X POST "$API_URL/categorize" \
  -H "Content-Type: application/json" \
  -H "X-API-Secret: $SECRET" \
  -d '{"transaction": "INVALID 123-456-789"}' | jq .
echo ""

echo "Done!"
