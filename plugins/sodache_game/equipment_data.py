from .models.game_models import Equipment, EquipmentType
from typing import Dict, List

# ==================== 装备类型常量 ====================
EQUIPMENT_TYPE_WEAPON = EquipmentType.WEAPON        # 武器
EQUIPMENT_TYPE_ARMOR = EquipmentType.ARMOR          # 防具
EQUIPMENT_TYPE_BACKPACK = EquipmentType.BACKPACK    # 背包
EQUIPMENT_TYPE_ACCESSORY = EquipmentType.ACCESSORY  # 饰品
EQUIPMENT_TYPE_OTHER = EquipmentType.OTHER          # 其他

# ==================== 武器 (WEAPON) ====================
weapons: List[Equipment] = [
    Equipment(
    id="smg_uzi",
    name="乌兹冲锋枪",
    value=10,
    equipment_type=EQUIPMENT_TYPE_WEAPON,
    add_to_attack=5,
    increase_attack=15,
    equip_attack_cooldown=-30,
    weight=100
),

    Equipment(
    id="smg_bison",
    name="野牛冲锋枪",
    value=10,
    equipment_type=EQUIPMENT_TYPE_WEAPON,
    add_to_attack=9,
    equip_attack_cooldown=-30,
    weight=100
),

    Equipment(
    id="ar_G3",
    name="G3战斗步枪",
    value=30,
    quality=1,
    equipment_type=EQUIPMENT_TYPE_WEAPON,
    add_to_attack=10,
    increase_attack=10,
    weight=60
),

    Equipment(
    id="ar_QBZ95",
    name="95式步枪",
    value=30,
    quality=1,
    equipment_type=EQUIPMENT_TYPE_WEAPON,
    add_to_attack=15,
    increase_attack=5,
    weight=60
),

    Equipment(
    id="ar_M4A1",
    name="M4A1步枪",
    value=100,
    quality=2,
    equipment_type=EQUIPMENT_TYPE_WEAPON,
    add_to_attack=15,
    increase_attack=25,
    weight=15
),

    Equipment(
    id="lmg_pkm",
    name="pkm轻机枪",
    value=10,
    equipment_type=EQUIPMENT_TYPE_WEAPON,
    add_to_attack=45,
    extra_retreat_time=30,
    equip_attack_cooldown=-30,
    weight=10
),

    Equipment(
    id="ar_m7",
    name="m7战斗步枪",
    value=350,
    quality=3,
    equipment_type=EQUIPMENT_TYPE_WEAPON,
    add_to_attack=30,
    increase_attack=30,
    add_to_defense=5,
    weight=3
),

    Equipment(
    id="sr_m700",
    name="m700狙击步枪",
    value=150,
    quality=2,
    equipment_type=EQUIPMENT_TYPE_WEAPON,
    add_to_attack=10,
    increase_attack=55,
    extra_retreat_time=30,
    equip_attack_cooldown=180,
    weight=9
),

    Equipment(
    id="sr_awm",
    name="AWM狙击步枪",
    value=600,
    quality=3,
    equipment_type=EQUIPMENT_TYPE_WEAPON,
    add_to_attack=20,
    increase_attack=100,
    extra_retreat_time=60,
    equip_attack_cooldown=360
),

]

# ==================== 防具 (ARMOR) ====================
armors: List[Equipment] = [
    Equipment(
    id="moto_vest",
    name="摩托背心",
    value=10,
    equipment_type=EQUIPMENT_TYPE_ARMOR,
    add_to_defense=5,
    increase_defense=15,
    weight=100
),

    Equipment(
    id="havvk_armor",
    name="哈哈克保安背心",
    value=10,
    equipment_type=EQUIPMENT_TYPE_ARMOR,
    add_to_defense=10,
    weight=100
),

    Equipment(
    id="stab_armor",
    name="简易防刺服",
    value=30,
    quality=1,
    equipment_type=EQUIPMENT_TYPE_ARMOR,
    add_to_defense=12,
    increase_defense=12,
    weight=60
),

    Equipment(
    id="warrior_armor",
    name="武士防弹背心",
    value=10,
    equipment_type=EQUIPMENT_TYPE_ARMOR,
    add_to_defense=20,
    increase_defense=15,
    weight=10,
    extra_attack_protection_duration=30
),

    Equipment(
    id="mk2_armor",
    name="MK2防弹背心",
    value=100,
    quality=2,
    equipment_type=EQUIPMENT_TYPE_ARMOR,
    add_to_defense=25,
    increase_defense=25,
    extra_retreat_time=30,
    equip_attack_cooldown=30,
    weight=20,
    extra_attack_protection_duration=60
),

    Equipment(
    id="heavy_armor",
    name="重型突击背心",
    value=300,
    quality=3,
    equipment_type=EQUIPMENT_TYPE_ARMOR,
    add_to_defense=45,
    increase_defense=30,
    extra_search_speed=60,
    extra_retreat_time=150,
    equip_attack_cooldown=90,
    weight=8,
    extra_attack_protection_duration=90
),

    Equipment(
    id="elite_armor",
    name="精英防弹背心",
    value=300,
    quality=3,
    equipment_type=EQUIPMENT_TYPE_ARMOR,
    add_to_defense=20,
    increase_defense=30,
    weight=8,
    extra_attack_protection_duration=30
),

    Equipment(
    id="titan_armor",
    name="泰坦防弹装甲",
    value=500,
    quality=3,
    equipment_type=EQUIPMENT_TYPE_ARMOR,
    add_to_defense=100,
    increase_defense=40,
    extra_search_speed=120,
    extra_retreat_time=240,
    equip_attack_cooldown=150,
    extra_attack_protection_duration=120,
    weight=2
),
]

# ==================== 背包 (BACKPACK) ====================
backpacks: List[Equipment] = [
    Equipment(
    id="camping_backpack",
    name="露营背包",
    value=10,
    equipment_type=EQUIPMENT_TYPE_BACKPACK,
    extra_backpack_capacity=2,
    weight=60
),

    Equipment(
    id="gti_backpack",
    name="GTI野战背包",
    value=50,
    quality=1,
    equipment_type=EQUIPMENT_TYPE_BACKPACK,
    extra_backpack_capacity=3,
    weight=30
),

    Equipment(
    id="havvk_backpack",
    name="哈哈克野战背包",
    value=100,
    quality=2,
    equipment_type=EQUIPMENT_TYPE_BACKPACK,
    extra_retreat_time=30,
    extra_backpack_capacity=4,
    weight=15
),

    Equipment(
    id="heavy_hiking_backpack",
    name="重型登山包",
    value=500,
    quality=3,
    equipment_type=EQUIPMENT_TYPE_BACKPACK,
    extra_retreat_time=120,
    extra_backpack_capacity=7,
    weight=3
),
]

# ==================== 饰品 (ACCESSORY) ====================
accessories: List[Equipment] = [
    # 在此添加饰品装备（预留）
]

# ==================== 其他 (OTHER) ====================
other_equipment: List[Equipment] = [
    # 在此添加其他类型装备（预留）
]

# ==================== 所有装备合并列表 ====================
all_equipment = weapons + armors + backpacks + accessories + other_equipment

# ==================== 按装备类型分类的装备字典 ====================
equipment_by_type: Dict[int, List[Equipment]] = {
    EQUIPMENT_TYPE_WEAPON: weapons,
    EQUIPMENT_TYPE_ARMOR: armors,
    EQUIPMENT_TYPE_BACKPACK: backpacks,
    EQUIPMENT_TYPE_ACCESSORY: accessories,
    EQUIPMENT_TYPE_OTHER: other_equipment,
}

# ==================== 按品质分类的装备字典（动态生成）====================
def _get_equipment_by_quality() -> Dict[int, List[Equipment]]:
    """动态生成按品质分类的字典"""
    result: Dict[int, List[Equipment]] = {
        0: [],  # 普通
        1: [],  # 稀有
        2: [],  # 史诗
        3: [],  # 传说
    }
    
    for eq in all_equipment:
        quality = getattr(eq, "quality", 0)
        if quality in result:
            result[quality].append(eq)
    
    return result

equipment_by_quality: Dict[int, List[Equipment]] = _get_equipment_by_quality()
