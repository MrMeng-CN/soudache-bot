#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏关键词路由管理模块 (NoneBot2版本)
负责定义游戏命令关键词与对应的处理函数映射
"""

from nonebot import on_command, on_message, get_driver
from nonebot.rule import to_me, Rule
from nonebot.adapters.onebot.v11 import Bot, Event
from .game_core import search, retreat, attack, user_init, check_status,check_retreat_status,users,stop_retreat, purchase_cheese_ticket
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.params import ArgPlainText
from nonebot.rule import Rule
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
        msg += f"撤离开始！10分钟后完成撤离并结算物品\n"
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
    if(status_info['status']==1):
        msg+=f"攻击力：{user.attack},防御力：{user.defense}\n"
        msg+=f"（距离获得下一件物品还剩{300-(int(time.time())-user.search_start_time)%300}秒）\n"
    elif(status_info['status']==2):
        if(600-int(time.time())+user.retreat_start_time<0):
            msg+=f"本次撤离带出物品价值：{total_value}哈哈币\n"
            msg+=f"撤离成功！\n"
        else:
            msg+=f"攻击力：{user.attack},防御力：{user.defense}\n"
            msg+=f"（距离撤离完成还剩{600-int(time.time())+user.retreat_start_time}秒）\n"
    elif(status_info['status']==0):
        msg+=f"哈哈币：{status_info['gold']}"
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


# 起装命令：启动购买芝士券交互
equip_start_cmd = on_command("起装", rule=is_exact_command("起装"), priority=10)
@equip_start_cmd.handle()
async def _equip_start( event: Event):
    qq = event.get_user_id()
    user = users.get(qq)
    if not user:
        user = user_init(qq)
    if user.status!=0:
        await equip_start_cmd.finish(MessageSegment.at(qq)+"\n你不在空闲状态，不能起装！")
    current_equips = ", ".join(e.name for e in user.equipment) if user.equipment else "无"
    prompt = (
        MessageSegment.at(qq) + "\n"
        + "请选择要购买的套装：\n"
        + "0. 我后悔了，不起了\n"
        + "1. 新兵芝士券 (50G)\n"
        + "2. 标准芝士券 (200G)\n"
        + "3. 精锐芝士券 (1000G)\n"
        + "4. 特种芝士券 (5000G)\n"
        + "警告：购买任意芝士券都会使已经装备的物品立刻被回收为哈哈币！\n"
        + f"当前装备：{current_equips}"
    )
    # 标记用户处于等待选择状态（仅内存）
    await equip_start_cmd.send(prompt)


# 处理用户对起装的回复
@equip_start_cmd.got("selection")
async def _handle_pack_choice(event: Event,selection: str = ArgPlainText()):
    qq = event.get_user_id()
    # 仅接受 0-4 的回复
    if selection not in ("0", "1", "2", "3", "4"):
        await equip_start_cmd.finish(MessageSegment.at(qq)+"\n你只能在芝士券中选择！")

    choice = int(selection)
    success, msg = purchase_cheese_ticket(qq, choice)
    await equip_start_cmd.finish(MessageSegment.at(qq)+"\n"+msg)

