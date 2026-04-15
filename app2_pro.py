import streamlit as st
import pandas as pd
import os
import time

st.set_page_config(page_title="后台管理系统", layout="wide")
st.title("后台管理系统")

DATA_FILE = "history.csv"

# =========================
# 读取历史
# =========================
if os.path.exists(DATA_FILE):
    history_df = pd.read_csv(DATA_FILE)
    history_df["login_time"] = pd.to_datetime(history_df["login_time"], errors="coerce")
else:
    history_df = pd.DataFrame()

# =========================
# 工具函数
# =========================
def fix_date(col):
    return pd.to_datetime(
        col.astype(str)
        .str.replace("年", "-")
        .str.replace("月", "-")
        .str.replace("日", ""),
        errors="coerce"
    )

def safe_rename(df, cols):
    df = df.copy()
    if len(df.columns) >= len(cols):
        df.columns = cols
    return df

# =========================
# 上传
# =========================
st.header("上传数据")

deposit_file = st.file_uploader("上传充值数据", type=["xlsx"])
withdraw_file = st.file_uploader("上传提现数据", type=["xlsx"])
login_file = st.file_uploader("上传登录数据", type=["xlsx"])

# =========================
# 分析按钮
# =========================
if deposit_file and withdraw_file and login_file:

    if st.button("开始分析"):

        progress = st.progress(0)

        try:
            # =========================
            # 读取
            # =========================
            progress.progress(10)
            df_deposit = pd.read_excel(deposit_file)
            df_withdraw = pd.read_excel(withdraw_file)
            df_login = pd.read_excel(login_file)

            # =========================
            # 重命名（防报错）
            # =========================
            progress.progress(20)
            df_deposit = safe_rename(df_deposit, ["user_id", "deposit", "time"])
            df_withdraw = safe_rename(df_withdraw, ["user_id", "withdraw", "time"])
            df_login = safe_rename(df_login, ["user_id", "login_time"])

            # =========================
            # 修复时间
            # =========================
            progress.progress(40)
            if "time" in df_deposit:
                df_deposit["time"] = fix_date(df_deposit["time"])
            if "time" in df_withdraw:
                df_withdraw["time"] = fix_date(df_withdraw["time"])
            if "login_time" in df_login:
                df_login["login_time"] = fix_date(df_login["login_time"])

            # =========================
            # 汇总
            # =========================
            progress.progress(60)

            deposit_sum = df_deposit.groupby("user_id")["deposit"].sum().reset_index() \
                if "deposit" in df_deposit else pd.DataFrame()

            withdraw_sum = df_withdraw.groupby("user_id")["withdraw"].sum().reset_index() \
                if "withdraw" in df_withdraw else pd.DataFrame()

            last_login = df_login.groupby("user_id")["login_time"].max().reset_index() \
                if "login_time" in df_login else pd.DataFrame()

            # =========================
            # 合并
            # =========================
            progress.progress(75)

            df = pd.merge(deposit_sum, withdraw_sum, on="user_id", how="outer")
            df = pd.merge(df, last_login, on="user_id", how="outer")

            # =========================
            # 修复空值（关键）
            # =========================
            df["deposit"] = df.get("deposit", 0).fillna(0)
            df["withdraw"] = df.get("withdraw", 0).fillna(0)

            # login_time 不填0 ❗
            df["login_time"] = pd.to_datetime(df.get("login_time"), errors="coerce")

            # =========================
            # 合并历史
            # =========================
            if not history_df.empty:
                df = pd.concat([history_df, df])

                df = df.groupby("user_id").agg({
                    "deposit": "sum",
                    "withdraw": "sum",
                    "login_time": "max"
                }).reset_index()

            # 保存
            df.to_csv(DATA_FILE, index=False)

            # =========================
            # 不登录天数
            # =========================
            progress.progress(85)

            df["不登录天数"] = (pd.Timestamp.now() - df["login_time"]).dt.days
            df["不登录天数"] = df["不登录天数"].fillna(999)

            # =========================
            # 分类
            # =========================
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

            # =========================
            # 奖金
            # =========================
            progress.progress(95)

            def bonus(row):
                if row["不登录天数"] <= 3:
                    return row["deposit"] * 0.05
                elif row["不登录天数"] <= 7:
                    return row["deposit"] * 0.1
                else:
                    return row["deposit"] * 0.2

            df["建议奖金"] = df.apply(bonus, axis=1)

            progress.progress(100)
            st.success("分析完成")

            # =========================
            # 显示
            # =========================
            st.dataframe(df)

            # =========================
            # 筛选
            # =========================
            st.header("筛选用户")
            days = st.slider("不登录天数 >=", 0, 30, 3)
            st.dataframe(df[df["不登录天数"] >= days])

            # =========================
            # 下载
            # =========================
            st.download_button(
                "下载结果",
                df.to_csv(index=False).encode("utf-8"),
                "result.csv",
                "text/csv"
            )

        except Exception as e:
            st.error(f"系统错误: {e}")

# =========================
# 历史数据
# =========================
st.header("历史数据")

if not history_df.empty:
    st.dataframe(history_df)
else:
    st.write("暂无历史数据")

# =========================
# 清空
# =========================
if st.button("清空历史数据"):
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    st.success("已清空")
