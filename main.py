# ... (前面的代码保持不变，只替换 def main(): 及其后面的部分) ...

# 请只替换 main() 函数部分，或者干脆把整个文件替换成下面的完整版
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
    "Public Mgmt Rev": "https://www.tandfonline.com/feed/rss/rpxm20",
    "Governance": "https://onlinelibrary.wiley.com/feed/14680493/most-recent",
    "IPMJ": "https://www.tandfonline.com/journals/upmj20",
    "PPMR": "https://www.tandfonline.com/journals/mpmr20",
    "PA": "https://onlinelibrary.wiley.com/journal/14679299",
    "Regul&Govern": "https://onlinelibrary.wiley.com/journal/17485991"
}

def clean_text(html_text):
    if not html_text: return ""
    text = re.sub(r'<[^>]+>', '', str(html_text))
    return text.strip()

def safe_get_summary(entry):
    try:
        content = ""
        if 'content' in entry:
            c_list = entry.get('content', [])
            for c in c_list:
                if isinstance(c, dict) and 'value' in c:
                    content += c['value']
                elif hasattr(c, 'value'):
                    content += c.value
        if not content and 'summary' in entry:
            content = entry['summary']
        if not content and 'description' in entry:
            content = entry['description']
        clean_content = clean_text(content)
        if len(clean_content) < 20:
            return "Abstract not available in RSS feed."
        if len(clean_content) > 1000:
            return clean_content[:1000] + "..."
        return clean_content
    except:
        return "Summary parsing error."

def main():
    print("Starting Daily Reader (Archive Safe Mode)...")
    
    try:
        try:
            tz = pytz.timezone('Asia/Shanghai')
            today_str = datetime.datetime.now(tz).strftime('%Y-%m-%d')
        except:
            today_str = str(datetime.date.today())

        all_articles = []
        for journal_name, url in RSS_FEEDS.items():
            try:
                feed = feedparser.parse(url)
                if not feed.entries: continue
                for entry in feed.entries[:2]:
                    all_articles.append({
                        "journal": journal_name,
                        "title": entry.get('title', 'No Title'),
                        "link": entry.get('link', '#'),
                        "summary": safe_get_summary(entry)
                    })
            except:
                continue

        if not all_articles:
            print("No articles found.")
            return

        selected = random.sample(all_articles, min(2, len(all_articles)))

        # 生成今日内容块
        new_content = f"""
        <article class="day-entry" style="margin-bottom: 40px; border-bottom: 3px dashed #ddd; padding-bottom: 20px;">
            <div class="date-header" style="color:#d35400; font-size:1.4em; margin-bottom:15px; font-weight:bold;">📅 {today_str} Daily Picks</div>
        """
        
        for art in selected:
            new_content += f"""
            <div class="paper-card" style="background:white; padding:20px; border-radius:10px; box-shadow:0 2px 4px rgba(0,0,0,0.1); margin-bottom:15px;">
                <span class="tag" style="background:#e1ecf4; color:#39739d; padding:3px 8px; border-radius:4px; font-size:0.8em; font-weight:bold;">{art['journal']}</span>
                <h3 style="margin:10px 0;"><a href="{art['link']}" target="_blank" style="color:#2c3e50; text-decoration:none;">{art['title']}</a></h3>
                <p style="color:#666; font-size:0.95em; line-height:1.6;">{art['summary']}</p>
                <div style="text-align:right;"><a href="{art['link']}" target="_blank" style="color:#3498db; font-size:0.9em;">Read Source 👉</a></div>
            </div>
            """
        new_content += "</article>\n"

        # --- 核心逻辑：确保历史记录不丢失 ---
        if os.path.exists("index.html"):
            with open("index.html", "r", encoding="utf-8") as f:
                content = f.read()
            
            # 1. 先把今天的（如果已经存在）删掉，防止重复
            content = re.sub(f".*?", "", content, flags=re.DOTALL)
            
            # 2. 检查是否有锚点
            if "" in content:
                # 正常情况：插入到锚点后面
                content = content.replace("", "\n" + new_content)
            else:
                # 异常情况：锚点丢了，强行找 body 插入，并补上锚点
                print("Warning: Anchor missing. Restoring...")
                if "<body>" in content:
                    content = content.replace("<body>", "<body>\n<h1 style='text-align:center'>📚 My Personal Academic Journal</h1>\n\n" + new_content)
                else:
                    # 极度异常：连 body 都没有，直接重写
                    content = "\n" + new_content
        else:
            # 文件不存在（第一天）
            content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Daily Reader</title>
<style>body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;max-width:800px;margin:20px auto;padding:20px;background:#f6f8fa;}}</style>
</head>
<body>
<h1 style="text-align:center">📚 My Personal Academic Journal</h1>
{new_content}
</body></html>"""

        with open("index.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("Done.")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(0)

if __name__ == "__main__":
    main()
