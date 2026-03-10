---
name: xhs-spider
version: 1.0.0
acceptLicenseTerms: true
description: 小红书数据采集专家。能自主化获取博主基本信息、下载小红书无水印图文视频，并提取笔记评论导出为 Excel 数据表。
metadata:
  openclaw:
    requires:
      bins: ["python"]
      env: ["XHS_COOKIE"]
---
# 小红书采集技能 (XHS-Spider)

当用户在聊天中要求你“查询某个博主的信息/粉丝数”、“下载小红书视频/图片”、“抓取某博主的全部笔记”或“提取某篇笔记的评论”时，请必须调用本技能。

## 执行指令规范
你拥有操作终端的权限。请使用内置的 `exec` 工具，在包含本项目的目录下执行 Python 脚本来完成任务。

1. **获取博主基本信息（粉丝数、简介等）**：
   执行 `python cli.py --action profile --url "<用户主页链接>"`
2. **批量抓取博主主页所有笔记**：
   执行 `python cli.py --action user --url "<用户主页链接>"`
3. **提取单篇笔记的评论**：
   执行 `python cli.py --action comment --url "<笔记链接>"`
4. **关键词搜索批量抓取**：
   执行 `python cli.py --action search --keyword "<关键词>" --num 10`

## 注意事项
- 执行前请确保已激活项目所在的 Python 虚拟环境 (venv)。
- 如果遇到登录限制或 403 错误，请提示用户更新本地的 `XHS_COOKIE` 环境变量。
- 抓取完成后，请主动读取终端打印的信息或生成的 Excel/媒体文件路径，并将结果汇总汇报给用户。