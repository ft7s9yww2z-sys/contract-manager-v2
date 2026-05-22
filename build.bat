@echo off
REM 合同管理系统 V2.0 打包脚本 (Windows)

echo ========================================
echo 合同管理系统 V2.0 打包工具
echo ========================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.10+
    pause
    exit /b 1
)

REM 安装依赖
echo [1/4] 安装依赖...
pip install -r requirements.txt

REM 安装PyInstaller
echo [2/4] 安装PyInstaller...
pip install pyinstaller

REM 清理旧的构建文件
echo [3/4] 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

REM 打包
echo [4/4] 开始打包...
pyinstaller --onefile --windowed --name "合同管理系统V2" ^
    --add-data "config.py;." ^
    --add-data "models;models" ^
    --add-data "services;services" ^
    --add-data "utils;utils" ^
    --hidden-import "customtkinter" ^
    --hidden-import "plotly" ^
    --hidden-import "openpyxl" ^
    main.py

REM 检查打包结果
if exist "dist\合同管理系统V2.exe" (
    echo.
    echo ========================================
    echo 打包成功！
    echo 可执行文件位置: dist\合同管理系统V2.exe
    for %%I in (dist\合同管理系统V2.exe) do echo 文件大小: %%~zI 字节
    echo ========================================
) else (
    echo.
    echo [错误] 打包失败，请检查错误信息
)

pause
