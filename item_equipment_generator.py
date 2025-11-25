"""
物品和装备生成器 - 带可视化界面
用于生成 Item 和 Equipment 实例并自动添加到数据文件中
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import re
from pathlib import Path


class ItemEquipmentGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("物品/装备生成器")
        self.root.geometry("900x700")
        
        # 定义装备类型映射
        self.equipment_types = {
            "武器 (WEAPON)": 0,
            "防具 (ARMOR)": 1,
            "背包 (BACKPACK)": 2,
            "饰品 (ACCESSORY)": 3,
            "其他 (OTHER)": 99
        }
        
        # 定义品质映射
        self.quality_map = {
            "普通": 0,
            "稀有": 1,
            "史诗": 2,
            "传说": 3
        }
        
        self.create_widgets()
    
    def create_widgets(self):
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ==================== 基本信息区域 ====================
        basic_frame = ttk.LabelFrame(main_frame, text="基本信息", padding="10")
        basic_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # ID
        ttk.Label(basic_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.id_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.id_var, width=40).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # 名称
        ttk.Label(basic_frame, text="名称:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.name_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.name_var, width=40).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # 价值
        ttk.Label(basic_frame, text="价值:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.value_var = tk.IntVar(value=10)
        ttk.Entry(basic_frame, textvariable=self.value_var, width=40).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # 品质
        ttk.Label(basic_frame, text="品质:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.quality_var = tk.StringVar(value="普通")
        quality_combo = ttk.Combobox(basic_frame, textvariable=self.quality_var, 
                                      values=list(self.quality_map.keys()), width=37, state="readonly")
        quality_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # 权重
        ttk.Label(basic_frame, text="权重:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.weight_var = tk.IntVar(value=10)
        ttk.Entry(basic_frame, textvariable=self.weight_var, width=40).grid(row=4, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # ==================== 类型选择 ====================
        type_frame = ttk.LabelFrame(main_frame, text="生成类型", padding="10")
        type_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.is_equipment = tk.BooleanVar(value=False)
        ttk.Radiobutton(type_frame, text="普通物品 (Item)", variable=self.is_equipment, 
                       value=False, command=self.toggle_equipment_fields).grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Radiobutton(type_frame, text="装备 (Equipment)", variable=self.is_equipment, 
                       value=True, command=self.toggle_equipment_fields).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # ==================== 装备专属字段 ====================
        self.equipment_frame = ttk.LabelFrame(main_frame, text="装备属性", padding="10")
        self.equipment_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 装备类型
        ttk.Label(self.equipment_frame, text="装备类型:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.equipment_type_var = tk.StringVar(value="武器 (WEAPON)")
        equipment_type_combo = ttk.Combobox(self.equipment_frame, textvariable=self.equipment_type_var,
                                           values=list(self.equipment_types.keys()), width=37, state="readonly")
        equipment_type_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # 攻击力相关
        ttk.Label(self.equipment_frame, text="直接增加攻击力:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.add_to_attack_var = tk.IntVar(value=0)
        ttk.Entry(self.equipment_frame, textvariable=self.add_to_attack_var, width=40).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(self.equipment_frame, text="提高攻击力百分比:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.increase_attack_var = tk.IntVar(value=0)
        ttk.Entry(self.equipment_frame, textvariable=self.increase_attack_var, width=40).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # 防御力相关
        ttk.Label(self.equipment_frame, text="直接增加防御力:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.add_to_defense_var = tk.IntVar(value=0)
        ttk.Entry(self.equipment_frame, textvariable=self.add_to_defense_var, width=40).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(self.equipment_frame, text="提高防御力百分比:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.increase_defense_var = tk.IntVar(value=0)
        ttk.Entry(self.equipment_frame, textvariable=self.increase_defense_var, width=40).grid(row=4, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # 其他属性
        ttk.Label(self.equipment_frame, text="幸运值:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.equip_luck_var = tk.IntVar(value=0)
        ttk.Entry(self.equipment_frame, textvariable=self.equip_luck_var, width=40).grid(row=5, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(self.equipment_frame, text="搜索速度:").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.extra_search_speed_var = tk.IntVar(value=0)
        ttk.Entry(self.equipment_frame, textvariable=self.extra_search_speed_var, width=40).grid(row=6, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(self.equipment_frame, text="撤退时间(秒):").grid(row=7, column=0, sticky=tk.W, pady=2)
        self.extra_retreat_time_var = tk.IntVar(value=0)
        ttk.Entry(self.equipment_frame, textvariable=self.extra_retreat_time_var, width=40).grid(row=7, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(self.equipment_frame, text="攻击冷却时间(秒):").grid(row=8, column=0, sticky=tk.W, pady=2)
        self.equip_attack_cooldown_var = tk.IntVar(value=0)
        ttk.Entry(self.equipment_frame, textvariable=self.equip_attack_cooldown_var, width=40).grid(row=8, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(self.equipment_frame, text="背包空间:").grid(row=9, column=0, sticky=tk.W, pady=2)
        self.extra_backpack_capacity_var = tk.IntVar(value=0)
        ttk.Entry(self.equipment_frame, textvariable=self.extra_backpack_capacity_var, width=40).grid(row=9, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(self.equipment_frame, text="保护时长(秒):").grid(row=10, column=0, sticky=tk.W, pady=2)
        self.extra_attack_protection_duration_var = tk.IntVar(value=0)
        ttk.Entry(self.equipment_frame, textvariable=self.extra_attack_protection_duration_var, width=40).grid(row=10, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # 初始状态禁用装备字段
        self.toggle_equipment_fields()
        
        # ==================== 预览和生成按钮 ====================
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="预览代码", command=self.preview_code).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="生成并添加到文件", command=self.generate_and_save).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="清空表单", command=self.clear_form).grid(row=0, column=2, padx=5)
        
        # ==================== 预览区域 ====================
        preview_frame = ttk.LabelFrame(main_frame, text="代码预览", padding="10")
        preview_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, width=80, height=10, wrap=tk.WORD)
        self.preview_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
    
    def toggle_equipment_fields(self):
        """切换装备字段的启用/禁用状态"""
        state = 'normal' if self.is_equipment.get() else 'disabled'
        for child in self.equipment_frame.winfo_children():
            if isinstance(child, (ttk.Entry, ttk.Combobox)):
                child.configure(state=state)
    
    def validate_fields(self):
        """验证必填字段"""
        if not self.id_var.get().strip():
            messagebox.showerror("错误", "ID 不能为空！")
            return False
        if not self.name_var.get().strip():
            messagebox.showerror("错误", "名称不能为空！")
            return False
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', self.id_var.get()):
            messagebox.showerror("错误", "ID 必须是有效的标识符（字母、数字、下划线，且不能以数字开头）！")
            return False
        return True
    
    def generate_code(self):
        """生成代码字符串"""
        if not self.validate_fields():
            return None
        
        item_id = self.id_var.get().strip()
        name = self.name_var.get().strip()
        value = self.value_var.get()
        quality = self.quality_map[self.quality_var.get()]
        weight = self.weight_var.get()
        
        if self.is_equipment.get():
            # 生成装备代码
            equipment_type = self.equipment_types[self.equipment_type_var.get()]
            
            # 构建参数列表，只包含非默认值的参数
            params = []
            params.append(f'id="{item_id}"')
            params.append(f'name="{name}"')
            params.append(f'value={value}')
            
            # quality默认为0，只有非0时才添加
            if quality != 0:
                params.append(f'quality={quality}')
            
            # equipment_type默认为99，只有非99时才添加
            if equipment_type != 99:
                # 使用EquipmentType常量名称
                type_const_map = {
                    0: "EQUIPMENT_TYPE_WEAPON",
                    1: "EQUIPMENT_TYPE_ARMOR",
                    2: "EQUIPMENT_TYPE_BACKPACK",
                    3: "EQUIPMENT_TYPE_ACCESSORY",
                    99: "EQUIPMENT_TYPE_OTHER"
                }
                params.append(f'equipment_type={type_const_map[equipment_type]}')
            
            # 只添加非0的装备属性
            if self.add_to_attack_var.get() != 0:
                params.append(f'add_to_attack={self.add_to_attack_var.get()}')
            if self.increase_attack_var.get() != 0:
                params.append(f'increase_attack={self.increase_attack_var.get()}')
            if self.add_to_defense_var.get() != 0:
                params.append(f'add_to_defense={self.add_to_defense_var.get()}')
            if self.increase_defense_var.get() != 0:
                params.append(f'increase_defense={self.increase_defense_var.get()}')
            if self.equip_luck_var.get() != 0:
                params.append(f'equip_luck={self.equip_luck_var.get()}')
            if self.extra_search_speed_var.get() != 0:
                params.append(f'extra_search_speed={self.extra_search_speed_var.get()}')
            if self.extra_retreat_time_var.get() != 0:
                params.append(f'extra_retreat_time={self.extra_retreat_time_var.get()}')
            if self.equip_attack_cooldown_var.get() != 0:
                params.append(f'equip_attack_cooldown={self.equip_attack_cooldown_var.get()}')
            if self.extra_backpack_capacity_var.get() != 0:
                params.append(f'extra_backpack_capacity={self.extra_backpack_capacity_var.get()}')
            if self.extra_attack_protection_duration_var.get() != 0:
                params.append(f'extra_attack_protection_duration={self.extra_attack_protection_duration_var.get()}')
            
            # weight默认为1，只有非1时才添加
            if weight != 1:
                params.append(f'weight={weight}')
            
            # 组合成代码
            code = 'Equipment(\n'
            code += ',\n'.join(f'    {param}' for param in params)
            code += '\n),'
            
            return ('equipment', quality, code)
        else:
            # 生成物品代码
            params = []
            params.append(f'id="{item_id}"')
            params.append(f'name="{name}"')
            params.append(f'value={value}')
            
            # quality默认为0，只有非0时才添加
            if quality != 0:
                params.append(f'quality={quality}')
            
            # weight默认为1，只有非1时才添加
            if weight != 1:
                params.append(f'weight={weight}')
            
            code = f'Item({", ".join(params)}),'
            return ('item', quality, code)
    
    def preview_code(self):
        """预览生成的代码"""
        result = self.generate_code()
        if result:
            item_type, quality, code = result
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, f"# 类型: {item_type.upper()}\n# 品质: {quality}\n\n{code}")
        else:
            # 如果生成失败，清空预览区域
            self.preview_text.delete(1.0, tk.END)
    
    def generate_and_save(self):
        """生成代码并添加到相应的数据文件"""
        result = self.generate_code()
        if not result:
            return
        
        item_type, quality, code = result
        
        # 确定文件路径和变量名
        if item_type == 'equipment':
            file_path = Path(__file__).parent / "plugins" / "sodache_game" / "equipment_data.py"
            # 根据装备类型确定列表名
            equipment_type = self.equipment_types[self.equipment_type_var.get()]
            type_to_list = {
                0: "weapons",           # 武器
                1: "armors",            # 防具
                2: "backpacks",         # 背包
                3: "accessories",       # 饰品
                99: "other_equipment"   # 其他
            }
            list_name = type_to_list[equipment_type]
            list_pattern = rf'{list_name}:\s*List\[Equipment\]\s*=\s*\['
        else:
            file_path = Path(__file__).parent / "plugins" / "sodache_game" / "item_data.py"
            quality_names = {0: "common", 1: "rare", 2: "epic", 3: "legendary"}
            list_name = f"{quality_names[quality]}_items"
            list_pattern = rf'{list_name}\s*=\s*\['
        
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找对应的列表
            match = re.search(list_pattern, content)
            if not match:
                messagebox.showerror("错误", f"无法在文件中找到 {list_name} 列表！")
                return
            
            # 找到列表的结束位置
            start_pos = match.end()
            bracket_count = 1
            pos = start_pos
            
            while bracket_count > 0 and pos < len(content):
                if content[pos] == '[':
                    bracket_count += 1
                elif content[pos] == ']':
                    bracket_count -= 1
                pos += 1
            
            if bracket_count != 0:
                messagebox.showerror("错误", "列表格式错误！")
                return
            
            insert_pos = pos - 1  # 在 ] 之前插入
            
            # 获取列表内容
            list_content = content[start_pos:insert_pos]
            
            # 检查列表是否只包含注释（空列表）
            # 移除所有注释和空白，看是否还有实际代码
            lines = list_content.split('\n')
            has_actual_code = False
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    has_actual_code = True
                    break
            
            if has_actual_code:
                # 列表有实际内容，在末尾添加
                new_content = content[:insert_pos] + f"\n    {code}\n" + content[insert_pos:]
            else:
                # 列表为空（只有注释），清空注释并添加代码
                new_content = content[:start_pos] + f"\n    {code}\n" + content[insert_pos:]
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            messagebox.showinfo("成功", f"已成功添加到 {file_path.name} 的 {list_name} 列表中！")
            self.clear_form()
            
        except FileNotFoundError:
            messagebox.showerror("错误", f"找不到文件: {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def clear_form(self):
        """清空表单"""
        self.id_var.set("")
        self.name_var.set("")
        self.value_var.set(10)
        self.quality_var.set("普通")
        self.weight_var.set(10)
        self.is_equipment.set(False)
        self.equipment_type_var.set("武器 (WEAPON)")
        self.add_to_attack_var.set(0)
        self.increase_attack_var.set(0)
        self.add_to_defense_var.set(0)
        self.increase_defense_var.set(0)
        self.equip_luck_var.set(0)
        self.extra_search_speed_var.set(0)
        self.extra_retreat_time_var.set(0)
        self.equip_attack_cooldown_var.set(0)
        self.extra_backpack_capacity_var.set(0)
        self.extra_attack_protection_duration_var.set(0)
        self.preview_text.delete(1.0, tk.END)
        self.toggle_equipment_fields()


def main():
    root = tk.Tk()
    app = ItemEquipmentGenerator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
