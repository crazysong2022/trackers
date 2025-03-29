import streamlit as st
import datetime
import pandas as pd
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
if "selected_investment_type" not in st.session_state:
    st.session_state["selected_investment_type"] = "全部"

def format_details(details):
    """将 details 字段转换为更易读的文本格式"""
    try:
        if isinstance(details, str):
            details = json.loads(details)  # 如果是字符串，解析为字典
        
        # 构造易读的文本
        readable_text = []
        if "team_a" in details and "team_b" in details:
            readable_text.append(f"{details['team_a']} vs {details['team_b']}")
        if "game" in details and details["game"]:
            readable_text.append(f"赛制: {details['game']}")
        if "amount" in details:
            readable_text.append(f"押注金额: ${details['amount']:.2f}")
        if "return_amount" in details:
            readable_text.append(f"回报金额: ${details['return_amount']:.2f}")
        if "bet_options" in details:
            bet_options = ", ".join(
                f"{opt['type']} (赔率: {opt['odds']}, {'已选' if opt['selected'] else '未选'})"
                for opt in details["bet_options"]
            )
            readable_text.append(f"赔率选项: {bet_options}")
        
        return " | ".join(readable_text)
    except Exception as e:
        return "无法解析详情字段"

def main():
    st.title("Habitats Investment Tracking")

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
            
            # 投资类型筛选按钮
            investment_types = ["全部", "股票", "黄金", "期货", "博彩"]
            cols = st.columns(len(investment_types))
            for i, inv_type in enumerate(investment_types):
                if cols[i].button(inv_type, key=f"btn_{inv_type}"):
                    st.session_state["selected_investment_type"] = inv_type
            
            # 显示当前选中的投资类型
            st.write(f"当前筛选条件: **{st.session_state['selected_investment_type']}**")
            
            # 计算默认日期范围（过去一个月）
            today = datetime.date.today()
            one_month_ago = today - datetime.timedelta(days=30)  # 当前日期往前推 30 天
            
            # 日期范围选择
            date_range = st.date_input(
                "日期范围",
                value=(one_month_ago, today),  # 默认值为过去一个月到今天
                min_value=None,
                max_value=None,
                key="date_range"
            )
            
            # 确保 date_range 是一个长度为 2 的元组
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date, end_date = date_range
            else:
                # 如果用户未选择完整日期范围，则使用默认值
                start_date, end_date = one_month_ago, today
            
            # 查询投资记录
            filtered_investments = filter_investments(
                user["id"],
                investment_type=None if st.session_state["selected_investment_type"] == "全部" else st.session_state["selected_investment_type"],
                start_date=start_date,
                end_date=end_date
            )

            if filtered_investments:
                # 将投资记录转换为 Pandas DataFrame
                filtered_investments_mapped = [
                    {
                        "类型": inv["investment_type"],
                        "子类型": inv["sub_type"],
                        "金额": inv["amount"],
                        "回报": inv["return_amount"],
                        "日期": inv["investment_date"],
                        "详情": format_details(inv["details"])  # 转换为易读文本
                    }
                    for inv in filtered_investments
                ]
                
                df = pd.DataFrame(filtered_investments_mapped)
                
                # 美化表格
                st.dataframe(df.style.format({
                    "金额": "${:.2f}",
                    "回报": "${:.2f}"
                }), use_container_width=True)
            else:
                st.info("未找到符合条件的投资记录。")

        elif user["role"] == "admin":
            st.success(f"欢迎回来, 管理员!")
            admin_dashboard()

if __name__ == "__main__":
    main()