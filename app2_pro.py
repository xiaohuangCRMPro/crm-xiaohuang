import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="后台管理系统", layout="wide")
st.title("后台管理系统")

DATA_FILE = "history.csv"

# =========================
# 读取历史数据
# =========================
if os.path.exists(DATA_FILE):
    history_df = pd.read_csv(DATA_FILE)
else:
    history_df = pd.DataFrame()

# =========================
# 上传
# =========================
st.header("上传数据")

deposit_file = st.file_uploader("充值", type=["xlsx"])
withdraw_file = st.file_uploader("提现", type=["xlsx"])
login_file = st.file_uploader("登录", type=["xlsx"])

# =========================
# 时间处理
# =========================
def fix_date(col):
    return pd.to_datetime(
        col.astype(str)
        .str.replace("年", "-")
        .str.replace("月", "-")
        .str.replace("日", ""),
        errors="coerce"
    )

# =========================
# 按钮
# =========================
if deposit_file and withdraw_file and login_file:

    if st.button("开始分析"):

        df_deposit = pd.read_excel(deposit_file)
        df_withdraw = pd.read_excel(withdraw_file)
        df_login = pd.read_excel(login_file)

        df_deposit.columns = ["user_id", "deposit", "time"]
        df_withdraw.columns = ["user_id", "withdraw", "time"]
        df_login.columns = ["user_id", "login_time"]

        df_deposit["time"] = fix_date(df_deposit["time"])
        df_withdraw["time"] = fix_date(df_withdraw["time"])
        df_login["login_time"] = fix_date(df_login["login_time"])

        # =========================
        # 汇总
        # =========================
        deposit_sum = df_deposit.groupby("user_id")["deposit"].sum().reset_index()
        withdraw_sum = df_withdraw.groupby("user_id")["withdraw"].sum().reset_index()
        last_login = df_login.groupby("user_id")["login_time"].max().reset_index()

        df = deposit_sum.merge(withdraw_sum, on="user_id", how="outer")
        df = df.merge(last_login, on="user_id", how="outer")
        df = df.fillna(0)

        # =========================
        # 合并历史（关键）
        # =========================
        if not history_df.empty:
            df = pd.concat([history_df, df])

        # 再次汇总（累加）
        df = df.groupby("user_id").agg({
            "deposit": "sum",
            "withdraw": "sum",
            "login_time": "max"
        }).reset_index()

        # =========================
        # 保存历史
        # =========================
        df.to_csv(DATA_FILE, index=False)

        # =========================
        # 分析
        # =========================
        df["不登录天数"] = (pd.Timestamp.now() - df["login_time"]).dt.days.fillna(999)

        def classify(row):
            if row["deposit"] > 50000 and row["不登录天数"] <= 3:
                return "VIP用户"
            elif row["不登录天数"] <= 3:
                return "活跃用户"
            elif row["不登录天数"] <= 7:
                return "警告用户"
            elif row["withdraw"] > row["deposit"]:
                return "风险用户"
            else:
                return "流失用户"

        df["用户等级"] = df.apply(classify, axis=1)

        st.success("分析完成（已保存历史）")

        st.dataframe(df)

# =========================
# 显示历史
# =========================
st.header("历史数据")

if not history_df.empty:
    st.dataframe(history_df)
else:
    st.write("暂无历史数据")

# =========================
# 清空按钮
# =========================
if st.button("清空历史数据"):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    st.success("已清空")
