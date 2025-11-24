from .models.game_models import Equipment

# 普通装备（quality=0）
common_equipment = [
    Equipment(id="eq_havvk_armor", name="哈夫克小兵甲", value=15, quality=0, equip_defense=8, weight=20),
    Equipment(id="eq_asara_armor", name="阿萨拉小兵甲", value=10, quality=0, equip_defense=7, weight=30),
    Equipment(id="eq_uz_smg", name="乌兹冲锋枪", value=15, quality=0, equip_attack=7, equip_attack_cooldown=-60, weight=20),
    Equipment(id="eq_bison_smg", name="野牛冲锋枪", value=10, quality=0, equip_attack=6, equip_attack_cooldown=-60, weight=30),
    Equipment(id="eq_camp_backpack", name="露营背包", value=10, quality=0, extra_backpack_capacity=2, weight=60),
]

# 稀有装备（quality=1）
rare_equipment = [
    Equipment(id="eq_gti_bulletproof_vest", name="GTI防弹背心", value=35, quality=1, equip_defense=12, weight=30),
    Equipment(id="eq_gti_field_pack", name="GTI野战背包", value=25, quality=1, extra_backpack_capacity=5, weight=60),
    Equipment(id="eq_g3_rifle", name="G3战斗步枪", value=40, quality=1, equip_attack=12, weight=30),
    Equipment(id="eq_mp5_smg", name="MP5冲锋枪", value=35, quality=1, equip_attack=9, equip_attack_cooldown=-60, weight=20),
    Equipment(id="eq_sv98_sniper", name="SV98狙击枪", value=50, quality=1, equip_attack=20, equip_attack_cooldown=60, weight=10),
]

# 史诗装备（quality=2）
epic_equipment = [
    Equipment(id="eq_mk2_vest", name="MK2防弹背心", value=95, quality=2, equip_defense=20, extra_attack_protection_duration=60, weight=35),
    Equipment(id="eq_heavy_assault_vest", name="重型突击背心", value=130, quality=2, equip_defense=25, extra_attack_protection_duration=90, weight=20),
    Equipment(id="eq_havvk_field_pack", name="哈夫克野战背包", value=100, quality=2, extra_backpack_capacity=8, weight=60),
    Equipment(id="eq_mp7_smg", name="MP7冲锋枪", value=90, quality=2, equip_attack=16, equip_attack_cooldown=-60, weight=40),
    Equipment(id="eq_tenglong_rifle", name="腾龙突击步枪", value=100, quality=2, equip_attack=24, equip_attack_cooldown=-30, weight=30),
    Equipment(id="eq_m700_sniper", name="M700狙击枪", value=150, quality=2, equip_attack=55, equip_attack_cooldown=60, weight=10),
]

# 传说装备（quality=3）
legendary_equipment = [
    Equipment(id="eq_titan_armor", name="泰坦防弹装甲", value=500, quality=3, equip_defense=65, extra_attack_protection_duration=120, weight=30),
    Equipment(id="eq_trick_armor", name="特里克防弹装甲", value=500, quality=3, equip_defense=50, extra_attack_protection_duration=150, weight=30),
    Equipment(id="eq_m7_rifle", name="M7战斗步枪", value=500, quality=3, equip_attack=50, weight=30),
    Equipment(id="eq_awm_sniper", name="AWM狙击枪", value=700, quality=3, equip_attack=150, equip_attack_cooldown=90, weight=10),
    Equipment(id="eq_northstar", name="北极星", value=600, quality=3, equip_attack=40, equip_attack_cooldown=-60, weight=20),
]

# 所有装备合并列表
all_equipment = common_equipment + rare_equipment + epic_equipment + legendary_equipment

# 按品质分类的装备字典，便于按品质获取
equipment_by_quality = {
    0: common_equipment,
    1: rare_equipment,
    2: epic_equipment,
    3: legendary_equipment,
}
