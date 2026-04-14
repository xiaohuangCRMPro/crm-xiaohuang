import streamlit as st
import pandas as pd

st.title("🔥 CRM 系统（真实数据版）")

# ========================
# 上传 3 文件
# ========================
col1, col2, col3 = st.columns(3)

with col1:
    deposit_file = st.file_uploader("上传充值数据", type=["xlsx"])

with col2:
    withdraw_file = st.file_uploader("上传提现数据", type=["xlsx"])

with col3:
    login_file = st.file_uploader("上传登录数据", type=["xlsx"])

if not (deposit_file and withdraw_file and login_file):
    st.warning("请上传全部3个文件")
    st.stop()

# ========================
# 读取
# ========================
deposit = pd.read_excel(deposit_file)
withdraw = pd.read_excel(withdraw_file)
login = pd.read_excel(login_file)

# ========================
# 重命名字段
# ========================
deposit.columns = ["uid", "充值金额", "时间"]
withdraw.columns = ["uid", "提现金额", "时间"]
login.columns = ["uid", "日期"]

# 转时间
deposit["时间"] = pd.to_datetime(deposit["时间"])
withdraw["时间"] = pd.to_datetime(withdraw["时间"])
login["日期"] = pd.to_datetime(login["日期"])

# ========================
# 计算7天充值
# ========================
today = deposit["时间"].max()
last7 = today - pd.Timedelta(days=7)

deposit_7d = deposit[deposit["时间"] >= last7]
dep_sum = deposit_7d.groupby("uid")["充值金额"].sum().reset_index()
dep_sum.columns = ["uid", "7天充值"]

# ========================
# 计算历史充值
# ========================
hist_dep = deposit.groupby("uid")["充值金额"].sum().reset_index()
hist_dep.columns = ["uid", "历史充值"]

# ========================
# 登录天数
# ========================
login_7d = login[login["日期"] >= last7]
login_days = login_7d.groupby("uid")["日期"].nunique().reset_index()
login_days.columns = ["uid", "7天登录天数"]

# ========================
# 合并
# ========================
df = hist_dep.merge(dep_sum, on="uid", how="left")
df = df.merge(login_days, on="uid", how="left")

df.fillna(0, inplace=True)

# ========================
# 计算未充值天数
# ========================
last_dep_time = deposit.groupby("uid")["时间"].max().reset_index()
last_dep_time["未充值天数"] = (today - last_dep_time["时间"]).dt.days

df = df.merge(last_dep_time[["uid", "未充值天数"]], on="uid", how="left")

# ========================
# 简单评分
# ========================
df["流失评分"] = (
    df["未充值天数"] * 0.2 +
    (df["7天充值"] == 0) * 3 +
    (df["7天登录天数"] < 2) * 2
)

# ========================
# 优先级
# ========================
df["优先级"] = df["流失评分"].apply(lambda x: "P1" if x > 5 else "P2" if x > 3 else "P3")

# ========================
# 显示
# ========================
st.dataframe(df, use_container_width=True)

st.bar_chart(df["流失评分"])
