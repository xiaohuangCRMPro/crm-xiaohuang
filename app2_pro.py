from fastapi import FastAPI
import datetime
from db import 获取用户数据
from auto import 发送奖励

app = FastAPI()

# ========================
# 标签规则
# ========================
def 获取用户标签(user):
    标签 = []

    if user["登录天数"] > 0 and user["7天充值"] == 0:
        标签.append("A1_登录未充值")

    if user["历史充值"] > 0 and user["最近7天充值"] == 0:
        标签.append("A2_近期流失")

    if user["充值下降比例"] > 0.5:
        标签.append("A3_充值下降")

    if user["是否高价值用户"] and user["充值下降比例"] > 0.3:
        标签.append("A4_高价值降温")

    return 标签


# ========================
# 优先级
# ========================
def 计算优先级(标签):
    if "A4_高价值降温" in 标签:
        return "P1"
    if "A2_近期流失" in 标签:
        return "P1"
    if "A3_充值下降" in 标签:
        return "P2"
    return "P3"


# ========================
# 流失评分
# ========================
def 计算流失评分(user):
    分数 = 0

    分数 += min(user["未充值天数"] * 0.1, 3)
    分数 += user["充值下降比例"] * 5

    if user["7天登录天数"] < 2:
        分数 += 2

    if user["是否高价值用户"]:
        分数 *= 1.5

    return round(分数, 2)


# ========================
# 自动运营策略
# ========================
def 自动运营(user, 分数, 优先级):
    if 分数 > 6:
        return "发送高额优惠 + 人工跟进"

    if 优先级 == "P1":
        return "发送召回奖励"

    if 优先级 == "P2":
        return "普通优惠提醒"

    return "无需处理"


# ========================
# 主处理
# ========================
def 分析用户(user):
    标签 = 获取用户标签(user)
    优先级 = 计算优先级(标签)
    分数 = 计算流失评分(user)
    操作 = 自动运营(user, 分数, 优先级)

    return {
        "uid": user["uid"],
        "标签": 标签,
        "优先级": 优先级,
        "流失评分": 分数,
        "建议操作": 操作,
        "时间": str(datetime.datetime.now())
    }


# ========================
# 执行自动运营（赚钱🔥）
# ========================
def 执行自动(result):
    for user in result:
        if user["流失评分"] > 6:
            发送奖励(user["uid"])


# ========================
# API
# ========================
@app.get("/analysis")
def 获取分析结果():
    users = 获取用户数据()

    result = []
    for user in users:
        result.append(分析用户(user))

    # 自动执行运营
    执行自动(result)

    return result
