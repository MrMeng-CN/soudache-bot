import time
import random
from typing import Dict, List
from .models.game_models import User, Item
from .item_data import items_by_quality
from .db import init_db, load_all, save_all, save_user, save_user_items

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
    
    # 每300秒抽取一件物品
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
    
    # 在抽取完成后，更新搜索时间到最近一次抽取的位置，避免重复抽取
    # 只有在确实抽取了物品的情况下才更新时间
    if items_to_extract > 0:
        user.search_start_time = int(time.time()) - elapsed%300
    
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
    if elapsed_time >= 600-user.speed*30:
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
    current_time = int(time.time())
    if attacker.attack_cooldown_end_time - current_time > 0:
        return f"冷却中，{attacker.attack_cooldown_end_time - current_time}秒后可再次攻击"
    # 检查防守方是否处于被攻击保护状态
    if current_time < defender.attack_protection_end_time:
        remaining_time = defender.attack_protection_end_time - current_time
        return f"攻击失败！目标处于被攻击保护中，剩余{remaining_time}秒"
    # 计算攻击成功率：进攻方攻击力 / (进攻方攻击力 + 防守方防御力)
    attack_success_rate = attacker.attack / (attacker.attack + defender.defense)

    attacker.attack_cooldown_end_time = current_time

    if random.random() >= attack_success_rate:
        # 攻击失败：只计算进攻方的损失
        # 损失哈哈币 = 防守方攻击力 - 进攻方防御力，最低损失10哈哈币
        damage = max(10, defender.attack - attacker.defense)*2
        attacker.gold = attacker.gold - damage
        attacker.attack_cooldown_end_time +=180
        # 保存进攻方数据到数据库
        save_user(attacker)
        
        return f"没打过！你损失了{damage}哈哈币"
    
    # 攻击成功
    # 1. 抢夺防守方一件随机物品（从当前搜索物品中）
    defender_user = users.get(defender_qq)
    stolen_item = None
    if defender_user and defender_user.inventory:
        stolen_item = random.choice(defender_user.inventory)
        attacker_user = users.get(attacker_qq)
        # 将物品添加到进攻方当前搜索物品
        attacker_user.inventory.append(stolen_item)
        attacker_user.user_bag_items_nums += 1
        # 从防守方当前搜索物品中移除
        defender_user.inventory.remove(stolen_item)
        defender_user.user_bag_items_nums -= 1

    # 2. 计算双方损失哈哈币
    # 进攻方损失：防守方攻击力 - 进攻方防御力，最低10哈哈币
    attacker_damage = max(10, defender.attack - attacker.defense)
    attacker.gold = attacker.gold - attacker_damage
    attacker.attack_cooldown_end_time += 360
    
    # 设置被攻击保护时间
    defender.attack_protection_end_time = current_time + defender.attack_protection_duration
    
    # 保存进攻方和防守方的数据及物品到数据库
    save_user(attacker)
    save_user(defender)
    save_user_items(attacker.qq, attacker.inventory)
    save_user_items(defender.qq, defender.inventory)
    defender.search_start_time = current_time

    if stolen_item is None:
        return f"打赢了！你损失了{attacker_damage}哈哈币，但是没有抢夺到物品!"
    return f"打赢了！你损失了{attacker_damage}哈哈币，抢夺到了{stolen_item.name}!"


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

def upgrade_attribute(qq: str, attribute_tag: int, amount: int) -> tuple[bool,str]:
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
        cost = amount * 500
        if user.gold < cost:
            return False,f"哈哈币不足"
        user.gold -= cost
        user.attack += amount
    elif attribute_tag == 2:
        cost = amount * 500
        if user.gold < cost:
            return False,f"哈哈币不足"
        user.gold -= cost
        user.defense += amount
    elif attribute_tag == 3:
        cost = amount * 2000
        if user.gold < cost:
            return False,f"哈哈币不足"
        # 每级加快30秒撤离速度
        if user.speed+amount>10:
            return False,f"速度已经提升到最高了"
        user.gold -= cost
        user.speed += amount
    elif attribute_tag == 4:
        # 初始容量为4，计算当前升级的等级
        current_level = user.backpack_capacity - 4
        # 价格按比例上升：5000 * (current_level + 1)
        cost = 4000 * (current_level + 1)
        if user.gold < cost:
            return False,f"哈哈币不足"
        user.gold -= cost
        user.backpack_capacity += 1
    else:
        return False,f"输入错误，没有你要升级的属性"

    # 保存用户数据到数据库
    save_user(user)
    return True,f"升级成功"