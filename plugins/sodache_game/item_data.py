from .models.game_models import Item

# 普通物品列表（quality=0）
common_items = [
    Item(id="item_bread", name="军事情报", value=15 , quality=0, weight=20),
    Item(id="item_water", name="单筒望远镜", value=10, quality=0, weight=20),
    Item(id="item_apple", name="苹果", value=15 , quality=0, weight=15),
    Item(id="item_bandage", name="银币", value=10 , quality=0, weight=25),
    Item(id="item_stone", name="跳舞的女郎", value=10 , quality=0, weight=10),
    Item(id="item_wood", name="香喷喷烤面", value=20 , quality=0, weight=10)
]

# 稀有物品列表（quality=1）
rare_items = [
    Item(id="item_iron_sword", name="仪式匕首", value=150 , quality=1, weight=15),
    Item(id="item_iron_armor", name="后妈耳环", value=40 , quality=1, weight=100),
    Item(id="item_leather_boot", name="黄金饰章", value=40 , quality=1, weight=100),
    Item(id="item_silver_ring", name="电动车电池", value=100 , quality=1, weight=15),
    Item(id="item_hunting_knife", name="完整牛角", value=40 , quality=1, weight=100)
]

# 史诗物品列表（quality=2）
epic_items = [
    Item(id="item_steel_sword", name="本地特色首饰", value=300, quality=2, weight=5),
    Item(id="item_steel_armor", name="大型电台", value=300, quality=2, weight=10),
    Item(id="item_magic_amulet", name="珠宝王冠", value=250 , quality=2, weight=30),
    Item(id="item_elf_bow", name="金杯", value=200, quality=2, weight=50),
    Item(id="item_dragon_scale", name="金图纸", value=200, quality=2, weight=50)
]

# 传说物品列表（quality=3）
legendary_items = [
    Item(id="item_excalibur", name="军用炮弹", value=2500 , quality=3, weight=30),
    Item(id="item_holy_armor", name="笔记本电脑", value=3000 , quality=3, weight=15),
    Item(id="item_philosophers_stone", name="非洲之心", value=20000 , quality=3, weight=1),
    Item(id="item_dragon_slayer", name="量子存储", value=1500 , quality=3, weight=100),
    Item(id="item_amulet_of_immortality", name="复苏呼吸机", value=15000 , quality=3, weight=5),
    Item(id="item_holy_armor", name="光盘", value=1500 , quality=3, weight=100),
    Item(id="item_holy_armor", name="劳力士", value=1400 , quality=3, weight=100),
]

# 所有物品合并列表，用于搜索时随机获取物品
all_items = common_items + rare_items + epic_items + legendary_items

# 按品质分类的物品字典，便于按品质获取
items_by_quality = {
    0: common_items,
    1: rare_items,
    2: epic_items,
    3: legendary_items
}