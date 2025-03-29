import bcrypt

# 明文密码 HT348921,HT731649
plain_password = "HT731649"

# 生成哈希密码
hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())
print(hashed_password.decode('utf-8'))