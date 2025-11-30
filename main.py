import feedparser
import random
import os
import datetime
import pytz
import re

# --- 配置区域 ---
RSS_FEEDS = {
    "JPART": "https://academic.oup.com/rss/site_5332/3062.xml",
    "Public Admin Rev": "https://onlinelibrary.wiley.com/feed/15406210/most-recent",
    "Academy of Mgmt Jnl": "https://journals.aom.org/action/showFeed?type=etoc&feed=rss&jc=amj",
    "Public Mgmt Rev": "https://www.tandfonline.com/feed/rss/rpxm20",
    "Governance": "https://onlinelibrary.wiley.com/feed/14680493/most-recent"，
    "IPMJ":"https://www.tandfonline.com/journals/upmj20",
    "PPMR":"https://www.tandfonline.com/journals/mpmr20"
}

def main():
    print("Starting Daily Reader (No-AI Mode)...")
    
    tz = pytz.timezone('Asia/Shanghai')
    today_str = datetime.datetime.now(tz).strftime('%Y-%m-%d')
    
    articles = []
    
    # 1. 抓取文章
    for journal, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]: # 每个期刊多抓几篇备选
                articles.append({
                    "journal": journal,
                    "title": entry.title,
                    "link": entry.link,
                    # 清理摘要中可能出现的复杂HTML标签，只保留基本文本
                    "summary": entry.summary if 'summary' in entry else "No abstract available."
                })
        except:
            continue
            
    # 2. 随机选 2 篇
    if len(articles) < 2:
        selection = articles
    else:
        selection = random.sample(articles, 2)
        
    # 3. 生成 HTML 内容
    # 我们给摘要加一个灰色背景框，方便阅读
    new_content = f"""
    <article class="day-entry" id="{today_str}">
        <div class="date-header">{today_str} Daily Picks</div>
    """
    
    for art in selection:
        new_content += f"""
        <div class="paper-card">
            <span class="tag">{art['journal']}</span>
            <h3><a href="{art['link']}" target="_blank">{art['title']}</a></h3>
            
            <div class="abstract-box">
                <h4>📄 Abstract</h4>
                <div class="abstract-content">
                    {art['summary']}
                </div>
            </div>
            
            <div style="margin-top:15px; text-align:right;">
                <a href="{art['link']}" target="_blank" style="font-size:0.9em; color:#3498db;">👉 Read Full Article</a>
            </div>
        </div>
        """
    new_content += "</article>\n"
    
    # 4. 写入 index.html (包含防重复逻辑)
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            existing_html = f.read()
            
        # 清理旧的今日数据
        pattern = f".*?"
        existing_html = re.sub(pattern, "", existing_html, flags=re.DOTALL)
        
        # 插入新的
        if "" in existing_html:
             final_html = existing_html.replace('', '' + new_content)
        else:
             final_html = existing_html.replace('<body>', '<body>\n\n' + new_content)
             
    else:
        # 初始化模版
        final_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>My PA/OB Daily Reader</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f0f2f5; color: #333; }}
                .date-header {{ font-size: 1.5em; font-weight: bold; margin: 40px 0 20px; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
                .paper-card {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px; }}
                .tag {{ background: #e1ecf4; color: #39739d; padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: 600; }}
                h3 a {{ color: #2c3e50; text-decoration: none; }}
                h3 a:hover {{ color: #3498db; }}
                .abstract-box {{ background: #f9f9f9; padding: 15px; border-radius: 8px; margin-top: 15px; border-left: 4px solid #bdc3c7; }}
                .abstract-box h4 {{ margin: 0 0 10px 0; color: #7f8c8d; font-size: 0.9em; text-transform: uppercase; }}
                .abstract-content {{ font-size: 0.95em; line-height: 1.6; color: #444; }}
            </style>
        </head>
        <body>
            <h1 style="text-align:center">📚 My Personal Academic Journal</h1>
            {new_content}
        </body>
        </html>
        """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)

if __name__ == "__main__":
    main()
