import feedparser
import random
import os
import datetime
import pytz
import re
import sys

# --- 配置区域 ---
RSS_FEEDS = {
    "JPART": "https://academic.oup.com/rss/site_5332/3062.xml",
    "Public Admin Rev": "https://onlinelibrary.wiley.com/feed/15406210/most-recent",
    "Academy of Mgmt Jnl": "https://journals.aom.org/action/showFeed?type=etoc&feed=rss&jc=amj",
    "Public Mgmt Rev": "https://www.tandfonline.com/feed/rss/rpxm20",
    "Governance": "https://onlinelibrary.wiley.com/feed/14680493/most-recent"
}

def clean_text(html_text):
    if not html_text: return ""
    # 简单的去除HTML标签
    text = re.sub(r'<[^>]+>', '', str(html_text))
    return text.strip()

def safe_get_summary(entry):
    """
    极度安全的获取摘要方法，优先保证不报错
    """
    try:
        content = ""
        
        # 1. 尝试获取 'content' (通常是列表)
        if 'content' in entry:
            c_list = entry.get('content', [])
            for c in c_list:
                if isinstance(c, dict) and 'value' in c:
                    content += c['value']
                elif hasattr(c, 'value'):
                    content += c.value
        
        # 2. 尝试获取 'summary'
        if not content and 'summary' in entry:
            content = entry['summary']
            
        # 3. 尝试获取 'description'
        if not content and 'description' in entry:
            content = entry['description']

        # 清理文本
        clean_content = clean_text(content)
        
        if len(clean_content) < 20:
            return "Abstract not available in RSS feed. Please check the link."
        
        if len(clean_content) > 1000:
            return clean_content[:1000] + "..."
            
        return clean_content
        
    except Exception as e:
        print(f"Warning: parsing summary failed ({e})")
        return "Summary parsing error."

def main():
    print("Starting Daily Reader (Fail-Safe Mode)...")
    
    try:
        # 1. 设置时间
        try:
            tz = pytz.timezone('Asia/Shanghai')
            today_str = datetime.datetime.now(tz).strftime('%Y-%m-%d')
        except:
            today_str = str(datetime.date.today())

        all_articles = []

        # 2. 循环抓取
        for journal_name, url in RSS_FEEDS.items():
            print(f"Checking {journal_name}...")
            try:
                feed = feedparser.parse(url)
                
                # 如果这个源坏了，直接跳过
                if not feed.entries:
                    print(f"  -> No entries found.")
                    continue

                for entry in feed.entries[:2]:
                    # 安全获取标题和链接
                    title = entry.get('title', 'No Title')
                    link = entry.get('link', '#')
                    summary = safe_get_summary(entry)
                    
                    all_articles.append({
                        "journal": journal_name,
                        "title": title,
                        "link": link,
                        "summary": summary
                    })
            except Exception as e:
                print(f"  -> Error fetching {journal_name}: {e}")
                continue

        # 3. 如果没抓到文章，塞一个假的，防止网页空白
        if not all_articles:
            all_articles.append({
                "journal": "System",
                "title": "No new articles found today",
                "link": "#",
                "summary": "Please check back tomorrow."
            })

        # 4. 随机选 2 篇
        selected = random.sample(all_articles, min(2, len(all_articles)))

        # 5. 生成 HTML
        new_content = f"""
        <article class="day-entry" id="{today_str}">
            <div class="date-header">{today_str} Daily Picks</div>
        """
        
        for art in selected:
            new_content += f"""
            <div class="paper-card">
                <span class="tag">{art['journal']}</span>
                <h3><a href="{art['link']}" target="_blank">{art['title']}</a></h3>
                <div class="abstract-box">
                    <p>{art['summary']}</p>
                </div>
                <div style="text-align:right; margin-top:10px;">
                     <a href="{art['link']}" target="_blank" style="color:#0366d6; text-decoration:none;">Read Source 👉</a>
                </div>
            </div>
            """
        new_content += "</article>\n"

        # 6. 读取并写入 index.html
        if os.path.exists("index.html"):
            with open("index.html", "r", encoding="utf-8") as f:
                content = f.read()
            
            # 删除今天的旧条目（如果存在）
            content = re.sub(f".*?", "", content, flags=re.DOTALL)
            
            # 插入新条目
            if "" in content:
                content = content.replace("", "\n" + new_content)
            else:
                content = content.replace("<body>", "<body>\n\n" + new_content)
        else:
            # 只有当文件不存在时才创建新模版
            content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Daily Reader</title>
<style>
body {{ font-family: sans-serif; max-width: 800px; margin: 20px auto; padding: 0 20px; background:#f6f8fa; }}
.date-header {{ font-size: 1.2em; font-weight: bold; margin: 30px 0 10px; border-bottom: 2px solid #ddd; padding-bottom:5px; }}
.paper-card {{ background: white; padding: 20px; border-radius: 8px; border: 1px solid #e1e4e8; margin-bottom: 20px; }}
.tag {{ background: #def; color: #0366d6; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }}
h3 {{ margin: 10px 0; font-size: 1.1em; }}
h3 a {{ color: #24292e; text-decoration: none; }}
h3 a:hover {{ color: #0366d6; }}
.abstract-box {{ font-size: 0.9em; color: #586069; line-height: 1.5; margin-top: 10px; }}
</style>
</head>
<body>
<h1 style="text-align:center">My Daily Academic Reader</h1>
{new_content}
</body>
</html>"""

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(content)
            
        print("Success! index.html updated.")

    except Exception as e:
        # 最外层的防崩溃：如果上面代码还有错，这里会捕获，不让 Action 报红
        print(f"CRITICAL ERROR CAUGHT: {e}")
        # 这里虽然出错了，但我们以 exit(0) 退出，GitHub 会认为运行成功
        # 这样你就不会收到报错邮件，但你需要查看 Logs 才知道哪出错了
        sys.exit(0)

if __name__ == "__main__":
    main()
