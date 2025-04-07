import subprocess
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

def backup_database():
    try:
        command = 'pg_dump -U postgres -d trackers -F c > trackers_backup.dump'
        subprocess.run(command, shell=True, check=True)
        st.success("数据库备份成功！备份文件为 trackers_backup.dump")
    except subprocess.CalledProcessError as e:
        st.error(f"数据库备份失败: {e}")

def admin_dashboard():
    """管理员面板"""
    st.success(f"欢迎回来, 管理员!")

    # 备份数据库按钮
    if st.button("备份数据库"):
        backup_database()

    # 录入新投资记录
    st.subheader("录入新投资记录")
    users = fetch_all("SELECT id, username FROM users WHERE role != 'admin'")
    user_options = {user["username"]: user["id"] for user in users}

    selected_user = st.selectbox("选择用户", list(user_options.keys()))
    user_id = user_options[selected_user]

    investment_type = st.selectbox("投资类型", ["股票", "黄金", "期货", "博彩", "虚拟币"])  # 新增 "虚拟币"

    if investment_type == "博彩":
        sub_type = st.selectbox("博彩子类型", ["体育类", "Casino 类"])

        if sub_type == "体育类":
            # 查询所有队伍信息
            teams = fetch_all("SELECT id, english_name, chinese_name FROM teams")

            # 动态文本框：对阵双方 - A队
            team_a_search = st.text_input("对阵双方 - A队（输入英文或中文名称）")
            filtered_teams_a = [
                team for team in teams
                if team_a_search.lower() in team["english_name"].lower() or team_a_search.lower() in team["chinese_name"].lower()
            ]
            team_a_options = {f"{team['english_name']} ({team['chinese_name']})": team for team in filtered_teams_a}

            if team_a_options:
                selected_team_a = st.selectbox("选择 A队", list(team_a_options.keys()), key="team_a_select")
                team_a = team_a_options[selected_team_a]
            else:
                st.warning("未找到匹配的 A队，请检查输入或添加新队伍。")
                return

            # 动态文本框：对阵双方 - B队
            team_b_search = st.text_input("对阵双方 - B队（输入英文或中文名称）")
            filtered_teams_b = [
                team for team in teams
                if team_b_search.lower() in team["english_name"].lower() or team_b_search.lower() in team["chinese_name"].lower()
            ]
            team_b_options = {f"{team['english_name']} ({team['chinese_name']})": team for team in filtered_teams_b}

            if team_b_options:
                selected_team_b = st.selectbox("选择 B队", list(team_b_options.keys()), key="team_b_select")
                team_b = team_b_options[selected_team_b]
            else:
                st.warning("未找到匹配的 B队，请检查输入或添加新队伍。")
                return

            # 输入赛制
            game = st.text_input("赛制（例如 NHL、NBA）")

            bet_options = []
            num_bets = st.number_input("赔率选项数量", min_value=1, step=1)
            for i in range(num_bets):
                st.markdown(f"**赔率选项 {i + 1}**")
                bet_type = st.text_input(f"选项 {i + 1} - 赔率类型", key=f"bet_type_{i}")
                odds = st.number_input(f"选项 {i + 1} - 赔率", min_value=0.0, step=0.01, key=f"odds_{i}")
                selected = st.checkbox(f"选项 {i + 1} - 是否选择", key=f"selected_{i}")
                bet_options.append({
                    "type": bet_type,
                    "odds": Decimal(str(odds)),
                    "selected": selected
                })

            selected_bet = [bet["type"] for bet in bet_options if bet["selected"]]
            selected_bet = selected_bet[0] if selected_bet else None

            amount = st.number_input("押注金额", min_value=0.0, step=0.01)
            amount = Decimal(str(amount))

            return_amount = st.number_input("回报金额", min_value=0.0, step=0.01)
            return_amount = Decimal(str(return_amount))

            # 投资日期选择
            investment_date = st.date_input("投资日期", value=None, key="investment_date")
            if not investment_date:
                st.warning("请选择投资日期！")
                return

            # 构造 details 字段
            details = {
                "game": game,  # 赛制字段
                "amount": float(amount),
                "team_a": {
                    "english_name": team_a["english_name"],
                    "chinese_name": team_a["chinese_name"]
                },
                "team_b": {
                    "english_name": team_b["english_name"],
                    "chinese_name": team_b["chinese_name"]
                },
                "bet_options": [
                    {
                        "type": bet["type"],
                        "odds": float(bet["odds"]),
                        "selected": bet["selected"]
                    }
                    for bet in bet_options
                ],
                "selected_bet": selected_bet,
                "return_amount": float(return_amount)
            }

            # 插入博彩记录
            if st.button("提交"):
                query = """
                    INSERT INTO investments (user_id, investment_type, sub_type, amount, return_amount, investment_date, details)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                execute_query(query, (
                    user_id, "博彩", sub_type, str(amount), str(return_amount),
                    investment_date, json.dumps(details, default=custom_serializer)
                ))

                st.success("博彩投资记录已成功添加到数据库！")
                st.rerun()

        elif sub_type == "Casino 类":
            st.warning("Casino 类投资暂不支持，请稍后再试！")

    elif investment_type == "虚拟币":
        sub_type = st.selectbox("选择虚拟币类型", ["BTC", "ETH", "SOL", "ADA", "BTT"])  # 支持多种虚拟币

        # 手动输入买入价格和购买数量
        buy_price = st.number_input("买入价格 (USDT)", min_value=0.0, step=0.01)
        quantity = st.number_input("购买数量", min_value=0.0, step=0.0001)

        # 计算总购买金额
        total_amount = Decimal(str(buy_price * quantity))
        st.write(f"总购买金额: ${total_amount:.2f}")

        # 投资日期选择
        investment_date = st.date_input("投资日期", value=None, key="crypto_investment_date")
        if not investment_date:
            st.warning("请选择投资日期！")
            return

        # 插入虚拟币投资记录
        if st.button("提交"):
            query = """
                INSERT INTO crypto_investments (user_id, sub_type, buy_price, quantity, investment_date)
                VALUES (%s, %s, %s, %s, %s)
            """
            execute_query(query, (
                user_id, sub_type, str(buy_price), str(quantity), investment_date
            ))

            st.success("虚拟币投资记录已成功添加到数据库！")
            st.rerun()

    elif investment_type == "股票":
        sub_type = st.text_input("输入股票代码（如 AAPL、TSLA）")  # 手动输入股票代码

        # 手动输入买入价格和购买数量
        buy_price = st.number_input("买入价格 (美元)", min_value=0.0, step=0.01)
        quantity = st.number_input("购买数量", min_value=0.0, step=0.0001)

        # 计算总购买金额
        total_amount = Decimal(str(buy_price * quantity))
        st.write(f"总购买金额: ${total_amount:.2f}")

        # 投资日期选择
        investment_date = st.date_input("投资日期", value=None, key="stock_investment_date")
        if not investment_date:
            st.warning("请选择投资日期！")
            return

        # 插入股票投资记录
        if st.button("提交"):
            query = """
                INSERT INTO stock_investments (user_id, sub_type, buy_price, quantity, investment_date)
                VALUES (%s, %s, %s, %s, %s)
            """
            execute_query(query, (
                user_id, sub_type, str(buy_price), str(quantity), investment_date
            ))

            st.success("股票投资记录已成功添加到数据库！")
            st.rerun()

    else:
        st.warning("暂不支持其他投资类型的录入，请稍后再试！")

    
    