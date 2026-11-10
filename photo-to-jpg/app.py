#!/usr/bin/env python3
"""Batch convert images to JPEG, with optional source cleanup."""
import argparse
import queue
import subprocess
import sys
import threading
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

IGNORED_FILES = {'.DS_Store'}
EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff', '.gif'}


def convert(source, destination, quality=55, report=lambda message: None, delete=False):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_dir():
        raise ValueError('输入文件夹不存在。')
    if source == destination or source in destination.parents:
        raise ValueError('输出文件夹不能是输入文件夹或其子文件夹。')
    if destination in source.parents:
        raise ValueError('输出文件夹不能是输入文件夹的上级文件夹。')
    if not 1 <= quality <= 95:
        raise ValueError('质量须在 1 到 95 之间。')
    entries = list(source.rglob('*'))
    input_files = [p for p in entries if p.is_file() and p.name not in IGNORED_FILES]
    files = sorted(p for p in input_files if p.suffix.lower() in EXTENSIONS)
    initial_stats = {p: (p.stat().st_dev, p.stat().st_ino, p.stat().st_size, p.stat().st_mtime_ns) for p in files}
    created = []
    destination.mkdir(parents=True, exist_ok=True)
    successes, failures = 0, 0
    for path in files:
        target = destination / path.relative_to(source).with_suffix('.jpg')
        target.parent.mkdir(parents=True, exist_ok=True)
        # Never overwrite an existing file or another image with the same stem.
        base = target
        number = 2
        while target.exists():
            target = base.with_name(f'{base.stem}_{number}{base.suffix}')
            number += 1
        try:
            with Image.open(path) as image:
                image = ImageOps.exif_transpose(image)
                if image.mode in ('RGBA', 'LA') or 'transparency' in image.info:
                    rgba = image.convert('RGBA')
                    background = Image.new('RGB', rgba.size, 'white')
                    background.paste(rgba, mask=rgba.getchannel('A'))
                    image = background
                else:
                    image = image.convert('RGB')
                # Exclusive creation prevents overwriting if another process creates the name.
                with target.open('xb') as out:
                    try:
                        image.save(out, 'JPEG', quality=quality, optimize=True)
                        current_quality = quality
                        for _ in range(3):
                            if out.tell() <= 1024 * 1024 or current_quality == 1:
                                break
                            current_quality = max(1, current_quality - 10)
                            out.seek(0)
                            out.truncate()
                            image.save(out, 'JPEG', quality=current_quality, optimize=True)
                    except Exception:
                        out.close()
                        target.unlink(missing_ok=True)
                        raise
            created.append(target)
            successes += 1
            report(f'完成：{path.relative_to(source)} → {target.relative_to(destination)}')
        except (OSError, ValueError, UnidentifiedImageError) as exc:
            failures += 1
            report(f'失败：{path.relative_to(source)}（{exc}）')
    current_entries = list(source.rglob('*'))
    current_files = [p for p in current_entries if p.is_file() and p.name not in IGNORED_FILES]
    output_files = [p for p in destination.rglob('*') if p.is_file() and p.name not in IGNORED_FILES]
    match = len(current_files) == len(output_files)
    report(f'文件数量核对：输入 {len(current_files)} 个，输出 {len(output_files)} 个（{"一致" if match else "不一致"}）。')
    if delete:
        unchanged = (set(current_files) == set(files) and all(
            (p.stat().st_dev, p.stat().st_ino, p.stat().st_size, p.stat().st_mtime_ns) == initial_stats[p]
            for p in files))
        safe = (bool(files) and not failures and successes == len(files) and match
                and unchanged and not any(p.is_symlink() for p in current_entries)
                and all(p.is_file() for p in created))
        if not safe:
            reasons = []
            unsupported = [p for p in current_files if p.suffix.lower() not in EXTENSIONS]
            links = [p for p in current_entries if p.is_symlink()]
            if not files: reasons.append('没有找到支持的图片')
            if failures: reasons.append(f'{failures} 张图片转换失败，详情见上方失败记录')
            if unsupported: reasons.append('不支持的文件：' + '、'.join(str(p.relative_to(source)) for p in unsupported[:10]))
            if links: reasons.append('符号链接：' + '、'.join(str(p.relative_to(source)) for p in links[:10]))
            if set(current_files) != set(input_files): reasons.append('运行期间输入文件列表发生变化')
            elif not unchanged and not unsupported: reasons.append('运行期间输入文件发生变化')
            if not match: reasons.append(f'文件数量不一致：输入 {len(current_files)}，输出 {len(output_files)}')
            if not all(p.is_file() for p in created): reasons.append('本次生成的输出文件缺失')
            raise ValueError('未清空输入文件夹：' + '；'.join(reasons))
        for path in files:
            path.unlink()
        for path in current_entries:
            if path.name in IGNORED_FILES and path.is_file():
                path.unlink()
        for path in sorted((p for p in current_entries if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
            path.rmdir()
        report('已清空输入文件夹，文件夹本身已保留。')
    return len(files), successes, failures


def mac_gui(delete=False):
    """Use native macOS dialogs without depending on the system Tcl/Tk build."""
    def dialog(script, *arguments):
        result = subprocess.run(['osascript', '-e', script, *arguments],
                                capture_output=True, text=True)
        if result.returncode:
            if '(-128)' in result.stderr:
                return None
            raise RuntimeError(result.stderr.strip() or '无法打开 macOS 对话框。')
        return result.stdout.strip()

    try:
        source = dialog('POSIX path of (choose folder with prompt "选择照片文件夹")')
        if source is None: return
        destination = dialog('POSIX path of (choose folder with prompt "选择输出文件夹（不能与照片文件夹互为上下级）")')
        if destination is None: return
        value = dialog('text returned of (display dialog "输入 JPG 质量（1–95，越低文件通常越小）" default answer "55" buttons {"取消", "开始转换"} default button "开始转换")')
        if value is None: return
        try:
            quality = int(value)
        except ValueError:
            raise ValueError('质量须为 1 到 95 的整数。')
        failures = []
        checks = []
        def report(message):
            print(message, flush=True)
            if message.startswith('失败：'):
                failures.append(message)
            if message.startswith(('文件数量核对：', '已清空输入文件夹')):
                checks.append(message)
        total, ok, failed = convert(source, destination, quality, report, delete)
        summary = f'转换结束：找到 {total} 张，成功 {ok} 张，失败 {failed} 张。\n输出文件夹：{destination}'
        if checks:
            summary += '\n' + '\n'.join(checks)
        if failures:
            summary += '\n\n' + '\n'.join(failures[:5])
            if len(failures) > 5: summary += '\n更多失败详情请查看终端。'
        dialog('on run argv\n display dialog (item 1 of argv) buttons {"确定"} default button "确定" with title "照片转 JPG"\nend run', summary)
    except (ValueError, OSError, RuntimeError) as exc:
        print(f'错误：{exc}', file=sys.stderr)
        dialog('on run argv\n display dialog (item 1 of argv) buttons {"确定"} default button "确定" with title "转换失败" with icon stop\nend run', str(exc))


def gui(delete=False):
    if sys.platform == 'darwin':
        return mac_gui(delete)
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    root = tk.Tk()
    root.title('照片转 JPG')
    root.geometry('720x520')
    root.minsize(560, 400)
    frame = ttk.Frame(root, padding=16)
    frame.pack(fill='both', expand=True)
    source = tk.StringVar()
    destination = tk.StringVar()
    quality = tk.IntVar(value=55)
    ttk.Label(frame, text='批量转换并压缩照片为 JPG', font=('', 18, 'bold')).pack(anchor='w', pady=(0, 12))
    def row(label, variable, choose):
        box = ttk.Frame(frame)
        box.pack(fill='x', pady=5)
        ttk.Label(box, text=label, width=12).pack(side='left')
        ttk.Entry(box, textvariable=variable).pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(box, text='选择…', command=choose).pack(side='left')
    def choose_source():
        value = filedialog.askdirectory(title='选择照片文件夹')
        if value:
            source.set(value)
            if not destination.get():
                p = Path(value)
                destination.set(str(p.parent / (p.name + '_JPG')))
    def choose_destination():
        value = filedialog.askdirectory(title='选择输出文件夹')
        if value:
            destination.set(value)
    row('照片文件夹', source, choose_source)
    row('输出文件夹', destination, choose_destination)
    options = ttk.Frame(frame)
    options.pack(fill='x', pady=8)
    ttk.Label(options, text='JPG 质量（1–95）').pack(side='left')
    ttk.Spinbox(options, from_=1, to=95, textvariable=quality, width=5).pack(side='left', padx=8)
    ttk.Label(options, text='数值越低，文件通常越小').pack(side='left')
    log = tk.Text(frame, height=12, state='disabled', wrap='word')
    log.pack(fill='both', expand=True, pady=8)
    messages = queue.Queue()
    def append(text):
        log.configure(state='normal')
        log.insert('end', text + '\n')
        log.see('end')
        log.configure(state='disabled')
    def poll():
        try:
            while True:
                kind, value = messages.get_nowait()
                if kind == 'log': append(value)
                else:
                    button.configure(state='normal')
                    append(value)
                    if kind == 'error': messagebox.showerror('转换失败', value)
        except queue.Empty:
            pass
        root.after(100, poll)
    def start():
        try:
            q = quality.get()
            if not source.get().strip() or not destination.get().strip():
                raise ValueError('请选择输入和输出文件夹。')
            if not 1 <= q <= 95: raise ValueError('质量须在 1 到 95 之间。')
        except (ValueError, tk.TclError) as exc:
            messagebox.showerror('请检查设置', str(exc)); return
        src, dst = source.get(), destination.get()
        button.configure(state='disabled')
        append('开始转换……')
        def work():
            try:
                total, ok, failed = convert(src, dst, q, lambda s: messages.put(('log', s)), delete)
                messages.put(('done', f'结束：找到 {total} 张，成功 {ok} 张，失败 {failed} 张。'))
            except Exception as exc:
                messages.put(('error', str(exc)))
        threading.Thread(target=work, daemon=True).start()
    button = ttk.Button(frame, text='开始转换', command=start)
    button.pack(anchor='e')
    poll()
    root.mainloop()


def main():
    parser = argparse.ArgumentParser(
        description='离线批量转换并压缩图片为 JPG。未指定文件夹时打开选择界面。',
        epilog='示例：\n'
               '  %(prog)s /照片文件夹 /输出文件夹\n'
               '  %(prog)s /照片文件夹 /输出文件夹 --quality 55 --delete\n'
               '  %(prog)s /照片文件夹 /输出文件夹 --inspect\n'
               '默认质量为 55；输出超过 1 MB 时每次降低质量 10，最多重试三次。',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('source', nargs='?', help='输入文件夹；不指定时打开图形界面')
    parser.add_argument('destination', nargs='?', help='输出文件夹（可自动创建；建议使用空文件夹）')
    parser.add_argument('--quality', type=int, help='JPG 质量 1–95，默认 55；指定后跳过命令行询问')
    parser.add_argument('--delete', action='store_true', help='转换及数量核对成功后清空输入文件夹，保留文件夹本身')
    parser.add_argument('--inspect', action='store_true', help='仅检查文件数量、不支持的文件和符号链接，不转换或删除')
    args = parser.parse_args()
    if args.inspect:
        if not args.source or not args.destination or args.delete:
            parser.error('--inspect 需要输入和输出文件夹，且不能与 --delete 同时使用。')
        src, dst = Path(args.source), Path(args.destination)
        if not src.is_dir() or not dst.is_dir():
            parser.error('输入和输出文件夹必须存在。')
        entries = list(src.rglob('*'))
        input_files = [p for p in entries if p.is_file() and p.name not in IGNORED_FILES]
        output_files = [p for p in dst.rglob('*') if p.is_file() and p.name not in IGNORED_FILES]
        print(f'输入文件：{len(input_files)} 个；输出文件：{len(output_files)} 个（均不计 .DS_Store）。')
        unsupported = [p for p in input_files if p.suffix.lower() not in EXTENSIONS]
        links = [p for p in entries if p.is_symlink()]
        for label, items in [('不支持的文件', unsupported), ('符号链接', links)]:
            print(f'{label}：{len(items)} 个')
            for path in items:
                print(f'  {path.relative_to(src)}')
        print('此检查不会转换或删除文件，也不能判断之前的转换是否全部成功。')
    elif args.source is None and args.destination is None:
        gui(args.delete)
    elif args.source and args.destination:
        try:
            quality = args.quality
            if quality is None:
                while True:
                    value = input('请输入 JPG 质量（1–95，直接回车使用 55）：').strip()
                    try:
                        quality = int(value) if value else 55
                        if 1 <= quality <= 95:
                            break
                    except ValueError:
                        pass
                    print('请输入 1 到 95 之间的整数。')
            total, ok, failed = convert(args.source, args.destination, quality, print, args.delete)
            print(f'结束：找到 {total} 张，成功 {ok} 张，失败 {failed} 张。')
            if failed: raise SystemExit(1)
        except (ValueError, EOFError, OSError) as exc:
            parser.error(str(exc) or '无法读取质量，请使用 --quality 指定。')
    else:
        parser.error('请同时提供输入和输出文件夹。')

if __name__ == '__main__':
    main()
