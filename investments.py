from database import fetch_all

def get_user_investments(user_id):
    """获取用户的全部投资记录"""
    query = """
        SELECT id, investment_type, amount, return_amount, investment_date
        FROM investments
        WHERE user_id = %s
    """
    return fetch_all(query, (user_id,))

def calculate_user_stats(user_id):
    """计算用户的总投资、总回报、净收益和 ROI"""
    query = """
        SELECT SUM(amount), SUM(return_amount)
        FROM investments
        WHERE user_id = %s
    """
    result = fetch_all(query, (user_id,))
    total_investment, total_return = result[0]
    net_profit = total_return - total_investment if total_investment else 0
    roi = (net_profit / total_investment * 100) if total_investment else 0
    return {
        "total_investment": total_investment or 0,
        "total_return": total_return or 0,
        "net_profit": net_profit,
        "roi": roi
    }

def filter_investments(user_id, investment_type=None, start_date=None, end_date=None):
    """根据条件筛选投资记录"""
    conditions = []
    params = [user_id]

    if investment_type:
        conditions.append("investment_type = %s")
        params.append(investment_type)
    if start_date:
        conditions.append("investment_date >= %s")
        params.append(start_date)
    if end_date:
        conditions.append("investment_date <= %s")
        params.append(end_date)

    query = f"""
        SELECT id, investment_type, sub_type, amount, return_amount, investment_date, details
        FROM investments
        WHERE user_id = %s
    """
    if conditions:
        query += " AND " + " AND ".join(conditions)

    return fetch_all(query, tuple(params))