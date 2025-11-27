import sqlite3
from typing import Dict, List, Optional
from .models.game_models import User, Item, Equipment
from .connection_pool import ConnectionPool

db_path = "game_data.db"
db_timeout = 5  # 数据库操作超时时间（秒）
pool_size = 10  # 连接池大小

sqlite_pool = ConnectionPool(db_path, pool_size, db_timeout)

def init_db():
    """初始化数据库表"""
    conn = sqlite_pool.get_conn()  # 从连接池获取连接
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        qq TEXT PRIMARY KEY,
        attack INTEGER DEFAULT 10,
        defense INTEGER DEFAULT 5,
        luck INTEGER DEFAULT 0,
        speed INTEGER DEFAULT 0,
        search_time INTEGER DEFAULT 0,
        gold INTEGER DEFAULT 100,
        status INTEGER DEFAULT 0,
        search_start_time INTEGER DEFAULT 0,
        attack_cooldown_start INTEGER DEFAULT 0,
        retreat_start_time INTEGER DEFAULT 0,
        search_group TEXT DEFAULT '',
        user_bag_items_nums INTEGER DEFAULT 0,
        have_searched_nums INTEGER DEFAULT 0,
        attack_cooldown_time INTEGER DEFAULT 0,
        backpack_capacity INTEGER DEFAULT 4,
        attack_protection_end_time INTEGER DEFAULT 0
    )
    """)
    # 检查user_items表是否存在旧结构
    cursor.execute("PRAGMA table_info(user_items)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'id' not in columns:
        # 旧表结构存在，需要迁移数据
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_items_temp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_qq TEXT,
            item_id TEXT,
            item_name TEXT,
            item_value INTEGER,
            item_quality INTEGER
        )
        """)
        
        # 检查旧表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_items'")
        old_table_exists = cursor.fetchone() is not None
        
        if old_table_exists:
            # 复制数据到新表
            cursor.execute("""
            INSERT INTO user_items_temp (user_qq, item_id, item_name, item_value, item_quality)
            SELECT user_qq, item_id, item_name, item_value, item_quality FROM user_items
            """)
            # 删除旧表
            cursor.execute("DROP TABLE user_items")
        
        # 重命名新表
        cursor.execute("ALTER TABLE user_items_temp RENAME TO user_items")
    else:
        # 新表结构已经存在，只需要确保表存在
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_qq TEXT,
            item_id TEXT,
            item_name TEXT,
            item_value INTEGER,
            item_quality INTEGER
        )
        """)
    
    # 创建用户装备表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_qq TEXT,
        item_id TEXT,
        item_name TEXT,
        item_value INTEGER,
        item_quality INTEGER,
        equipment_type INTEGER DEFAULT 99,
        add_to_attack INTEGER DEFAULT 0,
        add_to_defense INTEGER DEFAULT 0,
        increase_attack INTEGER DEFAULT 0,
        increase_defense INTEGER DEFAULT 0,
        equip_luck INTEGER DEFAULT 0,
        extra_search_time INTEGER DEFAULT 0,
        extra_retreat_time INTEGER DEFAULT 0,
        equip_attack_cooldown INTEGER DEFAULT 0,
        extra_backpack_capacity INTEGER DEFAULT 0,
        extra_attack_protection_duration INTEGER DEFAULT 0
    )
    """)
    
    # 创建装备仓库表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_equipment_storage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_qq TEXT,
        item_id TEXT,
        item_name TEXT,
        item_value INTEGER,
        item_quality INTEGER,
        equipment_type INTEGER DEFAULT 99,
        add_to_attack INTEGER DEFAULT 0,
        add_to_defense INTEGER DEFAULT 0,
        increase_attack INTEGER DEFAULT 0,
        increase_defense INTEGER DEFAULT 0,
        equip_luck INTEGER DEFAULT 0,
        extra_search_time INTEGER DEFAULT 0,
        extra_retreat_time INTEGER DEFAULT 0,
        equip_attack_cooldown INTEGER DEFAULT 0,
        extra_backpack_capacity INTEGER DEFAULT 0,
        extra_attack_protection_duration INTEGER DEFAULT 0
    )
    """)
    
    # 为user_qq字段创建索引，提高查询效率
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_equipment_qq ON user_equipment(user_qq)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_equipment_storage_qq ON user_equipment_storage(user_qq)")
    
    conn.commit()
    sqlite_pool.put_conn(conn)  # 将连接放回连接池

def save_user(user: User, conn: Optional[sqlite3.Connection] = None):
    """保存用户数据到数据库"""
    use_pool = conn is None
    if use_pool:
        conn = sqlite_pool.get_conn()
    
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO users (
        qq, attack, defense, luck, speed, search_time, gold, status, search_start_time,
        attack_cooldown_start, retreat_start_time, search_group, user_bag_items_nums, have_searched_nums, attack_cooldown_time, backpack_capacity, attack_protection_end_time
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user.qq, user.attack, user.defense, user.luck, user.speed, user.search_time, user.gold, user.status,
        user.search_start_time, user.attack_cooldown_start, user.retreat_start_time, user.search_group,
        user.user_bag_items_nums, user.have_searched_nums, user.attack_cooldown_time, user.backpack_capacity, user.attack_protection_end_time
    ))
    
    if use_pool:
        conn.commit()
        sqlite_pool.put_conn(conn)

def load_user(qq: str, conn: Optional[sqlite3.Connection] = None) -> User:
    """从数据库加载用户数据"""
    use_pool = conn is None
    if use_pool:
        conn = sqlite_pool.get_conn()
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE qq = ?", (qq,))
    row = cursor.fetchone()
    
    if use_pool:
        sqlite_pool.put_conn(conn)
    
    if row:
        return User(
            qq=row[0],
            attack=row[1],
            defense=row[2],
            luck=row[3],
            speed=row[4],
            search_time=row[5],
            gold=row[6],
            status=row[7],
            search_start_time=row[8],
            attack_cooldown_start=row[9],
            retreat_start_time=row[10],
            search_group=row[11],
            user_bag_items_nums=row[12],
            have_searched_nums=row[13],
            attack_cooldown_time=row[14],
            backpack_capacity=row[15],
            attack_protection_end_time=row[16]
        )
    return None

def save_user_items(user_qq: str, items: List[Item], conn: Optional[sqlite3.Connection] = None):
    """保存用户物品到数据库"""
    use_pool = conn is None
    if use_pool:
        conn = sqlite_pool.get_conn()
    
    cursor = conn.cursor()
    
    # 先删除旧的物品记录
    cursor.execute("DELETE FROM user_items WHERE user_qq = ?", (user_qq,))
    
    # 插入新的物品记录
    for item in items:
        cursor.execute("""
        INSERT INTO user_items (user_qq, item_id, item_name, item_value, item_quality)
        VALUES (?, ?, ?, ?, ?)
        """, (user_qq, item.id, item.name, item.value, item.quality))
    
    if use_pool:
        conn.commit()
        sqlite_pool.put_conn(conn)

def save_user_equipment(user_qq: str, equipment: List[Equipment], conn: Optional[sqlite3.Connection] = None):
    """保存用户装备到数据库"""
    use_pool = conn is None
    if use_pool:
        conn = sqlite_pool.get_conn()
    
    cursor = conn.cursor()
    
    # 先删除旧的装备记录
    cursor.execute("DELETE FROM user_equipment WHERE user_qq = ?", (user_qq,))
    
    # 插入新的装备记录
    for eq in equipment:
        cursor.execute("""
        INSERT INTO user_equipment (
            user_qq, item_id, item_name, item_value, item_quality, equipment_type,
            add_to_attack, add_to_defense, increase_attack, increase_defense,
            equip_luck, extra_search_time, extra_retreat_time, equip_attack_cooldown,
            extra_backpack_capacity, extra_attack_protection_duration
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_qq, eq.id, eq.name, eq.value, eq.quality, getattr(eq, 'equipment_type', 99),
            getattr(eq, 'add_to_attack', 0), getattr(eq, 'add_to_defense', 0),
            getattr(eq, 'increase_attack', 0), getattr(eq, 'increase_defense', 0),
            getattr(eq, 'equip_luck', 0), getattr(eq, 'extra_search_time', 0),
            getattr(eq, 'extra_retreat_time', 0), getattr(eq, 'equip_attack_cooldown', 0),
            getattr(eq, 'extra_backpack_capacity', 0), getattr(eq, 'extra_attack_protection_duration', 0)
        ))
    
    if use_pool:
        conn.commit()
        sqlite_pool.put_conn(conn)

def load_user_items(user_qq: str, conn: Optional[sqlite3.Connection] = None) -> List[Item]:
    """从数据库加载用户物品"""
    use_pool = conn is None
    if use_pool:
        conn = sqlite_pool.get_conn()
    
    cursor = conn.cursor()
    cursor.execute("SELECT item_id, item_name, item_value, item_quality FROM user_items WHERE user_qq = ?", (user_qq,))
    rows = cursor.fetchall()
    
    if use_pool:
        sqlite_pool.put_conn(conn)
    
    items = []
    for row in rows:
        items.append(Item(id=row[0], name=row[1], value=row[2], quality=row[3]))
    
    return items

def save_user_equipment_storage(user_qq: str, equipment_storage: List[Equipment], conn: Optional[sqlite3.Connection] = None):
    """保存用户装备仓库到数据库"""
    use_pool = conn is None
    if use_pool:
        conn = sqlite_pool.get_conn()
    
    cursor = conn.cursor()
    
    # 先删除旧的装备仓库记录
    cursor.execute("DELETE FROM user_equipment_storage WHERE user_qq = ?", (user_qq,))
    
    # 插入新的装备仓库记录
    for eq in equipment_storage:
        cursor.execute("""
        INSERT INTO user_equipment_storage (
            user_qq, item_id, item_name, item_value, item_quality, equipment_type,
            add_to_attack, add_to_defense, increase_attack, increase_defense,
            equip_luck, extra_search_time, extra_retreat_time, equip_attack_cooldown,
            extra_backpack_capacity, extra_attack_protection_duration
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_qq, eq.id, eq.name, eq.value, eq.quality, getattr(eq, 'equipment_type', 99),
            getattr(eq, 'add_to_attack', 0), getattr(eq, 'add_to_defense', 0),
            getattr(eq, 'increase_attack', 0), getattr(eq, 'increase_defense', 0),
            getattr(eq, 'equip_luck', 0), getattr(eq, 'extra_search_time', 0),
            getattr(eq, 'extra_retreat_time', 0), getattr(eq, 'equip_attack_cooldown', 0),
            getattr(eq, 'extra_backpack_capacity', 0), getattr(eq, 'extra_attack_protection_duration', 0)
        ))
    
    if use_pool:
        conn.commit()
        sqlite_pool.put_conn(conn)

def load_user_equipment(user_qq: str, conn: Optional[sqlite3.Connection] = None) -> List[Equipment]:
    """从数据库加载用户装备"""
    use_pool = conn is None
    if use_pool:
        conn = sqlite_pool.get_conn()
    
    cursor = conn.cursor()
    cursor.execute("""
    SELECT item_id, item_name, item_value, item_quality, equipment_type,
           add_to_attack, add_to_defense, increase_attack, increase_defense,
           equip_luck, extra_search_time, extra_retreat_time, equip_attack_cooldown,
           extra_backpack_capacity, extra_attack_protection_duration
    FROM user_equipment WHERE user_qq = ?
    """, (user_qq,))
    rows = cursor.fetchall()
    
    if use_pool:
        sqlite_pool.put_conn(conn)
    
    equipment = []
    for row in rows:
        equipment.append(Equipment(
            id=row[0],
            name=row[1],
            value=row[2],
            quality=row[3],
            equipment_type=row[4],
            add_to_attack=row[5],
            add_to_defense=row[6],
            increase_attack=row[7],
            increase_defense=row[8],
            equip_luck=row[9],
            extra_search_time=row[10],
            extra_retreat_time=row[11],
            equip_attack_cooldown=row[12],
            extra_backpack_capacity=row[13],
            extra_attack_protection_duration=row[14]
        ))
    
    return equipment

def load_user_equipment_storage(user_qq: str, conn: Optional[sqlite3.Connection] = None) -> List[Equipment]:
    """从数据库加载用户装备仓库"""
    use_pool = conn is None
    if use_pool:
        conn = sqlite_pool.get_conn()
    
    cursor = conn.cursor()
    cursor.execute("""
    SELECT item_id, item_name, item_value, item_quality, equipment_type,
           add_to_attack, add_to_defense, increase_attack, increase_defense,
           equip_luck, extra_search_time, extra_retreat_time, equip_attack_cooldown,
           extra_backpack_capacity, extra_attack_protection_duration
    FROM user_equipment_storage WHERE user_qq = ?
    """, (user_qq,))
    rows = cursor.fetchall()
    
    if use_pool:
        sqlite_pool.put_conn(conn)
    
    equipment_storage = []
    for row in rows:
        equipment_storage.append(Equipment(
            id=row[0],
            name=row[1],
            value=row[2],
            quality=row[3],
            equipment_type=row[4],
            add_to_attack=row[5],
            add_to_defense=row[6],
            increase_attack=row[7],
            increase_defense=row[8],
            equip_luck=row[9],
            extra_search_time=row[10],
            extra_retreat_time=row[11],
            equip_attack_cooldown=row[12],
            extra_backpack_capacity=row[13],
            extra_attack_protection_duration=row[14]
        ))
    
    return equipment_storage

def save_all(users_dict: Dict[str, User]):
    """保存所有用户、物品和装备数据到数据库"""
    conn = sqlite3.connect(db_path, timeout=db_timeout)
    try:
        for qq, user in users_dict.items():
            save_user(user, conn=conn)
            save_user_items(qq, user.inventory, conn=conn)
            save_user_equipment(qq, user.equipment, conn=conn)
            save_user_equipment_storage(qq, user.equipment_storage, conn=conn)
        conn.commit()
    finally:
        conn.close()

def load_all() -> Dict[str, User]:
    """从数据库加载所有用户、物品和装备数据"""
    users_dict = {}
    
    conn = sqlite3.connect(db_path, timeout=db_timeout)
    
    # 加载所有用户
    cursor = conn.cursor()
    cursor.execute("SELECT qq FROM users")
    user_qqs = [row[0] for row in cursor.fetchall()]
    cursor.close()  # 关闭查询用户列表的游标
    
    for qq in user_qqs:
        user = load_user(qq, conn=conn)
        if user:
            # 加载用户物品到inventory
            user.inventory = load_user_items(qq, conn=conn)
            # 加载用户装备到equipment
            equipment_list = load_user_equipment(qq, conn=conn)
            # 应用装备加成
            for eq in equipment_list:
                user.equip_item(eq)
            # 加载装备仓库到equipment_storage
            user.equipment_storage = load_user_equipment_storage(qq, conn=conn)
            users_dict[qq] = user
    
    conn.close()
    return users_dict