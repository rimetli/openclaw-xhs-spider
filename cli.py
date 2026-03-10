import argparse
import os
import pandas as pd
from loguru import logger
from main import Data_Spider
from xhs_utils.common_util import init

def get_cookie():
    """
    优先尝试从环境变量（AI 传入）读取 Cookie，
    如果没有，则回退读取本地配置文件的 Cookie。
    """
    env_cookie = os.environ.get("XHS_COOKIE")
    if env_cookie and env_cookie.strip():
        logger.info("已读取到环境变量 XHS_COOKIE")
        return env_cookie
        
    try:
        cookies_str, _ = init()
        return cookies_str
    except Exception as e:
        logger.error(f"无法读取 Cookie: {e}")
        return ""

def main():
    # 1. 定义命令行参数解析器 (新增了 profile 选项)
    parser = argparse.ArgumentParser(description="🍉 小红书爬虫 CLI (专为 AI Agent 设计)")
    parser.add_argument("--action", choices=["profile", "user", "comment", "search", "note"], required=True, help="要执行的任务类型")
    parser.add_argument("--url", type=str, help="小红书的主页链接或笔记链接")
    parser.add_argument("--keyword", type=str, help="搜索关键词 (仅 action=search 时需要)")
    parser.add_argument("--num", type=int, default=10, help="抓取数量限制")
    
    args = parser.parse_args()
    
    # 2. 初始化配置和爬虫实例
    cookies_str = get_cookie()
    if not cookies_str:
        print("[ERROR] 缺少小红书 Cookie，请设置 XHS_COOKIE 环境变量或检查本地配置！")
        return

    _, base_path = init()
    data_spider = Data_Spider()
    excel_dir = base_path.get('excel', './')
    if not os.path.exists(excel_dir):
        os.makedirs(excel_dir)

    print(f"[INFO] 正在启动 {args.action} 任务...")

    # 3. 任务分发执行
    if args.action == "profile":
        if not args.url:
            print("[ERROR] 缺少 --url 参数")
            return
        # 提取 user_id 并调用接口获取信息
        user_id = args.url.split('?')[0].split('/')[-1]
        success, msg, res_json = data_spider.xhs_apis.get_user_info(user_id, cookies_str)
        
        if success:
            user_data = res_json.get("data", {})
            basic_info = user_data.get("basic_info", {})
            interactions = user_data.get("interactions", [])
            
            # 打印格式化文本，供 AI 提取并自然语言输出
            print("[SUCCESS] 成功获取博主信息：")
            print(f"- 昵称: {basic_info.get('nickname', '未知')}")
            print(f"- 简介: {basic_info.get('desc', '无')}")
            print(f"- 小红书号: {basic_info.get('red_id', '未知')}")
            if len(interactions) >= 3:
                print(f"- 关注数: {interactions[0].get('count', 0)}")
                print(f"- 粉丝数: {interactions[1].get('count', 0)}")
                print(f"- 获赞与收藏: {interactions[2].get('count', 0)}")
        else:
            print(f"[ERROR] 获取博主信息失败，原因: {msg}")

    elif args.action == "user":
        if not args.url:
            print("[ERROR] 缺少 --url 参数")
            return
        # 抓取博主主页
        data_spider.spider_user_all_note(args.url, cookies_str, base_path, 'all')
        print(f"[SUCCESS] 博主主页抓取完成，文件已保存至: {os.path.abspath(base_path.get('media', './'))}")

    elif args.action == "note":
        if not args.url:
            print("[ERROR] 缺少 --url 参数")
            return
        # 抓取单篇笔记内容
        data_spider.spider_some_note([args.url], cookies_str, base_path, 'all', 'cli_note_export')
        print(f"[SUCCESS] 笔记抓取完成，媒体文件位于: {os.path.abspath(base_path.get('media', './'))}")

    elif args.action == "search":
        if not args.keyword:
            print("[ERROR] 缺少 --keyword 参数")
            return
        # 搜索并抓取
        data_spider.spider_some_search_note(
            query=args.keyword, 
            require_num=args.num, 
            cookies_str=cookies_str, 
            base_path=base_path, 
            save_choice='all', 
            sort_type_choice=0, note_type=0, note_time=0, note_range=0, pos_distance=0, geo=None
        )
        print(f"[SUCCESS] 关键词搜索抓取完成，媒体文件位于: {os.path.abspath(base_path.get('media', './'))}")

    elif args.action == "comment":
        if not args.url:
            print("[ERROR] 缺少 --url 参数")
            return
        # 复用之前的评论抓取逻辑
        success, msg, all_comments = data_spider.xhs_apis.get_note_all_comment(args.url, cookies_str)
        if success and all_comments:
            parsed_data = []
            for comment in all_comments:
                user_info = comment.get('user_info', {})
                user_id = user_info.get('user_id', '')
                parsed_data.append({
                    "层级": "一级评论",
                    "评论者昵称": user_info.get('nickname', ''),
                    "系统用户ID": user_id,
                    "主页链接": f"https://www.xiaohongshu.com/user/profile/{user_id}" if user_id else "",
                    "评论内容": comment.get('content', ''),
                    "点赞数": comment.get('like_count', 0),
                    "IP属地": comment.get('ip_location', '未知')
                })
                
                for sub in comment.get('sub_comments', []):
                    sub_user = sub.get('user_info', {})
                    sub_user_id = sub_user.get('user_id', '')
                    target_user = sub.get('target_user_info', {})
                    target_name = target_user.get('nickname', '') if target_user else ''
                    
                    content = sub.get('content', '')
                    if target_name:
                        content = f"回复 @{target_name} : {content}"
                        
                    parsed_data.append({
                        "层级": "--- 二级回复",
                        "评论者昵称": sub_user.get('nickname', ''),
                        "系统用户ID": sub_user_id,
                        "主页链接": f"https://www.xiaohongshu.com/user/profile/{sub_user_id}" if sub_user_id else "",
                        "评论内容": content,
                        "点赞数": sub.get('like_count', 0),
                        "IP属地": sub.get('ip_location', '未知')
                    })

            df = pd.DataFrame(parsed_data)
            # 使用 URL 最后一段的 ID 作为文件名
            note_id = args.url.split('?')[0].split('/')[-1]
            final_excel_path = os.path.abspath(os.path.join(excel_dir, f"评论_{note_id}.xlsx"))
            df.to_excel(final_excel_path, index=False)
            
            # 这句 print 非常关键，龙虾 AI 会读取这句话来回答人类
            print(f"[SUCCESS] 成功抓取 {len(df)} 条评论！Excel 文件已保存至绝对路径: {final_excel_path}")
        else:
            print(f"[ERROR] 评论抓取失败或无评论，原因: {msg}")

if __name__ == "__main__":
    main()