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

        # 汇总
        dep = df_deposit.groupby("user_id")["deposit"].sum().reset_index()
        wd = df_withdraw.groupby("user_id")["withdraw"].sum().reset_index()
        lg = df_login.groupby("user_id")["login_time"].max().reset_index()

        df = dep.merge(wd, on="user_id", how="outer")
        df = df.merge(lg, on="user_id", how="outer")

        df["deposit"] = df["deposit"].fillna(0)
        df["withdraw"] = df["withdraw"].fillna(0)
        df["login_time"] = pd.to_datetime(df["login_time"], errors="coerce")

        # merge history
        if not history_df.empty:
            df = pd.concat([history_df, df])
            df = df.groupby("user_id").agg({
                "deposit":"sum",
                "withdraw":"sum",
                "login_time":"max"
            }).reset_index()

        df.to_csv(DATA_FILE, index=False)

        # days inactive
        df["不登录天数"] = (pd.Timestamp.now() - df["login_time"]).dt.days
        df["不登录天数"] = df["不登录天数"].fillna(999)

        # classify
        def classify(r):
            if r["deposit"]>50000 and r["不登录天数"]<=3:
                return "VIP"
            elif r["不登录天数"]<=3:
                return "活跃"
            elif r["不登录天数"]<=7:
                return "警告"
            elif r["withdraw"]>r["deposit"]:
                return "风险"
            else:
                return "流失"

        df["等级"] = df.apply(classify, axis=1)

        # suggestion
        def action(r):
            if r["等级"]=="VIP":
                return "送5%奖金 + 专属客服"
            elif r["等级"]=="流失":
                return "发消息 + 送彩金20%"
            elif r["等级"]=="风险":
                return "减少奖励 + 观察"
            else:
                return "正常维护"

        df["维护建议"] = df.apply(action, axis=1)

        # ======================
        # DASHBOARD
        # ======================
        st.header("📊 数据总览")

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("总充值", int(df["deposit"].sum()))
        c2.metric("总提现", int(df["withdraw"].sum()))
        c3.metric("净盈利", int(df["deposit"].sum()-df["withdraw"].sum()))
        c4.metric("用户数", len(df))

        # ======================
        # 搜索
        # ======================
        uid = st.text_input("🔍 搜索用户ID")
        if uid:
            st.dataframe(df[df["user_id"]==int(uid)])

        # ======================
        # Tabs
        # ======================
        st.header("用户分类")

        t1,t2,t3,t4 = st.tabs(["VIP","活跃","流失","风险"])

        t1.dataframe(df[df["等级"]=="VIP"])
        t2.dataframe(df[df["等级"]=="活跃"])
        t3.dataframe(df[df["等级"]=="流失"])
        t4.dataframe(df[df["等级"]=="风险"])

        # ======================
        # 警告
        # ======================
        danger = df[df["withdraw"]>df["deposit"]]
        if not danger.empty:
            st.error(f"⚠️ 风险用户: {len(danger)}")

        # ======================
        # chart
        # ======================
        st.header("📈 充值趋势")
        df_deposit["date"] = df_deposit["time"].dt.date
        chart = df_deposit.groupby("date")["deposit"].sum()
        st.line_chart(chart)

        # ======================
        # full table
        # ======================
        st.header("全部数据")
        st.dataframe(df)
