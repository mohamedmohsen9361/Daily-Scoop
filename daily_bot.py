import os
import time
import requests
import feedparser
from bs4 import BeautifulSoup
from google import genai

# جلب المفاتيح من خوادم GitHub المشفرة
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = "-5460023224"

RSS_SOURCES = {
    "BBC Arabic": "http://feeds.bbci.co.uk/arabic/rss.xml",
    "BBC World News": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "BBC Business": "http://feeds.bbci.co.uk/news/business/rss.xml",
    "BBC Europe": "http://feeds.bbci.co.uk/news/world/europe/rss.xml",
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex"
}

def fetch_all_news():
    print("⚡ [1/3] جاري جلب الأخبار...")
    news_items = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    for source, url in RSS_SOURCES.items():
        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                feed = feedparser.parse(res.content)
                for entry in feed.entries[:3]:
                    title = entry.get('title', '').strip()
                    summary_raw = entry.get('summary', '') or entry.get('description', '')
                    summary = BeautifulSoup(summary_raw, "html.parser").get_text()[:200].strip()
                    news_items.append(f"المصدر: {source}\nالعنوان: {title}\nالملخص: {summary}\n---")
        except Exception as e:
            print(f"⚠️ تعذر جلب {source}: {e}")
            
    if not news_items:
        news_items.append("المصدر: المستجدات الاقتصادية والسياسية.")
    return "\n".join(news_items)

def generate_report(news_payload):
    print("🧠 [2/3] جاري التوليد مع Gemini...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = f"أنت خبير اقتصادي ومحلل سياسي واستراتيجي. مهمتك صياغة تقرير إخباري وتحليلي صباحي دقيق وشامل ومصمم خصيصاً للتليجرام بناءً على الأخبار والنصوص المرفقة أدناه.\n\nتعليمات التنسيق المخصصة للتليجرام (Markdown):\n1. استخدم نجمتين **نص** لجعل الخط عريضاً (Bold).\n2. استخدم الرموز التعبيرية (Emojis) بشكل أنيق لتمييز العناوين والأقسام.\n3. اكتب بأسلوب رصين، محترف، وأكاديمي.\n4. اذكر مصدر كل خبر/معلومة بدقة بين قوسين بجانب الفقرة.\n\nهيكل التقرير المطلوب بالترتيب:\n\n📊 **التقرير الإخباري والتحليلي الصباحي**\n\n1️⃣ **أولاً: موجز الأخبار المحلية والدولية الرئيسية**\n(أخبار الاقتصاد والمالية والمؤسسات المحلية والدولية)\n\n2️⃣ **ثانياً: الشأن الإسباني والأوروبي (السياسة والاقتصاد)**\n(فقرة فرعية خاصة ومفصلة تركز على المستجدات السياسية والاقتصادية في إسبانيا والاتحاد الأوروبي)\n\n3️⃣ **ثالثاً: زاوية تحليلية (Analytic Insight)**\n[تحليل خاص بالذكاء الاصطناعي: ...]\n\n4️⃣ **رابعاً: ترشيحات للاستزادة (Books & Videos)**\n(كتب مرجعية وفيديوهات وثائقية مع توضيح الصلة بالحدث)\n\n5️⃣ **خامساً: أفكار صناعة المحتوى (Content Ideas)**\n• **فيديوهات طويلة (+10 دقائق):**\n• **فيديوهات قصيرة (~دقيقة):**\n• **منشورات كاروسيل:**\n• **أسئلة ونقاشات تفاعلية:**\n\nالنصوص والأخبار المجمعة اليوم:\n{news_payload}"
    
    for attempt in range(1, 11):
        try:
            response = client.models.generate_content(
                model='gemini-3.8-flash',
                contents=prompt,
            )
            return response.text
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                raise e
            time.sleep(30)
    raise Exception("تعذر الاتصال بـ Gemini.")

def send_to_telegram(report_text):
    print("📱 [3/3] جاري الإرسال للتليجرام...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    MAX_LEN = 3800
    chunks = [report_text[i:i+MAX_LEN] for i in range(0, len(report_text), MAX_LEN)]
    
    for idx, chunk in enumerate(chunks, 1):
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": chunk, "parse_mode": "Markdown"}
        success = False
        for _ in range(5):
            try:
                res = requests.post(url, json=payload, timeout=20)
                if res.status_code == 200:
                    success = True
                    break
                if "parse_mode" in payload:
                    payload.pop("parse_mode")
            except:
                time.sleep(5)
        if not success:
            print(f"❌ فشل إرسال الجزء {idx}")

def run_daily_job():
    print(f"🚀 بدء التنفيذ: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    news_data = fetch_all_news()
    report = generate_report(news_data)
    send_to_telegram(report)
    print("🎉 تم الإرسال بنجاح!")

if __name__ == "__main__":
    run_daily_job()
