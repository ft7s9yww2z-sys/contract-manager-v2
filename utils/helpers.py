#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数模块
"""

import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


def safe_format_money(value: Any, default: str = '0.00') -> str:
    """安全格式化金额，处理字符串、None、空值等情况"""
    if value is None or value == '':
        return default
    
    try:
        # 如果是字符串，尝试转换
        if isinstance(value, str):
            value = value.replace(',', '').strip()
            if not value:
                return default
            value = float(value)
        
        # 如果是数字，直接格式化
        if isinstance(value, (int, float)):
            return f'{value:,.2f}'
        
        return str(value)
    except (ValueError, AttributeError, TypeError):
        return str(value) if value else default


def normalize_header(header: str) -> str:
    """标准化表头名称，去除空格、统一命名"""
    from config import HEADER_MAPPING
    
    if not header:
        return ''
    
    # 去除空格、换行等
    header = str(header).strip().replace(' ', '').replace('\n', '').replace('\r', '')
    
    # 查找映射
    for standard_name, variants in HEADER_MAPPING.items():
        if header in variants:
            return standard_name
    
    return header


def generate_hash(data: Dict, fields: List[str]) -> str:
    """生成数据哈希用于去重"""
    hash_str = '|'.join([str(data.get(f, '')) for f in fields])
    return hashlib.md5(hash_str.encode('utf-8')).hexdigest()


def parse_date(date_str: str) -> Optional[datetime]:
    """解析日期字符串"""
    if not date_str:
        return None
    
    date_formats = [
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%Y.%m.%d',
        '%Y年%m月%d日',
        '%m/%d/%Y',
        '%d/%m/%Y'
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except ValueError:
            continue
    
    return None


def format_date(date_obj: Optional[datetime], fmt: str = '%Y-%m-%d') -> str:
    """格式化日期对象"""
    if not date_obj:
        return ''
    return date_obj.strftime(fmt)


def get_days_until_deadline(deadline_str: str) -> Optional[int]:
    """计算距离截止日期的天数"""
    deadline = parse_date(deadline_str)
    if not deadline:
        return None
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    deadline = deadline.replace(hour=0, minute=0, second=0, microsecond=0)
    
    delta = deadline - today
    return delta.days


def get_warning_level(days: Optional[int]) -> str:
    """根据天数获取预警级别"""
    from config import WARNING_CONFIG
    
    if days is None:
        return 'none'
    
    if days < WARNING_CONFIG['red_days']:
        return 'red'
    elif days <= WARNING_CONFIG['orange_days']:
        return 'orange'
    elif days <= WARNING_CONFIG['yellow_days']:
        return 'yellow'
    else:
        return 'none'


def validate_contract_data(data: Dict) -> tuple[bool, str]:
    """验证合同数据"""
    if not data.get('合同编号'):
        return False, "合同编号不能为空"
    
    # 验证金额字段
    amount_fields = ['参考金额', '合同额', '开票金额', '开票余额', '到款金额', '合同余额', '应收账款', '项目预算']
    for field in amount_fields:
        value = data.get(field)
        if value and not isinstance(value, (int, float)):
            try:
                float(str(value).replace(',', ''))
            except ValueError:
                return False, f"{field} 格式错误"
    
    # 验证日期字段
    date_fields = ['下单日期', '合同评审日期', '合同签字日期', 'crm日期', 
                   '合同起始日期', '合同终止日期', '开票日期']
    for field in date_fields:
        value = data.get(field)
        if value and not parse_date(str(value)):
            return False, f"{field} 日期格式错误"
    
    return True, "验证通过"


def calculate_statistics(contracts: List[Dict]) -> Dict:
    """计算统计数据"""
    if not contracts:
        return {
            'total_count': 0,
            'total_amount': 0,
            'avg_amount': 0,
            'max_amount': 0,
            'min_amount': 0
        }
    
    amounts = []
    for contract in contracts:
        amount = contract.get('合同额', 0)
        if isinstance(amount, (int, float)):
            amounts.append(amount)
        elif isinstance(amount, str):
            try:
                amounts.append(float(amount.replace(',', '')))
            except:
                pass
    
    if not amounts:
        amounts = [0]
    
    return {
        'total_count': len(contracts),
        'total_amount': sum(amounts),
        'avg_amount': sum(amounts) / len(amounts),
        'max_amount': max(amounts),
        'min_amount': min(amounts)
    }
