#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合同管理系统 V2.0 - 主程序
技术栈：CustomTkinter + Plotly + SQLite
架构：MVC 模式，模块化设计
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
from typing import Optional, List, Dict
import webbrowser
import tempfile
import os

from config import UI_CONFIG, CONTRACT_FIELDS, INVOICE_FIELDS
from models.entities import Contract, Invoice, CollectionRecord
from services.contract_service import ContractService
from services.invoice_service import InvoiceService
from utils.helpers import safe_format_money, get_days_until_deadline, get_warning_level

# Plotly 图表
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


class ModernButton(ctk.CTkButton):
    """现代化按钮组件"""
    
    def __init__(self, master, text: str, command=None, style: str = 'primary', **kwargs):
        colors = {
            'primary': ('#1f6aa5', '#144870'),
            'success': ('#2ecc71', '#27ae60'),
            'danger': ('#e74c3c', '#c0392b'),
            'warning': ('#f39c12', '#d68910'),
            'secondary': ('#95a5a6', '#7f8c8d')
        }
        
        fg_color, hover_color = colors.get(style, colors['primary'])
        
        super().__init__(
            master,
            text=text,
            command=command,
            font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=UI_CONFIG['font_size']['normal']),
            fg_color=fg_color,
            hover_color=hover_color,
            corner_radius=8,
            height=36,
            **kwargs
        )


class ModernEntry(ctk.CTkEntry):
    """现代化输入框组件"""
    
    def __init__(self, master, placeholder: str = '', **kwargs):
        super().__init__(
            master,
            placeholder_text=placeholder,
            font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=UI_CONFIG['font_size']['normal']),
            corner_radius=8,
            height=36,
            **kwargs
        )


class ModernComboBox(ctk.CTkComboBox):
    """现代化下拉框组件"""
    
    def __init__(self, master, values: List[str] = None, **kwargs):
        super().__init__(
            master,
            values=values or [],
            font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=UI_CONFIG['font_size']['normal']),
            dropdown_font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=UI_CONFIG['font_size']['normal']),
            corner_radius=8,
            height=36,
            **kwargs
        )


class ContractManagerApp(ctk.CTk):
    """主应用"""
    
    def __init__(self):
        super().__init__()
        
        # 设置主题
        ctk.set_appearance_mode(UI_CONFIG['theme'])
        ctk.set_default_color_theme(UI_CONFIG['color_theme'])
        
        # 设置窗口
        self.title("合同管理系统 V2.0")
        self.geometry(f"{UI_CONFIG['window_size'][0]}x{UI_CONFIG['window_size'][1]}")
        self.minsize(1200, 700)
        
        # 初始化服务
        self.contract_service = ContractService()
        self.invoice_service = InvoiceService()
        
        # 数据缓存
        self.contracts_cache: List[Contract] = []
        self.invoices_cache: List[Invoice] = []
        
        # 创建UI
        self._create_ui()
        
        # 加载数据
        self._load_initial_data()
    
    def _create_ui(self):
        """创建UI界面"""
        # 创建主容器
        self.main_container = ctk.CTkFrame(self, fg_color='transparent')
        self.main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 创建侧边栏
        self._create_sidebar()
        
        # 创建内容区域
        self._create_content_area()
    
    def _create_sidebar(self):
        """创建侧边栏"""
        self.sidebar = ctk.CTkFrame(
            self.main_container,
            width=200,
            corner_radius=15,
            fg_color='#2c3e50'
        )
        self.sidebar.pack(side='left', fill='y', padx=(0, 10))
        self.sidebar.pack_propagate(False)
        
        # 标题
        title_label = ctk.CTkLabel(
            self.sidebar,
            text="合同管理系统",
            font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=UI_CONFIG['font_size']['title'], weight='bold'),
            text_color='white'
        )
        title_label.pack(pady=30)
        
        # 导航按钮
        nav_buttons = [
            ("📋 合同管理", self._show_contracts_tab),
            ("📄 发票管理", self._show_invoices_tab),
            ("⚠️ 到期预警", self._show_warnings_tab),
            ("📊 统计分析", self._show_statistics_tab),
            ("💰 应收账款", self._show_receivables_tab)
        ]
        
        for text, command in nav_buttons:
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                command=command,
                font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=UI_CONFIG['font_size']['normal']),
                fg_color='transparent',
                hover_color='#34495e',
                text_color='white',
                anchor='w',
                height=45,
                corner_radius=10
            )
            btn.pack(fill='x', padx=15, pady=5)
        
        # 底部信息
        info_label = ctk.CTkLabel(
            self.sidebar,
            text="V2.0 - 现代化版本",
            font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=UI_CONFIG['font_size']['small']),
            text_color='#95a5a6'
        )
        info_label.pack(side='bottom', pady=20)
    
    def _create_content_area(self):
        """创建内容区域"""
        self.content_area = ctk.CTkFrame(
            self.main_container,
            corner_radius=15,
            fg_color='#ecf0f1'
        )
        self.content_area.pack(side='right', fill='both', expand=True)
        
        # 创建各个标签页容器
        self.contracts_frame = None
        self.invoices_frame = None
        self.warnings_frame = None
        self.statistics_frame = None
        self.receivables_frame = None
        
        # 默认显示合同管理
        self._show_contracts_tab()
    
    def _clear_content_area(self):
        """清空内容区域"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
    
    def _show_contracts_tab(self):
        """显示合同管理标签页"""
        self._clear_content_area()
        
        # 标题栏
        header = ctk.CTkFrame(self.content_area, fg_color='transparent', height=60)
        header.pack(fill='x', padx=20, pady=20)
        header.pack_propagate(False)
        
        title = ctk.CTkLabel(
            header,
            text="合同管理",
            font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=UI_CONFIG['font_size']['title'], weight='bold'),
            text_color='#2c3e50'
        )
        title.pack(side='left')
        
        # 操作按钮
        btn_frame = ctk.CTkFrame(header, fg_color='transparent')
        btn_frame.pack(side='right')
        
        ModernButton(btn_frame, "导入", command=self._import_contracts, style='success').pack(side='left', padx=5)
        ModernButton(btn_frame, "导出", command=self._export_contracts, style='primary').pack(side='left', padx=5)
        ModernButton(btn_frame, "添加", command=self._add_contract_dialog, style='primary').pack(side='left', padx=5)
        
        # 筛选栏
        filter_frame = ctk.CTkFrame(self.content_area, fg_color='white', corner_radius=10)
        filter_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        filter_inner = ctk.CTkFrame(filter_frame, fg_color='transparent')
        filter_inner.pack(fill='x', padx=15, pady=15)
        
        # 搜索框
        self.contract_search_entry = ModernEntry(filter_inner, placeholder="搜索合同编号、名称...")
        self.contract_search_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.contract_search_entry.bind('<KeyRelease>', lambda e: self._search_contracts())
        
        # 筛选下拉框
        ctk.CTkLabel(filter_inner, text="年份:", font=ctk.CTkFont(size=13)).pack(side='left', padx=(10, 5))
        self.year_combo = ModernComboBox(filter_inner, values=['全部', '2026', '2025', '2024'], width=100)
        self.year_combo.set('全部')
        self.year_combo.pack(side='left', padx=5)
        self.year_combo.bind('<<ComboboxSelected>>', lambda e: self._filter_contracts())
        
        ctk.CTkLabel(filter_inner, text="区域:", font=ctk.CTkFont(size=13)).pack(side='left', padx=(10, 5))
        self.region_combo = ModernComboBox(filter_inner, values=['全部'], width=120)
        self.region_combo.set('全部')
        self.region_combo.pack(side='left', padx=5)
        self.region_combo.bind('<<ComboboxSelected>>', lambda e: self._filter_contracts())
        
        ctk.CTkLabel(filter_inner, text="负责人:", font=ctk.CTkFont(size=13)).pack(side='left', padx=(10, 5))
        self.salesperson_combo = ModernComboBox(filter_inner, values=['全部'], width=120)
        self.salesperson_combo.set('全部')
        self.salesperson_combo.pack(side='left', padx=5)
        self.salesperson_combo.bind('<<ComboboxSelected>>', lambda e: self._filter_contracts())
        
        # 数据表格
        table_frame = ctk.CTkFrame(self.content_area, fg_color='white', corner_radius=10)
        table_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # 创建表格（使用 Treeview）
        from tkinter import ttk
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Custom.Treeview', 
                       background='white',
                       foreground='#2c3e50',
                       fieldbackground='white',
                       font=('Microsoft YaHei UI', 11),
                       rowheight=35)
        style.configure('Custom.Treeview.Heading',
                       background='#3498db',
                       foreground='white',
                       font=('Microsoft YaHei UI', 11, 'bold'))
        style.map('Custom.Treeview', background=[('selected', '#3498db')])
        
        self.contract_tree = ttk.Treeview(
            table_frame,
            columns=['合同编号', '合同名称', '对方单位', '销售负责人', '合同额', '合同签字日期', '到期日期', '状态'],
            show='headings',
            style='Custom.Treeview',
            selectmode='browse'
        )
        
        # 设置列
        columns_config = [
            ('合同编号', 120),
            ('合同名称', 200),
            ('对方单位', 150),
            ('销售负责人', 100),
            ('合同额', 100),
            ('合同签字日期', 110),
            ('到期日期', 110),
            ('状态', 80)
        ]
        
        for col, width in columns_config:
            self.contract_tree.heading(col, text=col)
            self.contract_tree.column(col, width=width, anchor='center')
        
        # 滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.contract_tree.yview)
        self.contract_tree.configure(yscrollcommand=scrollbar.set)
        
        self.contract_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 绑定双击事件
        self.contract_tree.bind('<Double-1>', lambda e: self._view_contract_detail())
        self.contract_tree.bind('<Button-3>', self._show_contract_context_menu)
        
        # 统计信息栏
        stats_frame = ctk.CTkFrame(self.content_area, fg_color='white', corner_radius=10, height=60)
        stats_frame.pack(fill='x', padx=20, pady=(0, 20))
        stats_frame.pack_propagate(False)
        
        self.stats_label = ctk.CTkLabel(
            stats_frame,
            text="共 0 条记录，总金额: ¥0.00",
            font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=UI_CONFIG['font_size']['normal']),
            text_color='#7f8c8d'
        )
        self.stats_label.pack(pady=18)
    
    def _load_initial_data(self):
        """加载初始数据"""
        # 在后台线程加载
        def load_data():
            self.contracts_cache = self.contract_service.get_all_contracts()
            self.invoices_cache = self.invoice_service.get_all_invoices()
            
            # 更新UI
            self.after(0, self._update_contracts_table)
            self.after(0, self._update_filter_combos)
        
        thread = threading.Thread(target=load_data, daemon=True)
        thread.start()
    
    def _update_contracts_table(self):
        """更新合同表格"""
        # 清空表格
        for item in self.contract_tree.get_children():
            self.contract_tree.delete(item)
        
        # 添加数据
        for contract in self.contracts_cache:
            # 计算状态
            days = get_days_until_deadline(contract.合同终止日期)
            level = get_warning_level(days)
            
            status_map = {
                'red': '已超期',
                'orange': '即将到期',
                'yellow': '需关注',
                'none': '正常'
            }
            status = status_map.get(level, '正常')
            
            # 插入数据
            self.contract_tree.insert('', 'end', values=(
                contract.合同编号,
                contract.合同名称 or '',
                contract.对方单位名称 or '',
                contract.销售负责人 or '',
                safe_format_money(contract.合同额),
                contract.合同签字日期 or '',
                contract.合同终止日期 or '',
                status
            ))
        
        # 更新统计
        total_amount = sum(c.合同额 or 0 for c in self.contracts_cache)
        self.stats_label.configure(
            text=f"共 {len(self.contracts_cache)} 条记录，总金额: ¥{safe_format_money(total_amount)}"
        )
    
    def _update_filter_combos(self):
        """更新筛选下拉框"""
        regions = self.contract_service.get_distinct_regions()
        salespersons = self.contract_service.get_distinct_salespersons()
        
        self.region_combo.configure(values=['全部'] + regions)
        self.salesperson_combo.configure(values=['全部'] + salespersons)
    
    def _search_contracts(self):
        """搜索合同"""
        search_text = self.contract_search_entry.get()
        filters = {'search': search_text} if search_text else None
        self.contracts_cache = self.contract_service.get_all_contracts(filters)
        self._update_contracts_table()
    
    def _filter_contracts(self):
        """筛选合同"""
        filters = {}
        
        year = self.year_combo.get()
        if year != '全部':
            filters['year'] = year
        
        region = self.region_combo.get()
        if region != '全部':
            filters['region'] = region
        
        salesperson = self.salesperson_combo.get()
        if salesperson != '全部':
            filters['salesperson'] = salesperson
        
        self.contracts_cache = self.contract_service.get_all_contracts(filters if filters else None)
        self._update_contracts_table()
    
    def _import_contracts(self):
        """导入合同"""
        file_path = filedialog.askopenfilename(
            title="选择要导入的文件",
            filetypes=[("Excel 文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        # 在后台线程导入
        def import_data():
            success, fail, errors = self.contract_service.import_from_excel(file_path)
            
            # 更新UI
            self.after(0, lambda: self._show_import_result(success, fail, errors))
        
        thread = threading.Thread(target=import_data, daemon=True)
        thread.start()
    
    def _show_import_result(self, success: int, fail: int, errors: List[str]):
        """显示导入结果"""
        msg = f"导入完成\n成功: {success} 条\n失败: {fail} 条"
        if errors:
            msg += f"\n\n错误信息:\n" + '\n'.join(errors[:5])
            if len(errors) > 5:
                msg += f"\n...还有 {len(errors) - 5} 条错误"
        
        messagebox.showinfo("导入结果", msg)
        
        # 重新加载数据
        self._load_initial_data()
    
    def _export_contracts(self):
        """导出合同"""
        file_path = filedialog.asksaveasfilename(
            title="保存文件",
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx")]
        )
        
        if not file_path:
            return
        
        if self.contract_service.export_to_excel(file_path, self.contracts_cache):
            messagebox.showinfo("导出成功", f"文件已保存到:\n{file_path}")
        else:
            messagebox.showerror("导出失败", "导出过程中出现错误")
    
    def _add_contract_dialog(self):
        """添加合同对话框"""
        # TODO: 实现添加合同对话框
        messagebox.showinfo("提示", "添加合同功能开发中...")
    
    def _view_contract_detail(self):
        """查看合同详情"""
        selection = self.contract_tree.selection()
        if not selection:
            return
        
        item = self.contract_tree.item(selection[0])
        contract_no = item['values'][0]
        
        # TODO: 实现详情对话框
        messagebox.showinfo("合同详情", f"合同编号: {contract_no}\n详情功能开发中...")
    
    def _show_contract_context_menu(self, event):
        """显示右键菜单"""
        # TODO: 实现右键菜单
        pass
    
    def _show_invoices_tab(self):
        """显示发票管理标签页"""
        self._clear_content_area()
        
        # 标题
        header = ctk.CTkFrame(self.content_area, fg_color='transparent', height=60)
        header.pack(fill='x', padx=20, pady=20)
        header.pack_propagate(False)
        
        title = ctk.CTkLabel(
            header,
            text="发票管理",
            font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=UI_CONFIG['font_size']['title'], weight='bold'),
            text_color='#2c3e50'
        )
        title.pack(side='left')
        
        btn_frame = ctk.CTkFrame(header, fg_color='transparent')
        btn_frame.pack(side='right')
        
        ModernButton(btn_frame, "导入", command=self._import_invoices, style='success').pack(side='left', padx=5)
        ModernButton(btn_frame, "导出", command=self._export_invoices, style='primary').pack(side='left', padx=5)
        
        # 数据表格
        table_frame = ctk.CTkFrame(self.content_area, fg_color='white', corner_radius=10)
        table_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        from tkinter import ttk
        style = ttk.Style()
        style.configure('Custom.Treeview')
        
        self.invoice_tree = ttk.Treeview(
            table_frame,
            columns=['开票日期', '合同号', '付款单位', '发票金额', '发票项目', '类型'],
            show='headings',
            style='Custom.Treeview'
        )
        
        columns_config = [
            ('开票日期', 110),
            ('合同号', 120),
            ('付款单位', 150),
            ('发票金额', 100),
            ('发票项目', 150),
            ('类型', 100)
        ]
        
        for col, width in columns_config:
            self.invoice_tree.heading(col, text=col)
            self.invoice_tree.column(col, width=width, anchor='center')
        
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.invoice_tree.yview)
        self.invoice_tree.configure(yscrollcommand=scrollbar.set)
        
        self.invoice_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 加载数据
        self._update_invoices_table()
    
    def _update_invoices_table(self):
        """更新发票表格"""
        for item in self.invoice_tree.get_children():
            self.invoice_tree.delete(item)
        
        for invoice in self.invoices_cache:
            self.invoice_tree.insert('', 'end', values=(
                invoice.开票日期 or '',
                invoice.合同号,
                invoice.付款单位名称 or '',
                safe_format_money(invoice.发票金额),
                invoice.发票项目 or '',
                invoice.类型 or ''
            ))
    
    def _import_invoices(self):
        """导入发票"""
        file_path = filedialog.askopenfilename(
            title="选择要导入的文件",
            filetypes=[("Excel 文件", "*.xlsx *.xls")]
        )
        
        if not file_path:
            return
        
        def import_data():
            success, fail, errors = self.invoice_service.import_from_excel(file_path)
            self.after(0, lambda: self._show_import_result(success, fail, errors))
        
        thread = threading.Thread(target=import_data, daemon=True)
        thread.start()
    
    def _export_invoices(self):
        """导出发票"""
        file_path = filedialog.asksaveasfilename(
            title="保存文件",
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx")]
        )
        
        if not file_path:
            return
        
        if self.invoice_service.export_to_excel(file_path, self.invoices_cache):
            messagebox.showinfo("导出成功", f"文件已保存到:\n{file_path}")
    
    def _show_warnings_tab(self):
        """显示到期预警标签页"""
        self._clear_content_area()
        
        # 标题
        header = ctk.CTkFrame(self.content_area, fg_color='transparent', height=60)
        header.pack(fill='x', padx=20, pady=20)
        header.pack_propagate(False)
        
        title = ctk.CTkLabel(
            header,
            text="到期预警",
            font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=UI_CONFIG['font_size']['title'], weight='bold'),
            text_color='#2c3e50'
        )
        title.pack(side='left')
        
        # 预警统计卡片
        cards_frame = ctk.CTkFrame(self.content_area, fg_color='transparent')
        cards_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        warning_data = self.contract_service.get_warning_contracts()
        
        # 统计各级别数量
        red_count = sum(1 for w in warning_data if w['level'] == 'red')
        orange_count = sum(1 for w in warning_data if w['level'] == 'orange')
        yellow_count = sum(1 for w in warning_data if w['level'] == 'yellow')
        
        cards_info = [
            ('已超期', red_count, '#e74c3c'),
            ('7天内到期', orange_count, '#f39c12'),
            ('30天内到期', yellow_count, '#f1c40f')
        ]
        
        for label, count, color in cards_info:
            card = ctk.CTkFrame(cards_frame, fg_color='white', corner_radius=10, width=200)
            card.pack(side='left', padx=10)
            card.pack_propagate(False)
            
            ctk.CTkLabel(
                card,
                text=str(count),
                font=ctk.CTkFont(size=32, weight='bold'),
                text_color=color
            ).pack(pady=(20, 5))
            
            ctk.CTkLabel(
                card,
                text=label,
                font=ctk.CTkFont(size=13),
                text_color='#7f8c8d'
            ).pack(pady=(0, 20))
        
        # 预警列表
        table_frame = ctk.CTkFrame(self.content_area, fg_color='white', corner_radius=10)
        table_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        from tkinter import ttk
        
        self.warning_tree = ttk.Treeview(
            table_frame,
            columns=['合同编号', '合同名称', '到期日期', '剩余天数', '合同额', '销售负责人', '状态'],
            show='headings',
            style='Custom.Treeview'
        )
        
        columns_config = [
            ('合同编号', 120),
            ('合同名称', 200),
            ('到期日期', 110),
            ('剩余天数', 100),
            ('合同额', 100),
            ('销售负责人', 100),
            ('状态', 100)
        ]
        
        for col, width in columns_config:
            self.warning_tree.heading(col, text=col)
            self.warning_tree.column(col, width=width, anchor='center')
        
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.warning_tree.yview)
        self.warning_tree.configure(yscrollcommand=scrollbar.set)
        
        self.warning_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 加载数据
        for item in warning_data:
            contract = item['contract']
            days = item['days']
            level = item['level']
            
            status_map = {
                'red': '已超期',
                'orange': '即将到期',
                'yellow': '需关注'
            }
            
            self.warning_tree.insert('', 'end', values=(
                contract.合同编号,
                contract.合同名称 or '',
                contract.合同终止日期 or '',
                f"{days} 天" if days >= 0 else f"超期 {abs(days)} 天",
                safe_format_money(contract.合同额),
                contract.销售负责人 or '',
                status_map.get(level, '')
            ))
    
    def _show_statistics_tab(self):
        """显示统计分析标签页"""
        self._clear_content_area()
        
        # 标题
        header = ctk.CTkFrame(self.content_area, fg_color='transparent', height=60)
        header.pack(fill='x', padx=20, pady=20)
        header.pack_propagate(False)
        
        title = ctk.CTkLabel(
            header,
            text="统计分析",
            font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=UI_CONFIG['font_size']['title'], weight='bold'),
            text_color='#2c3e50'
        )
        title.pack(side='left')
        
        # 图表区域
        charts_frame = ctk.CTkFrame(self.content_area, fg_color='transparent')
        charts_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # 生成图表
        self._generate_statistics_charts(charts_frame)
    
    def _generate_statistics_charts(self, parent):
        """生成统计图表"""
        stats = self.contract_service.get_statistics(self.contracts_cache)
        
        # 创建两个图表容器
        left_frame = ctk.CTkFrame(parent, fg_color='white', corner_radius=10)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        right_frame = ctk.CTkFrame(parent, fg_color='white', corner_radius=10)
        right_frame.pack(side='right', fill='both', expand=True)
        
        # 按区域分布饼图
        if stats['by_region']:
            fig1 = go.Figure(data=[go.Pie(
                labels=list(stats['by_region'].keys()),
                values=list(stats['by_region'].values()),
                hole=0.4,
                marker_colors=px.colors.qualitative.Set3
            )])
            fig1.update_layout(
                title='合同额按区域分布',
                font=dict(family='Microsoft YaHei UI', size=14),
                height=400
            )
            
            # 保存为HTML并在浏览器中打开
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as f:
                fig1.write_html(f.name)
                html_path1 = f.name
            
            # 在WebView中显示（简化版：使用按钮打开）
            ctk.CTkLabel(
                left_frame,
                text="📊 按区域分布",
                font=ctk.CTkFont(size=16, weight='bold')
            ).pack(pady=20)
            
            ModernButton(
                left_frame,
                text="查看图表",
                command=lambda: webbrowser.open(f'file://{html_path1}'),
                style='primary'
            ).pack(pady=10)
            
            ctk.CTkLabel(
                left_frame,
                text=f"共 {len(stats['by_region'])} 个区域",
                font=ctk.CTkFont(size=13),
                text_color='#7f8c8d'
            ).pack(pady=10)
        
        # 按销售负责人柱状图
        if stats['by_salesperson']:
            fig2 = go.Figure(data=[go.Bar(
                x=list(stats['by_salesperson'].keys()),
                y=list(stats['by_salesperson'].values()),
                marker_color='#3498db'
            )])
            fig2.update_layout(
                title='合同额按销售负责人分布',
                font=dict(family='Microsoft YaHei UI', size=14),
                height=400,
                xaxis_tickangle=-45
            )
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as f:
                fig2.write_html(f.name)
                html_path2 = f.name
            
            ctk.CTkLabel(
                right_frame,
                text="📊 按销售负责人",
                font=ctk.CTkFont(size=16, weight='bold')
            ).pack(pady=20)
            
            ModernButton(
                right_frame,
                text="查看图表",
                command=lambda: webbrowser.open(f'file://{html_path2}'),
                style='primary'
            ).pack(pady=10)
            
            ctk.CTkLabel(
                right_frame,
                text=f"共 {len(stats['by_salesperson'])} 位销售",
                font=ctk.CTkFont(size=13),
                text_color='#7f8c8d'
            ).pack(pady=10)
    
    def _show_receivables_tab(self):
        """显示应收账款标签页"""
        self._clear_content_area()
        
        # 标题
        header = ctk.CTkFrame(self.content_area, fg_color='transparent', height=60)
        header.pack(fill='x', padx=20, pady=20)
        header.pack_propagate(False)
        
        title = ctk.CTkLabel(
            header,
            text="应收账款管理",
            font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=UI_CONFIG['font_size']['title'], weight='bold'),
            text_color='#2c3e50'
        )
        title.pack(side='left')
        
        # 统计卡片
        cards_frame = ctk.CTkFrame(self.content_area, fg_color='transparent')
        cards_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        total_receivable = sum(c.应收账款 or 0 for c in self.contracts_cache if c.应收账款 and c.应收账款 > 0)
        total_balance = sum(c.合同余额 or 0 for c in self.contracts_cache if c.合同余额 and c.合同余额 > 0)
        
        cards_info = [
            ('应收账款总额', total_receivable, '#e74c3c'),
            ('合同余额总额', total_balance, '#f39c12')
        ]
        
        for label, amount, color in cards_info:
            card = ctk.CTkFrame(cards_frame, fg_color='white', corner_radius=10, width=250)
            card.pack(side='left', padx=10)
            card.pack_propagate(False)
            
            ctk.CTkLabel(
                card,
                text=f"¥{safe_format_money(amount)}",
                font=ctk.CTkFont(size=24, weight='bold'),
                text_color=color
            ).pack(pady=(20, 5))
            
            ctk.CTkLabel(
                card,
                text=label,
                font=ctk.CTkFont(size=13),
                text_color='#7f8c8d'
            ).pack(pady=(0, 20))
        
        # 应收账款列表
        table_frame = ctk.CTkFrame(self.content_area, fg_color='white', corner_radius=10)
        table_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        from tkinter import ttk
        
        self.receivable_tree = ttk.Treeview(
            table_frame,
            columns=['合同编号', '对方单位', '合同额', '到款金额', '应收账款', '销售负责人', '催款状态'],
            show='headings',
            style='Custom.Treeview'
        )
        
        columns_config = [
            ('合同编号', 120),
            ('对方单位', 150),
            ('合同额', 100),
            ('到款金额', 100),
            ('应收账款', 100),
            ('销售负责人', 100),
            ('催款状态', 100)
        ]
        
        for col, width in columns_config:
            self.receivable_tree.heading(col, text=col)
            self.receivable_tree.column(col, width=width, anchor='center')
        
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.receivable_tree.yview)
        self.receivable_tree.configure(yscrollcommand=scrollbar.set)
        
        self.receivable_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 加载数据
        for contract in self.contracts_cache:
            if contract.应收账款 and contract.应收账款 > 0:
                self.receivable_tree.insert('', 'end', values=(
                    contract.合同编号,
                    contract.对方单位名称 or '',
                    safe_format_money(contract.合同额),
                    safe_format_money(contract.到款金额),
                    safe_format_money(contract.应收账款),
                    contract.销售负责人 or '',
                    contract.催款状态 or '未催款'
                ))


def main():
    """主函数"""
    app = ContractManagerApp()
    app.mainloop()


if __name__ == '__main__':
    main()
