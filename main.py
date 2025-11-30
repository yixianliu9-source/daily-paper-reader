import feedparser
import random
import os
import datetime
import pytz
from openai import OpenAI

# --- 配置区域 ---
# 如果用 DeepSeek，Base URL 是 https://api.deepseek.com
# 如果用其它(如ChatGPT)，请改为对应 URL
API_BASE = "https://api.deepseek.com" 
MODEL_NAME = "deepseek-chat" # 或者 "gpt-3.5-turbo"

RSS_FEEDS = {
    "JPART": "https://academic.oup.com/rss/site_5332/3062.xml",
    "Public Admin Rev": "https://onlinelibrary.wiley.com/feed/15406210/most-recent",
    "Academy of Mgmt Jnl": "https://journals.aom.org/action/showFeed?type=etoc&feed=rss&jc=amj",
    "Public Mgmt Rev": "https://www.tandfonline.com/feed/rss/rpxm20",
    "Governance": "https://onlinelibrary.wiley.com/feed/14680493/most-recent",
    "IPMJ":"https://www.tandfonline.com/journals/upmj20",
    "PPMR":"https://www.tandfonline.com/journals/mpmr20"
}

def get_summary(title, abstract):
    client = OpenAI(api_key=os.environ.get("LLM_API_KEY"), base_url=API_BASE)
    
    prompt = f"""
    You are a Professor in Public Administration. Summarize the following academic paper abstract.
    Paper Title: {title}
    Abstract: {abstract}
    
    Output format (in Chinese, use HTML tags):
    <div class='analysis'>
        <p><strong>💡 Key Ideas:</strong> [Summarize core arguments in 2-3 bullet points]</p>
        <p><strong>⚠️ Limitations:</strong> [Critique potential limitations]</p>
    </div>
    """
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"<p>AI Summary failed: {str(e)}</p>"

def main():
    print("Starting Daily Reader...")
    articles = []
    
    # 1. Fetch Articles
    for journal, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]: # Check top 3
                articles.append({
                    "journal": journal,
                    "title": entry.title,
                    "link": entry.link,
                    "summary": entry.summary[:1000] if 'summary' in entry else "No abstract"
                })
        except:
            continue
            
    # 2. Pick 2 Random
    if len(articles) < 2:
        selection = articles
    else:
        selection = random.sample(articles, 2)
        
    # 3. Generate HTML Content
    tz = pytz.timezone('Asia/Shanghai')
    today_str = datetime.datetime.now(tz).strftime('%Y-%m-%d')
    
    new_content = f"""
    <article class="day-entry" id="{today_str}">
        <div class="date-header">{today_str} Daily Picks</div>
    """
    
    for art in selection:
        print(f"Summarizing: {art['title']}")
        ai_summary = get_summary(art['title'], art['summary'])
        new_content += f"""
        <div class="paper-card">
            <span class="tag">{art['journal']}</span>
            <h3><a href="{art['link']}" target="_blank">{art['title']}</a></h3>
            {ai_summary}
        </div>
        """
    new_content += "</article>"
    
    # 4. Read existing index.html or create new
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            existing_html = f.read()
            # Split to insert new content after the <body> tag
            parts = existing_html.split('')
            if len(parts) == 2:
                final_html = parts[0] + '' + new_content + parts[1]
            else:
                final_html = existing_html # Fallback
    else:
        # Initial Template
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
                .analysis {{ background: #fafafa; border-left: 4px solid #27ae60; padding: 15px; margin-top: 15px; }}
                .analysis p {{ margin: 5px 0; }}
            </style>
        </head>
        <body>
            <h1 style="text-align:center">📚 My Personal Academic Journal</h1>
            </body>
        </html>
        """
        # Inject first content
        final_html = final_html.replace('', '' + new_content)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)

if __name__ == "__main__":
    main()
