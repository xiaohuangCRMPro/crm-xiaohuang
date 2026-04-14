import streamlit as st
import pandas as pd

st.set_page_config(page_title="CRM 分析系统", layout="wide")

# ========================
# 规则
# ========================
def 获取用户标签(user):
    标签 = []

    if user["7天充值"] == 0:
        标签.append("A1_登录未充值")

    if user["历史充值"] > 0 and user["最近7天充值"] == 0:
        标签.append("A2_近期流失")

    if user["充值下降比例"] > 0.5:
        标签.append("A3_充值下降")

    if user["是否高价值用户"] and user["充值下降比例"] > 0.3:
        标签.append("A4_高价值降温")

    return ",".join(标签)


def 计算优先级(标签):
    if "A4" in 标签:
        return "P1"
    if "A2" in 标签:
        return "P1"
    if "A3" in 标签:
        return "P2"
    return "P3"


def 计算流失评分(user):
    分数 = 0
    分数 += min(user["未充值天数"] * 0.1, 3)
    分数 += user["充值下降比例"] * 5

    if user["7天登录天数"] < 2:
        分数 += 2

    if user["是否高价值用户"]:
        分数 *= 1.5

    return round(分数, 2)


def 自动运营(分数, 优先级):
    if 分数 > 6:
        return "🔥 高额奖励"
    if 优先级 == "P1":
        return "召回奖励"
    if 优先级 == "P2":
        return "普通提醒"
    return "无"


# ========================
# 模拟数据
# ========================
data = [
    {"uid": 1001, "历史充值": 1000, "最近7天充值": 0, "充值下降比例": 0.7, "未充值天数": 5, "7天登录天数": 1, "是否高价值用户": True, "7天充值": 0},
    {"uid": 1002, "历史充值": 500, "最近7天充值": 100, "充值下降比例": 0.1, "未充值天数": 1, "7天登录天数": 5, "是否高价值用户": False, "7天充值": 100},
    {"uid": 1003, "历史充值": 2000, "最近7天充值": 0, "充值下降比例": 0.8, "未充值天数": 7, "7天登录天数": 0, "是否高价值用户": True, "7天充值": 0},
]

df = pd.DataFrame(data)

# ========================
# 计算
# ========================
df["标签"] = df.apply(获取用户标签, axis=1)
df["优先级"] = df["标签"].apply(计算优先级)
df["流失评分"] = df.apply(计算流失评分, axis=1)
df["建议操作"] = df.apply(lambda x: 自动运营(x["流失评分"], x["优先级"]), axis=1)

# ========================
# UI
# ========================
st.title("🔥 CRM 用户分析系统")

col1, col2, col3 = st.columns(3)

col1.metric("总用户数", len(df))
col2.metric("高风险用户", len(df[df["流失评分"] > 6]))
col3.metric("P1用户", len(df[df["优先级"] == "P1"]))

st.dataframe(df, use_container_width=True)

# ========================
# 图表
# ========================
st.subheader("📊 风险评分分布")
st.bar_chart(df["流失评分"])
