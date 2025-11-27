#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏关键词路由管理模块 (NoneBot2版本)
负责定义游戏命令关键词与对应的处理函数映射
"""

from nonebot import on_command, on_message, get_driver
from nonebot.rule import to_me, Rule
from nonebot.adapters.onebot.v11 import Bot, Event
from .game_core import search, retreat, attack, user_init, check_status,check_retreat_status,users,stop_retreat, draw_equipment_for_purchase, format_equipment_attributes, get_actual_retreat_time, get_player_stats
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.params import ArgPlainText
from nonebot.rule import Rule
import time
from .models.game_models import EquipmentType
from .db import save_user, save_user_equipment, save_user_equipment_storage

quality_map = {0: "普通", 1: "稀有", 2: "史诗", 3: "传说"}
equipment_type_map = {0: "武器", 1: "防具", 2: "背包", 3: "饰品", 99: "其他"}

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
    stats = get_player_stats(user) if user else None
    # 构建回复消息
    msg = MessageSegment.at(qq)+"\n"
    msg += f"当前状态：{status_info['status_text']}\n"
    if(status_info['status']==1):
        msg+=f"攻击力：{int(user.attack)}+{int(stats.attack)-int(user.attack)}，防御力：{int(user.defense)}+{int(stats.defense)-int(user.defense)}\n"
        # 与抽取逻辑一致的实际间隔：基础300秒，受"搜索时长（search_time）"影响
        # 搜索时长为正数：增加间隔（减慢），为负数：减少间隔（加快）
        base_interval = 300
        actual_interval = base_interval + int(stats.search_time)
        # 限制范围保持一致：50~1800 秒
        actual_interval = max(50, min(1800, actual_interval))
        elapsed = int(time.time()) - user.search_start_time
        rem = elapsed % actual_interval
        remaining_time = actual_interval - rem if rem != 0 else actual_interval
        msg+=f"（距离获得下一件物品还剩{remaining_time}秒）\n"
    elif(status_info['status']==2):
        actual_retreat_time = get_actual_retreat_time(user)
        remaining_time = actual_retreat_time - (int(time.time()) - user.retreat_start_time)
        if remaining_time <= 0:
            msg+=f"本次撤离带出物品价值：{total_value}哈哈币\n"
            msg+=f"撤离成功！\n"
        else:
            msg+=f"攻击力：{int(user.attack)}+{int(stats.attack)-int(user.attack)}，防御力：{int(user.defense)}+{int(stats.defense)-int(user.defense)}\n"
            msg+=f"（距离撤离完成还剩{remaining_time}秒，总撤退时间：{actual_retreat_time}秒）\n"
    elif(status_info['status']==0):
        msg+=f"攻击力：{int(user.attack)}+{int(stats.attack)-int(user.attack)}，防御力：{int(user.defense)}+{int(stats.defense)-int(user.defense)}\n"
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


# 起装命令：启动抽奖交互
equip_start_cmd = on_command("起装", rule=is_exact_command("起装"), priority=10)
@equip_start_cmd.handle()
async def _equip_start(event: Event):
    qq = event.get_user_id()
    check_retreat_status(qq)
    user = users.get(qq)
    if not user:
        user = user_init(qq)
    if user.status != 0:
        await equip_start_cmd.finish(MessageSegment.at(qq) + "\n你不在空闲状态，不能起装！")
    if len(user.equipment_storage) >= 10:
        await equip_start_cmd.finish(MessageSegment.at(qq) + "\n装备仓库已满，无法起装，请先整理仓库！")
    prompt = (
        MessageSegment.at(qq) + "\n"
        + "请选择：\n"
        + "0. 我后悔了，不抽了\n"
        + "1. 在标准装备池中随机抽取一件装备（5000哈哈币）"
    )
    await equip_start_cmd.send(prompt)


# 处理用户选择确认
@equip_start_cmd.got("selection")
async def _handle_equipment_pool_choice(event: Event, selection: str = ArgPlainText()):
    qq = event.get_user_id()
    if selection not in ("0", "1"):
        await equip_start_cmd.reject(MessageSegment.at(qq)+"\n请输入0或1！")
    choice = int(selection)
    if choice == 0:
        await equip_start_cmd.finish(MessageSegment.at(qq)+"\n已取消抽奖。")
    # 抽取装备
    success, msg, new_eq = draw_equipment_for_purchase(qq)
    if not success or new_eq is None:
        await equip_start_cmd.finish(MessageSegment.at(qq)+"\n"+msg)
    
    # 直接将装备存入仓库
    user = users.get(qq)
    user.equipment_storage.append(new_eq)
    save_user(user)
    save_user_equipment_storage(qq, user.equipment_storage)
    
    # 将装备信息存入 state，NoneBot2 会自动管理
    from nonebot.matcher import current_matcher
    matcher = current_matcher.get()
    matcher.state["new_equipment"] = new_eq
    msg += f"\n\n请选择要进行的操作：\n1. 存入装备仓库\n2. 出售装备，获得{new_eq.value}哈哈币"
    await equip_start_cmd.send(MessageSegment.at(qq)+"\n"+msg)


# 处理用户确认装备
@equip_start_cmd.got("store_or_sell")
async def _handle_equipment_store_or_sell(event: Event, store_or_sell: str = ArgPlainText()):
    qq = event.get_user_id()
    user = users.get(qq)
    from nonebot.matcher import current_matcher
    matcher = current_matcher.get()
    new_eq = matcher.state.get("new_equipment")
    msg = MessageSegment.at(qq)+"\n"
    if not new_eq:
        await equip_start_cmd.finish(msg+"错误：未找到装备信息！")
    
    store_or_sell = store_or_sell.strip()
    
    if store_or_sell == "2":
        # 选择出售：从仓库移除装备并给予哈哈币
        if new_eq in user.equipment_storage:
            user.equipment_storage.remove(new_eq)
            save_user_equipment_storage(qq, user.equipment_storage)
        user.gold += new_eq.value
        save_user(user)
        await equip_start_cmd.finish(msg+f"已出售{new_eq.name}，获得{new_eq.value}哈哈币。\n当前哈哈币：{user.gold}")
    else:
        # 选择1或其他输入：装备已在仓库，只需提示
        await equip_start_cmd.finish(msg+f"已存入装备仓库（当前{len(user.equipment_storage)}/10）！")

# 配装命令
peizhuang_cmd = on_command("配装", rule=is_exact_command("配装"), priority=10)

@peizhuang_cmd.handle()
async def _peizhuang_handler(bot: Bot, event: Event):
    qq = event.get_user_id()
    check_retreat_status(qq)
    user = users.get(qq)
    msg = MessageSegment.at(qq) + "\n"
    if not user:
        user = user_init(qq)
    if user.status != 0:
        await peizhuang_cmd.finish(msg + "你只能在空闲状态下配装！")
    if not user.equipment_storage:
        msg += "装备仓库为空，可通过抽奖获得装备。"
        await peizhuang_cmd.finish(msg)
    msg += "装备仓库列表：\n"
    for idx, eq in enumerate(user.equipment_storage, 1):
        quality = quality_map.get(getattr(eq, 'quality', 0), "未知")
        eq_type = equipment_type_map.get(getattr(eq, 'equipment_type', 99), "未知")
        msg += f"[{idx}] {quality} {eq_type} {eq.name}\n"
    msg += "\n请输入序号选择装备，回复0退出。"
    await peizhuang_cmd.send(msg)

from .game_core import format_equipment_attributes

@peizhuang_cmd.got("select_idx")
async def _peizhuang_select(event: Event, select_idx: str = ArgPlainText()):
    qq = event.get_user_id()
    user = users.get(qq)
    msg = MessageSegment.at(qq) + "\n"
    if not user or not user.equipment_storage:
        await peizhuang_cmd.finish(msg + "装备仓库为空。")
    if not select_idx.isdigit():
        await peizhuang_cmd.reject(msg + "请输入正确的序号！")
    idx = int(select_idx)
    if idx == 0:
        await peizhuang_cmd.finish(msg + "已退出配装。")
    if idx < 1 or idx > len(user.equipment_storage):
        await peizhuang_cmd.finish(msg + "没有的东西，你还想卖？已退出装备仓库！")
    eq = user.equipment_storage[idx-1]
    # 展示非默认属性
    attr_str = format_equipment_attributes(eq)
    msg += f"已选择{eq.name}：\n{attr_str}\n"
    msg += f"价值：{eq.value}哈哈币\n"
    msg += f"请选择要进行的操作：\n1. 装备当前装备\n2. 出售装备，获得{eq.value}哈哈币"
    from nonebot.matcher import current_matcher
    matcher = current_matcher.get()
    matcher.state["selected_eq_idx"] = idx-1
    await peizhuang_cmd.send(msg)

@peizhuang_cmd.got("action")
async def _peizhuang_action(event: Event, action: str = ArgPlainText()):
    qq = event.get_user_id()
    user = users.get(qq)
    msg = MessageSegment.at(qq) + "\n"
    from nonebot.matcher import current_matcher
    matcher = current_matcher.get()
    idx = matcher.state.get("selected_eq_idx")
    eq = user.equipment_storage[idx]
    if action == "2":
        # 出售
        user.gold += eq.value
        user.equipment_storage.pop(idx)
        save_user(user)
        save_user_equipment_storage(qq, user.equipment_storage)
        await peizhuang_cmd.finish(msg + f"已出售{eq.name}，获得{eq.value}哈哈币。\n当前哈哈币：{user.gold}")
    elif action == "1":
        # 装备
        if len(user.equipment) < 4:
            # 检查是否已经装备了相同ID的装备
            if any(e.id == eq.id for e in user.equipment):
                await peizhuang_cmd.finish(msg + "不能重复装备相同物品，请尝试出售重复装备！")
            user.equipment.append(eq)
            user.equipment_storage.pop(idx)
            save_user(user)
            save_user_equipment(qq, user.equipment)
            save_user_equipment_storage(qq, user.equipment_storage)
            await peizhuang_cmd.finish(msg + f"已装备{eq.name}！\n当前装备数：{len(user.equipment)}/4")
        else:
            # 已装备4件，需替换
            msg += "你已装备4件装备，需要替换现有装备：\n"
            for i, old_eq in enumerate(user.equipment, 1):
                quality = quality_map.get(getattr(old_eq, 'quality', 0), "未知")
                eq_type = equipment_type_map.get(getattr(old_eq, 'equipment_type', 99), "未知")
                msg += f"[{i}] {quality} {eq_type} {old_eq.name}\n"
            msg += f"\n请选择要进行的操作：\n1-4. 选择对应装备进行替换\n5. 出售装备，获得{eq.value}哈哈币\n6. 取消替换，装备放回仓库"
            matcher.state["to_equip_idx"] = idx
            await peizhuang_cmd.send(msg)
    else:
        await peizhuang_cmd.reject(msg + "请输入1装备或2出售！")

@peizhuang_cmd.got("replace_idx")
async def _peizhuang_replace(event: Event, replace_idx: str = ArgPlainText()):
    qq = event.get_user_id()
    user = users.get(qq)
    msg = MessageSegment.at(qq) + "\n"
    from nonebot.matcher import current_matcher
    matcher = current_matcher.get()
    to_equip_idx = matcher.state.get("to_equip_idx")
    if not replace_idx.isdigit():
        await peizhuang_cmd.reject(msg + "请输入正确的序号！")
    rep_idx = int(replace_idx)
    
    # 选项6：取消替换，装备留在仓库
    if rep_idx == 6:
        await peizhuang_cmd.finish(msg + "已取消替换，装备保留在仓库中。")
    
    # 选项5：出售装备
    if rep_idx == 5:
        eq = user.equipment_storage[to_equip_idx]
        user.gold += eq.value
        user.equipment_storage.pop(to_equip_idx)
        save_user(user)
        save_user_equipment_storage(qq, user.equipment_storage)
        await peizhuang_cmd.finish(msg + f"已出售{eq.name}，获得{eq.value}哈哈币。\n当前哈哈币：{user.gold}")
    
    # 选项1-4：替换装备
    if rep_idx < 1 or rep_idx > len(user.equipment):
        await peizhuang_cmd.reject(msg + "序号超出范围，请重新输入！")
    
    # 检查是否装备了相同的装备
    new_eq = user.equipment_storage[to_equip_idx]
    if any(e.id == new_eq.id for e in user.equipment):
        await peizhuang_cmd.finish(msg + "不能重复装备相同物品，请尝试出售重复装备！")
    
    # 交换装备
    old_eq = user.equipment[rep_idx-1]
    user.equipment_storage[to_equip_idx] = old_eq
    user.equipment[rep_idx-1] = new_eq
    save_user(user)
    save_user_equipment(qq, user.equipment)
    save_user_equipment_storage(qq, user.equipment_storage)
    await peizhuang_cmd.finish(msg + f"已用{new_eq.name}（{equipment_type_map.get(getattr(new_eq, 'equipment_type', 99), '未知')}）替换{old_eq.name}（{equipment_type_map.get(getattr(old_eq, 'equipment_type', 99), '未知')}）！")


