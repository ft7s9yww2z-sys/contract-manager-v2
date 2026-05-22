#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复日期选择器大小
"""

import re

file_path = 'views/dialogs_fixed.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换 DateEntry 的配置
old_dateentry = '''                    entry = DateEntry(
                        date_frame,
                        width=40,
                        background='darkblue',
                        foreground='white',
                        borderwidth=2,
                        date_pattern='yyyy-mm-dd'
                    )'''

new_dateentry = '''                    entry = DateEntry(
                        date_frame,
                        width=50,
                        font=('Arial', 12),
                        background='darkblue',
                        foreground='white',
                        borderwidth=2,
                        date_pattern='yyyy-mm-dd'
                    )'''

content = content.replace(old_dateentry, new_dateentry)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ 已放大日期选择器：width=40 → 50，添加字体大小 12")
