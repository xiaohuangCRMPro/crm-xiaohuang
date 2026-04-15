import streamlit as st
import pandas as pd

st.set_page_config(page_title="后台管理系统", layout="wide")

st.title("后台管理系统")

# ========================
# 上传文件
# ========================
st.header("上传数据")

uploaded_file = st.file_uploader("上传 Excel 文件", type=["xlsx", "csv"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write("数据预览:")
    st.dataframe(df)

    # ========================
    # 处理数据
    # ========================
    df["净值"] = df["deposit"] - df["withdraw"]

    # 计算不活跃天数（假设有 last_login）
    if "last_login" in df.columns:
        df["last_login"] = pd.to_datetime(df["last_login"])
        df["不登录天数"] = (pd.Timestamp.now() - df["last_login"]).dt.days
    else:
        df["不登录天数"] = 0

    # ========================
    # 分类
    # ========================
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

    # ========================
    # 奖金建议
    # ========================
    def bonus(row):
        if row["不登录天数"] <= 3:
            return row["deposit"] * 0.05
        elif row["不登录天数"] <= 7:
            return row["deposit"] * 0.1
        else:
            return row["deposit"] * 0.2

    df["建议奖金"] = df.apply(bonus, axis=1)

    # ========================
    # 显示结果
    # ========================
    st.header("处理结果")
    st.dataframe(df)

    # ========================
    # 筛选
    # ========================
    st.header("筛选用户")

    days = st.slider("不登录天数 >=", 0, 30, 3)

    filtered = df[df["不登录天数"] >= days]

    st.dataframe(filtered)

    # ========================
    # 下载
    # ========================
    st.download_button(
        "下载结果",
        df.to_csv(index=False).encode("utf-8"),
        "result.csv",
        "text/csv"
    )
