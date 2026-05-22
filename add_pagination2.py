#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为预警和应收账款列表添加分页功能
"""

import re

file_path = 'main.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 在预警列表中添加分页控件
old_warning_end = '''        self.warning_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 加载数据
        self._update_warnings_table(warning_data)'''

new_warning_end = '''        self.warning_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 分页控件
        page_frame = ctk.CTkFrame(self.content_area, fg_color='white', corner_radius=10, height=50)
        page_frame.pack(fill='x', padx=20, pady=(0, 20))
        page_frame.pack_propagate(False)
        
        # 左侧统计信息
        self.warning_stats_label = ctk.CTkLabel(
            page_frame,
            text="共 0 条记录",
            font=ctk.CTkFont(size=12),
            text_color='#7f8c8d'
        )
        self.warning_stats_label.pack(side='left', pady=13, padx=20)
        
        # 右侧分页控件
        warning_page_frame = ctk.CTkFrame(page_frame, fg_color='transparent')
        warning_page_frame.pack(side='right', pady=10, padx=20)
        
        ModernButton(warning_page_frame, "上一页", command=self._prev_warning_page, style='secondary').pack(side='left', padx=5)
        
        self.warning_page_label = ctk.CTkLabel(warning_page_frame, text="第 1/1 页", font=ctk.CTkFont(size=12))
        self.warning_page_label.pack(side='left', padx=10)
        
        ModernButton(warning_page_frame, "下一页", command=self._next_warning_page, style='secondary').pack(side='left', padx=5)
        
        # 保存预警数据到缓存
        self.warning_cache = warning_data
        
        # 加载数据
        self._update_warnings_table(warning_data)'''

content = content.replace(old_warning_end, new_warning_end)

# 2. 修改 _update_warnings_table 方法，添加分页
old_update_warnings = '''    def _update_warnings_table(self, warning_data: List[Dict]):
        """更新预警表格"""
        for item in self.warning_tree.get_children():
            self.warning_tree.delete(item)
        
        for item in warning_data:'''

new_update_warnings = '''    def _update_warnings_table(self, warning_data: List[Dict]):
        """更新预警表格"""
        for item in self.warning_tree.get_children():
            self.warning_tree.delete(item)
        
        # 应用分页
        start_idx = (self.warning_page - 1) * self.warning_page_size
        end_idx = start_idx + self.warning_page_size
        page_data = warning_data[start_idx:end_idx]
        
        for item in page_data:'''

content = content.replace(old_update_warnings, new_update_warnings)

# 3. 在 _update_warnings_table 方法末尾添加分页信息更新
old_warnings_end = '''            self.warning_tree.insert('', 'end', values=(
                contract.合同编号,
                contract.合同名称 or '',
                contract.对方单位名称 or '',
                contract.区域 or '',
                contract.销售负责人 or '',
                safe_format_money(contract.合同额),
                contract.合同终止日期 or '',
                f"{days} 天" if days >= 0 else f"超期 {abs(days)} 天",
                safe_format_money(contract.开票金额),
                safe_format_money(contract.到款金额),
                safe_format_money(contract.应收账款)
            ), tags=(tag,))'''

new_warnings_end = '''            self.warning_tree.insert('', 'end', values=(
                contract.合同编号,
                contract.合同名称 or '',
                contract.对方单位名称 or '',
                contract.区域 or '',
                contract.销售负责人 or '',
                safe_format_money(contract.合同额),
                contract.合同终止日期 or '',
                f"{days} 天" if days >= 0 else f"超期 {abs(days)} 天",
                safe_format_money(contract.开票金额),
                safe_format_money(contract.到款金额),
                safe_format_money(contract.应收账款)
            ), tags=(tag,))
        
        # 更新分页信息
        total = len(warning_data)
        self.warning_total_pages = max(1, (total + self.warning_page_size - 1) // self.warning_page_size)
        
        if hasattr(self, 'warning_stats_label'):
            self.warning_stats_label.configure(text=f"共 {total} 条记录")
            self.warning_page_label.configure(text=f"第 {self.warning_page}/{self.warning_total_pages} 页")'''

content = content.replace(old_warnings_end, new_warnings_end)

# 4. 修改 _filter_warnings 方法，使用缓存
old_filter_warnings = '''    def _filter_warnings(self):
        """筛选预警数据"""
        warning_data = self.contract_service.get_warning_contracts()
        
        # 按级别过滤
        level_filter = self.warning_filter.get()
        if level_filter != '全部':
            warning_data = [w for w in warning_data if w['level'] == level_filter]
        
        # 按搜索词过滤
        search_text = self.warning_search_entry.get().lower()
        if search_text:
            warning_data = [
                w for w in warning_data
                if search_text in w['contract'].合同编号.lower()
                or search_text in (w['contract'].合同名称 or '').lower()
            ]
        
        self._update_warnings_table(warning_data)'''

new_filter_warnings = '''    def _filter_warnings(self):
        """筛选预警数据"""
        warning_data = self.contract_service.get_warning_contracts()
        
        # 按级别过滤
        level_filter = self.warning_filter.get()
        if level_filter != '全部':
            warning_data = [w for w in warning_data if w['level'] == level_filter]
        
        # 按搜索词过滤
        search_text = self.warning_search_entry.get().lower()
        if search_text:
            warning_data = [
                w for w in warning_data
                if search_text in w['contract'].合同编号.lower()
                or search_text in (w['contract'].合同名称 or '').lower()
            ]
        
        # 保存过滤后的数据
        self.warning_cache = warning_data
        self.warning_page = 1  # 重置页码
        self._update_warnings_table(warning_data)
    
    def _prev_warning_page(self):
        """预警列表上一页"""
        if self.warning_page > 1:
            self.warning_page -= 1
            self._update_warnings_table(self.warning_cache)
    
    def _next_warning_page(self):
        """预警列表下一页"""
        if self.warning_page < self.warning_total_pages:
            self.warning_page += 1
            self._update_warnings_table(self.warning_cache)'''

content = content.replace(old_filter_warnings, new_filter_warnings)

# 5. 在应收账款列表中添加分页控件
old_receivable_end = '''        self.receivable_tree.bind('<Double-1>', lambda e: self._show_collection_dialog())
        self.receivable_tree.bind('<Button-3>', self._show_receivable_context_menu)
        
        # 加载数据
        self._update_receivables_table()'''

new_receivable_end = '''        self.receivable_tree.bind('<Double-1>', lambda e: self._show_collection_dialog())
        self.receivable_tree.bind('<Button-3>', self._show_receivable_context_menu)
        
        # 分页控件
        page_frame = ctk.CTkFrame(self.content_area, fg_color='white', corner_radius=10, height=50)
        page_frame.pack(fill='x', padx=20, pady=(0, 20))
        page_frame.pack_propagate(False)
        
        # 左侧统计信息
        self.receivable_stats_label = ctk.CTkLabel(
            page_frame,
            text="共 0 条记录",
            font=ctk.CTkFont(size=12),
            text_color='#7f8c8d'
        )
        self.receivable_stats_label.pack(side='left', pady=13, padx=20)
        
        # 右侧分页控件
        receivable_page_frame = ctk.CTkFrame(page_frame, fg_color='transparent')
        receivable_page_frame.pack(side='right', pady=10, padx=20)
        
        ModernButton(receivable_page_frame, "上一页", command=self._prev_receivable_page, style='secondary').pack(side='left', padx=5)
        
        self.receivable_page_label = ctk.CTkLabel(receivable_page_frame, text="第 1/1 页", font=ctk.CTkFont(size=12))
        self.receivable_page_label.pack(side='left', padx=10)
        
        ModernButton(receivable_page_frame, "下一页", command=self._next_receivable_page, style='secondary').pack(side='left', padx=5)
        
        # 加载数据
        self._update_receivables_table()'''

content = content.replace(old_receivable_end, new_receivable_end)

# 6. 修改 _update_receivables_table 方法，添加分页
old_update_receivables = '''    def _update_receivables_table(self):
        """更新应收账款表格"""
        for item in self.receivable_tree.get_children():
            self.receivable_tree.delete(item)
        
        for contract in self.contracts_cache:
            if contract.应收账款 and contract.应收账款 > 0:'''

new_update_receivables = '''    def _update_receivables_table(self):
        """更新应收账款表格"""
        for item in self.receivable_tree.get_children():
            self.receivable_tree.delete(item)
        
        # 筛选有应收账款的合同
        receivable_contracts = [c for c in self.contracts_cache if c.应收账款 and c.应收账款 > 0]
        
        # 应用分页
        start_idx = (self.receivable_page - 1) * self.receivable_page_size
        end_idx = start_idx + self.receivable_page_size
        page_contracts = receivable_contracts[start_idx:end_idx]
        
        for contract in page_contracts:'''

content = content.replace(old_update_receivables, new_update_receivables)

# 7. 在 _update_receivables_table 方法末尾添加分页信息更新
old_receivables_end = '''                self.receivable_tree.insert('', 'end', values=(
                    contract.合同编号,
                    contract.对方单位名称 or '',
                    safe_format_money(contract.合同额),
                    safe_format_money(contract.到款金额),
                    safe_format_money(contract.应收账款),
                    contract.销售负责人 or '',
                    contract.催款状态 or '未催款'
                ))'''

new_receivables_end = '''                self.receivable_tree.insert('', 'end', values=(
                    contract.合同编号,
                    contract.对方单位名称 or '',
                    safe_format_money(contract.合同额),
                    safe_format_money(contract.到款金额),
                    safe_format_money(contract.应收账款),
                    contract.销售负责人 or '',
                    contract.催款状态 or '未催款'
                ))
        
        # 更新分页信息
        total = len(receivable_contracts)
        self.receivable_total_pages = max(1, (total + self.receivable_page_size - 1) // self.receivable_page_size)
        
        if hasattr(self, 'receivable_stats_label'):
            self.receivable_stats_label.configure(text=f"共 {total} 条记录")
            self.receivable_page_label.configure(text=f"第 {self.receivable_page}/{self.receivable_total_pages} 页")
    
    def _prev_receivable_page(self):
        """应收账款列表上一页"""
        if self.receivable_page > 1:
            self.receivable_page -= 1
            self._update_receivables_table()
    
    def _next_receivable_page(self):
        """应收账款列表下一页"""
        if self.receivable_page < self.receivable_total_pages:
            self.receivable_page += 1
            self._update_receivables_table()'''

content = content.replace(old_receivables_end, new_receivables_end)

# 8. 修改 _search_receivables 方法，添加分页支持
old_search_receivables = '''    def _search_receivables(self):
        """搜索应收账款"""
        keyword = self.receivable_search_entry.get().strip()
        
        for item in self.receivable_tree.get_children():
            self.receivable_tree.delete(item)
        
        for contract in self.contracts_cache:
            if contract.应收账款 and contract.应收账款 > 0:
                if keyword in contract.合同编号 or keyword in (contract.对方单位名称 or ''):
                    self.receivable_tree.insert('', 'end', values=(
                        contract.合同编号,
                        contract.对方单位名称 or '',
                        safe_format_money(contract.合同额),
                        safe_format_money(contract.到款金额),
                        safe_format_money(contract.应收账款),
                        contract.销售负责人 or '',
                        contract.催款状态 or '未催款'
                    ))'''

new_search_receivables = '''    def _search_receivables(self):
        """搜索应收账款"""
        keyword = self.receivable_search_entry.get().strip()
        
        # 筛选有应收账款的合同
        receivable_contracts = [c for c in self.contracts_cache if c.应收账款 and c.应收账款 > 0]
        
        if keyword:
            filtered = [
                c for c in receivable_contracts
                if keyword in c.合同编号 or keyword in (c.对方单位名称 or '')
            ]
            
            # 临时显示搜索结果（不分页）
            for item in self.receivable_tree.get_children():
                self.receivable_tree.delete(item)
            
            for contract in filtered:
                self.receivable_tree.insert('', 'end', values=(
                    contract.合同编号,
                    contract.对方单位名称 or '',
                    safe_format_money(contract.合同额),
                    safe_format_money(contract.到款金额),
                    safe_format_money(contract.应收账款),
                    contract.销售负责人 or '',
                    contract.催款状态 or '未催款'
                ))
            
            # 更新统计信息
            if hasattr(self, 'receivable_stats_label'):
                self.receivable_stats_label.configure(text=f"共 {len(filtered)} 条记录（搜索结果）")
        else:
            # 恢复分页显示
            self.receivable_page = 1
            self._update_receivables_table()'''

content = content.replace(old_search_receivables, new_search_receivables)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ 已为预警列表添加分页功能")
print("✓ 已为应收账款列表添加分页功能")
