#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为发票、预警、应收账款列表添加分页功能
"""

import re

file_path = 'main.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 在初始化方法中添加发票和预警的分页变量
old_init = '''        # 分页相关
        self.current_page = 1
        self.page_size = 50
        self.total_pages = 1'''

new_init = '''        # 分页相关 - 合同列表
        self.current_page = 1
        self.page_size = 50
        self.total_pages = 1
        
        # 发票列表分页
        self.invoice_page = 1
        self.invoice_page_size = 50
        self.invoice_total_pages = 1
        
        # 预警列表分页
        self.warning_page = 1
        self.warning_page_size = 50
        self.warning_total_pages = 1
        
        # 应收账款列表分页
        self.receivable_page = 1
        self.receivable_page_size = 50
        self.receivable_total_pages = 1'''

content = content.replace(old_init, new_init)

# 2. 在发票列表中添加分页控件
old_invoice_end = '''        self.invoice_tree.bind('<Double-1>', lambda e: self._edit_invoice())
        
        # 加载数据
        self._update_invoices_table()'''

new_invoice_end = '''        self.invoice_tree.bind('<Double-1>', lambda e: self._edit_invoice())
        
        # 分页控件
        page_frame = ctk.CTkFrame(self.content_area, fg_color='white', corner_radius=10, height=50)
        page_frame.pack(fill='x', padx=20, pady=(0, 20))
        page_frame.pack_propagate(False)
        
        # 左侧统计信息
        self.invoice_stats_label = ctk.CTkLabel(
            page_frame,
            text="共 0 条记录",
            font=ctk.CTkFont(size=12),
            text_color='#7f8c8d'
        )
        self.invoice_stats_label.pack(side='left', pady=13, padx=20)
        
        # 右侧分页控件
        invoice_page_frame = ctk.CTkFrame(page_frame, fg_color='transparent')
        invoice_page_frame.pack(side='right', pady=10, padx=20)
        
        ModernButton(invoice_page_frame, "上一页", command=self._prev_invoice_page, style='secondary').pack(side='left', padx=5)
        
        self.invoice_page_label = ctk.CTkLabel(invoice_page_frame, text="第 1/1 页", font=ctk.CTkFont(size=12))
        self.invoice_page_label.pack(side='left', padx=10)
        
        ModernButton(invoice_page_frame, "下一页", command=self._next_invoice_page, style='secondary').pack(side='left', padx=5)
        
        # 加载数据
        self._update_invoices_table()'''

content = content.replace(old_invoice_end, new_invoice_end)

# 3. 修改 _update_invoices_table 方法，添加分页
old_update_invoices = '''    def _update_invoices_table(self):
        """更新发票表格"""
        if hasattr(self, 'invoice_tree'):
            for item in self.invoice_tree.get_children():
                self.invoice_tree.delete(item)
            
            for invoice in self.invoices_cache:'''

new_update_invoices = '''    def _update_invoices_table(self):
        """更新发票表格"""
        if hasattr(self, 'invoice_tree'):
            for item in self.invoice_tree.get_children():
                self.invoice_tree.delete(item)
            
            # 应用分页
            start_idx = (self.invoice_page - 1) * self.invoice_page_size
            end_idx = start_idx + self.invoice_page_size
            page_invoices = self.invoices_cache[start_idx:end_idx]
            
            for invoice in page_invoices:'''

content = content.replace(old_update_invoices, new_update_invoices)

# 4. 在 _update_invoices_table 方法末尾添加分页信息更新
old_invoices_end = '''                self.invoice_tree.insert('', 'end', values=(
                    invoice.开票日期 or '',
                    invoice.合同号 or '',
                    invoice.付款单位名称 or '',
                    invoice.代码 or '',
                    safe_format_money(invoice.发票金额),
                    invoice.发票项目 or '',
                    invoice.类型 or '',
                    invoice.发票类型 or '',
                    invoice.除税 or '',
                    invoice.备注 or ''
                ))'''

new_invoices_end = '''                self.invoice_tree.insert('', 'end', values=(
                    invoice.开票日期 or '',
                    invoice.合同号 or '',
                    invoice.付款单位名称 or '',
                    invoice.代码 or '',
                    safe_format_money(invoice.发票金额),
                    invoice.发票项目 or '',
                    invoice.类型 or '',
                    invoice.发票类型 or '',
                    invoice.除税 or '',
                    invoice.备注 or ''
                ))
            
            # 更新分页信息
            total = len(self.invoices_cache)
            self.invoice_total_pages = max(1, (total + self.invoice_page_size - 1) // self.invoice_page_size)
            
            if hasattr(self, 'invoice_stats_label'):
                self.invoice_stats_label.configure(text=f"共 {total} 条记录")
                self.invoice_page_label.configure(text=f"第 {self.invoice_page}/{self.invoice_total_pages} 页")'''

content = content.replace(old_invoices_end, new_invoices_end)

# 5. 添加发票分页导航方法
old_search_invoices = '''    def _search_invoices(self):
        """搜索发票"""
        keyword = self.invoice_search_entry.get().strip()
        if keyword:
            filtered = [inv for inv in self.invoices_cache 
                       if keyword in (inv.合同号 or '') 
                       or keyword in (inv.付款单位名称 or '')]
        else:
            filtered = self.invoices_cache
        
        # 更新表格
        for item in self.invoice_tree.get_children():
            self.invoice_tree.delete(item)
        
        for invoice in filtered:
            self.invoice_tree.insert('', 'end', values=(
                invoice.开票日期 or '',
                invoice.合同号 or '',
                invoice.付款单位名称 or '',
                invoice.代码 or '',
                safe_format_money(invoice.发票金额),
                invoice.发票项目 or '',
                invoice.类型 or '',
                invoice.发票类型 or '',
                invoice.除税 or '',
                invoice.备注 or ''
            ))'''

new_search_invoices = '''    def _search_invoices(self):
        """搜索发票"""
        keyword = self.invoice_search_entry.get().strip()
        if keyword:
            filtered = [inv for inv in self.invoices_cache 
                       if keyword in (inv.合同号 or '') 
                       or keyword in (inv.付款单位名称 or '')]
            # 临时使用过滤结果
            for item in self.invoice_tree.get_children():
                self.invoice_tree.delete(item)
            
            for invoice in filtered:
                self.invoice_tree.insert('', 'end', values=(
                    invoice.开票日期 or '',
                    invoice.合同号 or '',
                    invoice.付款单位名称 or '',
                    invoice.代码 or '',
                    safe_format_money(invoice.发票金额),
                    invoice.发票项目 or '',
                    invoice.类型 or '',
                    invoice.发票类型 or '',
                    invoice.除税 or '',
                    invoice.备注 or ''
                ))
        else:
            # 恢复分页显示
            self._update_invoices_table()
    
    def _prev_invoice_page(self):
        """发票列表上一页"""
        if self.invoice_page > 1:
            self.invoice_page -= 1
            self._update_invoices_table()
    
    def _next_invoice_page(self):
        """发票列表下一页"""
        if self.invoice_page < self.invoice_total_pages:
            self.invoice_page += 1
            self._update_invoices_table()'''

content = content.replace(old_search_invoices, new_search_invoices)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ 已为发票列表添加分页功能")
