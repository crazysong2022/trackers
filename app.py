import streamlit as st
import datetime
import json
from auth import login, get_user_by_username
from admin import admin_dashboard
from investments import filter_investments

# 初始化会话状态
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None
if "balance" not in st.session_state:
    st.session_state["balance"] = 0.0

def main():
    st.title("投资追踪系统")

    # 显示登出按钮（仅当用户已登录时）
    if st.session_state["logged_in"]:
        if st.button("登出"):
            st.session_state["logged_in"] = False
            st.session_state["username"] = None
            st.session_state["balance"] = 0.0
            st.query_params.clear()
            st.rerun()

    if not st.session_state["logged_in"]:
        # 登录页面
        st.subheader("登录")
        username = st.text_input("用户名")
        password = st.text_input("密码", type="password")
        if st.button("登录"):
            user = login(username, password)
            if user:
                balance = user.get("balance", 0.0)
                
                st.session_state["logged_in"] = True
                st.session_state["username"] = user["username"]
                st.session_state["balance"] = balance  # 加载最新的余额
                st.query_params.update(logged_in="True", username=user["username"])
                st.rerun()
            else:
                st.error("用户名或密码错误")
    else:
        # 获取用户信息
        user = get_user_by_username(st.session_state["username"])
        if not user:
            st.error("用户信息加载失败，请重新登录。")
            st.session_state["logged_in"] = False
            st.rerun()
            return
        
        if user["role"] == "user":
            # 普通用户界面
            st.success(f"欢迎回来, {st.session_state['username']}!")
            st.write(f"当前余额: ${user['balance']:.2f}")  # 显示最新的余额

            # 查询模块
            st.subheader("我的投资记录")
            col1, col2 = st.columns(2)
            with col1:
                investment_type = st.selectbox("投资类型", ["全部", "股票", "黄金", "期货", "博彩"], index=0)
            with col2:
                date_range = st.date_input("日期范围", value=(datetime.date.today(), datetime.date.today()))
            
            start_date, end_date = date_range
            
            filtered_investments = filter_investments(
                user["id"],
                investment_type=None if investment_type == "全部" else investment_type,
                start_date=start_date,
                end_date=end_date
            )

            if filtered_investments:
                st.subheader("查询结果")
                for inv in filtered_investments:
                    st.write(f"类型: {inv['investment_type']}, 子类型: {inv['sub_type']}, 金额: {inv['amount']}, 回报: {inv['return_amount']}, 日期: {inv['investment_date']}")
                    
                    if inv["sub_type"] == "体育类":
                        try:
                            # 检查 details 是否已经是字典
                            if isinstance(inv["details"], dict):
                                details = inv["details"]
                            else:
                                # 如果不是字典，则尝试解析为 JSON（备用逻辑）
                                details = json.loads(inv["details"])
                            
                            st.write(f"- 对阵双方: {details['team_a']} vs {details['team_b']}")
                            st.write(f"- 押注金额: {details['amount']}")
                            st.write(f"- 回报金额: {details['return_amount']}")  # 显示管理员录入的回报金额
                            
                            st.write("- 赔率选项:")
                            for bet in details["bet_options"]:
                                st.write(f"  - {bet['type']}, 赔率: {bet['odds']}, 是否选择: {'是' if bet['selected'] else '否'}")
                        except Exception as e:
                            st.warning(f"无法解析详情字段: {e}")
            else:
                st.info("未找到符合条件的投资记录。")

        elif user["role"] == "admin":
            st.success(f"欢迎回来, 管理员!")
            admin_dashboard()

if __name__ == "__main__":
    main()