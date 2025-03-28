import bcrypt
from database import fetch_one

def hash_password(password):
    """加密密码"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(stored_password, provided_password):
    """验证密码"""
    try:
        stored_password_bytes = stored_password.encode('utf-8')
        provided_password_bytes = provided_password.encode('utf-8')
        return bcrypt.checkpw(provided_password_bytes, stored_password_bytes)
    except ValueError as e:
        print(f"密码验证失败: {e}")
        return False

def login(username, password):
    """用户登录验证"""
    query = """
        SELECT id, username, password, role, balance
        FROM users
        WHERE username = %s
    """
    user = fetch_one(query, (username,))
    if user and verify_password(user["password"], password):
        return {
            "id": user["id"],
            "username": user["username"],
            "password": user["password"],
            "role": user["role"],
            "balance": user["balance"]
        }
    return None

def get_user_by_username(username):
    """根据用户名获取用户信息"""
    query = """
        SELECT id, username, password, role, balance
        FROM users
        WHERE username = %s
    """
    user = fetch_one(query, (username,))
    if user:
        return {
            "id": user["id"],
            "username": user["username"],
            "password": user["password"],
            "role": user["role"],
            "balance": user["balance"]
        }
    return None