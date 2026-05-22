#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型定义
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Contract:
    """合同数据模型"""
    序号: Optional[int] = None
    下单日期: Optional[str] = None
    合同编号: str = ''
    项目代码: Optional[str] = None
    是否变更: Optional[str] = None
    合同评审日期: Optional[str] = None
    合同签字日期: Optional[str] = None
    crm日期: Optional[str] = None
    合同名称: Optional[str] = None
    对方单位名称: Optional[str] = None
    区域: Optional[str] = None
    销售负责人: Optional[str] = None
    参考金额: Optional[float] = None
    合同额: Optional[float] = None
    联系人: Optional[str] = None
    联系电话: Optional[str] = None
    合同内容: Optional[str] = None
    到款情况: Optional[str] = None
    合同起始日期: Optional[str] = None
    合同终止日期: Optional[str] = None
    开票日期: Optional[str] = None
    开票金额: Optional[float] = None
    开票余额: Optional[float] = None
    到款金额: Optional[float] = None
    合同余额: Optional[float] = None
    应收账款: Optional[float] = None
    备注: Optional[str] = None
    项目预算: Optional[float] = None
    设备数量: Optional[int] = None
    催款状态: str = '未催款'
    催款日期: Optional[str] = None
    催款备注: Optional[str] = None
    数据哈希: Optional[str] = None
    id: Optional[int] = None
    创建时间: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            '序号': self.序号,
            '下单日期': self.下单日期,
            '合同编号': self.合同编号,
            '项目代码': self.项目代码,
            '是否变更': self.是否变更,
            '合同评审日期': self.合同评审日期,
            '合同签字日期': self.合同签字日期,
            'crm日期': self.crm日期,
            '合同名称': self.合同名称,
            '对方单位名称': self.对方单位名称,
            '区域': self.区域,
            '销售负责人': self.销售负责人,
            '参考金额': self.参考金额,
            '合同额': self.合同额,
            '联系人': self.联系人,
            '联系电话': self.联系电话,
            '合同内容': self.合同内容,
            '到款情况': self.到款情况,
            '合同起始日期': self.合同起始日期,
            '合同终止日期': self.合同终止日期,
            '开票日期': self.开票日期,
            '开票金额': self.开票金额,
            '开票余额': self.开票余额,
            '到款金额': self.到款金额,
            '合同余额': self.合同余额,
            '应收账款': self.应收账款,
            '备注': self.备注,
            '项目预算': self.项目预算,
            '设备数量': self.设备数量
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Contract':
        """从字典创建"""
        return cls(
            序号=data.get('序号'),
            下单日期=data.get('下单日期'),
            合同编号=data.get('合同编号', ''),
            项目代码=data.get('项目代码'),
            是否变更=data.get('是否变更'),
            合同评审日期=data.get('合同评审日期'),
            合同签字日期=data.get('合同签字日期'),
            crm日期=data.get('crm日期'),
            合同名称=data.get('合同名称'),
            对方单位名称=data.get('对方单位名称'),
            区域=data.get('区域'),
            销售负责人=data.get('销售负责人'),
            参考金额=data.get('参考金额'),
            合同额=data.get('合同额'),
            联系人=data.get('联系人'),
            联系电话=data.get('联系电话'),
            合同内容=data.get('合同内容'),
            到款情况=data.get('到款情况'),
            合同起始日期=data.get('合同起始日期'),
            合同终止日期=data.get('合同终止日期'),
            开票日期=data.get('开票日期'),
            开票金额=data.get('开票金额'),
            开票余额=data.get('开票余额'),
            到款金额=data.get('到款金额'),
            合同余额=data.get('合同余额'),
            应收账款=data.get('应收账款'),
            备注=data.get('备注'),
            项目预算=data.get('项目预算'),
            设备数量=data.get('设备数量')
        )


@dataclass
class Invoice:
    """发票数据模型"""
    开票日期: Optional[str] = None
    合同号: str = ''
    付款单位名称: Optional[str] = None
    代码: Optional[str] = None
    发票金额: Optional[float] = None
    发票项目: Optional[str] = None
    类型: Optional[str] = None
    发票类型: Optional[str] = None
    除税: Optional[float] = None
    备注: Optional[str] = None
    数据哈希: Optional[str] = None
    id: Optional[int] = None
    创建时间: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            '开票日期': self.开票日期,
            '合同号': self.合同号,
            '付款单位名称': self.付款单位名称,
            '代码': self.代码,
            '发票金额': self.发票金额,
            '发票项目': self.发票项目,
            '类型': self.类型,
            '发票类型': self.发票类型,
            '除税': self.除税,
            '备注': self.备注
        }


@dataclass
class CollectionRecord:
    """催款记录数据模型"""
    合同编号: str = ''
    催款日期: Optional[str] = None
    催款方式: Optional[str] = None
    联系人: Optional[str] = None
    催款内容: Optional[str] = None
    对方反馈: Optional[str] = None
    催款结果: Optional[str] = None
    id: Optional[int] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            '合同编号': self.合同编号,
            '催款日期': self.催款日期,
            '催款方式': self.催款方式,
            '联系人': self.联系人,
            '催款内容': self.催款内容,
            '对方反馈': self.对方反馈,
            '催款结果': self.催款结果
        }
