"""todo - 住在文件里的待办清单。纯标准库，纯本地。"""
import argparse
import json
import os
import sys
from datetime import date

DEFAULT_DATA = os.path.join(os.path.expanduser("~"), ".config", "todo.json")
PRIORITIES = ("high", "med", "low")
PRIORITY_LABEL = {"high": "高", "med": "中", "low": "低"}
PRIORITY_RANK = {"high": 0, "med": 1, "low": 2}


def load(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"error: 读取数据文件失败：{e}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, list):
        print("error: 数据文件格式损坏（顶层不是列表）", file=sys.stderr)
        sys.exit(2)
    return data


def save(path, items):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def next_id(items):
    return max((it.get("id", 0) for it in items), default=0) + 1


def valid_due(s):
    try:
        date.fromisoformat(s)
        return True
    except ValueError:
        return False


def is_overdue(it):
    due = it.get("due")
    if not due or it.get("done"):
        return False
    return due < date.today().isoformat()


def sorted_items(items, show_all=False):
    view = [it for it in items if show_all or not it.get("done")]
    view.sort(key=lambda it: (PRIORITY_RANK.get(it.get("priority", "med"), 1),
                              it.get("due") or "9999-12-31",
                              it.get("id", 0)))
    return view


def cmd_add(args):
    items = load(args.data)
    if args.priority not in PRIORITIES:
        print(f"error: 优先级必须是 high/med/low 之一，得到：{args.priority}", file=sys.stderr)
        return 2
    if args.due and not valid_due(args.due):
        print(f"error: 日期格式错误（用 YYYY-MM-DD）：{args.due}", file=sys.stderr)
        return 2
    it = {"id": next_id(items), "text": args.text, "priority": args.priority,
          "due": args.due, "done": False, "created": date.today().isoformat()}
    items.append(it)
    save(args.data, items)
    print(f"已添加 #{it['id']}：{it['text']}")
    return 0


def cmd_list(args):
    items = load(args.data)
    view = sorted_items(items, show_all=args.all)
    if not view:
        print("没有待办事项。" if not args.all else "没有事项。")
        return 0
    today = date.today().isoformat()
    for i, it in enumerate(view, 1):
        flag = "🔴" if is_overdue(it) else "  "
        done_mark = "✓ " if it.get("done") else "  "
        due = f" 截止 {it['due']}" if it.get("due") else ""
        if it.get("due") and it["due"] < today and not it.get("done"):
            due += "（已逾期）"
        print(f"{flag}{done_mark}{i}. [#{it['id']}] [{PRIORITY_LABEL.get(it.get('priority'), '?')}] "
              f"{it['text']}{due}")
    return 0


def find_by_number(items, n, show_all=True):
    view = sorted_items(items, show_all=show_all)
    if n < 1 or n > len(view):
        return None
    return view[n - 1]


def cmd_done(args):
    items = load(args.data)
    it = find_by_number(items, args.n)
    if it is None:
        print(f"error: 没有第 {args.n} 项", file=sys.stderr)
        return 1
    it["done"] = True
    save(args.data, items)
    print(f"已完成 #{it['id']}：{it['text']}")
    return 0


def cmd_rm(args):
    items = load(args.data)
    it = find_by_number(items, args.n)
    if it is None:
        print(f"error: 没有第 {args.n} 项", file=sys.stderr)
        return 1
    items = [x for x in items if x["id"] != it["id"]]
    save(args.data, items)
    print(f"已删除 #{it['id']}：{it['text']}")
    return 0


def cmd_edit(args):
    items = load(args.data)
    it = find_by_number(items, args.n)
    if it is None:
        print(f"error: 没有第 {args.n} 项", file=sys.stderr)
        return 1
    if args.text is not None:
        it["text"] = args.text
    if args.priority is not None:
        if args.priority not in PRIORITIES:
            print(f"error: 优先级必须是 high/med/low 之一", file=sys.stderr)
            return 2
        it["priority"] = args.priority
    if args.due is not None:
        if not valid_due(args.due):
            print(f"error: 日期格式错误（用 YYYY-MM-DD）：{args.due}", file=sys.stderr)
            return 2
        it["due"] = args.due
    if args.clear_due:
        it["due"] = None
    save(args.data, items)
    print(f"已更新 #{it['id']}：{it['text']}")
    return 0


def cmd_clear_done(args):
    items = load(args.data)
    done = [it for it in items if it.get("done")]
    if not done:
        print("没有已完成的事项，无需清理。")
        return 0
    if not args.yes:
        print(f"将删除 {len(done)} 条已完成事项：")
        for it in done:
            print(f"  [#{it['id']}] {it['text']}")
        try:
            ans = input("确认删除？(y/N) ").strip().lower()
        except EOFError:
            ans = ""
        if ans not in ("y", "yes"):
            print("已取消。")
            return 1
    items = [it for it in items if not it.get("done")]
    save(args.data, items)
    print(f"已清理 {len(done)} 条已完成事项。")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="todo", description="住在文件里的待办清单")
    p.add_argument("--data", default=DEFAULT_DATA, help="数据文件路径（默认 ~/.config/todo.json）")
    p.add_argument("--version", action="version", version="todo 0.1.0")
    sub = p.add_subparsers(dest="cmd")

    a = sub.add_parser("add", help="添加事项")
    a.add_argument("text", help="事项内容")
    a.add_argument("--priority", default="med", help="优先级：high/med/low（默认 med）")
    a.add_argument("--due", default=None, help="截止日期 YYYY-MM-DD")

    l = sub.add_parser("list", help="列出事项")
    l.add_argument("--all", action="store_true", help="同时显示已完成")

    d = sub.add_parser("done", help="标记完成")
    d.add_argument("n", type=int, help="列表中的序号")

    r = sub.add_parser("rm", help="删除事项")
    r.add_argument("n", type=int, help="列表中的序号")

    e = sub.add_parser("edit", help="编辑事项")
    e.add_argument("n", type=int, help="列表中的序号")
    e.add_argument("--text", default=None, help="新内容")
    e.add_argument("--priority", default=None, help="新优先级")
    e.add_argument("--due", default=None, help="新截止日期")
    e.add_argument("--clear-due", action="store_true", help="清除截止日期")

    c = sub.add_parser("clear-done", help="清理已完成事项")
    c.add_argument("--yes", action="store_true", help="跳过确认")

    args = p.parse_args(argv)
    if args.cmd is None:
        p.print_help()
        return 2
    return {"add": cmd_add, "list": cmd_list, "done": cmd_done,
            "rm": cmd_rm, "edit": cmd_edit, "clear-done": cmd_clear_done}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
