#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 允许合同编号为空
"""

import sqlite3
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DB_PATH

def migrate_database():
    """迁移数据库，允许合同编号为空"""
    print(f"正在迁移数据库: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print("数据库文件不存在，无需迁移")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 检查是否需要迁移
        cursor.execute("PRAGMA table_info(contracts)")
        columns = cursor.fetchall()
        
        for col in columns:
            if col[1] == '合同编号':
                # 检查是否有 NOT NULL 约束
                if col[3] == 1:  # notnull = 1
                    print("检测到合同编号字段有 NOT NULL 约束，开始迁移...")
                    break
        else:
            print("合同编号字段已允许为空，无需迁移")
            return
        
        # 创建新表（允许合同编号为空）
        cursor.execute('''
            CREATE TABLE contracts_new (
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
        
        # 复制数据
        cursor.execute('''
            INSERT INTO contracts_new 
            SELECT * FROM contracts
        ''')
        
        # 删除旧表
        cursor.execute('DROP TABLE contracts')
        
        # 重命名新表
        cursor.execute('ALTER TABLE contracts_new RENAME TO contracts')
        
        # 重建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_contract_no ON contracts(合同编号)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_salesperson ON contracts(销售负责人)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_region ON contracts(区域)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_end_date ON contracts(合同终止日期)')
        
        conn.commit()
        print("✓ 数据库迁移成功！合同编号字段现在允许为空")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ 迁移失败: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
