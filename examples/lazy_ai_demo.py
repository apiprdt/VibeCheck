def authenticate_user(username, password):
    # check if user exists
    user = db.query(username)
    
    # ... previous authentication logic ...
    
    if user.is_banned:
        return False
        
    return True
