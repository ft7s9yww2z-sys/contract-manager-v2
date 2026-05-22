#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复脚本 - 修复所有问题
"""

import os
import re

# 读取主程序
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 修复导入验证 - 只要一个字段不为空即可
print("1. 修复导入验证...")
old_check = '''                    # 检查合同编号
                    if not data.get('合同编号'):
                        errors.append(f"第{row_idx}行: 合同编号为空")
                        fail_count += 1
                        continue'''

new_check = '''                    # 只要有一个字段不为空就可以导入
                    has_data = any(v is not None and str(v).strip() != '' for v in data.values())
                    if not has_data:
                        errors.append(f"第{row_idx}行: 所有字段都为空")
                        fail_count += 1
                        continue'''

content = content.replace(old_check, new_check)

# 2. 修复对话框导入
print("2. 修复对话框导入...")
old_import = "from views.dialogs import ContractDialog, InvoiceDialog, CollectionRecordDialog"
new_import = "from views.dialogs_fixed import ContractDialog, InvoiceDialog, CollectionRecordDialog"
content = content.replace(old_import, new_import)

# 3. 修复合同列表字段 - 补全所有29个字段
print("3. 修复合同列表字段...")
old_columns = """        self.contract_tree = ttk.Treeview(
            table_frame,
            columns=['合同编号', '合同名称', '对方单位', '区域', '销售负责人', '合同额', '签字日期', '到期日期', '状态'],
            show='headings',
            style='Custom.Treeview',
            selectmode='browse'
        )
        
        # 设置列
        columns_config = [
            ('合同编号', 120),
            ('合同名称', 200),
            ('对方单位', 150),
            ('区域', 100),
            ('销售负责人', 100),
            ('合同额', 100),
            ('签字日期', 110),
            ('到期日期', 110),
            ('状态', 80)
        ]"""

new_columns = """        # 合同列表显示所有29个字段
        columns = ['序号', '下单日期', '合同编号', '项目代码', '是否变更', '合同评审日期',
                  '合同签字日期', 'crm日期', '合同名称', '对方单位名称', '区域', '销售负责人',
                  '参考金额', '合同额', '联系人', '联系电话', '合同内容', '到款情况',
                  '合同起始日期', '合同终止日期', '开票日期', '开票金额', '开票余额',
                  '到款金额', '合同余额', '应收账款', '备注', '项目预算', '设备数量']
        
        self.contract_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            style='Custom.Treeview',
            selectmode='browse'
        )
        
        # 设置列
        for col in columns:
            self.contract_tree.heading(col, text=col, command=lambda c=col: self._sort_contract_tree(c))
            self.contract_tree.column(col, width=100, anchor='center')
        
        # 调整部分列宽
        self.contract_tree.column('合同名称', width=150)
        self.contract_tree.column('对方单位名称', width=150)
        self.contract_tree.column('合同内容', width=150)
        self.contract_tree.column('备注', width=150)"""

content = content.replace(old_columns, new_columns)

# 4. 修复更新合同表格方法
print("4. 修复更新合同表格方法...")
old_update = '''    def _update_contracts_table(self):
        """更新合同表格"""
        for item in self.contract_tree.get_children():
            self.contract_tree.delete(item)
        
        for contract in self.contracts_cache:
            days = get_days_until_deadline(contract.合同终止日期)
            level = get_warning_level(days)
            
            status_map = {
                'red': '已超期',
                'orange': '即将到期',
                'yellow': '需关注',
                'none': '正常'
            }
            status = status_map.get(level, '正常')
            
            self.contract_tree.insert('', 'end', values=(
                contract.合同编号,
                contract.合同名称 or '',
                contract.对方单位名称 or '',
                contract.区域 or '',
                contract.销售负责人 or '',
                safe_format_money(contract.合同额),
                contract.合同签字日期 or '',
                contract.合同终止日期 or '',
                status
            ))'''

new_update = '''    def _update_contracts_table(self):
        """更新合同表格"""
        for item in self.contract_tree.get_children():
            self.contract_tree.delete(item)
        
        # 应用分页
        start_idx = (self.current_page - 1) * self.page_size
        end_idx = start_idx + self.page_size
        page_contracts = self.contracts_cache[start_idx:end_idx]
        
        for contract in page_contracts:
            self.contract_tree.insert('', 'end', values=(
                contract.序号 or '',
                contract.下单日期 or '',
                contract.合同编号,
                contract.项目代码 or '',
                contract.是否变更 or '',
                contract.合同评审日期 or '',
                contract.合同签字日期 or '',
                contract.crm日期 or '',
                contract.合同名称 or '',
                contract.对方单位名称 or '',
                contract.区域 or '',
                contract.销售负责人 or '',
                safe_format_money(contract.参考金额),
                safe_format_money(contract.合同额),
                contract.联系人 or '',
                contract.联系电话 or '',
                contract.合同内容 or '',
                contract.到款情况 or '',
                contract.合同起始日期 or '',
                contract.合同终止日期 or '',
                contract.开票日期 or '',
                safe_format_money(contract.开票金额),
                safe_format_money(contract.开票余额),
                safe_format_money(contract.到款金额),
                safe_format_money(contract.合同余额),
                safe_format_money(contract.应收账款),
                contract.备注 or '',
                safe_format_money(contract.项目预算),
                contract.设备数量 or ''
            ))'''

content = content.replace(old_update, new_update)

# 5. 添加分页功能
print("5. 添加分页功能...")
# 在 __init__ 方法中添加分页变量
init_pattern = r'(self\.invoices_cache: List\[Invoice\] = \[\])'
init_replacement = r'\1\n        \n        # 分页相关\n        self.current_page = 1\n        self.page_size = 50\n        self.total_pages = 1'
content = re.sub(init_pattern, init_replacement, content)

# 6. 添加应收账款搜索功能
print("6. 添加应收账款搜索功能...")
old_receivable = '''        # 应收账款列表
        table_frame = ctk.CTkFrame(self.content_area, fg_color='white', corner_radius=10)
        table_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))'''

new_receivable = '''        # 搜索栏
        search_frame = ctk.CTkFrame(self.content_area, fg_color='white', corner_radius=10)
        search_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        search_inner = ctk.CTkFrame(search_frame, fg_color='transparent')
        search_inner.pack(fill='x', padx=15, pady=15)
        
        self.receivable_search_entry = ctk.CTkEntry(
            search_inner,
            placeholder_text="搜索合同编号、对方单位...",
            width=300
        )
        self.receivable_search_entry.pack(side='left')
        self.receivable_search_entry.bind('<KeyRelease>', lambda e: self._search_receivables())
        
        # 应收账款列表
        table_frame = ctk.CTkFrame(self.content_area, fg_color='white', corner_radius=10)
        table_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))'''

content = content.replace(old_receivable, new_receivable)

# 7. 添加搜索应收账款方法
print("7. 添加搜索应收账款方法...")
# 在文件末尾添加新方法
new_method = '''
    def _search_receivables(self):
        """搜索应收账款"""
        search_text = self.receivable_search_entry.get().lower()
        
        for item in self.receivable_tree.get_children():
            self.receivable_tree.delete(item)
        
        for contract in self.contracts_cache:
            if contract.应收账款 and contract.应收账款 > 0:
                # 搜索过滤
                if search_text:
                    if search_text not in contract.合同编号.lower() and \\
                       search_text not in (contract.对方单位名称 or '').lower():
                        continue
                
                self.receivable_tree.insert('', 'end', values=(
                    contract.合同编号,
                    contract.对方单位名称 or '',
                    safe_format_money(contract.合同额),
                    safe_format_money(contract.到款金额),
                    safe_format_money(contract.应收账款),
                    contract.销售负责人 or '',
                    contract.催款状态 or '未催款'
                ))
'''

# 在文件末尾的 main() 函数前添加
content = content.replace('def main():', new_method + '\ndef main():')

# 8. 添加分页控件
print("8. 添加分页控件...")
# 在统计信息栏后添加分页控件
old_stats = '''        # 统计信息栏
        stats_frame = ctk.CTkFrame(self.content_area, fg_color='white', corner_radius=10, height=60)
        stats_frame.pack(fill='x', padx=20, pady=(0, 20))
        stats_frame.pack_propagate(False)
        
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="共 0 条记录，总金额: ¥0.00",
            font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=UI_CONFIG['font_size']['normal']),
            text_color='#7f8c8d'
        )
        self.stats_label.pack(pady=18)'''

new_stats = '''        # 统计信息栏和分页控件
        stats_frame = ctk.CTkFrame(self.content_area, fg_color='white', corner_radius=10, height=60)
        stats_frame.pack(fill='x', padx=20, pady=(0, 20))
        stats_frame.pack_propagate(False)
        
        # 左侧统计信息
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="共 0 条记录，总金额: ¥0.00",
            font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=UI_CONFIG['font_size']['normal']),
            text_color='#7f8c8d'
        )
        self.stats_label.pack(side='left', pady=18, padx=20)
        
        # 右侧分页控件
        page_frame = ctk.CTkFrame(stats_frame, fg_color='transparent')
        page_frame.pack(side='right', pady=10, padx=20)
        
        ctk.CTkLabel(page_frame, text="每页显示:", font=ctk.CTkFont(size=12)).pack(side='left', padx=5)
        
        self.page_size_combo = ctk.CTkComboBox(
            page_frame,
            values=['10', '50', '100'],
            width=80,
            command=self._change_page_size
        )
        self.page_size_combo.set('50')
        self.page_size_combo.pack(side='left', padx=5)
        
        ModernButton(page_frame, "上一页", command=self._prev_page, style='secondary').pack(side='left', padx=5)
        
        self.page_label = ctk.CTkLabel(page_frame, text="第 1/1 页", font=ctk.CTkFont(size=12))
        self.page_label.pack(side='left', padx=10)
        
        ModernButton(page_frame, "下一页", command=self._next_page, style='secondary').pack(side='left', padx=5)'''

content = content.replace(old_stats, new_stats)

# 9. 添加分页方法
print("9. 添加分页方法...")
pagination_methods = '''
    def _change_page_size(self, value):
        """改变每页显示数量"""
        self.page_size = int(value)
        self.current_page = 1
        self._update_contracts_table()
        self._update_page_label()
    
    def _prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self._update_contracts_table()
            self._update_page_label()
    
    def _next_page(self):
        """下一页"""
        if self.current_page < self.total_pages:
            self.current_page += 1
            self._update_contracts_table()
            self._update_page_label()
    
    def _update_page_label(self):
        """更新页码标签"""
        self.total_pages = max(1, (len(self.contracts_cache) + self.page_size - 1) // self.page_size)
        self.page_label.configure(text=f"第 {self.current_page}/{self.total_pages} 页")
        total_amount = sum(c.合同额 or 0 for c in self.contracts_cache)
        self.stats_label.configure(
            text=f"共 {len(self.contracts_cache)} 条记录，总金额: ¥{safe_format_money(total_amount)}"
        )
'''

content = content.replace('def _search_receivables(self):', pagination_methods + '\n    def _search_receivables(self):')

# 保存修复后的文件
print("\n保存修复后的文件...")
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✓ 所有修复已完成！")
print("\n修复内容：")
print("1. ✓ 导入验证：只要一个字段不为空即可导入")
print("2. ✓ 对话框导入：使用修复版对话框")
print("3. ✓ 合同列表字段：补全所有29个字段")
print("4. ✓ 更新合同表格：显示所有字段")
print("5. ✓ 分页功能：添加分页变量")
print("6. ✓ 应收账款搜索：添加搜索框")
print("7. ✓ 搜索应收账款方法：实现搜索功能")
print("8. ✓ 分页控件：添加分页UI")
print("9. ✓ 分页方法：实现分页逻辑")
print("\n数据持久化：SQLite 数据库已确保数据持久保存")
