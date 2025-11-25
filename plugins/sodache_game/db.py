import sqlite3
from typing import Dict, List, Optional
from .models.game_models import User, Item
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
        gold INTEGER DEFAULT 100,
        status INTEGER DEFAULT 0,
        search_start_time INTEGER DEFAULT 0,
        attack_cooldown_start INTEGER DEFAULT 0,
        retreat_start_time INTEGER DEFAULT 0,
        search_group TEXT DEFAULT '',
        user_bag_items_nums INTEGER DEFAULT 0,
        have_searched_nums INTEGER DEFAULT 0,
        attack_cooldown_end_time INTEGER DEFAULT 0,
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
        qq, attack, defense, luck, speed, gold, status, search_start_time,
        attack_cooldown_start, retreat_start_time, search_group, user_bag_items_nums, have_searched_nums, attack_cooldown_end_time, backpack_capacity, attack_protection_end_time
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user.qq, user.attack, user.defense, user.luck, user.speed, user.gold, user.status,
        user.search_start_time, user.attack_cooldown_start, user.retreat_start_time, user.search_group,
        user.user_bag_items_nums, user.have_searched_nums, user.attack_cooldown_end_time, user.backpack_capacity, user.attack_protection_end_time
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
            gold=row[5],
            status=row[6],
            search_start_time=row[7],

            # 已弃用
            attack_cooldown_start=row[8],

            retreat_start_time=row[9],
            search_group=row[10],
            user_bag_items_nums=row[11],
            
            # 已弃用
            have_searched_nums=row[12],

            attack_cooldown_end_time=row[13],
            backpack_capacity=row[14],
            attack_protection_end_time=row[15]
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

def save_all(users_dict: Dict[str, User]):
    """保存所有用户和物品数据到数据库"""
    conn = sqlite3.connect(db_path, timeout=db_timeout)
    try:
        for qq, user in users_dict.items():
            save_user(user, conn=conn)
            save_user_items(qq, user.inventory, conn=conn)
        conn.commit()
    finally:
        conn.close()

def load_all() -> Dict[str, User]:
    """从数据库加载所有用户和物品数据"""
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
            users_dict[qq] = user
    
    conn.close()
    return users_dict