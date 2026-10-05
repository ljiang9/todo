# todo

住在文件里的待办清单。小、快、离线：数据就是 `~/.config/todo.json`，纯标准库，零依赖。

## 安装

```bash
cd ~/workspace/ai-forks/todo
python3 -m todo add "买牛奶"
```

## 用法

```bash
# 添加（优先级 high/med/low，默认 med）
todo add "买牛奶" --priority high --due 2026-10-06

# 列表：按优先级排序，逾期标 🔴
todo list
todo list --all        # 同时显示已完成

# 完成 / 删除 / 编辑（序号是 list 显示的序号）
todo done 2
todo rm 3
todo edit 1 --due 2026-10-07
todo edit 1 --text "买燕麦奶" --priority low
todo edit 1 --clear-due

# 清理已完成（会先列出并要求确认）
todo clear-done
todo clear-done --yes   # 跳过确认（脚本用）
```

## 数据文件

默认 `~/.config/todo.json`，可用 `--data` 指定别处（方便测试和备份）。JSON 数组，每条：

```json
{"id": 1, "text": "买牛奶", "priority": "high", "due": "2026-10-06",
 "done": false, "created": "2026-10-05"}
```

## 已知局限

- 单机 JSON 文件，没有同步、多设备、协作——定位就是个人小清单。
- 排序是"优先级 > 截止日期 > id"，没有自定义排序。
- 序号是当前列表视图的序号，增删后会变；`--all` 视图和默认视图的序号可能不同。
- 提醒/通知不在范围内。

## License

MIT
