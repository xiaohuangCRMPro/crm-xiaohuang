import streamlit as st
import pandas as pd

st.title("后台管理系统")

# =========================
# 上传3个文件
# =========================
st.header("上传数据")

deposit_file = st.file_uploader("上传充值数据", type=["xlsx"])
withdraw_file = st.file_uploader("上传提现数据", type=["xlsx"])
login_file = st.file_uploader("上传登录数据", type=["xlsx"])

if deposit_file and withdraw_file and login_file:

    # =========================
    # 读取文件
    # =========================
    df_deposit = pd.read_excel(deposit_file)
    df_withdraw = pd.read_excel(withdraw_file)
    df_login = pd.read_excel(login_file)

    # =========================
    # 重命名列（根据你的截图）
    # =========================
    df_deposit.columns = ["user_id", "deposit", "time"]
    df_withdraw.columns = ["user_id", "withdraw", "time"]
    df_login.columns = ["user_id", "login_time"]

    # =========================
    # 转时间格式
    # =========================
    df_deposit["time"] = pd.to_datetime(df_deposit["time"])
    df_withdraw["time"] = pd.to_datetime(df_withdraw["time"])
    df_login["login_time"] = pd.to_datetime(df_login["login_time"])

    # =========================
    # 汇总数据
    # =========================
    deposit_sum = df_deposit.groupby("user_id")["deposit"].sum().reset_index()
    withdraw_sum = df_withdraw.groupby("user_id")["withdraw"].sum().reset_index()
    last_login = df_login.groupby("user_id")["login_time"].max().reset_index()

    # =========================
    # 合并
    # =========================
    df = deposit_sum.merge(withdraw_sum, on="user_id", how="outer")
    df = df.merge(last_login, on="user_id", how="outer")

    df = df.fillna(0)

    # =========================
    # 不登录天数
    # =========================
    df["不登录天数"] = (pd.Timestamp.now() - df["login_time"]).dt.days.fillna(999)

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
    def bonus(row):
        if row["不登录天数"] <= 3:
            return row["deposit"] * 0.05
        elif row["不登录天数"] <= 7:
            return row["deposit"] * 0.1
        else:
            return row["deposit"] * 0.2

    df["建议奖金"] = df.apply(bonus, axis=1)

    # =========================
    # 显示
    # =========================
    st.header("分析结果")
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
