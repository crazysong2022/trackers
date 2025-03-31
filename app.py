import streamlit as st
import datetime
import pandas as pd
from decimal import Decimal
import json
from auth import login, get_user_by_username
from admin import admin_dashboard
from database import fetch_all
import ccxt
import yfinance as yf  # 用于获取股票实时价格

def get_current_price(symbol):
    """
    获取虚拟币的实时价格（以 USDT 为单位）
    :param symbol: 虚拟币符号（如 "BTC", "ETH" 等）
    :return: 当前价格（float）
    """
    exchange = ccxt.binance()
    try:
        symbol_with_quote = f"{symbol.upper()}/USDT"
        ticker = exchange.fetch_ticker(symbol_with_quote)
        return ticker["last"]
    except Exception as e:
        print(f"无法获取 {symbol} 的实时价格: {e}")
        return None

def get_stock_current_price(symbol):
    """
    获取股票的实时价格（以美元为单位）
    :param symbol: 股票代码（如 "AAPL", "TSLA" 等）
    :return: 当前价格（float）
    """
    try:
        stock = yf.Ticker(symbol)
        current_price = stock.history(period="1d")["Close"].iloc[-1]  # 获取最近一天的收盘价
        return float(current_price)
    except Exception as e:
        print(f"无法获取 {symbol} 的实时价格: {e}")
        return None

def calculate_project_balances(user_id):
    """
    动态计算用户的各项目余额，包括：
    1. 博彩余额（净收益）
    2. 虚拟币余额（当前总价值）
    3. 股票余额（当前总价值）
    """
    project_balances = {
        "博彩余额": Decimal("0.0"),
        "虚拟币余额": Decimal("0.0"),
        "股票余额": Decimal("0.0")
    }
    
    # 计算博彩余额（净收益）
    query_betting = """
        SELECT SUM(return_amount) - SUM(amount) AS net_profit
        FROM investments
        WHERE user_id = %s
    """
    betting_balance = fetch_all(query_betting, (user_id,))
    if betting_balance and betting_balance[0]["net_profit"]:
        project_balances["博彩余额"] += Decimal(str(betting_balance[0]["net_profit"]))
    
    # 计算虚拟币余额（当前总价值）
    query_crypto = """
        SELECT sub_type, buy_price, quantity
        FROM crypto_investments
        WHERE user_id = %s
    """
    crypto_investments = fetch_all(query_crypto, (user_id,))
    for record in crypto_investments:
        current_price = get_current_price(record["sub_type"])
        if current_price is not None:
            project_balances["虚拟币余额"] += Decimal(str(current_price)) * Decimal(str(record["quantity"]))
    
    # 计算股票余额（当前总价值）
    query_stock = """
        SELECT sub_type, buy_price, quantity
        FROM stock_investments
        WHERE user_id = %s
    """
    stock_investments = fetch_all(query_stock, (user_id,))
    for record in stock_investments:
        current_price = get_stock_current_price(record["sub_type"])
        if current_price is not None:
            project_balances["股票余额"] += Decimal(str(current_price)) * Decimal(str(record["quantity"]))
    
    return project_balances

def format_details(details):
    """将 details 字段转换为更易读的文本格式"""
    try:
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except json.JSONDecodeError:
                return details
        
        readable_text = []
        if "team_a" in details and "team_b" in details:
            team_a_str = (
                f"{details['team_a']['english_name']} ({details['team_a']['chinese_name']})"
                if isinstance(details["team_a"], dict) else details["team_a"]
            )
            team_b_str = (
                f"{details['team_b']['english_name']} ({details['team_b']['chinese_name']})"
                if isinstance(details["team_b"], dict) else details["team_b"]
            )
            readable_text.append(f"{team_a_str} vs {team_b_str}")
        
        if "game" in details:
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
        
        return " | ".join(readable_text) if readable_text else "无详情信息"
    except Exception as e:
        print(f"解析 details 字段失败: {e}")
        return "无法解析详情字段"

def main():
    st.title("Habitats Investment Tracking")

    # 初始化会话状态
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = None
    if "project_balances" not in st.session_state:
        st.session_state["project_balances"] = {}
    if "selected_investment_type" not in st.session_state:
        st.session_state["selected_investment_type"] = None

    if not st.session_state["logged_in"]:
        # 登录页面
        st.subheader("登录")
        username = st.text_input("用户名")
        password = st.text_input("密码", type="password")
        if st.button("登录"):
            user = login(username, password)
            if user:
                # 动态计算各项目余额
                project_balances = calculate_project_balances(user["id"])
                
                st.session_state["logged_in"] = True
                st.session_state["username"] = user["username"]
                st.session_state["project_balances"] = project_balances
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
            
            # 显示各项目余额
            project_balances = st.session_state["project_balances"]
            st.write("当前余额:")
            st.write(f"- 博彩余额: ${project_balances['博彩余额']:.2f}")
            st.write(f"- 虚拟币余额: ${project_balances['虚拟币余额']:.2f}")
            st.write(f"- 股票余额: ${project_balances['股票余额']:.2f}")

            # 查询模块
            st.subheader("我的投资记录")
            
            # 投资类型筛选按钮
            investment_types = ["全部", "股票", "黄金", "期货", "博彩", "虚拟币"]
            cols = st.columns(len(investment_types))
            for i, inv_type in enumerate(investment_types):
                if cols[i].button(inv_type, key=f"btn_{i}"):
                    st.session_state["selected_investment_type"] = inv_type
            
            # 显示当前选中的投资类型
            if st.session_state["selected_investment_type"]:
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
                start_date, end_date = one_month_ago, today
            
            # 根据筛选条件查询投资记录
            if st.session_state["selected_investment_type"]:
                filtered_investments = []
                
                if st.session_state["selected_investment_type"] in ["全部", "博彩"]:
                    query = """
                        SELECT id, user_id, investment_type, sub_type, amount, return_amount, investment_date, details
                        FROM investments
                        WHERE user_id = %s AND investment_date BETWEEN %s AND %s
                    """
                    if st.session_state["selected_investment_type"] != "全部":
                        query += " AND investment_type = %s"
                        filtered_investments += fetch_all(query, (
                            user["id"], start_date, end_date, st.session_state["selected_investment_type"]
                        ))
                    else:
                        filtered_investments += fetch_all(query, (user["id"], start_date, end_date))
                
                if st.session_state["selected_investment_type"] in ["全部", "虚拟币"]:
                    query = """
                        SELECT id, user_id, sub_type, buy_price, quantity, investment_date
                        FROM crypto_investments
                        WHERE user_id = %s AND investment_date BETWEEN %s AND %s
                    """
                    filtered_investments += fetch_all(query, (user["id"], start_date, end_date))
                    
                    # 添加虚拟币的当前价格和总价值
                    for record in filtered_investments:
                        if "buy_price" in record and "quantity" in record:
                            current_price = get_current_price(record["sub_type"])
                            if current_price is not None:
                                record["current_price"] = current_price
                                record["current_value"] = Decimal(str(current_price)) * Decimal(str(record["quantity"]))
                            else:
                                record["current_price"] = None
                                record["current_value"] = None
                            
                            # 确保金额字段不为 None
                            record["buy_price"] = Decimal(str(record["buy_price"])) if record["buy_price"] else Decimal("0.0")
                            record["quantity"] = Decimal(str(record["quantity"])) if record["quantity"] else Decimal("0.0")
                
                if st.session_state["selected_investment_type"] in ["全部", "股票"]:
                    query = """
                        SELECT id, user_id, sub_type, buy_price, quantity, investment_date
                        FROM stock_investments
                        WHERE user_id = %s AND investment_date BETWEEN %s AND %s
                    """
                    filtered_investments += fetch_all(query, (user["id"], start_date, end_date))
                    
                    # 添加股票的当前价格和总价值
                    for record in filtered_investments:
                        if "buy_price" in record and "quantity" in record:
                            current_price = get_stock_current_price(record["sub_type"])
                            if current_price is not None:
                                record["current_price"] = current_price
                                record["current_value"] = Decimal(str(current_price)) * Decimal(str(record["quantity"]))
                            else:
                                record["current_price"] = None
                                record["current_value"] = None
                            
                            # 确保金额字段不为 None
                            record["buy_price"] = Decimal(str(record["buy_price"])) if record["buy_price"] else Decimal("0.0")
                            record["quantity"] = Decimal(str(record["quantity"])) if record["quantity"] else Decimal("0.0")
                
                # 显示投资记录
                if filtered_investments:
                    # 将投资记录转换为 Pandas DataFrame
                    filtered_investments_mapped = []
                    for inv in filtered_investments:
                        if "details" in inv:  # 博彩记录
                            readable_details = format_details(inv["details"])
                            filtered_investments_mapped.append({
                                "类型": inv["investment_type"],
                                "子类型": inv["sub_type"],
                                "金额": inv["amount"],
                                "回报": inv["return_amount"],
                                "日期": inv["investment_date"],
                                "详情": readable_details
                            })
                        elif "buy_price" in inv and "quantity" in inv:  # 虚拟币或股票记录
                            inv_type = "虚拟币" if st.session_state["selected_investment_type"] in ["全部", "虚拟币"] else "股票"
                            
                            readable_details = [
                                f"类型: {inv['sub_type']}",
                                f"买入价格: ${inv['buy_price']:.2f}" if inv['buy_price'] is not None else "买入价格: N/A",
                                f"购买数量: {inv['quantity']:.4f}" if inv['quantity'] is not None else "购买数量: N/A",
                                f"当前价格: ${inv['current_price']:.2f}" if inv['current_price'] is not None else "无法获取当前价格",
                                f"当前总价值: ${inv['current_value']:.2f}" if inv['current_value'] is not None else "无法计算当前价值"
                            ]
                            filtered_investments_mapped.append({
                                "类型": inv_type,
                                "子类型": inv["sub_type"],
                                "金额": Decimal(str(inv["buy_price"])) * Decimal(str(inv["quantity"])) if inv["buy_price"] and inv["quantity"] else Decimal("0.0"),
                                "回报": inv["current_value"] if inv["current_value"] else None,
                                "日期": inv["investment_date"],
                                "详情": " | ".join(readable_details)
                            })
                    
                    df = pd.DataFrame(filtered_investments_mapped)
                    
                    # 美化表格
                    st.dataframe(df.style.format({
                        "金额": lambda x: "${:.2f}".format(x) if x is not None else "N/A",
                        "回报": lambda x: "${:.2f}".format(x) if x is not None else "N/A"
                    }), use_container_width=True)
                else:
                    st.info("未找到符合条件的投资记录。")
        elif user["role"] == "admin":
            st.success(f"欢迎回来, 管理员!")
            admin_dashboard()

if __name__ == "__main__":
    main()