#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复对话框输入框宽度
"""

import re

file_path = 'views/dialogs_fixed.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换所有 width=300 为 width=500
content = re.sub(r'width=300', 'width=500', content)

# 替换 DateEntry 的 width=30 为 width=40
content = re.sub(r'width=30,', 'width=40,', content)

# 替换 Textbox 的 width=300 为 width=500
content = re.sub(r'height=80, width=300', 'height=100, width=500', content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ 已放大输入框宽度：300 → 500")
print("✓ 已放大日期选择器宽度：30 → 40")
print("✓ 已放大文本框：height=80 → 100, width=300 → 500")
