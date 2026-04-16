import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")
st.title("🔥 后台管理系统 PRO")

DATA_FILE = "history.csv"

# ======================
# Load history
# ======================
if os.path.exists(DATA_FILE):
    history_df = pd.read_csv(DATA_FILE)
    history_df["login_time"] = pd.to_datetime(history_df["login_time"], errors="coerce")
else:
    history_df = pd.DataFrame()

# ======================
# Fix date
# ======================
def fix_date(col):
    return pd.to_datetime(
        col.astype(str)
        .str.replace("年","-")
        .str.replace("月","-")
        .str.replace("日",""),
        errors="coerce"
    )

# ======================
# Upload
# ======================
st.header("📂 上传数据")

deposit_file = st.file_uploader("充值", type=["xlsx"])
withdraw_file = st.file_uploader("提现", type=["xlsx"])
login_file = st.file_uploader("登录", type=["xlsx"])

# ======================
# Start
# ======================
if deposit_file and withdraw_file and login_file:

    if st.button("🚀 开始分析"):

        df_deposit = pd.read_excel(deposit_file)
        df_withdraw = pd.read_excel(withdraw_file)
        df_login = pd.read_excel(login_file)

        df_deposit.columns = ["user_id","deposit","time"]
        df_withdraw.columns = ["user_id","withdraw","time"]
        df_login.columns = ["user_id","login_time"]

        df_deposit["time"] = fix_date(df_deposit["time"])
        df_withdraw["time"] = fix_date(df_withdraw["time"])
        df_login["login_time"] = fix_date(df_login["login_time"])

        # 去重
        df_deposit = df_deposit.drop_duplicates()
        df_withdraw = df_withdraw.drop_duplicates()
        df_login = df_login.drop_duplicates()

        # ===== 7天数据 =====
        now = pd.Timestamp.now()

        login_7 = df_login[df_login["login_time"] >= now - pd.Timedelta(days=7)]
        login_7 = login_7.groupby("user_id").size().reset_index(name="login_7_days")

        dep_7 = df_deposit[df_deposit["time"] >= now - pd.Timedelta(days=7)]
        dep_7 = dep_7.groupby("user_id")["deposit"].sum().reset_index(name="deposit_7_days")

        # ===== 汇总 =====
        dep = df_deposit.groupby("user_id")["deposit"].sum().reset_index()
        wd = df_withdraw.groupby("user_id")["withdraw"].sum().reset_index()
        lg = df_login.groupby("user_id")["login_time"].max().reset_index()

        df = dep.merge(wd, on="user_id", how="outer")
        df = df.merge(lg, on="user_id", how="outer")

        df = df.merge(login_7, on="user_id", how="left")
        df = df.merge(dep_7, on="user_id", how="left")

        df["deposit"] = df["deposit"].fillna(0)
        df["withdraw"] = df["withdraw"].fillna(0)
        df["login_7_days"] = df["login_7_days"].fillna(0)
        df["deposit_7_days"] = df["deposit_7_days"].fillna(0)

        df["login_time"] = pd.to_datetime(df["login_time"], errors="coerce")

        # ===== 历史合并 =====
        if not history_df.empty:
            df = pd.concat([history_df, df])
            df = df.groupby("user_id").agg({
                "deposit":"sum",
                "withdraw":"sum",
                "login_time":"max",
                "login_7_days":"max",
                "deposit_7_days":"sum"
            }).reset_index()

        df.to_csv(DATA_FILE, index=False)

        # ===== 不登录天数 =====
        df["不登录天数"] = (now - df["login_time"]).dt.days
        df["不登录天数"] = df["不登录天数"].fillna(999)

        # ===== 风控 =====
        def risk(row):
            if row["login_7_days"] >= 5 and row["deposit_7_days"] < 100:
                return "羊毛党"
            if row["login_7_days"] >= 6 and row["deposit_7_days"] < 150:
                return "疑似套利"
            if row["withdraw"] > row["deposit"]:
                return "高风险"
            return "正常"

        df["风险标签"] = df.apply(risk, axis=1)

        # ===== VIP =====
        def vip(x):
            if x > 100000: return "VIP5"
            elif x > 50000: return "VIP4"
            elif x > 10000: return "VIP3"
            elif x > 3000: return "VIP2"
            elif x > 500: return "VIP1"
            return "普通"

        df["VIP等级"] = df["deposit"].apply(vip)

        # ===== 分类 =====
        def classify(row):
            if row["风险标签"] == "羊毛党":
                return "异常"
            if row["不登录天数"] >= 3 and row["deposit_7_days"] == 0:
                return "流失"
            if row["login_7_days"] >= 3:
                return "活跃"
            return "普通"

        df["等级"] = df.apply(classify, axis=1)

        # ===== 奖励比例 =====
        def ratio(row):
            if row["风险标签"] == "羊毛党":
                return [0,0,0]
            if row["VIP等级"] in ["VIP4","VIP5"]:
                return [0.06,0.08,0.10]
            if row["等级"] == "流失":
                return [0.08,0.10,0.12]
            return [0.05,0.07,0.09]

        tiers = [100,300,1000]

        def calc_bonus(row):
            r = ratio(row)
            return [tiers[0]*r[0], tiers[1]*r[1], tiers[2]*r[2]]

        df["奖励方案"] = df.apply(calc_bonus, axis=1)

        # ===== 打码 =====
        def turnover(row):
            if row["VIP等级"] in ["VIP4","VIP5"]:
                return 3
            if row["风险标签"] == "疑似套利":
                return 8
            return 5

        df["打码倍数"] = df.apply(turnover, axis=1)

        # ===== 建议 =====
        def action(row):
            if row["风险标签"] == "羊毛党":
                return "禁止奖励"
            if row["等级"] == "流失":
                return "发大额优惠拉回"
            if row["VIP等级"] in ["VIP4","VIP5"]:
                return "重点维护"
            return "正常维护"

        df["维护建议"] = df.apply(action, axis=1)

        # ===== Dashboard =====
        st.header("📊 数据总览")

        c1,c2,c3 = st.columns(3)
        c1.metric("总充值", int(df["deposit"].sum()))
        c2.metric("总提现", int(df["withdraw"].sum()))
        c3.metric("净利润", int(df["deposit"].sum() - df["withdraw"].sum()))

        # ===== 搜索 =====
        uid = st.text_input("🔍 搜索用户ID")
        if uid:
            st.dataframe(df[df["user_id"] == int(uid)])

        # ===== 风险 =====
        st.header("⚠️ 风险用户")
        st.dataframe(df[df["风险标签"] != "正常"])

        # ===== 全部 =====
        st.header("全部数据")
        st.dataframe(df)
