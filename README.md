
# QQ聊天记录转PDF

## 项目介绍

本软件用于将QQ聊天记录导出的HTML文件转换为适合打印的HTML格式，并可自动通过Edge浏览器转换为PDF文件。适用于聊天记录的长期保存、归档及法律取证等场景。

### 适用范围

- **导出工具**：[NapCat-QCE-Windows-x64-v5.5.3](https://github.com/shuakami/qq-chat-exporter/releases/tag/v5.5.53)
- **QQ版本**：QQ 9.9.26.44343 (x64)
- **运行环境**：Windows 系统，需安装 Microsoft Edge 浏览器（用于PDF转换）

### 支持的消息类型

| 类型 | 说明 |
|------|------|
| 文本消息 | 含@提及、表情 |
| 图片消息 | 原图引用，打印时自动缩放 |
| 引用消息 | 显示被引用的发送者和内容 |
| 合并转发 | 以卡片形式展示 |
| 系统消息 | 撤回提示、群通知等 |
| 语音/视频 | 打印时隐藏播放控件，保留占位标识 |
| 日期分隔 | 按日期分组显示 |

### 核心特性

- 解决QQ导出HTML打印只显示一页的问题（虚拟滚动/固定高度容器）
- 支持按消息数量分片，防止大量消息导致浏览器卡死
- 自动调用Edge无头模式生成PDF，无需手动操作
- 分片文件标题标注序号（如 `聊天名 (第1/3部分)`）
- 打印样式优化：消息不被分页截断、背景色正确输出、隐藏无关控件

## 快速开始

### 面向使用者（使用exe文件）

1. 将QQ聊天记录通过 NapCat 导出为HTML文件
2. 将导出的HTML文件放在exe程序同级目录下（确保 `resources/` 图片文件夹也在同级目录）
3. 双击运行exe程序
4. 按提示输入每个文件的最大消息条数（输入 `0` 不分片，建议 500-2000）
5. 选择是否自动转换为PDF
6. 生成的文件位于同级目录下：
   - 不分片：`{原名}_print.html` / `{原名}_print.pdf`
   - 分片：`{原名}_print_part1.html` / `{原名}_print_part1.pdf` ...

> **提示**：也可以将HTML文件直接拖拽到exe程序图标上运行

### 面向开发者（从源码运行）

```bash
# 克隆项目
git clone <项目地址>

# 进入项目目录
cd <项目目录>

# 激活虚拟环境
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

### 打包为exe

```bash
pyinstaller --onefile --icon=my.ico --name="QQ聊天记录转PDF" main.py
```

## 实现方法

### 转换流程

```
QQ导出HTML → BeautifulSoup解析 → 提取消息数据 → 生成打印友好HTML → Edge无头模式转PDF
```

### 技术细节

1. **HTML解析**：使用 BeautifulSoup 解析QQ导出的HTML结构，提取元数据（`QCE_METADATA`）和消息列表
2. **格式转换**：将虚拟滚动布局的消息重新生成为标准文档流的HTML，内置打印专用CSS
3. **分片机制**：按消息数量分割，每个分片保留完整的页面头部信息和日期分隔
4. **PDF生成**：通过 Edge `--headless --print-to-pdf` 无头模式自动转换，使用 `--no-pdf-header-footer` 去除默认页眉页脚
5. **打包兼容**：通过 `sys.frozen` 判断运行环境，自动适配脚本运行和PyInstaller打包两种模式的工作目录

### 为什么原始HTML打印只有一页？

QQ导出的HTML使用了虚拟滚动技术：
- 容器设置 `overflow: hidden` 和固定高度（`100vh`）
- 底部工具栏 `position: fixed` 占用空间
- 图片使用 `loading="lazy"` 懒加载，打印时不触发

本工具将所有消息提取后重新生成标准文档流HTML，确保浏览器能正确分页打印。

## 版本日志

### v1.0.0    ----2026.6.11
- 支持QQ聊天记录HTML转打印友好格式
- 支持按消息数量分片输出
- 支持Edge无头模式自动转PDF

## 许可证

本项目采用 Prosperity Public License 2.0.0 许可证，详见 LICENSE 文件。