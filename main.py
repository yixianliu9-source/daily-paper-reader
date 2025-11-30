import feedparser
import random
import os
import datetime
import pytz
import re

# --- 配置区域 ---
RSS_FEEDS = {
    "JPART (OUP)": "https://academic.oup.com/rss/site_5332/3062.xml",
    "Public Admin Rev (Wiley)": "https://onlinelibrary.wiley.com/feed/15406210/most-recent",
    "Academy of Mgmt Jnl (AOM)": "https://journals.aom.org/action/showFeed?type=etoc&feed=rss&jc=amj",
    "Public Mgmt Rev (TandF)": "https://www.tandfonline.com/feed/rss/rpxm20",
    "Governance (Wiley)": "https://onlinelibrary.wiley.com/feed/14680493/most-recent"
}

def clean_html(raw_html):
    # 去除HTML标签，只保留文字
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

def get_best_summary(entry):
    # 策略1：尝试找 content (通常包含全文或长摘要)
    content = ""
    if hasattr(entry, 'content'):
        # feedparser有时把content解析为列表
        for c in entry.content:
            content += c.value
            
    # 策略2：如果没有content，找summary
    if not content and hasattr(entry, 'summary'):
        content = entry.summary
        
    # 策略3：如果也没有，找 description
    if not content and hasattr(entry, 'description'):
        content = entry.description

    # 清理HTML标签
    text = clean_html(content)
    
    # 策略4：质量检测
    # 如果抓到的内容太短（小于100字），通常是无效的元数据（如"Vol 32, Issue 4..."）
    if len(text) < 100:
        return "🔒 Abstract not in RSS. Please check the link."
    
    # 截取过长的摘要，防止页面太长
    if len(text) > 1500:
        return text[:1500] + "..."
        
    return text

def main():
    print("Starting Daily Reader (Deep Dig Mode)...")
    
    tz = pytz.timezone('Asia/Shanghai')
    today_str = datetime.datetime.now(tz).strftime('%Y-%m-%d')
    
    articles = []
    
    # 1. 抓取文章
    for journal, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            # 这里的 logic 改为：每个期刊只抓最新的 1 篇，但要多试几个期刊
            # 或者每个期刊抓前2篇放入池子
            for entry in feed.entries[:3]: 
                summary_text = get_best_summary(entry)
                
                articles.append({
                    "journal": journal,
                    "title": entry.title,
                    "link": entry.link,
                    "summary": summary_text
                })
        except Exception as e:
            print(f"Error fetching {journal}: {e}")
            continue
            
    # 2. 随机选 2 篇
    if len(articles) < 2:
        selection = articles
    else:
        selection = random.sample(articles, 2)
        
    # 3. 生成 HTML 内容
    new_content = f"""
    <article class="day-entry" id="{today_str}">
        <div class="date-header">{today_str} Daily Picks</div>
    """
    
    for art in selection:
        # 只有当摘要有效时，才显示摘要框，否则提示点击链接
        if "Abstract not in RSS" in art['summary']:
            abstract_display = f"<p style='color:#999; font-style:italic;'>{art['summary']}</p>"
        else:
            abstract_display = f"""
            <div class="abstract-box">
                <h4>📄 Abstract Snippet</h4>
                <div class="abstract-content">
                    {art['summary']}
                </div>
            </div>
            """

        new_content += f"""
        <div class="paper-card">
            <span class="tag">{art['journal']}</span>
            <h3><a href="{art['link']}" target="_blank">{art['title']}</a></h3>
            
            {abstract_display}
            
            <div style="margin-top:15px; text-align:right;">
                <a href="{art['link']}" target="_blank" style="font-size:0.9em; color:#3498db; font-weight:bold;">👉 Read Full Article on Publisher Site</a>
            </div>
        </div>
        """
    new_content += "</article>\n"
    
    # 4. 写入 index.html (包含防重复逻辑)
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            existing_html = f.read()
            
        pattern = f".*?"
        existing_html = re.sub(pattern, "", existing_html, flags=re.DOTALL)
        
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
            <title>My PA/OB Daily Reader</title
