from database import fetch_all, execute_query
import streamlit as st
import pandas as pd
from decimal import Decimal
import json

def custom_serializer(obj):
    """自定义 JSON 序列化器"""
    if isinstance(obj, Decimal):
        return float(obj)  # 将 Decimal 转换为浮点数
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def admin_dashboard():
    """管理员面板"""
    st.success(f"欢迎回来, 管理员!")
    
    # 录入新投资记录
    st.subheader("录入新投资记录")
    users = fetch_all("SELECT id, username, balance FROM users WHERE role != 'admin'")
    user_options = {user["username"]: {"id": user["id"], "balance": Decimal(str(user["balance"]))} for user in users}
    
    selected_user = st.selectbox("选择用户", list(user_options.keys()))
    user_info = user_options[selected_user]
    user_id = user_info["id"]
    current_balance = user_info["balance"]
    
    st.write(f"当前余额: ${current_balance:.2f}")
    
    investment_type = st.selectbox("投资类型", ["股票", "黄金", "期货", "博彩"])
    
    if investment_type == "博彩":
        sub_type = st.selectbox("博彩子类型", ["体育类", "Casino 类"])
        
        if sub_type == "体育类":
            team_a = st.text_input("对阵双方 - A队")
            team_b = st.text_input("对阵双方 - B队")
            
            bet_options = []
            num_bets = st.number_input("赔率选项数量", min_value=1, step=1)
            for i in range(num_bets):
                st.markdown(f"**赔率选项 {i+1}**")
                bet_type = st.text_input(f"选项 {i+1} - 赔率类型", key=f"bet_type_{i}")
                odds = st.number_input(f"选项 {i+1} - 赔率", min_value=0.0, step=0.01, key=f"odds_{i}")
                selected = st.checkbox(f"选项 {i+1} - 是否选择", key=f"selected_{i}")
                bet_options.append({"type": bet_type, "odds": Decimal(str(odds)), "selected": selected})
            
            selected_bet = [bet["type"] for bet in bet_options if bet["selected"]]
            selected_bet = selected_bet[0] if selected_bet else None
            
            amount = st.number_input("押注金额", min_value=0.0, step=0.01)
            amount = Decimal(str(amount))
            
            return_amount = st.number_input("回报金额", min_value=0.0, step=0.01)
            return_amount = Decimal(str(return_amount))
            
            # 计算新的余额
            new_balance = current_balance - amount + return_amount
            
            details = {
                "team_a": team_a,
                "team_b": team_b,
                "bet_options": bet_options,
                "selected_bet": selected_bet,
                "amount": float(amount),
                "return_amount": float(return_amount)
            }
        elif sub_type == "Casino 类":
            details = {}
            amount = Decimal("0.0")
            return_amount = Decimal("0.0")
            new_balance = current_balance
    else:
        sub_type = None
        details = {}
        amount = st.number_input("投资金额", min_value=0.0, step=0.01)
        return_amount = st.number_input("回报金额", min_value=0.0, step=0.01)
        amount = Decimal(str(amount))
        return_amount = Decimal(str(return_amount))
        
        # 计算新的余额
        new_balance = current_balance - amount + return_amount
    
    investment_date = st.date_input("投资日期")
    
    if st.button("提交"):
        # 确保 details 是有效的 JSON 字符串
        details_json = json.dumps(details, default=custom_serializer)
        
        # 插入投资记录
        query = """
            INSERT INTO investments (user_id, investment_type, sub_type, amount, return_amount, investment_date, details)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        execute_query(query, (
            user_id, investment_type, sub_type, str(amount), str(return_amount), investment_date, details_json
        ))
        
        # 更新用户余额
        update_balance_query = """
            UPDATE users SET balance = %s WHERE id = %s
        """
        execute_query(update_balance_query, (str(new_balance), user_id))
        
        st.success("投资记录已成功添加！")
        st.success(f"用户余额已更新为: ${new_balance:.2f}")
        st.rerun()