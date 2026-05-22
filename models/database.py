#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理器 - 使用 SQLAlchemy ORM
"""

import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_PATH, CONTRACT_FIELDS, INVOICE_FIELDS
from models.entities import Contract, Invoice, CollectionRecord
from utils.helpers import generate_hash, normalize_header


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # 返回字典格式
        return conn
    
    def init_database(self):
        """初始化数据库"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 创建合同表
        cursor.execute("PRAGMA table_info(contracts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if not columns:
            cursor.execute('''
                CREATE TABLE contracts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    序号 INTEGER,
                    下单日期 TEXT,
                    合同编号 TEXT,
                    项目代码 TEXT,
                    是否变更 TEXT,
                    合同评审日期 TEXT,
                    合同签字日期 TEXT,
                    crm日期 TEXT,
                    合同名称 TEXT,
                    对方单位名称 TEXT,
                    区域 TEXT,
                    销售负责人 TEXT,
                    参考金额 REAL,
                    合同额 REAL,
                    联系人 TEXT,
                    联系电话 TEXT,
                    合同内容 TEXT,
                    到款情况 TEXT,
                    合同起始日期 TEXT,
                    合同终止日期 TEXT,
                    开票日期 TEXT,
                    开票金额 REAL,
                    开票余额 REAL,
                    到款金额 REAL,
                    合同余额 REAL,
                    应收账款 REAL,
                    备注 TEXT,
                    项目预算 REAL,
                    设备数量 INTEGER,
                    催款状态 TEXT DEFAULT '未催款',
                    催款日期 TEXT,
                    催款备注 TEXT,
                    数据哈希 TEXT,
                    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引以提升查询性能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_contract_no ON contracts(合同编号)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_salesperson ON contracts(销售负责人)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_region ON contracts(区域)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_end_date ON contracts(合同终止日期)')
        else:
            # 升级数据库 - 添加缺失字段
            self._upgrade_database(cursor, columns)
        
        # 创建发票表
        cursor.execute("PRAGMA table_info(invoices_new)")
        if not cursor.fetchall():
            cursor.execute('''
                CREATE TABLE invoices_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    开票日期 TEXT,
                    合同号 TEXT,
                    付款单位名称 TEXT,
                    代码 TEXT,
                    发票金额 REAL,
                    发票项目 TEXT,
                    类型 TEXT,
                    发票类型 TEXT,
                    除税 REAL,
                    备注 TEXT,
                    数据哈希 TEXT,
                    创建时间 TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoice_contract ON invoices_new(合同号)')
        
        # 创建催款记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collection_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                合同编号 TEXT NOT NULL,
                催款日期 TEXT,
                催款方式 TEXT,
                联系人 TEXT,
                催款内容 TEXT,
                对方反馈 TEXT,
                催款结果 TEXT,
                FOREIGN KEY (合同编号) REFERENCES contracts(合同编号)
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_collection_contract ON collection_records(合同编号)')
        
        conn.commit()
        conn.close()
    
    def _upgrade_database(self, cursor, existing_columns: List[str]):
        """升级数据库结构"""
        required_columns = {
            '序号': 'INTEGER', '下单日期': 'TEXT', '是否变更': 'TEXT',
            '合同评审日期': 'TEXT', '合同签字日期': 'TEXT', 'crm日期': 'TEXT',
            '销售负责人': 'TEXT', '参考金额': 'REAL', '合同额': 'REAL',
            '联系人': 'TEXT', '联系电话': 'TEXT', '到款情况': 'TEXT',
            '开票日期': 'TEXT', '开票金额': 'REAL', '开票余额': 'REAL',
            '到款金额': 'REAL', '合同余额': 'REAL', '应收账款': 'REAL',
            '备注': 'TEXT', '项目预算': 'REAL', '设备数量': 'INTEGER',
            '数据哈希': 'TEXT'
        }
        
        for col_name, col_type in required_columns.items():
            if col_name not in existing_columns:
                try:
                    cursor.execute(f'ALTER TABLE contracts ADD COLUMN {col_name} {col_type}')
                except:
                    pass
    
    def add_contract(self, contract: Contract) -> tuple[bool, str]:
        """添加合同"""
        data = contract.to_dict()
        
        # 检查重复
        data_hash = generate_hash(data, CONTRACT_FIELDS)
        if self.check_duplicate_by_hash(data_hash):
            return False, "数据完全重复，已跳过"
        
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO contracts 
                (序号, 下单日期, 合同编号, 项目代码, 是否变更, 合同评审日期,
                 合同签字日期, crm日期, 合同名称, 对方单位名称, 区域, 销售负责人,
                 参考金额, 合同额, 联系人, 联系电话, 合同内容, 到款情况,
                 合同起始日期, 合同终止日期, 开票日期, 开票金额, 开票余额,
                 到款金额, 合同余额, 应收账款, 备注, 项目预算, 设备数量, 数据哈希)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('序号'), data.get('下单日期'), data.get('合同编号'),
                data.get('项目代码'), data.get('是否变更'), data.get('合同评审日期'),
                data.get('合同签字日期'), data.get('crm日期'), data.get('合同名称'),
                data.get('对方单位名称'), data.get('区域'), data.get('销售负责人'),
                data.get('参考金额'), data.get('合同额'), data.get('联系人'),
                data.get('联系电话'), data.get('合同内容'), data.get('到款情况'),
                data.get('合同起始日期'), data.get('合同终止日期'), data.get('开票日期'),
                data.get('开票金额'), data.get('开票余额'), data.get('到款金额'),
                data.get('合同余额'), data.get('应收账款'), data.get('备注'),
                data.get('项目预算'), data.get('设备数量'), data_hash
            ))
            conn.commit()
            return True, "添加成功"
        except Exception as e:
            return False, f"添加失败: {str(e)}"
        finally:
            conn.close()
    
    def check_duplicate_by_hash(self, data_hash: str) -> bool:
        """检查数据哈希是否已存在"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM contracts WHERE 数据哈希 = ?', (data_hash,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def get_contracts(self, filters: Optional[Dict] = None) -> List[Contract]:
        """获取合同列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM contracts WHERE 1=1'
        params = []
        
        if filters:
            if filters.get('year'):
                query += ' AND 合同签字日期 LIKE ?'
                params.append(f"{filters['year']}%")
            
            if filters.get('region'):
                query += ' AND 区域 = ?'
                params.append(filters['region'])
            
            if filters.get('salesperson'):
                query += ' AND 销售负责人 = ?'
                params.append(filters['salesperson'])
            
            if filters.get('search'):
                query += ' AND (合同编号 LIKE ? OR 合同名称 LIKE ? OR 对方单位名称 LIKE ?)'
                search_term = f"%{filters['search']}%"
                params.extend([search_term, search_term, search_term])
        
        query += ' ORDER BY 创建时间 DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        contracts = []
        for row in rows:
            contract = Contract(
                id=row['id'],
                序号=row['序号'],
                下单日期=row['下单日期'],
                合同编号=row['合同编号'],
                项目代码=row['项目代码'],
                是否变更=row['是否变更'],
                合同评审日期=row['合同评审日期'],
                合同签字日期=row['合同签字日期'],
                crm日期=row['crm日期'],
                合同名称=row['合同名称'],
                对方单位名称=row['对方单位名称'],
                区域=row['区域'],
                销售负责人=row['销售负责人'],
                参考金额=row['参考金额'],
                合同额=row['合同额'],
                联系人=row['联系人'],
                联系电话=row['联系电话'],
                合同内容=row['合同内容'],
                到款情况=row['到款情况'],
                合同起始日期=row['合同起始日期'],
                合同终止日期=row['合同终止日期'],
                开票日期=row['开票日期'],
                开票金额=row['开票金额'],
                开票余额=row['开票余额'],
                到款金额=row['到款金额'],
                合同余额=row['合同余额'],
                应收账款=row['应收账款'],
                备注=row['备注'],
                项目预算=row['项目预算'],
                设备数量=row['设备数量'],
                催款状态=row['催款状态'],
                催款日期=row['催款日期'],
                催款备注=row['催款备注'],
                创建时间=row['创建时间']
            )
            contracts.append(contract)
        
        return contracts
    
    def get_contract_by_no(self, contract_no: str) -> Optional[Contract]:
        """根据合同编号获取合同"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM contracts WHERE 合同编号=?', (contract_no,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return Contract(
            id=row['id'],
            序号=row['序号'],
            下单日期=row['下单日期'],
            合同编号=row['合同编号'],
            项目代码=row['项目代码'],
            是否变更=row['是否变更'],
            合同评审日期=row['合同评审日期'],
            合同签字日期=row['合同签字日期'],
            crm日期=row['crm日期'],
            合同名称=row['合同名称'],
            对方单位名称=row['对方单位名称'],
            区域=row['区域'],
            销售负责人=row['销售负责人'],
            参考金额=row['参考金额'],
            合同额=row['合同额'],
            联系人=row['联系人'],
            联系电话=row['联系电话'],
            合同内容=row['合同内容'],
            到款情况=row['到款情况'],
            合同起始日期=row['合同起始日期'],
            合同终止日期=row['合同终止日期'],
            开票日期=row['开票日期'],
            开票金额=row['开票金额'],
            开票余额=row['开票余额'],
            到款金额=row['到款金额'],
            合同余额=row['合同余额'],
            应收账款=row['应收账款'],
            备注=row['备注'],
            项目预算=row['项目预算'],
            设备数量=row['设备数量'],
            催款状态=row['催款状态'],
            催款日期=row['催款日期'],
            催款备注=row['催款备注'],
            创建时间=row['创建时间']
        )
    
    def get_contract_by_id(self, contract_id: int) -> Optional[Contract]:
        """根据 id 获取合同"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM contracts WHERE id=?', (contract_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return Contract(
            id=row['id'],
            序号=row['序号'],
            下单日期=row['下单日期'],
            合同编号=row['合同编号'],
            项目代码=row['项目代码'],
            是否变更=row['是否变更'],
            合同评审日期=row['合同评审日期'],
            合同签字日期=row['合同签字日期'],
            crm日期=row['crm日期'],
            合同名称=row['合同名称'],
            对方单位名称=row['对方单位名称'],
            区域=row['区域'],
            销售负责人=row['销售负责人'],
            参考金额=row['参考金额'],
            合同额=row['合同额'],
            联系人=row['联系人'],
            联系电话=row['联系电话'],
            合同内容=row['合同内容'],
            到款情况=row['到款情况'],
            合同起始日期=row['合同起始日期'],
            合同终止日期=row['合同终止日期'],
            开票日期=row['开票日期'],
            开票金额=row['开票金额'],
            开票余额=row['开票余额'],
            到款金额=row['到款金额'],
            合同余额=row['合同余额'],
            应收账款=row['应收账款'],
            备注=row['备注'],
            项目预算=row['项目预算'],
            设备数量=row['设备数量'],
            催款状态=row['催款状态'],
            催款日期=row['催款日期'],
            催款备注=row['催款备注'],
            创建时间=row['创建时间']
        )
    
    def update_contract(self, contract_no: str, data: Dict) -> bool:
        """更新合同"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE contracts SET 
                序号=?, 下单日期=?, 项目代码=?, 是否变更=?, 合同评审日期=?,
                合同签字日期=?, crm日期=?, 合同名称=?, 对方单位名称=?, 区域=?,
                销售负责人=?, 参考金额=?, 合同额=?, 联系人=?, 联系电话=?,
                合同内容=?, 到款情况=?, 合同起始日期=?, 合同终止日期=?,
                开票日期=?, 开票金额=?, 开票余额=?, 到款金额=?, 合同余额=?,
                应收账款=?, 备注=?, 项目预算=?, 设备数量=?
                WHERE 合同编号=?
            ''', (
                data.get('序号'), data.get('下单日期'), data.get('项目代码'),
                data.get('是否变更'), data.get('合同评审日期'), data.get('合同签字日期'),
                data.get('crm日期'), data.get('合同名称'), data.get('对方单位名称'),
                data.get('区域'), data.get('销售负责人'), data.get('参考金额'),
                data.get('合同额'), data.get('联系人'), data.get('联系电话'),
                data.get('合同内容'), data.get('到款情况'), data.get('合同起始日期'),
                data.get('合同终止日期'), data.get('开票日期'), data.get('开票金额'),
                data.get('开票余额'), data.get('到款金额'), data.get('合同余额'),
                data.get('应收账款'), data.get('备注'), data.get('项目预算'),
                data.get('设备数量'), contract_no
            ))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def delete_contract(self, contract_no: str) -> bool:
        """删除合同"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM collection_records WHERE 合同编号=?', (contract_no,))
            cursor.execute('DELETE FROM contracts WHERE 合同编号=?', (contract_no,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def delete_contract_by_id(self, contract_id: int) -> bool:
        """根据 id 删除合同"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 先获取合同编号，用于删除催款记录
            cursor.execute('SELECT 合同编号 FROM contracts WHERE id=?', (contract_id,))
            row = cursor.fetchone()
            if row:
                contract_no = row['合同编号']
                cursor.execute('DELETE FROM collection_records WHERE 合同编号=?', (contract_no,))
            
            cursor.execute('DELETE FROM contracts WHERE id=?', (contract_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def get_distinct_values(self, field: str) -> List[str]:
        """获取某个字段的所有不重复值"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f'SELECT DISTINCT {field} FROM contracts WHERE {field} IS NOT NULL AND {field} != "" ORDER BY {field}')
        values = [row[0] for row in cursor.fetchall()]
        conn.close()
        return values
    
    # 发票相关方法
    def add_invoice(self, invoice: Invoice) -> tuple[bool, str]:
        """添加发票"""
        data = invoice.to_dict()
        data_hash = generate_hash(data, INVOICE_FIELDS)
        
        if self.check_duplicate_invoice_by_hash(data_hash):
            return False, "发票数据重复，已跳过"
        
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO invoices_new
                (开票日期, 合同号, 付款单位名称, 代码, 发票金额, 发票项目, 类型, 发票类型, 除税, 备注, 数据哈希)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('开票日期'), data.get('合同号'), data.get('付款单位名称'),
                data.get('代码'), data.get('发票金额'), data.get('发票项目'),
                data.get('类型'), data.get('发票类型'), data.get('除税'),
                data.get('备注'), data_hash
            ))
            conn.commit()
            return True, "添加成功"
        except Exception as e:
            return False, f"添加失败: {str(e)}"
        finally:
            conn.close()
    
    def check_duplicate_invoice_by_hash(self, data_hash: str) -> bool:
        """检查发票数据哈希是否已存在"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM invoices_new WHERE 数据哈希 = ?', (data_hash,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def get_invoices(self, filters: Optional[Dict] = None) -> List[Invoice]:
        """获取发票列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM invoices_new WHERE 1=1'
        params = []
        
        if filters:
            if filters.get('contract_no'):
                query += ' AND 合同号 = ?'
                params.append(filters['contract_no'])
            
            if filters.get('search'):
                query += ' AND (合同号 LIKE ? OR 付款单位名称 LIKE ?)'
                search_term = f"%{filters['search']}%"
                params.extend([search_term, search_term])
        
        query += ' ORDER BY 创建时间 DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        invoices = []
        for row in rows:
            invoice = Invoice(
                id=row['id'],
                开票日期=row['开票日期'],
                合同号=row['合同号'],
                付款单位名称=row['付款单位名称'],
                代码=row['代码'],
                发票金额=row['发票金额'],
                发票项目=row['发票项目'],
                类型=row['类型'],
                发票类型=row['发票类型'],
                除税=row['除税'],
                备注=row['备注'],
                创建时间=row['创建时间']
            )
            invoices.append(invoice)
        
        return invoices
    
    # 催款记录相关方法
    def add_collection_record(self, record: CollectionRecord) -> bool:
        """添加催款记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO collection_records
                (合同编号, 催款日期, 催款方式, 联系人, 催款内容, 对方反馈, 催款结果)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.合同编号, record.催款日期, record.催款方式,
                record.联系人, record.催款内容, record.对方反馈, record.催款结果
            ))
            conn.commit()
            return True
        except Exception:
            return False
        finally:
            conn.close()
    
    def get_collection_records(self, contract_no: str) -> List[CollectionRecord]:
        """获取催款记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM collection_records WHERE 合同编号=? ORDER BY 催款日期 DESC', (contract_no,))
        rows = cursor.fetchall()
        conn.close()
        
        records = []
        for row in rows:
            record = CollectionRecord(
                id=row['id'],
                合同编号=row['合同编号'],
                催款日期=row['催款日期'],
                催款方式=row['催款方式'],
                联系人=row['联系人'],
                催款内容=row['催款内容'],
                对方反馈=row['对方反馈'],
                催款结果=row['催款结果']
            )
            records.append(record)
        
        return records
    
    # 统计相关方法
    def get_yearly_stats(self) -> List[Dict]:
        """获取年度统计"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                substr(合同签字日期, 1, 4) as year,
                COUNT(*) as count,
                SUM(合同额) as total_amount,
                SUM(到款金额) as received_amount
            FROM contracts
            WHERE 合同签字日期 IS NOT NULL AND 合同签字日期 != ''
            GROUP BY substr(合同签字日期, 1, 4)
            ORDER BY year DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        stats = []
        for row in rows:
            stats.append({
                'year': row['year'],
                'count': row['count'],
                'total_amount': row['total_amount'] or 0,
                'received_amount': row['received_amount'] or 0
            })
        
        return stats
    
    def get_region_stats(self, year: Optional[str] = None) -> List[Dict]:
        """获取区域统计"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if year:
            cursor.execute('''
                SELECT 
                    区域 as region,
                    COUNT(*) as count,
                    SUM(合同额) as total_amount
                FROM contracts
                WHERE 区域 IS NOT NULL AND 区域 != ''
                    AND 合同签字日期 LIKE ?
                GROUP BY 区域
                ORDER BY total_amount DESC
            ''', (f'{year}%',))
        else:
            cursor.execute('''
                SELECT 
                    区域 as region,
                    COUNT(*) as count,
                    SUM(合同额) as total_amount
                FROM contracts
                WHERE 区域 IS NOT NULL AND 区域 != ''
                GROUP BY 区域
                ORDER BY total_amount DESC
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        stats = []
        for row in rows:
            stats.append({
                'region': row['region'],
                'count': row['count'],
                'total_amount': row['total_amount'] or 0
            })
        
        return stats
    
    def get_salesperson_stats(self, year: Optional[str] = None) -> List[Dict]:
        """获取销售负责人统计"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if year:
            cursor.execute('''
                SELECT 
                    销售负责人 as salesperson,
                    COUNT(*) as count,
                    SUM(合同额) as total_amount
                FROM contracts
                WHERE 销售负责人 IS NOT NULL AND 销售负责人 != ''
                    AND 合同签字日期 LIKE ?
                GROUP BY 销售负责人
                ORDER BY total_amount DESC
            ''', (f'{year}%',))
        else:
            cursor.execute('''
                SELECT 
                    销售负责人 as salesperson,
                    COUNT(*) as count,
                    SUM(合同额) as total_amount
                FROM contracts
                WHERE 销售负责人 IS NOT NULL AND 销售负责人 != ''
                GROUP BY 销售负责人
                ORDER BY total_amount DESC
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        stats = []
        for row in rows:
            stats.append({
                'salesperson': row['salesperson'],
                'count': row['count'],
                'total_amount': row['total_amount'] or 0
            })
        
        return stats
    
    def get_years_with_receivables(self) -> List[str]:
        """获取有应收账款的年份列表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT substr(合同签字日期, 1, 4) as year
            FROM contracts
            WHERE 应收账款 > 0
                AND 合同签字日期 IS NOT NULL
                AND 合同签字日期 != ''
            ORDER BY year DESC
        ''')
        
        years = [row['year'] for row in cursor.fetchall()]
        conn.close()
        
        return years
