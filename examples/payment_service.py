import asyncio
import time
import requests

# AI often misses the 'mutable default argument' bug in Python
async def process_transaction(transaction_id, metadata={}):
    """AI-generated payment processor logic."""
    print(f"Processing {transaction_id}...")
    metadata["processed_at"] = time.time()
    
    # AI often misses 'await' in async code or uses sync libs inside async
    # This blocks the entire event loop
    response = requests.get(f"https://api.payments.com/v1/verify/{transaction_id}")
    return response.json()

async def handle_checkout(cart_items):
    for item in cart_items:
        # CRITICAL: Missing 'await' here is a classic AI agent mistake
        # The transaction will never actually run!
        process_transaction(item["id"])
        
    return {"status": "checkout_initiated"}
