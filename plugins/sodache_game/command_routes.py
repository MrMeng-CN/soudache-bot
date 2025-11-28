#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏关键词路由管理模块 (NoneBot2版本)
负责定义游戏命令关键词与对应的处理函数映射
"""

from nonebot import on_command, on_message, get_driver
from nonebot.rule import to_me, Rule
from nonebot.adapters.onebot.v11 import Bot, Event
from .game_core import search, retreat, attack, user_init, check_status,check_retreat_status,users,stop_retreat, upgrade_attribute
from nonebot.adapters.onebot.v11 import MessageSegment
from .db import save_user
from nonebot.rule import Rule
from nonebot.typing import T_State
import time

quality_map = {0: "普通", 1: "稀有", 2: "史诗", 3: "传说"}

# 创建精确匹配的规则
def is_exact_command(cmd: str) -> Rule:
    async def _is_exact(event: Event) -> bool:
        plain_text = event.get_message().extract_plain_text().strip()
        config = get_driver().config
        command_start = config.command_start
        
        # 检查所有可能的精确命令形式
        match_candidates = [cmd] + [prefix + cmd for prefix in command_start]
        return plain_text in match_candidates
    return Rule(_is_exact)

# 使用on_command并添加精确匹配规则
search_cmd = on_command("搜", rule=is_exact_command("搜"), priority=10)

@search_cmd.handle()
async def _search_handler(bot: Bot, event: Event):
    """
    处理搜索命令
    """
    qq = event.get_user_id()
    # try:
    success = search(qq)
    msg = MessageSegment.at(qq)+"\n"
    if success:
        msg+=f"搜索开始!"
        await search_cmd.finish(msg)
    else:
        msg+=f"搜索失败！可能已经在搜索中或处于其他状态,发送“当前状态”进行查看"
        await search_cmd.finish(msg)


# 攻击命令
attack_cmd = on_command("打", priority=10)
@attack_cmd.handle()
async def _attack_handler(bot: Bot, event: Event):
    """
    处理攻击命令
    """
    target_qq = None
    message = event.get_message()
    # 检查是否有艾特用户
    for seg in message:
        if seg.type == "at":
            target_qq = seg.data.get("qq")
            break
    
    # 如果没有艾特用户，则检查文本中的QQ号
    if not target_qq:
        plain_text = event.get_message().extract_plain_text().strip()
        # 提取命令后的内容
        if plain_text.startswith("打"):
            qq_str = plain_text[1:].strip()
            # 检查是否为纯数字
            if qq_str.isdigit():
                target_qq = qq_str
    
    # 如果没有找到有效的QQ号，不发送任何内容
    if not target_qq:
        await attack_cmd.finish()
        
    attacker_qq = event.get_user_id()
    defender_qq = target_qq
    msg = MessageSegment.at(attacker_qq)+"\n"
    success = attack(attacker_qq, defender_qq)
    if success:
        msg += success
        await attack_cmd.finish(msg)

# 撤离命令
retreat_cmd = on_command("撤", rule=is_exact_command("撤"), priority=10)
@retreat_cmd.handle()
async def _retreat_handler(bot: Bot, event: Event):
    """
    处理撤离命令
    """
    qq = event.get_user_id()
    user = users.get(qq)
    success = retreat(qq)
    msg = MessageSegment.at(qq)+"\n"
    
    if success:
        msg += f"撤离开始！{600-user.speed*40}秒后完成撤离并结算物品\n"
        if user.inventory:
            msg += "本次搜索已获取物品："
            for item in user.inventory:
                quality_name = quality_map.get(item.quality, "未知")
                msg += f"\n{item.name} {quality_name} {item.value}哈哈币"
        else:
            msg += "暂无新获取物品"
        await retreat_cmd.finish(msg)
    else:
        await retreat_cmd.finish(f"撤离失败！可能未在搜索中")

# 状态查询命令
status_cmd = on_command("当前状态", rule=is_exact_command("当前状态"), priority=10)
@status_cmd.handle()
async def _status_handler(bot: Bot, event: Event):
    """
    处理状态查询命令
    """
    qq = event.get_user_id()
    total_value = check_retreat_status(qq)
    status_info = check_status(qq)
    user = users.get(qq)
    # 构建回复消息
    msg = MessageSegment.at(qq)+"\n"
    msg += f"当前状态：{status_info['status_text']}\n"
    msg+=f"哈哈币：{status_info['gold']}\n"
    msg+=f"攻击力：{user.attack},防御力：{user.defense}\n"
    if(status_info['status']==1):
        msg+=f"（距离获得下一件物品还剩{360-(int(time.time())-user.search_start_time)%360}秒）\n"
    elif(status_info['status']==2):
        if(600-user.speed*40-int(time.time())+user.retreat_start_time<0):
            msg+=f"本次撤离带出物品价值：{total_value}哈哈币\n"
            msg+=f"撤离成功！\n"
        else:
            msg+=f"（距离撤离完成还剩{600-user.speed*40-int(time.time())+user.retreat_start_time}秒）\n"
    if user.status!=0:
        msg += f"背包物品数量：{status_info['bag_items_nums']}/{user.backpack_capacity}\n"
        if user.inventory:
            msg += "本次搜索已获取物品："
            for item in user.inventory:
                quality_name = quality_map.get(item.quality, "未知")
                msg += f"\n{item.name} {quality_name} {item.value}哈哈币"
    
    await status_cmd.finish(msg)

stop_retreat_cmd = on_command("不撤", rule=is_exact_command("不撤"), priority=10)
@stop_retreat_cmd.handle()
async def _stop_retreat_handler(bot: Bot, event: Event):
    """
    处理取消撤离命令
    """
    qq = event.get_user_id()
    success = stop_retreat(qq)
    msg = MessageSegment.at(qq)+"\n"
    if success:
        msg += "撤离已取消！"
    else:
        msg += "取消撤离失败！可能未在撤离状态"
    await stop_retreat_cmd.finish(msg)

# 锻体升级命令
train_cmd = on_command("锻体", rule=is_exact_command("锻体"), priority=10)
@train_cmd.handle()
async def _train_handler(bot: Bot, event: Event):
    """
    处理锻体升级命令 - 第一阶段：选择要升级的属性
    """
    qq = event.get_user_id()
    user = users.get(qq)
    if not user:
        user = user_init(qq)
    
    # 构建属性选择菜单
    msg = MessageSegment.at(qq) + "\n"
    msg += "===== 锻体升级 =====\n"
    msg += f"当前哈哈币：{user.gold}\n\n"
    msg += "请选择要升级的属性：\n"
    msg += "1. 攻击力 - 每级500哈哈币\n"
    msg += "2. 防御力 - 每级500哈哈币\n"
    msg += "3. 撤离速度 - 每级2000哈哈币（最高7级）\n"
    
    # 计算背包容量升级价格
    current_level = user.backpack_capacity - 4
    backpack_cost = 4000 * (current_level + 1)
    msg += f"4. 背包容量 - 本次升级需要{backpack_cost}哈哈币\n"
    msg += "0. 退出\n"
    
    await train_cmd.send(msg)

@train_cmd.got("selection")
async def _receive_attribute_choice(bot: Bot, event: Event,state: T_State):
    """
    接收用户选择的属性
    """
    qq = event.get_user_id()
    choice_text = event.get_message().extract_plain_text().strip()
    # 处理退出选择
    if choice_text == "0":
        await train_cmd.finish(MessageSegment.at(qq) + "\n已退出锻体升级")
    # 验证升级选择
    if not choice_text.isdigit():
        await train_cmd.finish("输入错误")
    attribute_choice = int(choice_text)
    if attribute_choice not in [1, 2, 3, 4]:
        await train_cmd.finish(MessageSegment.at(qq) + "输入错误")
    
    # 保存选择的属性，进入下一阶段
    state["attribute_choice"] = int(choice_text)
    
    # 对于背包容量(4)，直接升级
    if attribute_choice == 4:
        success, msg = upgrade_attribute(qq, attribute_choice, 1)
        user = users.get(qq)
        response = MessageSegment.at(qq) + "\n"
        if success:
            response += f"背包容量升级成功！当前容量：{user.backpack_capacity}\n"
            response += f"剩余哈哈币：{user.gold}"
        else:
            response += msg
        await train_cmd.finish(response)
    
    # 对于其他属性，询问升级数量
    await train_cmd.send(MessageSegment.at(qq) + f"\n请输入要升级的等级数：")

@train_cmd.got("amount")
async def _receive_upgrade_amount(bot: Bot, event: Event,state: T_State):
    """
    接收升级数量并处理升级
    """
    qq = event.get_user_id()
    attribute_choice = state.get("attribute_choice")
    amount_text = event.get_message().extract_plain_text().strip()
    
    # 验证升级数量
    if not amount_text.isdigit():
        await train_cmd.finish("输入错误")
    amount = int(amount_text)
    if amount <= 0:
        await train_cmd.finish("输入错误")
    
    # 执行升级
    success, msg = upgrade_attribute(qq, attribute_choice, amount)
    user = users.get(qq)
    response = MessageSegment.at(qq) + "\n"
    
    attribute_names = {1: "攻击力", 2: "防御力", 3: "撤离速度"}
    attribute_values = {1: user.attack, 2: user.defense, 3: user.speed}
    
    if success:
        response += f"{attribute_names[attribute_choice]}升级成功！\n"
        response += f"当前{attribute_names[attribute_choice]}：{attribute_values[attribute_choice]}\n"
        response += f"剩余哈哈币：{user.gold}"
    else:
        response += msg
    
    await train_cmd.finish(response)


# 使用on_command并添加精确匹配规则
buchang_cmd = on_command("加哈哈币", priority=10)
@buchang_cmd.handle()
async def _buchang_handler(bot: Bot, event: Event):
    """
    处理加哈哈币命令
    格式：加哈哈币 cq:at815953227 5000
    """
    qq = event.get_user_id()
    message = event.get_message()

    # 解析目标用户
    target_qq = None
    for seg in message:
        if seg.type == "at":
            target_qq = seg.data.get("qq")
            break
    
    # 如果没有找到@用户，则无法执行
    if not target_qq:
        await buchang_cmd.finish(MessageSegment.at(qq) + "\n请正确艾特目标用户")
    
    # 解析金额参数
    amount = None
    plain_text = event.get_message().extract_plain_text().strip()
    
    # 尝试从文本中提取数字金额
    words = plain_text.split()
    for word in words:
        if word.isdigit():
            amount = int(word)
            break
    
    # 如果没有找到有效金额，则无法执行
    if amount is None or amount <= 0:
        await buchang_cmd.finish(MessageSegment.at(qq) + "\n请输入有效金额")
    
    # 检查是否是管理员操作
    if qq != "815953227":
        user = users.get(qq)
        user.gold -= 100
        save_user(user)
        await buchang_cmd.finish(MessageSegment.at(qq) + "\n僭越之罪，扣100哈哈币")

    # 获取并更新目标用户的哈哈币
    target_user = users.get(target_qq)
    if not target_user:
        target_user = user_init(target_qq)
    
    target_user.gold += amount
    save_user(target_user)
    
    # 发送成功消息
    msg = MessageSegment.at(target_qq) + "\n"
    msg += f"获得{amount}哈哈币！当前哈哈币：{target_user.gold}"
    await buchang_cmd.finish(msg)
