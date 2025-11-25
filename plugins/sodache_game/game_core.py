import time
import random
from typing import Dict, List, Tuple
from .models.game_models import User, Item, PlayerStats
from .item_data import items_by_quality
from .db import init_db, load_all, save_all, save_user, save_user_items, save_user_equipment, save_user_equipment_storage
from .equipment_data import common_equipment, rare_equipment, epic_equipment, legendary_equipment
from dataclasses import asdict
from .models.game_models import Equipment

# 初始化数据库
init_db()
# 从数据库加载所有用户和物品数据
users = load_all()

def get_player_stats(user: User) -> PlayerStats:
    """
    计算玩家的综合属性，包括基础属性和装备加成。
    :param user: 用户对象
    :return: 包含综合属性的 PlayerStats 实例
    """
    # 初始化基础属性
    base_attack = float(user.attack)
    base_defense = float(user.defense)
    base_luck = float(user.luck)
    base_search_speed = float(user.search_speed)
    base_attack_cooldown_time = float(user.attack_cooldown_time)
    base_backpack_capacity = float(user.backpack_capacity)
    base_attack_protection_duration = float(user.attack_protection_duration)
    
    # 汇总所有装备的加法加成
    add_attack = 0.0
    add_defense = 0.0
    add_luck = 0.0
    add_search_speed = 0.0
    add_attack_cooldown_time = 0.0
    add_backpack_capacity = 0.0
    add_attack_protection_duration = 0.0
    add_extra_retreat_time = 0.0
    
    # 汇总所有装备的百分比加成
    increase_attack_percent = 0.0
    increase_defense_percent = 0.0
    
    for eq in user.equipment:
        # 加法加成
        add_attack += getattr(eq, "add_to_attack", 0)
        add_defense += getattr(eq, "add_to_defense", 0)
        add_luck += getattr(eq, "equip_luck", 0)
        add_search_speed += getattr(eq, "extra_search_speed", 0)
        add_attack_cooldown_time += getattr(eq, "equip_attack_cooldown", 0)
        add_backpack_capacity += getattr(eq, "extra_backpack_capacity", 0)
        add_attack_protection_duration += getattr(eq, "extra_attack_protection_duration", 0)
        add_extra_retreat_time += getattr(eq, "extra_retreat_time", 0)
        
        # 百分比加成（汇总）
        increase_attack_percent += getattr(eq, "increase_attack", 0)
        increase_defense_percent += getattr(eq, "increase_defense", 0)
    
    # 计算最终属性：(基础 + 加法) * (1 + 百分比总和 * 0.01)
    final_attack = (base_attack + add_attack) * (1.0 + increase_attack_percent * 0.01)
    final_defense = (base_defense + add_defense) * (1.0 + increase_defense_percent * 0.01)
    
    # 创建最终属性对象
    stats = PlayerStats(
        qq=user.qq,
        attack=final_attack,
        defense=final_defense,
        luck=base_luck + add_luck,
        speed=base_search_speed + add_search_speed,
        attack_cooldown_time=base_attack_cooldown_time + add_attack_cooldown_time,
        backpack_capacity=base_backpack_capacity + add_backpack_capacity,
        attack_protection_duration=base_attack_protection_duration + add_attack_protection_duration,
        extra_retreat_time=add_extra_retreat_time,
    )

    return stats

def user_init(qq: str) -> User:
    """
    用户初始化函数
    :param qq: QQ号
    :return: 初始化后的用户对象
    """
    # 创建用户对象
    new_user = User(
        qq=qq
        # 其他字段使用默认值
    )
    # 添加到用户注册表
    users[qq] = new_user
    # 保存新用户到数据库
    save_user(new_user)
    return new_user

def search(qq: str) -> bool:
    """
    用户搜索功能
    :param qq: 用户QQ号
    :return: 搜索开始是否成功
    """
    # 根据QQ号查找用户
    user = users.get(qq)
    if not user:
        # 用户不存在，初始化用户
        user = user_init(qq)
    check_retreat_status(qq)
    # 检查用户当前状态是否为0（未进行搜索）
    if user.status != 0:
        # 当前状态不是未搜索，无法开始新搜索
        return False
    
    # 开始搜索，修改状态和搜索开始时间
    user.status = 1  # 设置为搜索中状态
    user.search_start_time = int(time.time())  # 记录搜索开始时间（时间戳）
    
    # 重置当前搜索的物品记录
    user.inventory.clear()
    user.user_bag_items_nums = 0
    
    # 保存用户搜索状态到数据库
    save_user(user)
    save_user_items(qq, user.inventory)
    return True

def check_status(qq: str) -> dict:
    """
    检查用户当前状态，如果处于搜索状态则执行一次搜索
    :param qq: 用户QQ号
    :return: 包含状态信息和可能的抽取物品的字典
    """
    # 查找用户，如果不存在则初始化
    user = users.get(qq)
    if not user:
        user = user_init(qq)
    
    # 记录当前状态
    current_status = user.status
    # 如果处于搜索状态，执行一次物品抽取
    if current_status == 1:
        extract_items_by_time(qq)
    
    # 构建返回结果
    result = {
        "status": current_status,
        "status_text": {
            0: "空闲中",
            1: "搜索中",
            2: "撤离中"
        }.get(current_status, "未知状态"),
        "extracted_items": user.inventory,
        "gold": user.gold,
        "bag_items_nums": user.user_bag_items_nums
    }
    
    return result

def extract_items_by_time(qq: str) -> List[Item]:
    """
    根据用户搜索时间进行加权物品抽取
    :param qq: 用户QQ号
    :return: 抽取的物品列表
    """
    # 根据QQ号查找用户
    user = users.get(qq)
    if not user:
        return user.inventory
    # 检查用户背包物品数量是否已达上限
    if user.user_bag_items_nums >= user.backpack_capacity:
        user.search_start_time = int(time.time())
        return user.inventory
    # 检查用户是否处于搜索中状态
    if user.status != 1:
        return user.inventory
    
    current_time = int(time.time())
    elapsed = current_time - user.search_start_time
    
    # 获取包含装备加成的玩家属性
    stats = get_player_stats(user)
    # 基础每300秒抽取一件物品，搜索速度影响搜索间隔
    # 正数减少间隔（加快搜索），负数增加间隔（减慢搜索）
    # 计算公式：实际搜索间隔 = 300 - search_speed
    # 最少50秒，最多1800秒（30分钟）
    base_interval = 300
    actual_interval = base_interval - stats.search_speed
    # 限制范围：50秒到1800秒
    actual_interval = max(50, min(1800, actual_interval))
    
    # 每actual_interval秒抽取一件物品
    items_to_extract = elapsed // actual_interval
    if items_to_extract <= 0:
        return user.inventory
    
    # 定义品质权重（总和为100）
    quality_weights = {
        0: 60,   # 普通 (60%)
        1: 25,   # 稀有 (25%)
        2: 15,   # 史诗 (10%)
        3: 3     # 传说 (5%)
    }
    
    # 创建加权列表
    weighted_quality_list = []
    for quality, weight in quality_weights.items():
        weighted_quality_list.extend([quality] * weight)
    
    for _ in range(items_to_extract):
        # 随机选择品质
        selected_quality = random.choice(weighted_quality_list)
        
        # 从该品质的物品列表中随机选择一个
        quality_items = items_by_quality.get(selected_quality, [])
        if not quality_items:
            continue
        
        # 根据物品权重创建物品加权列表
        item_weighted_list = []
        for item in quality_items:
            item_weighted_list.extend([item] * item.weight)
        
        # 随机选择物品
        selected_item = random.choice(item_weighted_list)
        # 创建新的Item实例以避免修改原始数据
        new_item = Item(
            id=selected_item.id,
            name=selected_item.name,
            value=selected_item.value,
            quality=selected_item.quality,
            weight=selected_item.weight
        )

        # 添加到用户背包
        user.inventory.append(new_item)
        # 更新用户背包物品数量
        user.user_bag_items_nums += 1
        if user.user_bag_items_nums >= user.backpack_capacity:
            user.search_start_time = int(time.time())
            break
    
    # 更新搜索开始时间，减去已消耗的时间（保留未满一个间隔的剩余时间）
    remaining_time = elapsed % actual_interval
    user.search_start_time = current_time - remaining_time
    
    # 保存用户数据和物品到数据库
    save_user(user)
    save_user_items(user.qq, user.inventory)
    
    return user.inventory

def retreat(qq: str) -> bool:
    """
    用户撤离功能
    :param qq: 用户QQ号
    :return: 撤离开始是否成功
    """
    user = users.get(qq)
    extract_items_by_time(qq)
    if not user:
        return False
    # 检查用户当前状态是否为1（正在搜索）
    if user.status != 1:
        return False
    # 设置撤离状态和撤离开始时间
    user.status = 2
    user.retreat_start_time = int(time.time())
    
    # 保存用户撤离状态到数据库
    save_user(user)
    return True

def get_actual_retreat_time(user: User) -> int:
    """
    获取用户实际需要的撤退时间（包含装备加成）
    :param user: 用户对象
    :return: 实际撤退时间（秒）
    """
    stats = get_player_stats(user)
    # 基础撤退时间600秒 + 装备额外撤退时间（可正可负）
    # 注意：extra_retreat_time为负数时会减少撤退时间，正数时增加撤退时间
    # 最少60秒，最多1800秒
    base_retreat_time = 600
    actual_retreat_time = base_retreat_time + stats.extra_retreat_time
    return int(max(60, min(1800, actual_retreat_time)))

def check_retreat_status(qq: str) -> int:
    """
    检查用户撤离状态
    :param qq: 用户QQ号
    :return: 撤离是否成功完成
    """
    user = users.get(qq)
    if not user:
        return -1
    # 检查用户当前状态是否为2（撤离中）
    if user.status != 2:
        return -1
    # 计算撤离开始后经过的时间
    elapsed_time = int(time.time()) - user.retreat_start_time
    # 获取实际撤退时间（包含装备加成）
    actual_retreat_time = get_actual_retreat_time(user)
    
    # 如果撤离时间达到要求，则认为撤离成功
    if elapsed_time >= actual_retreat_time:
        # 计算本次搜索物品的总价值
        total_value = sum(item.value for item in user.inventory)
        # 将总价值添加到用户哈哈币中
        user.gold += total_value
        # 设置用户状态为未搜索
        user.status = 0
        # 重置撤离开始时间
        user.retreat_start_time = 0
        # 清空用户背包
        user.inventory.clear()
        # 重置背包物品数量
        user.user_bag_items_nums = 0
        
        # 保存用户撤离完成状态到数据库
        save_user(user)
        return total_value
    return -1

def attack(attacker_qq: str, defender_qq: str) -> str:
    """
    攻击函数：进攻方攻击防守方
    :param attacker_qq: 进攻方QQ号
    :param defender_qq: 防守方QQ号
    :return: 攻击是否成功
    """
    # 检查进攻方和防守方是否存在
    attacker = users.get(attacker_qq)
    defender = users.get(defender_qq)

    if not attacker:
        # 用户不存在，初始化用户
        attacker = user_init(attacker_qq)
        return f"你未在搜索状态"
    extract_items_by_time(attacker_qq)
    if not defender:
        return f"目标不存在"
    
    attacker_stats = get_player_stats(attacker)
    defender_stats = get_player_stats(defender)

    if attacker.gold < 0:
        return f"你已经破产了，不要再攻击别人了"
    # 检查防守方是否处于搜索状态（只有搜索中才能被攻击）
    check_retreat_status(defender_qq)
    if defender.status == 0:
        return f"目标未在搜索或撤离状态"
    extract_items_by_time(defender_qq)
    # 检查进攻方是否处于搜索状态（只有搜索中才能攻击）
    if attacker.status != 1:
        return f"你未在搜索状态"
    # 检查是否在攻击冷却时间内
    if int(time.time()) - attacker.attack_cooldown_start < attacker_stats.attack_cooldown_time:
        return f"冷却中，{attacker_stats.attack_cooldown_time - int(time.time()) + attacker.attack_cooldown_start}秒后可再次攻击"
    # 检查防守方是否处于被攻击保护状态
    current_time = int(time.time())
    if current_time < defender.attack_protection_end_time:
        remaining_time = defender.attack_protection_end_time - current_time
        return f"攻击失败！目标处于被攻击保护中，剩余{remaining_time}秒"
    # 计算攻击成功率：进攻方攻击力 / (进攻方攻击力 + 防守方防御力 + 1/4 * 防守方攻击力)
    attack_success_rate = attacker_stats.attack / (attacker_stats.attack + defender_stats.defense + 0.25 * defender_stats.attack)
    
    # 设置攻击冷却开始时间
    attacker.attack_cooldown_start = int(time.time())
    
    if random.random() >= attack_success_rate:
        # 攻击失败：冷却时间2分钟（120秒）+ 装备加成
        base_cooldown = 120
        
        # 设置冷却时间 = 基础冷却 + 装备的冷却时间加成
        attacker.attack_cooldown_time = base_cooldown + int(attacker_stats.attack_cooldown_time)
        
        # 保存攻击者状态
        save_user(attacker)
        return f"没打过！未损失任何物品。"
    

    # 攻击成功
    # 抢夺防守方背包中的一件随机物品（只影响 inventory，不影响 equipment）
    stolened_item = []
    if defender and defender.inventory:
        # 从防守方的背包物品中随机选择一件
        stolen_candidate = random.choice(defender.inventory)
        defender.inventory.remove(stolen_candidate)
        defender.user_bag_items_nums -= 1
        attacker.inventory.append(stolen_candidate)
        attacker.user_bag_items_nums += 1
        stolened_item.append(stolen_candidate)
    
    # 攻击成功：冷却时间10分钟（600秒）+ 装备加成
    base_cooldown = 600
    
    # 设置冷却时间 = 基础冷却 + 装备的冷却时间加成
    attacker.attack_cooldown_time = base_cooldown + int(attacker_stats.attack_cooldown_time)
    
    # 设置被攻击保护时间
    defender.attack_protection_end_time = int(time.time()) + defender_stats.attack_protection_duration
    
    # 保存进攻方和防守方的数据及物品到数据库
    save_user(attacker)
    save_user(defender)
    save_user_items(attacker.qq, attacker.inventory)
    save_user_items(defender.qq, defender.inventory)
    defender.search_start_time = int(time.time())

    if not stolened_item:
        return f"打赢了！但对方背包是空的，没有抢夺到物品！"
    else:
        msg = "打赢了！抢夺到以下物品:"
        for st in stolened_item:
            msg += f"\n{st.name}"
        return msg

def stop_retreat(qq: str) -> bool:
    """
    停止撤离函数：用户在撤离状态下调用，取消撤离
    :param qq: 用户QQ号
    :return: 是否成功取消撤离
    """
    user = users.get(qq)
    if not user:
        return False
    # 检查用户当前状态是否为2（撤离中）
    if user.status != 2:
        return False
    # 重置用户状态为搜索中
    user.status = 1
    # 重置搜索开始时间
    user.search_start_time = int(time.time())
    # 重置撤离开始时间
    user.retreat_start_time = 0
    
    # 保存用户撤离完成状态到数据库
    save_user(user)
    return True

def upgrade_attribute(qq: str, attribute_tag: int, amount: int) -> bool:
    """
    升级属性函数
    :param qq: 用户QQ号
    :param attribute: 要升级的属性名 (attack/defense/speed)
    :param amount: 要升级的数值
    :return: 是否升级成功
    """
    # 查找用户
    user = users.get(qq)
    if not user:
        user = user_init(qq)
    
    if attribute_tag == 1:
        cost = amount * 100
        if user.gold < cost:
            return False
        user.gold -= cost
        user.attack += amount
    elif attribute_tag == 2:
        cost = amount * 100
        if user.gold < cost:
            return False
        user.gold -= cost
        user.defense += amount
    elif attribute_tag == 3:
        cost = amount * 1000
        if user.gold < cost:
            return False
        user.gold -= cost
        user.speed += amount
    else:
        return False
    # 保存用户数据到数据库
    save_user(user)
    return True


def _clone_equipment_template(eq_template: Equipment) -> Equipment:
    """返回装备模板的浅拷贝（新的 Equipment 实例）。"""
    return Equipment(**asdict(eq_template))


def format_equipment_attributes(eq: Equipment) -> str:
    """格式化装备的非默认值属性。
    
    参数:
      - eq: 装备对象
    
    返回:
      - 格式化的属性字符串
    """
    attrs = []
    
    # 检查各个属性，只显示非默认值
    if getattr(eq, 'add_to_attack', 0) != 0:
        attrs.append(f"攻击力增加 {eq.add_to_attack}")
    if getattr(eq, 'increase_attack', 0) != 0:
        attrs.append(f"攻击力提高 {eq.increase_attack}%")
    if getattr(eq, 'add_to_defense', 0) != 0:
        attrs.append(f"防御力增加 {eq.add_to_defense}")
    if getattr(eq, 'increase_defense', 0) != 0:
        attrs.append(f"防御力提高 {eq.increase_defense}%")
    if getattr(eq, 'equip_luck', 0) != 0:
        attrs.append(f"幸运值 {eq.equip_luck:+d}")
    if getattr(eq, 'extra_search_speed', 0) != 0:
        attrs.append(f"搜索速度 {eq.extra_search_speed:+d}")
    if getattr(eq, 'extra_retreat_time', 0) != 0:
        attrs.append(f"撤退时间 {eq.extra_retreat_time:+d}秒")
    if getattr(eq, 'equip_attack_cooldown', 0) != 0:
        value = eq.equip_attack_cooldown
        attrs.append(f"攻击冷却 {value:+d}秒")
    if getattr(eq, 'extra_backpack_capacity', 0) != 0:
        attrs.append(f"背包容量 {eq.extra_backpack_capacity:+d}")
    if getattr(eq, 'extra_attack_protection_duration', 0) != 0:
        attrs.append(f"被攻击保护时长 {eq.extra_attack_protection_duration:+d}秒")
    
    if not attrs:
        return "无特殊属性"
    
    return "\n".join(attrs)


def draw_equipment_from_all_pool() -> Equipment:
    """从全装备奖池中抽取一件装备，type有额外权重。"""
    from .equipment_data import all_equipment
    type_weight_map = {0: 100, 1: 100, 2: 10}  # 武器100，防具100，背包10，其它默认1
    weighted_pool = []
    for eq in all_equipment:
        base = max(1, int(getattr(eq, "weight", 1)))
        type_w = type_weight_map.get(getattr(eq, "equipment_type", 99), 1)
        weighted_pool.extend([eq] * (base * type_w))
    if not weighted_pool:
        return None
    selected = random.choice(weighted_pool)
    return _clone_equipment_template(selected)


def draw_equipment_for_purchase(qq: str) -> Tuple[bool, str, Equipment]:
    """抽奖消耗300哈哈币，从全type奖池抽取装备。"""
    user = users.get(qq)
    if not user:
        user = user_init(qq)
    cost = 300
    if user.gold < cost:
        return False, f"哈哈币不足，无法抽奖！当前哈哈币：{user.gold}，需要：{cost}", None
    new_eq = draw_equipment_from_all_pool()
    if not new_eq:
        return False, "奖池为空，无法抽取！", None
    from .game_core import format_equipment_attributes
    attr_str = format_equipment_attributes(new_eq)
    msg = f"抽到装备：{new_eq.name}\n{attr_str}\n价值：{new_eq.value}哈哈币"
    return True, msg, new_eq



