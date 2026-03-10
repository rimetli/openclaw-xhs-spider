import streamlit as st
import os
import pandas as pd
from main import Data_Spider
from xhs_utils.common_util import init

# --- 页面基本设置 ---
st.set_page_config(page_title="小红书下载器 Web UI", layout="wide")
st.title("🍉 小红书爬虫可视化控制台")

# --- 初始化爬虫和配置 ---
@st.cache_resource
def get_spider_instance():
    return Data_Spider()

data_spider = get_spider_instance()

# 尝试读取本地的 Cookie 和保存路径配置
try:
    cookies_str, base_path = init()
    
    # 确保保存评论的 excel 目录存在
    excel_dir = base_path.get('excel', './')
    if not os.path.exists(excel_dir):
        os.makedirs(excel_dir)
        
    st.success(f"✅ 成功加载本地配置。媒体文件将保存至: {base_path.get('media', '默认路径')}")
except Exception as e:
    st.error("❌ 配置文件加载失败，请检查 .env 或 config 里的 Cookie 是否配置正确！")
    st.stop()

# --- 构建四个功能标签页 ---
tab1, tab2, tab3, tab4 = st.tabs(["📝 1. 指定链接下载", "👤 2. 博主主页下载", "🔍 3. 关键词搜索下载", "💬 4. 笔记评论提取"])

# ----------------- 模式一：指定链接下载 -----------------
with tab1:
    st.subheader("批量下载指定的笔记链接")
    notes_input = st.text_area("输入笔记链接 (每行一个)", height=150, placeholder="https://www.xiaohongshu.com/explore/...")
    
    col1, col2 = st.columns(2)
    with col1:
        t1_save_choice = st.selectbox("保存选项", ["all", "media", "excel"], index=0, key="t1_save")
    with col2:
        t1_excel_name = st.text_input("Excel文件名 (如果选了all或excel必填)", value="指定链接导出", key="t1_excel")
        
    if st.button("🚀 开始下载指定笔记", type="primary"):
        if not notes_input.strip():
            st.warning("请先输入链接！")
        else:
            # 将文本框里的内容按行分割成列表
            note_list = [note.strip() for note in notes_input.split('\n') if note.strip()]
            with st.spinner(f"正在下载 {len(note_list)} 篇笔记，请查看终端运行日志..."):
                data_spider.spider_some_note(note_list, cookies_str, base_path, t1_save_choice, t1_excel_name)
            st.success("🎉 下载任务完成！")

# ----------------- 模式二：博主主页下载 -----------------
with tab2:
    st.subheader("下载博主主页的所有笔记")
    user_url = st.text_input("输入博主主页链接", placeholder="https://www.xiaohongshu.com/user/profile/...")
    
    t2_save_choice = st.selectbox("保存选项", ["all", "media", "excel"], index=0, key="t2_save")
    
    if st.button("🚀 开始下载博主主页", type="primary"):
        if not user_url:
            st.warning("请先输入博主链接！")
        else:
            with st.spinner("正在疯狂抓取中，请查看终端日志..."):
                data_spider.spider_user_all_note(user_url, cookies_str, base_path, t2_save_choice)
            st.success("🎉 该博主所有笔记下载完成！")

# ----------------- 模式三：关键词搜索下载 -----------------
with tab3:
    st.subheader("根据关键词批量搜索并下载")
    
    col3, col4 = st.columns(2)
    with col3:
        query = st.text_input("搜索关键词", placeholder="例如：北京旅游攻略")
        query_num = st.number_input("抓取数量", min_value=1, max_value=200, value=10)
    with col4:
        t3_save_choice = st.selectbox("保存选项", ["all", "media", "excel"], index=0, key="t3_save")
        sort_type = st.selectbox("排序方式", ["0 综合排序", "1 最新", "2 最多点赞", "3 最多评论", "4 最多收藏"], index=0)
        note_type = st.selectbox("笔记类型", ["0 不限", "1 视频笔记", "2 普通图文"], index=0)
    
    if st.button("🚀 开始搜索并下载", type="primary"):
        if not query:
            st.warning("请先输入关键词！")
        else:
            sort_val = int(sort_type.split()[0])
            type_val = int(note_type.split()[0])
            
            with st.spinner(f"正在搜索【{query}】并下载前 {query_num} 篇..."):
                data_spider.spider_some_search_note(
                    query=query, 
                    require_num=query_num, 
                    cookies_str=cookies_str, 
                    base_path=base_path, 
                    save_choice=t3_save_choice, 
                    sort_type_choice=sort_val, 
                    note_type=type_val
                )
            st.success("🎉 搜索下载任务完成！")

# ----------------- 模式四：笔记评论提取 (新增) -----------------
with tab4:
    st.subheader("抓取单篇笔记下的所有评论与用户信息")
    
    col_a, col_b = st.columns([3, 1])
    with col_a:
        comment_note_url = st.text_input("输入要抓取评论的笔记链接", placeholder="https://www.xiaohongshu.com/explore/...", key="comment_url")
    with col_b:
        export_filename = st.text_input("导出的Excel文件名", value="笔记评论数据", key="comment_file")

    if st.button("🚀 开始抓取并导出 Excel", type="primary", key="btn_comment"):
        if not comment_note_url:
            st.warning("请先输入笔记链接！")
        else:
            with st.spinner("正在逐页请求评论数据，请稍候..."):
                # 复用 Data_Spider 内部的 xhs_apis 实例调用底层评论接口
                success, msg, all_comments = data_spider.xhs_apis.get_note_all_comment(comment_note_url, cookies_str)
                
                if success and all_comments:
                    parsed_data = []
                    
                    # 遍历解析每一条一级评论及其下的二级回复
                    for comment in all_comments:
                        # 提取一级评论
                        user_info = comment.get('user_info', {})
                        user_id = user_info.get('user_id', '')  # ⭐️ 改为获取底层的 user_id
                        
                        parsed_data.append({
                            "层级": "一级评论",
                            "评论者昵称": user_info.get('nickname', ''),
                            "系统用户ID": user_id,  # ⭐️ 替换掉获取不到的红书号
                            "主页链接": f"https://www.xiaohongshu.com/user/profile/{user_id}" if user_id else "", # ⭐️ 新增：拼出主页直达链接
                            "评论内容": comment.get('content', ''),
                            "点赞数": comment.get('like_count', 0),
                            "IP属地": comment.get('ip_location', '未知')
                        })
                        
                        # 提取二级评论（回复）
                        for sub in comment.get('sub_comments', []):
                            sub_user = sub.get('user_info', {})
                            sub_user_id = sub_user.get('user_id', '') # ⭐️ 二级评论的 user_id
                            
                            target_user = sub.get('target_user_info', {})
                            target_name = target_user.get('nickname', '') if target_user else ''
                            
                            content = sub.get('content', '')
                            if target_name:
                                content = f"回复 @{target_name} : {content}"
                                
                            parsed_data.append({
                                "层级": "--- 二级回复",
                                "评论者昵称": sub_user.get('nickname', ''),
                                "系统用户ID": sub_user_id,
                                "主页链接": f"https://www.xiaohongshu.com/user/profile/{sub_user_id}" if sub_user_id else "", # ⭐️ 新增：拼出主页直达链接
                                "评论内容": content,
                                "点赞数": sub.get('like_count', 0),
                                "IP属地": sub.get('ip_location', '未知')
                            })

                    # 转换为 Pandas 数据表并导出
                    df = pd.DataFrame(parsed_data)
                    final_excel_path = os.path.abspath(os.path.join(excel_dir, f"{export_filename}.xlsx"))
                    df.to_excel(final_excel_path, index=False)
                    
                    st.success(f"🎉 成功抓取 {len(df)} 条评论数据！文件已保存至：{final_excel_path}")
                    
                    # 在网页上直接预览前几条数据
                    st.write("📊 **数据预览：**")
                    st.dataframe(df.head(50))
                else:
                    if not all_comments and success:
                        st.warning("⚠️ 该笔记目前没有评论，或者已被作者关闭评论。")
                    else:
                        st.error(f"❌ 抓取失败。原因: {msg}")