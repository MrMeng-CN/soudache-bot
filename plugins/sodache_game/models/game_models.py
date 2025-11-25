from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Item:
    """物品类"""
    id: str                      # 物品唯一标识
    name: str                    # 物品名称
    value: int                   # 物品价值
    quality: int = 0             # 物品质量: 0普通, 1稀有, 2史诗, 3传说
    weight: int = 1              # 物品爆率权重


@dataclass
class User:
    """用户类"""
    qq: str                      # QQ号
    attack: int = 10             # 攻击力
    defense: int = 5             # 防御力
    luck: int = 0                # 幸运值
    speed: int = 0               # 撤离速度
    gold: int = 100              # 哈哈币数量
    inventory: List[Item] = field(default_factory=list)  # 背包物品列表
    status: int = 0              #0为未在搜索中，1为在搜索中，2为撤离中
    search_start_time: int = 0   # 搜索开始时间
    attack_cooldown_start: int = 0     # 攻击冷却时间开始时间
    retreat_start_time: int = 0        # 撤退开始时间
    search_group: str = ""            # 搜索所在群
    user_bag_items_nums: int = 0      # 用户背包物品数量
    have_searched_nums: int = 0       # 本次搜索已搜索物品数量
    attack_cooldown_end_time: int = 0     # 攻击冷却时间结束时间
    backpack_capacity: int = 4        # 背包容量
    attack_protection_end_time: int = 0  # 被攻击保护结束时间
    attack_protection_duration: int = 180 # 被攻击保护时长（秒）
