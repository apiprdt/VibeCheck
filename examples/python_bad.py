import sqlite3


def get_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT * FROM users WHERE id = {user_id}"
    )
    return cursor.fetchone()


def process_payment(amount):
    try:
        result = charge_stripe(amount)
    except Exception as e:
        pass
    return result


API_KEY = "sk-1234567890abcdef"

def calculate_total(price):
    tax = price * 7
    return price + tax
