import time
import random
from typing import Dict, List, Tuple
from .models.game_models import User, Item
from .item_data import items_by_quality
from .db import init_db, load_all, save_all, save_user, save_user_items, save_user_equipment
from .equipment_data import common_equipment, rare_equipment, epic_equipment, legendary_equipment
from dataclasses import asdict
from .models.game_models import Equipment

# 初始化数据库
init_db()
# 从数据库加载所有用户和物品数据
users = load_all()

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
    
    # 每30分钟（1800秒）抽取一件物品
    items_to_extract = elapsed // 300
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
    # 如果撤离时间超过10分钟（600秒），则认为撤离成功
    if elapsed_time >= 600:
        # 计算本次搜索物品的总价值
        total_value = sum(item.value for item in user.inventory)
        # 将总价值添加到用户金币中
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
    if int(time.time()) - attacker.attack_cooldown_start < attacker.attack_cooldown_time:
        return f"冷却中，{attacker.attack_cooldown_time - int(time.time()) + attacker.attack_cooldown_start}秒后可再次攻击"
    # 检查防守方是否处于被攻击保护状态
    current_time = int(time.time())
    if current_time < defender.attack_protection_end_time:
        remaining_time = defender.attack_protection_end_time - current_time
        return f"攻击失败！目标处于被攻击保护中，剩余{remaining_time}秒"
    # 记录攻击开始前进攻方是否佩戴任何装备（用于结算后可能增加额外冷却）
    attacker_had_no_equipment = not bool(attacker.equipment)
    # 计算攻击成功率：进攻方攻击力 / (进攻方攻击力 + 防守方防御力 + 1/4 * 防守方攻击力)
    attack_success_rate = attacker.attack / (attacker.attack + defender.defense + 0.25 * defender.attack)
    attacker.attack_cooldown_start = int(time.time())
    if random.random() >= attack_success_rate:

        # 攻击失败：不再损失金币，改为 50% 概率被抢走一件已装备的装备
        attacker.attack_cooldown_time += 120
        # 若攻击发起前未佩戴装备，则在本次结算后额外增加冷却
        if attacker_had_no_equipment:
            attacker.attack_cooldown_time += 360
        lost_equipment = None
        # 使用模块级的 random，使代码更易读；同时使用已有的 defender 变量
        if attacker.equipment and random.random() < 0.5:
            # 随机选一件装备并移除（unequip_item 会撤销属性）
            lost_equipment = random.choice(list(attacker.equipment))
            attacker.unequip_item(lost_equipment)
            # 将该装备以 Item 形式放入防守方的 inventory
            stolen_as_item = Item(id=lost_equipment.id, name=lost_equipment.name, value=lost_equipment.value, quality=lost_equipment.quality, weight=lost_equipment.weight)
            defender.inventory.append(stolen_as_item)
            defender.user_bag_items_nums += 1
            # 保存双方数据到数据库
            save_user(attacker)
            save_user(defender)
            save_user_items(defender.qq, defender.inventory)
            # 更新攻击者状态
            save_user_equipment(attacker.qq, attacker.equipment)
            return f"没打过！你被夺走了装备：{lost_equipment.name}，已放入对方背包！"
        # 未丢失装备的情况
        save_user(attacker)
        save_user_equipment(attacker.qq, attacker.equipment)
        return f"没打过！未损失装备或金币。"
    

    # 攻击成功
    # 1. 抢夺防守方一件随机物品（从当前搜索物品和已装备物品中）
    stolened_item = []
    if defender:
        # 抢夺池包含防守方的背包物品和已装备的装备，装备会被脱下并作为 Item 放入进攻方背包
        steal_pool = []
        # 背包物品（Item）
        steal_pool.extend(list(defender.inventory))
        if steal_pool:
            stolen_candidate = random.choice(steal_pool)
            defender.inventory.remove(stolen_candidate)
            defender.user_bag_items_nums -= 1
            attacker.inventory.append(stolen_candidate)
            attacker.user_bag_items_nums += 1
            stolened_item.append(stolen_candidate)
        
        # 装备物品（Equipment） 
        if defender.equipment!=[]:
            stolen_eq = random.choice(list(defender.equipment))
            defender.unequip_item(stolen_eq)
            stolened_eq = Equipment(id=stolen_eq.id, name=stolen_eq.name, value=stolen_eq.value, quality=stolen_eq.quality, weight=stolen_eq.weight)
            attacker.inventory.append(stolened_eq)
            attacker.user_bag_items_nums += 1
            stolened_item.append(stolened_eq)
    
    # # 2. 计算双方损失金币
    # # 进攻方损失：防守方攻击力 - 进攻方防御力，最低10金币
    # attacker_damage = max(10, defender.attack - attacker.defense)
    # attacker.gold = attacker.gold - attacker_damage

    attacker.attack_cooldown_start = int(time.time())
    attacker.attack_cooldown_time += 600
    # 若攻击发起前未佩戴装备，则在本次结算后额外增加冷却
    if attacker_had_no_equipment:
        attacker.attack_cooldown_time += 360
    
    # 设置被攻击保护时间
    defender.attack_protection_end_time = int(time.time()) + defender.attack_protection_duration
    
    # 保存进攻方和防守方的数据及物品到数据库
    save_user(attacker)
    save_user(defender)
    save_user_items(attacker.qq, attacker.inventory)
    save_user_items(defender.qq, defender.inventory)
    save_user_equipment(defender.qq, defender.equipment)
    defender.search_start_time = int(time.time())

    if stolened_item is None:
        return f"打赢了！但是没有抢夺到物品!"
    else:
        msg ="打赢了！抢夺到以下物品:"
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


def _weighted_draw_equipment(category_weights: dict, count: int) -> List[Equipment]:
    """按类别权重抽取若干装备。

    参数:
      - category_weights: dict，键为品质（0/1/2/3），值为该类别的权重。
      - count: 要抽取的装备数量。

    抽取逻辑：对每个类别中的每件装备，以 `类别权重 * 装备.weight` 作为其最终权重构建抽取池，
    然后从池中随机选择（不重复），并返回克隆后的 `Equipment` 实例列表。
    若池为空则返回空列表。
    """
    pool = []
    categories = {
        0: common_equipment,
        1: rare_equipment,
        2: epic_equipment,
        3: legendary_equipment,
    }
    for q, cat_weight in category_weights.items():
        items = categories.get(q, [])
        if not items or cat_weight <= 0:
            continue
        for it in items:
            # 最终权重 = 类别权重 * 装备自身权重
            w = max(1, int(cat_weight)) * max(1, int(getattr(it, "weight", 1)))
            pool.extend([it] * w)

    # 池为空则返回空
    if not pool:
        return []

    chosen = []
    # 为避免重复，选中后从池中移除该模板的所有出现
    for _ in range(count):
        if not pool:
            break
        sel = random.choice(pool)
        chosen.append(_clone_equipment_template(sel))
        # 从池中移除该模板的所有条目以避免重复抽中同一模板
        pool = [p for p in pool if p.id != sel.id]

    return chosen


def purchase_cheese_ticket(qq: str, choice: int) -> Tuple[bool, str]:
    """处理芝士券购买并按规则为用户重新配装。

    返回值：(是否成功, 返回给上层显示的消息字符串)
    """
    user = users.get(qq)
    if not user:
        user = user_init(qq)

    # cancel
    if choice == 0:
        return True, "已取消购买，保持现有装备。"

    cost_map = {1: 50, 2: 200, 3: 1000, 4: 5000}
    if choice not in cost_map:
        return False, "你只能在芝士券中选择！"

    cost = cost_map[choice]
    if user.gold < cost:
        return False, "金币不足，无法购买芝士券。"

    # 回收当前装备：计算总价值并移除所有装备（并撤销属性）
    total_recycle = sum(eq.value for eq in user.equipment)
    # remove all equipment safely
    for eq in list(user.equipment):
        user.unequip_item(eq)

    # 将回收价值加入金币
    user.gold += total_recycle

    # 扣除购买费用
    user.gold -= cost

    # 根据choice选择添加新装备
    new_eqs = []
    if choice == 1:
        weights = {0: 100, 1: 10, 3: 1}
        new_eqs = _weighted_draw_equipment(weights, 3)
    elif choice == 2:
        weights = {0: 10, 1: 100, 2: 10, 3: 1}
        new_eqs = _weighted_draw_equipment(weights, 3)
    elif choice == 3:
        weights = {1: 20, 2: 40, 3: 10}
        new_eqs = _weighted_draw_equipment(weights, 3)
    elif choice == 4:
        weights = {2: 30, 3: 30}
        new_eqs = _weighted_draw_equipment(weights, 4)

    added_names = []
    for eq in new_eqs:
        user.equip_item(eq)
        added_names.append(eq.name)

    # 保存用户和物品状态
    save_user(user)
    save_user_equipment(user.qq, user.equipment)

    if not new_eqs:
        return True, f"购买成功，回收了旧装备获得 {total_recycle} 金币，但未抽到新装备。"

    return True, f"购买成功，回收旧装备获得 {total_recycle} 金币；已为你添加装备：{', '.join(added_names)}"

