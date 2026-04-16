import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")
st.title("🔥 后台管理系统（运营版）")

DATA_FILE = "history.csv"

# ======================
# TIME (KHÔNG DÙNG TZ TRỰC TIẾP)
# ======================
now = pd.Timestamp.now()

# ======================
# LOAD HISTORY
# ======================
if os.path.exists(DATA_FILE):
    history_df = pd.read_csv(DATA_FILE)
    history_df["login_time"] = pd.to_datetime(history_df["login_time"], errors="coerce")
else:
    history_df = pd.DataFrame()

# ======================
# FIX DATE
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
# UPLOAD
# ======================
st.header("📂 上传今日数据")

deposit_file = st.file_uploader("充值", type=["xlsx"])
withdraw_file = st.file_uploader("提现", type=["xlsx"])
login_file = st.file_uploader("登录", type=["xlsx"])

if deposit_file and withdraw_file and login_file:

    if st.button("🚀 更新数据"):

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

        # 汇总今日
        dep = df_deposit.groupby("user_id")["deposit"].sum().reset_index()
        wd = df_withdraw.groupby("user_id")["withdraw"].sum().reset_index()
        lg = df_login.groupby("user_id")["login_time"].max().reset_index()

        df_today = dep.merge(wd, on="user_id", how="outer")
        df_today = df_today.merge(lg, on="user_id", how="outer")

        # 合并历史
        df_all = pd.concat([history_df, df_today])

        df_all = df_all.groupby("user_id").agg({
            "deposit":"sum",
            "withdraw":"sum",
            "login_time":"max"
        }).reset_index()

        df_all.to_csv(DATA_FILE, index=False)

        st.success("✅ 数据已更新")

# ======================
# LOAD FINAL DATA
# ======================
if os.path.exists(DATA_FILE):

    df = pd.read_csv(DATA_FILE)

    # 👉 FIX datetime chuẩn (KHÔNG timezone để tránh lỗi)
    df["login_time"] = pd.to_datetime(df["login_time"], errors="coerce")

    # ======================
    # 不登录天数 (KHÔNG LỖI)
    # ======================
    df["不登录天数"] = (now - df["login_time"]).dt.days
    df["不登录天数"] = df["不登录天数"].fillna(999)

    # ======================
    # VIP
    # ======================
    def vip(x):
        if x > 100000: return "VIP5"
        elif x > 50000: return "VIP4"
        elif x > 10000: return "VIP3"
        elif x > 3000: return "VIP2"
        elif x > 500: return "VIP1"
        return "普通"

    df["VIP等级"] = df["deposit"].apply(vip)

    # ======================
    # 风控
    # ======================
    def risk(row):
        if row["deposit"] < 100 and row["不登录天数"] < 1:
            return "羊毛党"
        if row["withdraw"] > row["deposit"]:
            return "高风险"
        return "正常"

    df["风险标签"] = df.apply(risk, axis=1)

    # ======================
    # 等级
    # ======================
    def classify(row):
        if row["不登录天数"] >= 3:
            return "流失"
        if row["不登录天数"] <= 1:
            return "活跃"
        return "普通"

    df["等级"] = df.apply(classify, axis=1)

    # ======================
    # 🎯 冻结彩金任务
    # ======================
    tiers = [100,300,1000]

    def task_plan(row):

        if row["风险标签"] == "羊毛党":
            return []

        if row["VIP等级"] in ["VIP4","VIP5"]:
            rewards = [10,30,120]
        elif row["风险标签"] == "高风险":
            rewards = [3,10,50]
        else:
            rewards = [5,20,90]

        plans = []
        for i in range(3):
            need = tiers[i]
            current = row["deposit"]

            if current >= need:
                status = "已完成"
                remain = 0
            else:
                remain = need - current
                status = f"还差{remain}"

            plans.append({
                "档位": need,
                "奖励": rewards[i],
                "状态": status,
                "还差": remain
            })

        return plans

    df["任务"] = df.apply(task_plan, axis=1)

    # ======================
    # 今日需跟进
    # ======================
    def need_follow(row):

        if row["风险标签"] == "羊毛党":
            return False

        if row["deposit"] < 300 and row["deposit"] > 100:
            return True

        if row["不登录天数"] >= 2:
            return True

        return False

    df["今日需跟进"] = df.apply(need_follow, axis=1)

    # ======================
    # DASHBOARD
    # ======================
    st.header("📊 今日概况")

    c1,c2,c3 = st.columns(3)
    c1.metric("总充值", int(df["deposit"].sum()))
    c2.metric("总提现", int(df["withdraw"].sum()))
    c3.metric("需跟进用户", int(df["今日需跟进"].sum()))

    # ======================
    # 跟进用户
    # ======================
    st.header("🔥 今日需跟进用户")

    follow_df = df[df["今日需跟进"] == True]
    st.dataframe(follow_df)

    st.download_button(
        "📥 下载今日跟进用户",
        follow_df.to_csv(index=False).encode("utf-8"),
        "today_follow.csv",
        "text/csv"
    )

    # ======================
    # 风险
    # ======================
    st.header("⚠️ 风险用户")
    st.dataframe(df[df["风险标签"] != "正常"])

    # ======================
    # 全部
    # ======================
    st.header("全部数据")
    st.dataframe(df)
