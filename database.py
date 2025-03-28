import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

def get_db_connection():
    """获取数据库连接"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("环境变量中未找到 DATABASE_URL，请检查 .env 文件。")
    
    try:
        return psycopg2.connect(database_url)
    except Exception as e:
        print(f"数据库连接失败: {e}")
        raise

def fetch_one(query, params=None):
    """执行查询并返回单条记录（字典形式）"""
    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, params)
        result = cursor.fetchone()
    conn.close()
    return result

def fetch_all(query, params=None):
    """执行查询并返回所有记录（列表形式，每条记录为字典）"""
    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, params)
        results = cursor.fetchall()
    conn.close()
    return results

def execute_query(query, params=None):
    """执行插入、更新或删除操作"""
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute(query, params)
        conn.commit()
    conn.close()