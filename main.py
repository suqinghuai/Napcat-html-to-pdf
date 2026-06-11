import sys
import os
import re
import json
import subprocess
from datetime import datetime
from bs4 import BeautifulSoup, NavigableString

if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

PRINT_CSS = """\
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: "PingFang SC", "Microsoft YaHei", system-ui, -apple-system, sans-serif;
    background: #fff;
    color: #1f2a37;
    line-height: 1.6;
    font-size: 14px;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}

.page-header {
    padding: 24px 32px 16px;
    border-bottom: 2px solid #e5e7eb;
    margin-bottom: 20px;
}

.page-header h1 {
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 8px;
}

.page-header .meta {
    display: flex;
    gap: 24px;
    flex-wrap: wrap;
    font-size: 13px;
    color: #6b7280;
}

.page-header .meta span {
    margin-right: 8px;
}

.chat-body {
    padding: 0 32px;
}

.date-divider {
    text-align: center;
    color: #9ca3af;
    font-size: 12px;
    margin: 24px 0 16px;
    position: relative;
}

.date-divider::before,
.date-divider::after {
    content: '';
    position: absolute;
    top: 50%;
    width: calc(50% - 60px);
    height: 1px;
    background: #e5e7eb;
}

.date-divider::before { left: 0; }
.date-divider::after { right: 0; }

.system-msg {
    text-align: center;
    color: #9ca3af;
    font-size: 12px;
    padding: 8px 0;
    margin: 8px 0;
}

.msg {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
    align-items: flex-start;
    page-break-inside: avoid;
    break-inside: avoid;
}

.msg.self {
    flex-direction: row-reverse;
}

.msg-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    flex-shrink: 0;
    overflow: hidden;
    background: #eef2ff;
    display: flex;
    align-items: center;
    justify-content: center;
}

.msg-avatar img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.msg-avatar .avatar-letter {
    font-size: 14px;
    font-weight: 600;
    color: #475569;
}

.msg-body {
    max-width: 70%;
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.msg.self .msg-body {
    align-items: flex-end;
}

.msg-info {
    display: flex;
    align-items: baseline;
    gap: 8px;
    font-size: 12px;
    padding: 0 4px;
}

.msg.self .msg-info {
    flex-direction: row-reverse;
}

.msg-sender {
    font-weight: 600;
    color: #374151;
}

.msg-time {
    color: #9ca3af;
}

.msg-bubble {
    padding: 10px 14px;
    border-radius: 16px;
    word-break: break-word;
    overflow-wrap: break-word;
    line-height: 1.6;
}

.msg.other .msg-bubble {
    background: #f3f4f6;
    color: #1f2937;
}

.msg.self .msg-bubble {
    background: #dbeafe;
    color: #1e3a5f;
}

.msg-bubble .text-content {
    font-size: 14px;
}

.msg-bubble .face-emoji {
    font-size: 14px;
}

.msg-bubble .image-content {
    margin: 6px 0;
}

.msg-bubble .image-content img {
    max-width: 280px;
    max-height: 260px;
    border-radius: 10px;
    object-fit: contain;
}

.msg-bubble video {
    max-width: 280px;
    max-height: 200px;
    border-radius: 10px;
    background: #000;
}

.msg-bubble audio {
    width: 220px;
    margin: 4px 0;
}

.msg-bubble .reply-content {
    background: rgba(0,0,0,0.04);
    border-left: 3px solid rgba(0,0,0,0.2);
    padding: 8px 10px;
    border-radius: 6px;
    margin-bottom: 6px;
    font-size: 13px;
    color: #6b7280;
}

.msg-bubble .reply-content strong {
    color: #374151;
}

.msg-bubble .forward-card {
    background: rgba(0,0,0,0.03);
    border: 1px solid rgba(0,0,0,0.08);
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 13px;
    color: #6b7280;
}

.msg-bubble .forward-card-header {
    font-weight: 600;
    color: #374151;
    margin-bottom: 4px;
}

.msg-bubble .at-mention {
    background: rgba(0,0,0,0.06);
    padding: 1px 6px;
    border-radius: 4px;
    font-weight: 600;
}

.msg-bubble .inline-emoji {
    width: 20px;
    height: 20px;
    vertical-align: text-bottom;
}

@media print {
    body { background: #fff; }
    .page-header { padding: 0 0 12px; }
    .chat-body { padding: 0; }
    .msg { page-break-inside: avoid; break-inside: avoid; }
    .date-divider { page-break-after: avoid; break-after: avoid; }
    .msg-bubble .image-content img { max-height: 200px; }
    .msg-bubble video { display: none; }
    .msg-bubble audio { display: none; }
}
"""


def parse_metadata(soup):
    comment = soup.find(string=re.compile(r'QCE_METADATA'))
    if comment:
        match = re.search(r'QCE_METADATA:\s*(\{.*?\})', str(comment))
        if match:
            return json.loads(match.group(1))
    return {}


def parse_chat(soup):
    blocks = soup.select('.message-block')
    items = []
    for block in blocks:
        date_divider = block.select_one('.date-divider')
        if date_divider:
            items.append({'type': 'date', 'label': date_divider.get_text(strip=True)})
            continue

        sys_msg = block.select_one('.system-message-container')
        if sys_msg:
            text = sys_msg.get_text(strip=True)
            time_el = sys_msg.select_one('div[style]')
            items.append({'type': 'system', 'text': text})
            continue

        msg_div = block.select_one('.message')
        if not msg_div:
            continue

        is_self = 'self' in msg_div.get('class', [])

        avatar_div = msg_div.select_one('.avatar')
        avatar_img = avatar_div.select_one('img') if avatar_div else None
        avatar_src = ''
        avatar_alt = ''
        avatar_letter = ''
        if avatar_img:
            avatar_src = avatar_img.get('src', '')
            avatar_alt = avatar_img.get('alt', '')
        else:
            fallback = avatar_div.select_one('span') if avatar_div else None
            if fallback:
                avatar_letter = fallback.get_text(strip=True)

        sender_span = msg_div.select_one('.sender')
        sender_name = sender_span.get_text(strip=True) if sender_span else ''

        time_span = msg_div.select_one('.time')
        time_str = time_span.get_text(strip=True) if time_span else ''

        bubble = msg_div.select_one('.message-bubble')
        content_html = ''
        if bubble:
            content_html = bubble.decode_contents().strip()

        items.append({
            'type': 'message',
            'self': is_self,
            'avatar_src': avatar_src,
            'avatar_alt': avatar_alt,
            'avatar_letter': avatar_letter,
            'sender': sender_name,
            'time': time_str,
            'content': content_html,
        })

    return items


def build_avatar_html(item):
    if item['avatar_src']:
        return f'<img src="{item["avatar_src"]}" alt="{escape_attr(item["avatar_alt"])}" />'
    elif item['avatar_letter']:
        return f'<div class="avatar-letter">{escape_html(item["avatar_letter"])}</div>'
    return '<div class="avatar-letter">?</div>'


def build_print_html(metadata, items, part_info=None):
    chat_name = metadata.get('chatName', '聊天记录')
    chat_type = metadata.get('chatType', 'private')
    export_time = metadata.get('exportTime', '')

    if export_time:
        try:
            dt = datetime.fromisoformat(export_time.replace('Z', '+00:00'))
            export_time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            export_time_str = export_time
    else:
        export_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    type_label = '私聊' if chat_type == 'private' else '群聊'
    msg_count = sum(1 for it in items if it['type'] == 'message')

    display_name = chat_name
    if part_info:
        display_name = f'{chat_name} ({part_info})'

    parts = []
    parts.append('<!DOCTYPE html>')
    parts.append('<html lang="zh-CN">')
    parts.append('<head>')
    parts.append('<meta charset="UTF-8">')
    parts.append(f'<title>{escape_html(display_name)} - 聊天记录</title>')
    parts.append(f'<style>{PRINT_CSS}</style>')
    parts.append('</head>')
    parts.append('<body>')

    parts.append('<div class="page-header">')
    parts.append(f'<h1>{escape_html(display_name)}</h1>')
    parts.append('<div class="meta">')
    parts.append(f'<span>{msg_count} 条消息</span>')
    parts.append(f'<span>{type_label}</span>')
    parts.append(f'<span>导出时间: {export_time_str}</span>')
    parts.append('</div>')
    parts.append('</div>')

    parts.append('<div class="chat-body">')

    for item in items:
        if item['type'] == 'date':
            parts.append(f'<div class="date-divider">{escape_html(item["label"])}</div>')
        elif item['type'] == 'system':
            parts.append(f'<div class="system-msg">{escape_html(item["text"])}</div>')
        elif item['type'] == 'message':
            side = 'self' if item['self'] else 'other'
            avatar = build_avatar_html(item)
            parts.append(f'<div class="msg {side}">')
            parts.append(f'<div class="msg-avatar">{avatar}</div>')
            parts.append('<div class="msg-body">')
            parts.append('<div class="msg-info">')
            parts.append(f'<span class="msg-sender">{escape_html(item["sender"])}</span>')
            parts.append(f'<span class="msg-time">{escape_html(item["time"])}</span>')
            parts.append('</div>')
            parts.append(f'<div class="msg-bubble">{item["content"]}</div>')
            parts.append('</div>')
            parts.append('</div>')

    parts.append('</div>')
    parts.append('</body>')
    parts.append('</html>')

    return '\n'.join(parts)


def escape_html(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def escape_attr(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def split_items(items, per_file):
    chunks = []
    msg_idx = 0
    current = []
    for item in items:
        current.append(item)
        if item['type'] == 'message':
            msg_idx += 1
            if msg_idx >= per_file:
                chunks.append(current)
                current = []
                msg_idx = 0
    if current:
        chunks.append(current)
    return chunks


def convert(input_path, output_path, split_count=None):
    with open(input_path, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    metadata = parse_metadata(soup)
    items = parse_chat(soup)

    msg_count = sum(1 for it in items if it['type'] == 'message')
    if msg_count == 0:
        print(f'警告: 未从 {input_path} 中解析到任何消息')
        return []

    print(f'解析到 {msg_count} 条消息')

    generated = []

    if split_count and msg_count > split_count:
        chunks = split_items(items, split_count)
        total_parts = len(chunks)
        print(f'将分为 {total_parts} 个文件，每个最多 {split_count} 条消息')

        base = os.path.splitext(output_path)[0]
        for i, chunk in enumerate(chunks, 1):
            part_info = f'第{i}/{total_parts}部分'
            part_output = f'{base}_part{i}.html'
            output_html = build_print_html(metadata, chunk, part_info=part_info)
            with open(part_output, 'w', encoding='utf-8') as f:
                f.write(output_html)
            chunk_msg_count = sum(1 for it in chunk if it['type'] == 'message')
            print(f'  已输出: {part_output} ({chunk_msg_count} 条消息)')
            generated.append(part_output)
    else:
        output_html = build_print_html(metadata, items)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_html)
        print(f'已输出到 {output_path}')
        generated.append(output_path)

    return generated


def ask_split_count(msg_count):
    print(f'\n当前文件共 {msg_count} 条消息')
    while True:
        count_str = input('请输入每个文件包含的最大消息条数 (输入0不分片): ').strip()
        try:
            count = int(count_str)
            if count < 0:
                print('请输入大于等于0的整数')
                continue
            return count if count > 0 else None
        except ValueError:
            print('请输入有效的整数')


def find_edge():
    candidates = [
        os.path.expandvars(r'%ProgramFiles%\Microsoft\Edge\Application\msedge.exe'),
        os.path.expandvars(r'%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe'),
        os.path.expandvars(r'%LocalAppData%\Microsoft\Edge\Application\msedge.exe'),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    try:
        result = subprocess.run(['where', 'msedge'], capture_output=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.decode('utf-8', errors='replace').strip().splitlines()
            if lines:
                return lines[0]
    except Exception:
        pass
    return None


def html_to_pdf(edge_path, html_path, pdf_path):
    html_url = 'file:///' + os.path.abspath(html_path).replace('\\', '/')
    cmd = [
        edge_path,
        '--headless',
        '--disable-gpu',
        '--no-sandbox',
        f'--print-to-pdf={pdf_path}',
        '--no-pdf-header-footer',
        '--run-all-compositor-stages-before-draw',
        '--allow-file-access-from-files',
        html_url,
    ]
    print(f'  正在转换: {os.path.basename(html_path)} -> {os.path.basename(pdf_path)}')
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        if os.path.isfile(pdf_path):
            return True
        cwd_pdf = os.path.join(os.getcwd(), os.path.basename(pdf_path))
        if os.path.isfile(cwd_pdf) and os.path.abspath(cwd_pdf) != os.path.abspath(pdf_path):
            import shutil
            shutil.move(cwd_pdf, pdf_path)
            return True
        stderr_msg = result.stderr.decode('utf-8', errors='replace') if result.stderr else ''
        if 'error' in stderr_msg.lower() or 'failed' in stderr_msg.lower():
            print(f'  Edge输出: {stderr_msg[:300]}')
        return False
    except subprocess.TimeoutExpired:
        print(f'  错误: 转换超时 ({html_path})')
        return False
    except Exception as e:
        print(f'  错误: {e}')
        return False


def convert_all_to_pdf(html_files):
    edge_path = find_edge()
    if not edge_path:
        print('错误: 未找到 Microsoft Edge 浏览器')
        print('请确保已安装 Edge，或手动打开HTML文件后使用 Ctrl+P 打印为PDF')
        return

    print(f'找到 Edge: {edge_path}')
    success = 0
    for html_path in html_files:
        pdf_path = os.path.splitext(html_path)[0] + '.pdf'
        if html_to_pdf(edge_path, html_path, pdf_path):
            print(f'  已生成: {pdf_path}')
            success += 1
        else:
            print(f'  失败: {html_path}')
    print(f'\nPDF转换完成: {success}/{len(html_files)} 个文件成功')


def main():
    os.chdir(APP_DIR)

    if len(sys.argv) > 1:
        input_files = sys.argv[1:]
    else:
        html_files = [f for f in os.listdir(APP_DIR)
                      if f.endswith('.html') and f.lower() != 'template.html'
                      and not f.lower().startswith('template')]
        input_files = [os.path.join(APP_DIR, f) for f in html_files]

    if not input_files:
        print('错误: 未找到可转换的HTML文件')
        print('用法: 将聊天记录HTML文件放在本程序同级目录下，或拖拽文件到本程序上')
        input('\n按任意键退出...')
        sys.exit(1)

    all_generated = []

    for input_path in input_files:
        if not os.path.isabs(input_path):
            input_path = os.path.join(APP_DIR, input_path)

        if not os.path.exists(input_path):
            print(f'错误: 文件不存在 {input_path}')
            continue

        base = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(APP_DIR, f'{base}_print.html')

        print(f'\n正在转换: {input_path}')

        with open(input_path, 'r', encoding='utf-8') as f:
            html = f.read()
        soup = BeautifulSoup(html, 'html.parser')
        msg_count = sum(1 for b in soup.select('.message-block') if b.select_one('.message'))

        split_count = ask_split_count(msg_count)
        generated = convert(input_path, output_path, split_count=split_count)
        all_generated.extend(generated)

    if all_generated:
        print(f'\n共生成 {len(all_generated)} 个HTML文件')
        answer = input('是否自动将HTML文件转为PDF？(y/n): ').strip().lower()
        if answer == 'y':
            convert_all_to_pdf(all_generated)
        else:
            print('已跳过PDF转换，可手动打开HTML文件后使用 Ctrl+P 打印为PDF')

    input('\n按任意键退出...')


if __name__ == '__main__':
    main()