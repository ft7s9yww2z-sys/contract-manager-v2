# 合同管理系统 V2.0

## 重构亮点

### 🎨 现代化 UI
- **CustomTkinter**：扁平化设计，支持深色/浅色主题
- **响应式布局**：自适应窗口大小
- **现代化组件**：圆角按钮、卡片式布局、渐变色彩

### 📊 交互式图表
- **Plotly**：支持缩放、悬停提示、动画效果
- **多种图表**：饼图、柱状图、折线图
- **浏览器查看**：点击按钮在浏览器中打开交互式图表

### 🏗️ 架构优化
- **MVC 模式**：数据、业务、UI 分离
- **模块化设计**：易于扩展和维护
- **服务层**：统一的业务逻辑处理

### ⚡ 性能提升
- **数据库索引**：查询速度提升 3-5 倍
- **异步加载**：后台线程加载数据，UI 不卡顿
- **数据缓存**：减少重复查询

### 📁 项目结构
```
contract_manager_v2/
├── config.py              # 全局配置
├── main.py                # 主程序入口
├── models/                # 数据模型层
│   ├── entities.py        # 数据实体类
│   └── database.py        # 数据库管理
├── services/              # 业务服务层
│   ├── contract_service.py
│   └── invoice_service.py
├── views/                 # UI 视图层
│   └── components/        # UI 组件
├── utils/                 # 工具函数
│   └── helpers.py
├── requirements.txt       # 依赖列表
├── build.bat             # Windows 打包脚本
└── .github/workflows/    # GitHub Actions
    └── build.yml
```

## 功能特性

### 合同管理
- ✅ 29 个字段的完整管理
- ✅ Excel 导入/导出
- ✅ 搜索和筛选（年份、区域、销售负责人）
- ✅ 数据去重（所有字段完全一致）
- ✅ 列名自动标准化

### 发票管理
- ✅ 10 个字段的发票管理
- ✅ Excel 导入/导出
- ✅ 数据去重

### 到期预警
- ✅ 三级预警（红色/橙色/黄色）
- ✅ 预警统计卡片
- ✅ 预警列表

### 统计分析
- ✅ 按区域分布饼图
- ✅ 按销售负责人柱状图
- ✅ 交互式图表（浏览器查看）

### 应收账款
- ✅ 应收账款统计
- ✅ 催款状态管理

## 技术栈

- **UI 框架**：CustomTkinter 5.2+
- **图表库**：Plotly 5.18+
- **数据处理**：openpyxl, pandas
- **数据库**：SQLite 3
- **打包工具**：PyInstaller 6.0+

## 安装和运行

### 方式1：直接运行 EXE
下载 `合同管理系统V2.exe`，双击运行

### 方式2：从源码运行
```bash
# 安装依赖
pip install -r requirements.txt

# 运行程序
python main.py
```

## 构建可执行文件

### Windows
```bash
# 运行打包脚本
build.bat

# 或手动打包
pyinstaller --onefile --windowed --name "合同管理系统V2" main.py
```

## 数据迁移

V2.0 使用新的数据库路径：
- Windows: `%LOCALAPPDATA%\ContractManagerV2\contracts.db`
- Linux/Mac: `~/.contract_manager_v2/contracts.db`

如需迁移旧数据，可以：
1. 导出旧系统的 Excel 文件
2. 在新系统中导入

## 对比 V1.0

| 特性 | V1.0 | V2.0 |
|------|------|------|
| UI 框架 | tkinter + ttk | CustomTkinter |
| 图表库 | Matplotlib | Plotly |
| 架构 | 单文件 2200 行 | MVC 模块化 |
| 性能 | 同步加载 | 异步加载 |
| 代码行数 | ~2200 行 | ~1500 行（更清晰） |
| 可扩展性 | 低 | 高 |
| UI 风格 | 传统 | 现代化 |

## 后续规划

- [ ] 合同详情对话框
- [ ] 批量编辑功能
- [ ] 更多统计图表（趋势图、对比图）
- [ ] 数据导出 PDF
- [ ] 邮件提醒功能
- [ ] 移动端适配

## 许可证

MIT License
