import streamlit as st
import pandas as pd
import io

st.set_page_config(layout="wide")

st.title("🔥 CRM 用户运营系统 VIP")

# ========================
# 上传
# ========================
file = st.file_uploader("📂 上传数据", type=["csv", "xlsx"])

if file:
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
else:
    st.warning("请上传数据")
    st.stop()

# ========================
# ⚙️ RULE CONFIG (VIP🔥)
# ========================
st.sidebar.header("⚙️ 规则配置")

drop_threshold = st.sidebar.slider("充值下降阈值", 0.0, 1.0, 0.5)
risk_threshold = st.sidebar.slider("高风险评分", 0.0, 10.0, 6.0)

# ========================
# 标签
# ========================
def 标签(row):
    tags = []

    if row["7天充值"] == 0:
        tags.append("A1")

    if row["历史充值"] > 0 and row["最近7天充值"] == 0:
        tags.append("A2")

    if row["充值下降比例"] > drop_threshold:
        tags.append("A3")

    if row["是否高价值用户"] and row["充值下降比例"] > 0.3:
        tags.append("A4")

    return ",".join(tags)


def 优先级(tag):
    if "A4" in tag:
        return "P1"
    if "A2" in tag:
        return "P1"
    if "A3" in tag:
        return "P2"
    return "P3"


def 评分(row):
    score = 0
    score += min(row["未充值天数"] * 0.1, 3)
    score += row["充值下降比例"] * 5

    if row["7天登录天数"] < 2:
        score += 2

    if row["是否高价值用户"]:
        score *= 1.5

    return round(score, 2)


# ========================
# 计算
# ========================
df["标签"] = df.apply(标签, axis=1)
df["优先级"] = df["标签"].apply(优先级)
df["流失评分"] = df.apply(评分, axis=1)

# ========================
# FILTER
# ========================
st.sidebar.header("🎯 筛选")

priority = st.sidebar.multiselect("优先级", ["P1", "P2", "P3"], default=["P1", "P2", "P3"])
score_filter = st.sidebar.slider("最低评分", 0.0, 10.0, 0.0)

df_f = df[(df["优先级"].isin(priority)) & (df["流失评分"] >= score_filter)]

# ========================
# KPI
# ========================
col1, col2, col3 = st.columns(3)

col1.metric("总用户", len(df))
col2.metric("当前筛选", len(df_f))
col3.metric("高风险", len(df[df["流失评分"] > risk_threshold]))

# ========================
# 高亮危险用户🔥
# ========================
def highlight(row):
    if row["流失评分"] > risk_threshold:
        return ['background-color: #ff4d4f'] * len(row)
    return [''] * len(row)

st.subheader("📋 用户列表")

st.dataframe(df_f.style.apply(highlight, axis=1), use_container_width=True)

# ========================
# 选择用户（VIP功能🔥）
# ========================
st.subheader("🎯 批量操作")

selected_ids = st.multiselect("选择用户UID", df_f["uid"])

if st.button("🔥 发送奖励"):
    if selected_ids:
        st.success(f"已对用户 {selected_ids} 发送奖励（模拟）")
    else:
        st.warning("请选择用户")

# ========================
# 下载
# ========================
st.subheader("📥 导出")

csv = df_f.to_csv(index=False).encode("utf-8")

st.download_button(
    "下载筛选结果",
    csv,
    "filtered_users.csv",
    "text/csv"
)

# ========================
# 图表
# ========================
st.subheader("📊 风险分布")
st.bar_chart(df_f["流失评分"])
