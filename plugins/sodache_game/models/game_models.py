from dataclasses import dataclass, field
from typing import List, Optional
from pydantic import BaseModel
from enum import IntEnum

class EquipmentType(IntEnum):
    """装备类型枚举"""
    WEAPON = 0      # 武器
    ARMOR = 1       # 防具
    BACKPACK = 2    # 背包
    ACCESSORY = 3   # 饰品
    OTHER = 99      # 其他

@dataclass
class PlayerStats(BaseModel):
    """最终结算属性"""
    qq: str
    attack: float = 10.0
    defense: float = 5.0
    luck: float = 0.0
    search_speed: float = 0.0
    attack_cooldown_time: float = 0.0
    backpack_capacity: float = 4.0
    attack_protection_duration: float = 180.0
    extra_retreat_time: float = 0.0

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
    speed: int = 0               # 速度（保留用于其他用途）
    search_speed: int = 0        # 搜索速度
    gold: int = 100              # 哈哈币数量
    inventory: List[Item] = field(default_factory=list)  # 背包物品列表
    equipment: List["Equipment"] = field(default_factory=list)  # 穿戴的装备列表
    equipment_storage: List["Equipment"] = field(default_factory=list)  # 装备仓库，容量10
    status: int = 0              #0为未在搜索中，1为在搜索中，2为撤离中
    search_start_time: int = 0   # 搜索开始时间
    attack_cooldown_start: int = 0     # 攻击冷却时间开始时间
    retreat_start_time: int = 0        # 撤退开始时间
    search_group: str = ""            # 搜索所在群
    user_bag_items_nums: int = 0      # 用户背包物品数量
    have_searched_nums: int = 0       # 本次搜索已搜索物品数量
    attack_cooldown_time: int = 0     # 攻击冷却时间
    backpack_capacity: int = 4        # 背包容量
    attack_protection_end_time: int = 0  # 被攻击保护结束时间
    attack_protection_duration: int = 180 # 被攻击保护时长（秒）

    def equip_item(self, eq: "Equipment") -> bool:
        """装备一个 `Equipment` 实例：
        - 若装备列表中已存在同 id 的装备则返回 False（避免重复叠加）。
        - 否则把装备加入 `equipment` 列表，返回 True。
        """
        # 防止重复装备（按 id 判断）
        if any(e.id == eq.id for e in self.equipment):
            return False

        # 添加装备
        self.equipment.append(eq)
        return True

    def unequip_item(self, eq_identifier) -> bool:
        """移除一个 `Equipment` 实例：
        - `eq_identifier` 可以是 `Equipment` 实例或装备的 `id`（字符串）。
        - 如果找到并移除装备，返回 True；否则返回 False。
        """
        # 支持传入对象或 id：用 next(...) 找到第一个匹配项（找不到返回 None）
        if isinstance(eq_identifier, str):
            target = next((e for e in self.equipment if e.id == eq_identifier), None)
        else:
            target = next(
                (e for e in self.equipment if e is eq_identifier or e.id == getattr(eq_identifier, "id", None)),
                None,
            )

        if target is None:
            return False

        # 移除
        try:
            self.equipment.remove(target)
        except ValueError:
            return False

        return True

@dataclass
class Equipment(Item):
    """装备类 — 继承自 物品类"""
    equipment_type: int = 99                    # 装备类型：0=武器, 1=防具, 2=背包, 3=饰品, 99=其他（使用EquipmentType枚举）
    add_to_attack: int = 0                      # 直接增加攻击力
    increase_attack: int = 0                    # 提高攻击力百分比
    add_to_defense: int = 0                     # 直接增加防御力
    increase_defense: int = 0                   # 提高防御力百分比
    equip_luck: int = 0                         # 装备提供的幸运值
    extra_search_speed: int = 0                 # 额外搜索速度
    extra_retreat_time: int = 0                 # 额外撤退时间（秒）
    equip_attack_cooldown: int = 0              # 装备攻击冷却时间（秒）
    extra_backpack_capacity: int = 0            # 额外背包空间
    extra_attack_protection_duration: int = 0   # 额外被攻击保护时长（秒）
