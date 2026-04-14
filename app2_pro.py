import streamlit as st
import pandas as pd

st.title("🔥 CRM 派发名单工具（快速版）")

# ========================
# 上传
# ========================
col1, col2, col3 = st.columns(3)

with col1:
    dep_file = st.file_uploader("充值", type=["xlsx"])

with col2:
    wd_file = st.file_uploader("提现", type=["xlsx"])

with col3:
    log_file = st.file_uploader("登录", type=["xlsx"])

# ========================
# RUN
# ========================
if st.button("🚀 生成名单"):

    if not (dep_file and wd_file and log_file):
        st.error("上传3个文件")
        st.stop()

    # 读取
    dep = pd.read_excel(dep_file)
    wd = pd.read_excel(wd_file)
    log = pd.read_excel(log_file)

    dep.columns = ["uid", "充值", "时间"]
    wd.columns = ["uid", "提现", "时间"]
    log.columns = ["uid", "日期"]

    dep["时间"] = pd.to_datetime(dep["时间"])
    wd["时间"] = pd.to_datetime(wd["时间"])
    log["日期"] = pd.to_datetime(log["日期"])

    # ========================
    # 计算
    # ========================
    today = dep["时间"].max()
    last7 = today - pd.Timedelta(days=7)

    # 历史充值
    hist = dep.groupby("uid")["充值"].sum().reset_index()

    # 提现
    wd_sum = wd.groupby("uid")["提现"].sum().reset_index()

    # 合并
    df = hist.merge(wd_sum, on="uid", how="left")
    df["提现"] = df["提现"].fillna(0)

    # 净充值
    df["净充值"] = df["充值"] - df["提现"]

    # 7天充值
    dep7 = dep[dep["时间"] >= last7]
    dep7 = dep7.groupby("uid")["充值"].sum().reset_index()
    df = df.merge(dep7, on="uid", how="left")
    df["充值_y"] = df["充值_y"].fillna(0)
    df.rename(columns={"充值_y": "7天充值"}, inplace=True)

    # 登录
    log7 = log[log["日期"] >= last7]
    log7 = log7.groupby("uid")["日期"].nunique().reset_index()
    log7.columns = ["uid", "7天登录"]
    df = df.merge(log7, on="uid", how="left")
    df["7天登录"] = df["7天登录"].fillna(0)

    # ========================
    # 分组（核心🔥）
    # ========================
    def group(row):
        if row["净充值"] < 0:
            return "套利用户"

        if row["7天充值"] == 0 and row["7天登录"] > 0:
            return "登录未充值"

        if row["充值"] > 1000 and row["7天充值"] == 0:
            return "高价值流失"

        return "正常"

    df["分组"] = df.apply(group, axis=1)

    # ========================
    # P1名单
    # ========================
    p1 = df[
        (df["分组"] != "正常")
    ]

    # ========================
    # 输出
    # ========================
    st.success(f"🔥 找到 {len(p1)} 个需要处理的用户")

    st.dataframe(p1, use_container_width=True)

    # 下载
    csv = p1.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ 下载名单",
        csv,
        "p1_users.csv",
        "text/csv"
    )
