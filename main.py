#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合同管理系统 V2.0 - 完整版
技术栈：CustomTkinter + Plotly + SQLite
架构：MVC 模式，模块化设计
功能：与 V1.0 完全一致，UI 更现代化
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import threading
from typing import Optional, List, Dict
import webbrowser
import tempfile
import os
import shutil
from datetime import datetime, timedelta

from config import UI_CONFIG, CONTRACT_FIELDS, INVOICE_FIELDS
from models.entities import Contract, Invoice, CollectionRecord
from models.database import DatabaseManager
from services.contract_service import ContractService
from services.invoice_service import InvoiceService
from utils.helpers import safe_format_money, get_days_until_deadline, get_warning_level
from views.dialogs_fixed import ContractDialog, InvoiceDialog, CollectionRecordDialog

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


class ContractManagerApp(ctk.CTk):
    """主应用 - 完整版"""
    
    def __init__(self):
        super().__init__()
        
        # 设置主题
        ctk.set_appearance_mode(UI_CONFIG['theme'])
        ctk.set_default_color_theme(UI_CONFIG['color_theme'])
        
        # 设置窗口
        self.title("合同管理系统 V2.0 - 完整版")
        self.geometry(f"{UI_CONFIG['window_size'][0]}x{UI_CONFIG['window_size'][1]}")
        self.minsize(1400, 800)
        
        # 初始化服务
        self.db = DatabaseManager()
        self.contract_service = ContractService()
        self.invoice_service = InvoiceService()
        
        # 数据缓存
        self.contracts_cache: List[Contract] = []
        self.invoices_cache: List[Invoice] = []
        
        # 分页相关
        self.current_page = 1
        self.page_size = 50
        self.total_pages = 1
        
        # 区域和销售负责人列表
        self.regions = ['北方区', '西北区', '华东区', '华南区', '国际部', '其他']
        self.collection_status = ['未催款', '催款中', '已承诺付款', '已回款', '坏账']
        
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
            ("💰 应收账款", self._show_receivables_tab),
            ("📊 年度统计", self._show_yearly_stats_tab),
            ("📈 区域统计", self._show_region_stats_tab),
            ("👤 销售统计", self._show_salesperson_stats_tab),
            ("💾 数据管理", self._show_data_management_tab)
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
            text="V2.0 - 完整版",
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
        
        # 默认显示合同管理
        self._show_contracts_tab()
    
    def _clear_content_area(self):
        """清空内容区域"""
        for widget in self.content_area.winfo_children():
            widget.destroy()
    
    # ==================== 合同管理 ====================
    
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
        ModernButton(btn_frame, "添加", command=self._add_contract, style='primary').pack(side='left', padx=5)
        ModernButton(btn_frame, "编辑", command=self._edit_contract, style='warning').pack(side='left', padx=5)
        ModernButton(btn_frame, "删除", command=self._delete_contract, style='danger').pack(side='left', padx=5)
        
        # 筛选栏
        filter_frame = ctk.CTkFrame(self.content_area, fg_color='white', corner_radius=10)
        filter_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        filter_inner = ctk.CTkFrame(filter_frame, fg_color='transparent')
        filter_inner.pack(fill='x', padx=15, pady=15)
        
        # 搜索框
        self.contract_search_entry = ctk.CTkEntry(
            filter_inner, 
            placeholder_text="搜索合同编号、名称、对方单位...",
            width=300
        )
        self.contract_search_entry.pack(side='left', padx=(0, 10))
        self.contract_search_entry.bind('<KeyRelease>', lambda e: self._search_contracts())
        
        # 筛选下拉框
        ctk.CTkLabel(filter_inner, text="年份:", font=ctk.CTkFont(size=13)).pack(side='left', padx=(10, 5))
        self.year_combo = ctk.CTkComboBox(filter_inner, values=['全部', '2026', '2025', '2024'], width=100)
        self.year_combo.set('全部')
        self.year_combo.pack(side='left', padx=5)
        self.year_combo.bind('<<ComboboxSelected>>', lambda e: self._filter_contracts())
        
        ctk.CTkLabel(filter_inner, text="区域:", font=ctk.CTkFont(size=13)).pack(side='left', padx=(10, 5))
        self.region_combo = ctk.CTkComboBox(filter_inner, values=['全部'] + self.regions, width=120)
        self.region_combo.set('全部')
        self.region_combo.pack(side='left', padx=5)
        self.region_combo.bind('<<ComboboxSelected>>', lambda e: self._filter_contracts())
        
        ctk.CTkLabel(filter_inner, text="负责人:", font=ctk.CTkFont(size=13)).pack(side='left', padx=(10, 5))
        self.salesperson_combo = ctk.CTkComboBox(filter_inner, values=['全部'], width=120)
        self.salesperson_combo.set('全部')
        self.salesperson_combo.pack(side='left', padx=5)
        self.salesperson_combo.bind('<<ComboboxSelected>>', lambda e: self._filter_contracts())
        
        # 清空按钮
        ModernButton(filter_inner, "清空筛选", command=self._clear_contract_filters, style='secondary').pack(side='left', padx=10)
        
        # 数据表格
        table_frame = ctk.CTkFrame(self.content_area, fg_color='white', corner_radius=10)
        table_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # 创建表格
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
        
        # 合同列表显示所有29个字段
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
        self.contract_tree.column('备注', width=150)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.contract_tree.yview)
        self.contract_tree.configure(yscrollcommand=scrollbar.set)
        
        self.contract_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 绑定双击事件
        self.contract_tree.bind('<Double-1>', lambda e: self._edit_contract())
        self.contract_tree.bind('<Button-3>', self._show_contract_context_menu)
        
        # 统计信息栏和分页控件
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
        
        ModernButton(page_frame, "下一页", command=self._next_page, style='secondary').pack(side='left', padx=5)
    
    def _add_contract(self):
        """添加合同"""
        salespersons = self.db.get_distinct_values('销售负责人')
        
        dialog = ContractDialog(
            self,
            regions=self.regions,
            salespersons=salespersons,
            on_save=self._save_contract
        )
    
    def _edit_contract(self):
        """编辑合同"""
        selection = self.contract_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要编辑的合同")
            return
        
        item = self.contract_tree.item(selection[0])
        contract_no = item['values'][0]
        
        # 获取合同详情
        contract = self.db.get_contract_by_no(contract_no)
        if not contract:
            messagebox.showerror("错误", "合同不存在")
            return
        
        salespersons = self.db.get_distinct_values('销售负责人')
        
        dialog = ContractDialog(
            self,
            contract_data=contract.to_dict(),
            regions=self.regions,
            salespersons=salespersons,
            on_save=lambda data: self._update_contract(contract_no, data)
        )
    
    def _delete_contract(self):
        """删除合同"""
        selection = self.contract_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要删除的合同")
            return
        
        item = self.contract_tree.item(selection[0])
        contract_no = item['values'][0]
        
        if messagebox.askyesno("确认删除", f"确定要删除合同 {contract_no} 吗？\n此操作不可恢复！"):
            if self.db.delete_contract(contract_no):
                messagebox.showinfo("成功", "合同已删除")
                self._load_initial_data()
            else:
                messagebox.showerror("错误", "删除失败")
    
    def _save_contract(self, data: Dict):
        """保存新合同"""
        contract = Contract.from_dict(data)
        success, msg = self.db.add_contract(contract)
        
        if success:
            messagebox.showinfo("成功", "合同添加成功")
            self._load_initial_data()
        else:
            messagebox.showerror("错误", msg)
    
    def _update_contract(self, contract_no: str, data: Dict):
        """更新合同"""
        if self.db.update_contract(contract_no, data):
            messagebox.showinfo("成功", "合同更新成功")
            self._load_initial_data()
        else:
            messagebox.showerror("错误", "更新失败")
    
    def _show_contract_context_menu(self, event):
        """显示右键菜单"""
        menu = ctk.CTkMenu(self)
        menu.add_command(label="编辑", command=self._edit_contract)
        menu.add_command(label="删除", command=self._delete_contract)
        menu.add_separator()
        menu.add_command(label="查看详情", command=self._view_contract_detail)
        menu.post(event.x_root, event.y_root)
    
    def _view_contract_detail(self):
        """查看合同详情"""
        selection = self.contract_tree.selection()
        if not selection:
            return
        
        item = self.contract_tree.item(selection[0])
        contract_no = item['values'][0]
        
        contract = self.db.get_contract_by_no(contract_no)
        if contract:
            self._edit_contract()
    
    def _sort_contract_tree(self, col: str):
        """排序合同表格"""
        items = [(self.contract_tree.set(item, col), item) for item in self.contract_tree.get_children('')]
        
        # 尝试数值排序
        try:
            items.sort(reverse=False, key=lambda x: float(x[0].replace(',', '').replace('¥', '')))
        except:
            items.sort(reverse=False, key=lambda x: x[0])
        
        for index, (val, item) in enumerate(items):
            self.contract_tree.move(item, '', index)
    
    def _clear_contract_filters(self):
        """清空筛选"""
        self.contract_search_entry.delete(0, 'end')
        self.year_combo.set('全部')
        self.region_combo.set('全部')
        self.salesperson_combo.set('全部')
        self._load_initial_data()
    
    # ==================== 发票管理 ====================
    
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
        ModernButton(btn_frame, "添加", command=self._add_invoice, style='primary').pack(side='left', padx=5)
        ModernButton(btn_frame, "编辑", command=self._edit_invoice, style='warning').pack(side='left', padx=5)
        ModernButton(btn_frame, "删除", command=self._delete_invoice, style='danger').pack(side='left', padx=5)
        
        # 搜索栏
        search_frame = ctk.CTkFrame(self.content_area, fg_color='white', corner_radius=10)
        search_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        search_inner = ctk.CTkFrame(search_frame, fg_color='transparent')
        search_inner.pack(fill='x', padx=15, pady=15)
        
        self.invoice_search_entry = ctk.CTkEntry(
            search_inner,
            placeholder_text="搜索合同号、付款单位...",
            width=300
        )
        self.invoice_search_entry.pack(side='left')
        self.invoice_search_entry.bind('<KeyRelease>', lambda e: self._search_invoices())
        
        # 数据表格
        table_frame = ctk.CTkFrame(self.content_area, fg_color='white', corner_radius=10)
        table_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        style = ttk.Style()
        style.configure('Custom.Treeview')
        
        self.invoice_tree = ttk.Treeview(
            table_frame,
            columns=['开票日期', '合同号', '付款单位', '发票金额', '发票项目', '类型', '发票类型', '除税', '备注'],
            show='headings',
            style='Custom.Treeview'
        )
        
        columns_config = [
            ('开票日期', 110),
            ('合同号', 120),
            ('付款单位', 150),
            ('发票金额', 100),
            ('发票项目', 150),
            ('类型', 100),
            ('发票类型', 100),
            ('除税', 100),
            ('备注', 150)
        ]
        
        for col, width in columns_config:
            self.invoice_tree.heading(col, text=col, command=lambda c=col: self._sort_invoice_tree(c))
            self.invoice_tree.column(col, width=width, anchor='center')
        
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.invoice_tree.yview)
        self.invoice_tree.configure(yscrollcommand=scrollbar.set)
        
        self.invoice_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.invoice_tree.bind('<Double-1>', lambda e: self._edit_invoice())
        
        # 加载数据
        self._update_invoices_table()
    
    def _add_invoice(self):
        """添加发票"""
        dialog = InvoiceDialog(self, on_save=self._save_invoice)
    
    def _edit_invoice(self):
        """编辑发票"""
        selection = self.invoice_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要编辑的发票")
            return
        
        item = self.invoice_tree.item(selection[0])
        # TODO: 实现编辑功能
        messagebox.showinfo("提示", "编辑功能开发中...")
    
    def _delete_invoice(self):
        """删除发票"""
        selection = self.invoice_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要删除的发票")
            return
        
        if messagebox.askyesno("确认删除", "确定要删除选中的发票吗？"):
            # TODO: 实现删除功能
            messagebox.showinfo("提示", "删除功能开发中...")
    
    def _save_invoice(self, data: Dict):
        """保存发票"""
        invoice = Invoice(
            开票日期=data.get('开票日期'),
            合同号=data.get('合同号', ''),
            付款单位名称=data.get('付款单位名称'),
            代码=data.get('代码'),
            发票金额=data.get('发票金额'),
            发票项目=data.get('发票项目'),
            类型=data.get('类型'),
            发票类型=data.get('发票类型'),
            除税=data.get('除税'),
            备注=data.get('备注')
        )
        
        success, msg = self.db.add_invoice(invoice)
        
        if success:
            messagebox.showinfo("成功", "发票添加成功")
            self._update_invoices_table()
        else:
            messagebox.showerror("错误", msg)
    
    def _sort_invoice_tree(self, col: str):
        """排序发票表格"""
        items = [(self.invoice_tree.set(item, col), item) for item in self.invoice_tree.get_children('')]
        
        try:
            items.sort(reverse=False, key=lambda x: float(x[0].replace(',', '')))
        except:
            items.sort(reverse=False, key=lambda x: x[0])
        
        for index, (val, item) in enumerate(items):
            self.invoice_tree.move(item, '', index)
    
    # ==================== 到期预警 ====================
    
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
        
        btn_frame = ctk.CTkFrame(header, fg_color='transparent')
        btn_frame.pack(side='right')
        
        ModernButton(btn_frame, "导出", command=self._export_warnings, style='primary').pack(side='left', padx=5)
        
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
        
        # 快速过滤和搜索
        filter_frame = ctk.CTkFrame(self.content_area, fg_color='white', corner_radius=10)
        filter_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        filter_inner = ctk.CTkFrame(filter_frame, fg_color='transparent')
        filter_inner.pack(fill='x', padx=15, pady=15)
        
        # 快速过滤单选按钮
        ctk.CTkLabel(filter_inner, text="快速过滤:", font=ctk.CTkFont(size=13)).pack(side='left', padx=(0, 10))
        
        self.warning_filter = ctk.StringVar(value='全部')
        
        for text, value in [('全部', '全部'), ('已超期', 'red'), ('7天内', 'orange'), ('30天内', 'yellow')]:
            rb = ctk.CTkRadioButton(
                filter_inner,
                text=text,
                variable=self.warning_filter,
                value=value,
                command=self._filter_warnings
            )
            rb.pack(side='left', padx=10)
        
        # 搜索框
        self.warning_search_entry = ctk.CTkEntry(
            filter_inner,
            placeholder_text="搜索合同编号、名称...",
            width=200
        )
        self.warning_search_entry.pack(side='left', padx=(20, 0))
        self.warning_search_entry.bind('<KeyRelease>', lambda e: self._filter_warnings())
        
        # 预警列表
        table_frame = ctk.CTkFrame(self.content_area, fg_color='white', corner_radius=10)
        table_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        self.warning_tree = ttk.Treeview(
            table_frame,
            columns=['合同编号', '合同名称', '对方单位', '区域', '销售负责人', '合同额', '到期日期', '剩余天数', '开票金额', '到款金额', '应收账款'],
            show='headings',
            style='Custom.Treeview'
        )
        
        columns_config = [
            ('合同编号', 120), ('合同名称', 180), ('对方单位', 150), ('区域', 100),
            ('销售负责人', 100), ('合同额', 100), ('到期日期', 110), ('剩余天数', 100),
            ('开票金额', 100), ('到款金额', 100), ('应收账款', 100)
        ]
        
        for col, width in columns_config:
            self.warning_tree.heading(col, text=col)
            self.warning_tree.column(col, width=width, anchor='center')
        
        # 配置标签颜色
        self.warning_tree.tag_configure('warning_yellow', background='#FFF3CD')
        self.warning_tree.tag_configure('warning_orange', background='#FFE5B4')
        self.warning_tree.tag_configure('warning_red', background='#FFCCCC')
        
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.warning_tree.yview)
        self.warning_tree.configure(yscrollcommand=scrollbar.set)
        
        self.warning_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 加载数据
        self._update_warnings_table(warning_data)
    
    def _filter_warnings(self):
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
        
        self._update_warnings_table(warning_data)
    
    def _update_warnings_table(self, warning_data: List[Dict]):
        """更新预警表格"""
        for item in self.warning_tree.get_children():
            self.warning_tree.delete(item)
        
        for item in warning_data:
            contract = item['contract']
            days = item['days']
            level = item['level']
            
            status_map = {
                'red': '已超期',
                'orange': '即将到期',
                'yellow': '需关注'
            }
            
            tag = f'warning_{level}'
            
            self.warning_tree.insert('', 'end', values=(
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
    
    def _export_warnings(self):
        """导出预警列表"""
        file_path = filedialog.asksaveasfilename(
            title="保存文件",
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx")]
        )
        
        if not file_path:
            return
        
        # TODO: 实现导出功能
        messagebox.showinfo("提示", "导出功能开发中...")
    
    # ==================== 应收账款 ====================
    
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
        
        btn_frame = ctk.CTkFrame(header, fg_color='transparent')
        btn_frame.pack(side='right')
        
        ModernButton(btn_frame, "导出", command=self._export_receivables, style='primary').pack(side='left', padx=5)
        
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
        
        # 搜索栏
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
        table_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        self.receivable_tree = ttk.Treeview(
            table_frame,
            columns=['合同编号', '对方单位', '合同额', '到款金额', '应收账款', '销售负责人', '催款状态'],
            show='headings',
            style='Custom.Treeview'
        )
        
        columns_config = [
            ('合同编号', 120), ('对方单位', 150), ('合同额', 100),
            ('到款金额', 100), ('应收账款', 100), ('销售负责人', 100), ('催款状态', 100)
        ]
        
        for col, width in columns_config:
            self.receivable_tree.heading(col, text=col)
            self.receivable_tree.column(col, width=width, anchor='center')
        
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.receivable_tree.yview)
        self.receivable_tree.configure(yscrollcommand=scrollbar.set)
        
        self.receivable_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.receivable_tree.bind('<Double-1>', lambda e: self._show_collection_dialog())
        self.receivable_tree.bind('<Button-3>', self._show_receivable_context_menu)
        
        # 加载数据
        self._update_receivables_table()
    
    def _update_receivables_table(self):
        """更新应收账款表格"""
        for item in self.receivable_tree.get_children():
            self.receivable_tree.delete(item)
        
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
    
    def _show_collection_dialog(self):
        """显示催款记录对话框"""
        selection = self.receivable_tree.selection()
        if not selection:
            return
        
        item = self.receivable_tree.item(selection[0])
        contract_no = item['values'][0]
        
        dialog = CollectionRecordDialog(
            self,
            contract_no=contract_no,
            on_save=self._save_collection_record
        )
    
    def _save_collection_record(self, data: Dict):
        """保存催款记录"""
        record = CollectionRecord(
            合同编号=data.get('合同编号', ''),
            催款日期=data.get('催款日期'),
            催款方式=data.get('催款方式'),
            联系人=data.get('联系人'),
            催款内容=data.get('催款内容'),
            对方反馈=data.get('对方反馈'),
            催款结果=data.get('催款结果')
        )
        
        if self.db.add_collection_record(record):
            messagebox.showinfo("成功", "催款记录已保存")
        else:
            messagebox.showerror("错误", "保存失败")
    
    def _show_receivable_context_menu(self, event):
        """显示应收账款右键菜单"""
        menu = ctk.CTkMenu(self)
        menu.add_command(label="添加催款记录", command=self._show_collection_dialog)
        menu.add_command(label="查看催款历史", command=self._view_collection_history)
        menu.post(event.x_root, event.y_root)
    
    def _view_collection_history(self):
        """查看催款历史"""
        selection = self.receivable_tree.selection()
        if not selection:
            return
        
        item = self.receivable_tree.item(selection[0])
        contract_no = item['values'][0]
        
        records = self.db.get_collection_records(contract_no)
        
        if not records:
            messagebox.showinfo("提示", "暂无催款记录")
            return
        
        # 显示催款记录
        msg = f"合同编号: {contract_no}\n\n催款记录:\n"
        for r in records:
            msg += f"\n{r.催款日期} - {r.催款方式} - {r.催款结果}\n"
        
        messagebox.showinfo("催款历史", msg)
    
    def _export_receivables(self):
        """导出应收账款"""
        file_path = filedialog.asksaveasfilename(
            title="保存文件",
            defaultextension=".xlsx",
            filetypes=[("Excel 文件", "*.xlsx")]
        )
        
        if not file_path:
            return
        
        # TODO: 实现导出
        messagebox.showinfo("提示", "导出功能开发中...")
    
    # ==================== 统计分析 ====================
    
    def _show_yearly_stats_tab(self):
        """显示年度统计标签页"""
        self._clear_content_area()
        
        # 标题
        header = ctk.CTkFrame(self.content_area, fg_color='transparent', height=60)
        header.pack(fill='x', padx=20, pady=20)
        header.pack_propagate(False)
        
        title = ctk.CTkLabel(
            header,
            text="年度统计分析",
            font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=UI_CONFIG['font_size']['title'], weight='bold'),
            text_color='#2c3e50'
        )
        title.pack(side='left')
        
        # 统计表格
        table_frame = ctk.CTkFrame(self.content_area, fg_color='white', corner_radius=10)
        table_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        stats = self.db.get_yearly_stats()
        
        # TODO: 实现年度统计图表
        ctk.CTkLabel(
            table_frame,
            text="年度统计图表（开发中）",
            font=ctk.CTkFont(size=16)
        ).pack(pady=50)
    
    def _show_region_stats_tab(self):
        """显示区域统计标签页"""
        self._clear_content_area()
        
        # 标题
        header = ctk.CTkFrame(self.content_area, fg_color='transparent', height=60)
        header.pack(fill='x', padx=20, pady=20)
        header.pack_propagate(False)
        
        title = ctk.CTkLabel(
            header,
            text="区域统计分析",
            font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=UI_CONFIG['font_size']['title'], weight='bold'),
            text_color='#2c3e50'
        )
        title.pack(side='left')
        
        # 图表区域
        charts_frame = ctk.CTkFrame(self.content_area, fg_color='transparent')
        charts_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # 生成图表
        self._generate_region_chart(charts_frame)
    
    def _generate_region_chart(self, parent):
        """生成区域统计图表"""
        stats = self.contract_service.get_statistics(self.contracts_cache)
        
        if not stats['by_region']:
            ctk.CTkLabel(
                parent,
                text="暂无数据",
                font=ctk.CTkFont(size=16)
            ).pack(pady=50)
            return
        
        # 创建饼图
        fig = go.Figure(data=[go.Pie(
            labels=list(stats['by_region'].keys()),
            values=list(stats['by_region'].values()),
            hole=0.4,
            marker_colors=px.colors.qualitative.Set3
        )])
        fig.update_layout(
            title='合同额按区域分布',
            font=dict(family='Microsoft YaHei UI', size=14),
            height=500
        )
        
        # 保存为HTML
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as f:
            fig.write_html(f.name)
            html_path = f.name
        
        # 显示按钮
        ctk.CTkLabel(
            parent,
            text="📊 按区域分布",
            font=ctk.CTkFont(size=16, weight='bold')
        ).pack(pady=20)
        
        ModernButton(
            parent,
            text="查看图表",
            command=lambda: webbrowser.open(f'file://{html_path}'),
            style='primary'
        ).pack(pady=10)
        
        ctk.CTkLabel(
            parent,
            text=f"共 {len(stats['by_region'])} 个区域",
            font=ctk.CTkFont(size=13),
            text_color='#7f8c8d'
        ).pack(pady=10)
    
    def _show_salesperson_stats_tab(self):
        """显示销售负责人统计标签页"""
        self._clear_content_area()
        
        # 标题
        header = ctk.CTkFrame(self.content_area, fg_color='transparent', height=60)
        header.pack(fill='x', padx=20, pady=20)
        header.pack_propagate(False)
        
        title = ctk.CTkLabel(
            header,
            text="销售负责人统计",
            font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=UI_CONFIG['font_size']['title'], weight='bold'),
            text_color='#2c3e50'
        )
        title.pack(side='left')
        
        # 图表区域
        charts_frame = ctk.CTkFrame(self.content_area, fg_color='transparent')
        charts_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # 生成图表
        self._generate_salesperson_chart(charts_frame)
    
    def _generate_salesperson_chart(self, parent):
        """生成销售负责人统计图表"""
        stats = self.contract_service.get_statistics(self.contracts_cache)
        
        if not stats['by_salesperson']:
            ctk.CTkLabel(
                parent,
                text="暂无数据",
                font=ctk.CTkFont(size=16)
            ).pack(pady=50)
            return
        
        # 创建柱状图
        fig = go.Figure(data=[go.Bar(
            x=list(stats['by_salesperson'].keys()),
            y=list(stats['by_salesperson'].values()),
            marker_color='#3498db'
        )])
        fig.update_layout(
            title='合同额按销售负责人分布',
            font=dict(family='Microsoft YaHei UI', size=14),
            height=500,
            xaxis_tickangle=-45
        )
        
        # 保存为HTML
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as f:
            fig.write_html(f.name)
            html_path = f.name
        
        # 显示按钮
        ctk.CTkLabel(
            parent,
            text="📊 按销售负责人",
            font=ctk.CTkFont(size=16, weight='bold')
        ).pack(pady=20)
        
        ModernButton(
            parent,
            text="查看图表",
            command=lambda: webbrowser.open(f'file://{html_path}'),
            style='primary'
        ).pack(pady=10)
        
        ctk.CTkLabel(
            parent,
            text=f"共 {len(stats['by_salesperson'])} 位销售",
            font=ctk.CTkFont(size=13),
            text_color='#7f8c8d'
        ).pack(pady=10)
    
    # ==================== 数据管理 ====================
    
    def _show_data_management_tab(self):
        """显示数据管理标签页"""
        self._clear_content_area()
        
        # 标题
        header = ctk.CTkFrame(self.content_area, fg_color='transparent', height=60)
        header.pack(fill='x', padx=20, pady=20)
        header.pack_propagate(False)
        
        title = ctk.CTkLabel(
            header,
            text="数据管理",
            font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=UI_CONFIG['font_size']['title'], weight='bold'),
            text_color='#2c3e50'
        )
        title.pack(side='left')
        
        # 功能卡片
        cards_frame = ctk.CTkFrame(self.content_area, fg_color='transparent')
        cards_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # 备份数据库
        backup_card = ctk.CTkFrame(cards_frame, fg_color='white', corner_radius=10)
        backup_card.pack(fill='x', pady=10)
        
        ctk.CTkLabel(
            backup_card,
            text="💾 备份数据库",
            font=ctk.CTkFont(size=16, weight='bold')
        ).pack(pady=(20, 10), padx=20, anchor='w')
        
        ctk.CTkLabel(
            backup_card,
            text="将当前数据库导出为备份文件",
            font=ctk.CTkFont(size=13),
            text_color='#7f8c8d'
        ).pack(padx=20, anchor='w')
        
        ModernButton(
            backup_card,
            text="备份数据库",
            command=self._backup_database,
            style='primary'
        ).pack(pady=20, padx=20, anchor='w')
        
        # 恢复数据库
        restore_card = ctk.CTkFrame(cards_frame, fg_color='white', corner_radius=10)
        restore_card.pack(fill='x', pady=10)
        
        ctk.CTkLabel(
            restore_card,
            text="📥 恢复数据库",
            font=ctk.CTkFont(size=16, weight='bold')
        ).pack(pady=(20, 10), padx=20, anchor='w')
        
        ctk.CTkLabel(
            restore_card,
            text="从备份文件恢复数据库（将覆盖当前数据）",
            font=ctk.CTkFont(size=13),
            text_color='#7f8c8d'
        ).pack(padx=20, anchor='w')
        
        ModernButton(
            restore_card,
            text="恢复数据库",
            command=self._restore_database,
            style='warning'
        ).pack(pady=20, padx=20, anchor='w')
    
    def _backup_database(self):
        """备份数据库"""
        from config import DB_PATH
        
        file_path = filedialog.asksaveasfilename(
            title="保存备份",
            defaultextension=".db",
            filetypes=[("数据库文件", "*.db"), ("所有文件", "*.*")],
            initialfile=f"contracts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        )
        
        if not file_path:
            return
        
        try:
            shutil.copy2(DB_PATH, file_path)
            messagebox.showinfo("成功", f"数据库已备份到:\n{file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"备份失败: {str(e)}")
    
    def _restore_database(self):
        """恢复数据库"""
        from config import DB_PATH
        
        if not messagebox.askyesno("确认", "恢复数据库将覆盖当前所有数据，是否继续？"):
            return
        
        file_path = filedialog.askopenfilename(
            title="选择备份文件",
            filetypes=[("数据库文件", "*.db"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            shutil.copy2(file_path, DB_PATH)
            messagebox.showinfo("成功", "数据库已恢复，程序将重启")
            self.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"恢复失败: {str(e)}")
    
    # ==================== 导入导出 ====================
    
    def _import_contracts(self):
        """导入合同"""
        file_path = filedialog.askopenfilename(
            title="选择要导入的文件",
            filetypes=[("Excel 文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        def import_data():
            success, fail, errors = self.contract_service.import_from_excel(file_path)
            self.after(0, lambda: self._show_import_result(success, fail, errors))
        
        thread = threading.Thread(target=import_data, daemon=True)
        thread.start()
    
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
        else:
            messagebox.showerror("导出失败", "导出过程中出现错误")
    
    def _show_import_result(self, success: int, fail: int, errors: List[str]):
        """显示导入结果"""
        msg = f"导入完成\n成功: {success} 条\n失败: {fail} 条"
        if errors:
            msg += f"\n\n错误信息:\n" + '\n'.join(errors[:5])
            if len(errors) > 5:
                msg += f"\n...还有 {len(errors) - 5} 条错误"
        
        messagebox.showinfo("导入结果", msg)
        self._load_initial_data()
    
    # ==================== 数据加载 ====================
    
    def _load_initial_data(self):
        """加载初始数据"""
        def load_data():
            self.contracts_cache = self.contract_service.get_all_contracts()
            self.invoices_cache = self.invoice_service.get_all_invoices()
            
            # 更新UI
            self.after(0, self._update_contracts_table)
            self.after(0, self._update_invoices_table)
            self.after(0, self._update_filter_combos)
        
        thread = threading.Thread(target=load_data, daemon=True)
        thread.start()
    
    def _update_contracts_table(self):
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
            ))
        
        total_amount = sum(c.合同额 or 0 for c in self.contracts_cache)
        self.stats_label.configure(
            text=f"共 {len(self.contracts_cache)} 条记录，总金额: ¥{safe_format_money(total_amount)}"
        )
    
    def _update_invoices_table(self):
        """更新发票表格"""
        if hasattr(self, 'invoice_tree'):
            for item in self.invoice_tree.get_children():
                self.invoice_tree.delete(item)
            
            for invoice in self.invoices_cache:
                self.invoice_tree.insert('', 'end', values=(
                    invoice.开票日期 or '',
                    invoice.合同号,
                    invoice.付款单位名称 or '',
                    safe_format_money(invoice.发票金额),
                    invoice.发票项目 or '',
                    invoice.类型 or '',
                    invoice.发票类型 or '',
                    safe_format_money(invoice.除税),
                    invoice.备注 or ''
                ))
    
    def _update_filter_combos(self):
        """更新筛选下拉框"""
        regions = self.contract_service.get_distinct_regions()
        salespersons = self.contract_service.get_distinct_salespersons()
        
        if hasattr(self, 'region_combo'):
            self.region_combo.configure(values=['全部'] + regions)
        if hasattr(self, 'salesperson_combo'):
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
    
    def _search_invoices(self):
        """搜索发票"""
        search_text = self.invoice_search_entry.get()
        filters = {'search': search_text} if search_text else None
        self.invoices_cache = self.invoice_service.get_all_invoices(filters)
        self._update_invoices_table()



    
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

    def _search_receivables(self):
        """搜索应收账款"""
        search_text = self.receivable_search_entry.get().lower()
        
        for item in self.receivable_tree.get_children():
            self.receivable_tree.delete(item)
        
        for contract in self.contracts_cache:
            if contract.应收账款 and contract.应收账款 > 0:
                # 搜索过滤
                if search_text:
                    if search_text not in contract.合同编号.lower() and \
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

def main():
    """主函数"""
    app = ContractManagerApp()
    app.mainloop()


if __name__ == '__main__':
    main()
