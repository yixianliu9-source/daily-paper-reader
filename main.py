import feedparser
import random
import os
import datetime
import pytz
import re
import sys

# --- 配置区域 ---
RSS_FEEDS = {
    "JPART (OUP)": "https://academic.oup.com/rss/site_5332/3062.xml",
    "Public Admin Rev (Wiley)": "https://onlinelibrary.wiley.com/feed/15406210/most-recent",
    "Academy of Mgmt Jnl (AOM)": "https://journals.aom.org/action/showFeed?type=etoc&feed=rss&jc=amj",
    "Public Mgmt Rev (TandF)": "https://www.tandfonline.com/feed/rss/rpxm20",
    "Governance (Wiley)": "https://onlinelibrary.wiley.com/feed/14680493/most-recent"
}

def clean_html(raw_html):
    if not raw_html: return ""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

def get_best_summary(entry):
    try:
        content = ""
        # 1. 尝试找 content 列表 (修复了之前的 bug)
        if hasattr(entry, 'content'):
            # feedparser 的 content 通常是一个列表
            for c in entry.content:
                if hasattr(c, 'value'):
                    content += c.value
                elif isinstance(c, dict) and 'value' in c:
                    content += c['value']
        
        # 2. 如果没找到，找 summary_detail
        if not content and hasattr(entry, 'summary_detail'):
            if hasattr(entry.summary_detail, 'value'):
                content = entry.summary_detail.value
            elif isinstance(entry.summary_detail, dict) and 'value' in entry.summary_detail:
                content = entry.summary_detail['value']

        # 3. 如果还没找到，找最基础的 summary
        if not content and hasattr(entry, 'summary'):
            content = entry.summary

        # 清理 HTML
        text = clean_html(content)
        
        # 4. 质量检测：如果内容太短，说明摘要被隐藏了
        if len(text) < 50: 
            return "🔒 Abstract hidden by publisher. Please read full article."
        
        # 截断过长内容
        if len(text) > 1200:
            return text[:1200] + "..."
            
        return text
    except Exception as e:
        print(f"Error parsing summary: {e}")
        return "Summary unavailable."

def main():
    print("Starting Daily Reader (Robust Mode)...")
    
    try:
        tz = pytz.timezone('Asia/Shanghai')
        today_str = datetime.datetime.now(tz).strftime('%Y-%m-%d')
        
        articles = []
        
        # 1. 抓取文章
        for journal, url in RSS_FEEDS.items():
            print(f"Fetching {journal}...")
            try:
                feed = feedparser.parse(url)
                if not feed.entries:
                    print(f"  - No entries found in {journal}")
                    continue
                    
                for entry in feed.entries[:3]: 
                    summary_text = get_best_summary(entry)
                    articles.append({
                        "journal": journal,
                        "title": entry.title,
