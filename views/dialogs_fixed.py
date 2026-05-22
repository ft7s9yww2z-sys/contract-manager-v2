#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话框组件 - 修复版
"""

import customtkinter as ctk
from tkinter import ttk
from typing import Optional, Dict, List, Callable
from datetime import datetime
from tkcalendar import DateEntry
import tkinter as tk

from config import UI_CONFIG, CONTRACT_FIELDS, INVOICE_FIELDS
from utils.helpers import safe_format_money


class ContractDialog(ctk.CTkToplevel):
    """合同添加/编辑对话框 - 修复版"""
    
    def __init__(self, parent, contract_data: Optional[Dict] = None, 
                 regions: List[str] = None, salespersons: List[str] = None,
                 on_save: Callable = None):
        super().__init__(parent)
        
        self.contract_data = contract_data or {}
        self.regions = regions or []
        self.salespersons = salespersons or []
        self.on_save = on_save
        self.result = None
        
        # 设置窗口
        self.title("编辑合同" if contract_data else "添加合同")
        self.geometry("1000x750")
        self.resizable(False, False)
        
        # 模态对话框
        self.transient(parent)
        self.grab_set()
        
        # 创建UI
        self._create_ui()
        
        # 居中显示
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        self.wait_window()
    
    def _create_ui(self):
        """创建UI"""
        # 主容器
        main_frame = ctk.CTkFrame(self, fg_color='transparent')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 标题
        title = ctk.CTkLabel(
            main_frame,
            text="编辑合同信息" if self.contract_data else "添加新合同",
            font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=18, weight='bold'),
            text_color='#2c3e50'
        )
        title.pack(pady=(0, 20))
        
        # 表单容器（使用 Canvas 支持滚动）
        canvas_frame = ctk.CTkFrame(main_frame, fg_color='transparent')
        canvas_frame.pack(fill='both', expand=True)
        
        canvas = tk.Canvas(canvas_frame, highlightthickness=0, bg='#f5f5f5')
        scrollbar = ctk.CTkScrollbar(canvas_frame, orientation="vertical", command=canvas.yview)
        scrollable_frame = ctk.CTkFrame(canvas, fg_color='transparent')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=940)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 输入字段
        self.entries = {}
        
        # 分组字段
        groups = [
            ('基本信息', ['合同编号', '合同名称', '项目代码', '对方单位名称', '区域', '销售负责人']),
            ('日期信息', ['下单日期', '合同评审日期', '合同签字日期', 'crm日期', '合同起始日期', '合同终止日期']),
            ('金额信息', ['参考金额', '合同额', '开票金额', '开票余额', '到款金额', '合同余额', '应收账款', '项目预算']),
            ('联系信息', ['联系人', '联系电话']),
            ('其他信息', ['序号', '是否变更', '到款情况', '设备数量', '合同内容', '备注'])
        ]
        
        for group_name, fields in groups:
            # 组标题
            group_label = ctk.CTkLabel(
                scrollable_frame,
                text=group_name,
                font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=14, weight='bold'),
                text_color='#3498db'
            )
            group_label.pack(anchor='w', pady=(15, 10), padx=10)
            
            # 字段网格
            frame = ctk.CTkFrame(scrollable_frame, fg_color='transparent')
            frame.pack(fill='x', pady=5, padx=10)
            
            for idx, field in enumerate(fields):
                row = idx // 2
                col = idx % 2
                
                field_frame = ctk.CTkFrame(frame, fg_color='transparent')
                field_frame.grid(row=row, column=col, padx=10, pady=8, sticky='ew')
                
                # 标签
                label = ctk.CTkLabel(
                    field_frame,
                    text=field + ":",
                    font=ctk.CTkFont(size=12),
                    width=120,
                    anchor='e'
                )
                label.pack(side='left', padx=(0, 10))
                
                # 输入框或下拉框
                value = self.contract_data.get(field, '')
                
                if field == '区域':
                    entry = ctk.CTkComboBox(
                        field_frame,
                        values=self.regions,
                        font=ctk.CTkFont(size=12),
                        width=300
                    )
                    entry.set(str(value) if value else '')
                elif field == '销售负责人':
                    entry = ctk.CTkComboBox(
                        field_frame,
                        values=self.salespersons,
                        font=ctk.CTkFont(size=12),
                        width=300
                    )
                    entry.set(str(value) if value else '')
                elif field == '是否变更':
                    entry = ctk.CTkComboBox(
                        field_frame,
                        values=['是', '否'],
                        font=ctk.CTkFont(size=12),
                        width=300
                    )
                    entry.set(str(value) if value else '否')
                elif field in ['下单日期', '合同评审日期', '合同签字日期', 'crm日期', '合同起始日期', '合同终止日期', '开票日期']:
                    # 使用日期选择器
                    date_frame = ctk.CTkFrame(field_frame, fg_color='transparent')
                    date_frame.pack(side='left')
                    
                    entry = DateEntry(
                        date_frame,
                        width=30,
                        background='darkblue',
                        foreground='white',
                        borderwidth=2,
                        date_pattern='yyyy-mm-dd'
                    )
                    entry.pack(side='left')
                    
                    # 设置默认值
                    if value:
                        try:
                            date_obj = datetime.strptime(str(value), '%Y-%m-%d')
                            entry.set_date(date_obj)
                        except:
                            pass
                elif field in ['合同内容', '备注']:
                    entry = ctk.CTkTextbox(field_frame, height=80, width=300)
                    if value:
                        entry.insert('1.0', str(value))
                else:
                    entry = ctk.CTkEntry(
                        field_frame,
                        font=ctk.CTkFont(size=12),
                        width=300
                    )
                    entry.insert(0, str(value) if value else '')
                
                entry.pack(side='left')
                self.entries[field] = entry
            
            frame.columnconfigure(0, weight=1)
            frame.columnconfigure(1, weight=1)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 按钮区域
        btn_frame = ctk.CTkFrame(main_frame, fg_color='transparent')
        btn_frame.pack(fill='x', pady=(20, 0))
        
        ctk.CTkButton(
            btn_frame,
            text="保存",
            command=self._save,
            font=ctk.CTkFont(size=13),
            fg_color='#3498db',
            hover_color='#2980b9',
            width=100
        ).pack(side='right', padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="取消",
            command=self._cancel,
            font=ctk.CTkFont(size=13),
            fg_color='#95a5a6',
            hover_color='#7f8c8d',
            width=100
        ).pack(side='right', padx=5)
    
    def _save(self):
        """保存数据"""
        data = {}
        
        for field, entry in self.entries.items():
            if isinstance(entry, ctk.CTkTextbox):
                value = entry.get('1.0', 'end').strip()
            elif isinstance(entry, ctk.CTkComboBox):
                value = entry.get()
            elif isinstance(entry, DateEntry):
                value = entry.get_date().strftime('%Y-%m-%d')
            else:
                value = entry.get().strip()
            
            # 数值字段转换
            if field in ['参考金额', '合同额', '开票金额', '开票余额', '到款金额', '合同余额', '应收账款', '项目预算']:
                try:
                    data[field] = float(value.replace(',', '')) if value else None
                except:
                    data[field] = None
            elif field in ['序号', '设备数量']:
                try:
                    data[field] = int(value) if value else None
                except:
                    data[field] = None
            else:
                data[field] = value if value else None
        
        # 只要有一个字段不为空就可以保存
        has_data = any(v is not None and v != '' for v in data.values())
        if not has_data:
            ctk.CTkMessagebox(title="错误", message="至少填写一个字段", icon="cancel")
            return
        
        self.result = data
        
        if self.on_save:
            self.on_save(data)
        
        self.destroy()
    
    def _cancel(self):
        """取消"""
        self.result = None
        self.destroy()


class InvoiceDialog(ctk.CTkToplevel):
    """发票添加/编辑对话框"""
    
    def __init__(self, parent, invoice_data: Optional[Dict] = None, on_save: Callable = None):
        super().__init__(parent)
        
        self.invoice_data = invoice_data or {}
        self.on_save = on_save
        self.result = None
        
        # 设置窗口
        self.title("编辑发票" if invoice_data else "添加发票")
        self.geometry("700x550")
        self.resizable(False, False)
        
        # 模态对话框
        self.transient(parent)
        self.grab_set()
        
        # 创建UI
        self._create_ui()
        
        # 居中显示
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        self.wait_window()
    
    def _create_ui(self):
        """创建UI"""
        # 主容器
        main_frame = ctk.CTkFrame(self, fg_color='transparent')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 标题
        title = ctk.CTkLabel(
            main_frame,
            text="编辑发票信息" if self.invoice_data else "添加新发票",
            font=ctk.CTkFont(family=UI_CONFIG['font_family'], size=18, weight='bold'),
            text_color='#2c3e50'
        )
        title.pack(pady=(0, 20))
        
        # 表单
        form_frame = ctk.CTkFrame(main_frame, fg_color='transparent')
        form_frame.pack(fill='both', expand=True)
        
        self.entries = {}
        
        for idx, field in enumerate(INVOICE_FIELDS):
            row = idx // 2
            col = idx % 2
            
            field_frame = ctk.CTkFrame(form_frame, fg_color='transparent')
            field_frame.grid(row=row, column=col, padx=10, pady=10, sticky='ew')
            
            # 标签
            label = ctk.CTkLabel(
                field_frame,
                text=field + ":",
                font=ctk.CTkFont(size=12),
                width=120,
                anchor='e'
            )
            label.pack(side='left', padx=(0, 10))
            
            value = self.invoice_data.get(field, '')
            
            # 日期字段使用日期选择器
            if field == '开票日期':
                date_frame = ctk.CTkFrame(field_frame, fg_color='transparent')
                date_frame.pack(side='left')
                
                entry = DateEntry(
                    date_frame,
                    width=35,
                    background='darkblue',
                    foreground='white',
                    borderwidth=2,
                    date_pattern='yyyy-mm-dd'
                )
                entry.pack(side='left')
                
                if value:
                    try:
                        date_obj = datetime.strptime(str(value), '%Y-%m-%d')
                        entry.set_date(date_obj)
                    except:
                        pass
            else:
                # 输入框
                entry = ctk.CTkEntry(
                    field_frame,
                    font=ctk.CTkFont(size=12),
                    width=250
                )
                entry.insert(0, str(value) if value else '')
                entry.pack(side='left')
            
            self.entries[field] = entry
        
        form_frame.columnconfigure(0, weight=1)
        form_frame.columnconfigure(1, weight=1)
        
        # 按钮
        btn_frame = ctk.CTkFrame(main_frame, fg_color='transparent')
        btn_frame.pack(fill='x', pady=(20, 0))
        
        ctk.CTkButton(
            btn_frame,
            text="保存",
            command=self._save,
            font=ctk.CTkFont(size=13),
            fg_color='#3498db',
            width=100
        ).pack(side='right', padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="取消",
            command=self._cancel,
            font=ctk.CTkFont(size=13),
            fg_color='#95a5a6',
            width=100
        ).pack(side='right', padx=5)
    
    def _save(self):
        """保存"""
        data = {}
        
        for field, entry in self.entries.items():
            if isinstance(entry, DateEntry):
                value = entry.get_date().strftime('%Y-%m-%d')
            else:
                value = entry.get().strip()
            
            if field in ['发票金额', '除税']:
                try:
                    data[field] = float(value.replace(',', '')) if value else None
                except:
                    data[field] = None
            else:
                data[field] = value if value else None
        
        # 只要有一个字段不为空就可以保存
        has_data = any(v is not None and v != '' for v in data.values())
        if not has_data:
            ctk.CTkMessagebox(title="错误", message="至少填写一个字段", icon="cancel")
            return
        
        self.result = data
        
        if self.on_save:
            self.on_save(data)
        
        self.destroy()
    
    def _cancel(self):
        """取消"""
        self.result = None
        self.destroy()


class CollectionRecordDialog(ctk.CTkToplevel):
    """催款记录对话框"""
    
    def __init__(self, parent, contract_no: str, on_save: Callable = None):
        super().__init__(parent)
        
        self.contract_no = contract_no
        self.on_save = on_save
        self.result = None
        
        # 设置窗口
        self.title("添加催款记录")
        self.geometry("500x450")
        self.resizable(False, False)
        
        # 模态对话框
        self.transient(parent)
        self.grab_set()
        
        # 创建UI
        self._create_ui()
        
        # 居中
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        self.wait_window()
    
    def _create_ui(self):
        """创建UI"""
        main_frame = ctk.CTkFrame(self, fg_color='transparent')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 标题
        title = ctk.CTkLabel(
            main_frame,
            text=f"催款记录 - {self.contract_no}",
            font=ctk.CTkFont(size=16, weight='bold')
        )
        title.pack(pady=(0, 20))
        
        # 表单
        fields = [
            ('催款日期', 'date'),
            ('催款方式', 'combo'),
            ('联系人', 'text'),
            ('催款内容', 'text'),
            ('对方反馈', 'text'),
            ('催款结果', 'combo')
        ]
        
        self.entries = {}
        
        for field, field_type in fields:
            frame = ctk.CTkFrame(main_frame, fg_color='transparent')
            frame.pack(fill='x', pady=8)
            
            label = ctk.CTkLabel(frame, text=field + ":", width=100, anchor='e')
            label.pack(side='left', padx=(0, 10))
            
            if field_type == 'date':
                date_frame = ctk.CTkFrame(frame, fg_color='transparent')
                date_frame.pack(side='left')
                
                entry = DateEntry(
                    date_frame,
                    width=35,
                    background='darkblue',
                    foreground='white',
                    borderwidth=2,
                    date_pattern='yyyy-mm-dd'
                )
                entry.pack(side='left')
            elif field_type == 'combo':
                if field == '催款方式':
                    values = ['电话', '邮件', '上门', '微信', '其他']
                else:
                    values = ['已承诺付款', '已回款', '继续跟进', '无回应', '坏账']
                
                entry = ctk.CTkComboBox(frame, values=values, width=300)
                entry.set(values[0])
                entry.pack(side='left')
            else:
                entry = ctk.CTkEntry(frame, width=300)
                entry.pack(side='left')
            
            self.entries[field] = entry
        
        # 按钮
        btn_frame = ctk.CTkFrame(main_frame, fg_color='transparent')
        btn_frame.pack(fill='x', pady=(20, 0))
        
        ctk.CTkButton(btn_frame, text="保存", command=self._save, width=100).pack(side='right', padx=5)
        ctk.CTkButton(btn_frame, text="取消", command=self._cancel, fg_color='#95a5a6', width=100).pack(side='right', padx=5)
    
    def _save(self):
        """保存"""
        self.result = {}
        
        for field, entry in self.entries.items():
            if isinstance(entry, DateEntry):
                self.result[field] = entry.get_date().strftime('%Y-%m-%d')
            elif isinstance(entry, ctk.CTkComboBox):
                self.result[field] = entry.get()
            else:
                self.result[field] = entry.get()
        
        self.result['合同编号'] = self.contract_no
        
        if self.on_save:
            self.on_save(self.result)
        
        self.destroy()
    
    def _cancel(self):
        """取消"""
        self.result = None
        self.destroy()
