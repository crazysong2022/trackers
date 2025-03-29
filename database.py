import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

def get_local_db_connection():
    """获取本地数据库连接"""
    local_db_url = os.getenv("LOCAL_DATABASE_URL")
    if not local_db_url:
        raise ValueError("环境变量中未找到 LOCAL_DATABASE_URL，请检查 .env 文件。")
    
    try:
        return psycopg2.connect(local_db_url)
    except Exception as e:
        print(f"本地数据库连接失败: {e}")
        raise

def get_cloud_db_connection():
    """获取云端数据库连接"""
    cloud_db_url = os.getenv("CLOUD_DATABASE_URL")
    if not cloud_db_url:
        raise ValueError("环境变量中未找到 CLOUD_DATABASE_URL，请检查 .env 文件。")
    
    try:
        return psycopg2.connect(cloud_db_url)
    except Exception as e:
        print(f"云端数据库连接失败: {e}")
        raise

def fetch_one(query, params=None):
    """执行查询并返回单条记录（字典形式）"""
    conn = get_local_db_connection()  # 默认从本地数据库读取数据
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, params)
        result = cursor.fetchone()
    conn.close()
    return result

def fetch_all(query, params=None):
    """执行查询并返回所有记录（列表形式，每条记录为字典）"""
    conn = get_local_db_connection()  # 默认从本地数据库读取数据
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query, params)
        results = cursor.fetchall()
    conn.close()
    return results

def execute_query(query, params=None):
    """
    执行插入、更新或删除操作，并同步到本地和云端数据库。
    :param query: SQL 查询语句
    :param params: 参数化查询的参数
    """
    try:
        # 连接到本地数据库并执行操作
        local_conn = get_local_db_connection()
        with local_conn.cursor() as local_cursor:
            local_cursor.execute(query, params)
            local_conn.commit()

        # 连接到云端数据库并执行操作
        cloud_conn = get_cloud_db_connection()
        with cloud_conn.cursor() as cloud_cursor:
            cloud_cursor.execute(query, params)
            cloud_conn.commit()

    except Exception as e:
        print(f"数据库操作失败: {e}")
    finally:
        # 确保关闭所有数据库连接
        if 'local_conn' in locals():
            local_conn.close()
        if 'cloud_conn' in locals():
            cloud_conn.close()