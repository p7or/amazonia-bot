import requests
import json
import time
import re
from datetime import datetime

BOT_TOKEN = "8856681028:AAFhlhK86ykh5kmm6yax_wfBCtgkgO8ycQM"
CHAT_ID = "-1003718314738"
MIN_DISCOUNT = 50
ASSOCIATE_TAG = "sadealsbot-20"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ar-SA,ar;q=0.9,en-US;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

def send_telegram(message, parse_mode="HTML"):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": parse_mode,
        "disable_web_page_preview": False
    }
    try:
        r = requests.post(url, json=data, timeout=15)
        result = r.json()
        if not result.get("ok"):
            print(f"Telegram error: {result}")
        return result
    except Exception as e:
        print(f"Telegram exception: {e}")
        return None

def fetch_deals_goldbox():
    deals = []
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        urls = [
            "https://www.amazon.sa/-/ar/gp/goldbox",
            "https://www.amazon.sa/gp/goldbox",
            "https://www.amazon.sa/-/ar/deals",
        ]
        html = ""
        for url in urls:
            try:
                r = session.get(url, timeout=20)
                if r.status_code == 200 and len(r.text) > 1000:
                    html = r.text
                    print(f"Got HTML from: {url} ({len(html)} chars)")
                    break
            except Exception as e:
                print(f"URL failed {url}: {e}")
                continue

        if not html:
            return deals

        asin_pattern = r'"asin"\s*:\s*"([A-Z0-9]{10})"'
        discount_pattern = r'"discountPercentage"\s*:\s*"(\d+)"'
        title_pattern = r'"title"\s*:\s*"([^"]{10,100})"'
        price_pattern = r'"price"\s*:\s*\{"amount"\s*:\s*"([\d.]+)"'

        asins = re.findall(asin_pattern, html)
        discounts = re.findall(discount_pattern, html)
        titles = re.findall(title_pattern, html)
        prices = re.findall(price_pattern, html)

        print(f"Found: {len(asins)} ASINs, {len(discounts)} discounts, {len(titles)} titles")

        seen = set()
        for i in range(min(len(asins), len(discounts), len(titles))):
            try:
                disc = int(discounts[i])
                asin = asins[i]
                if disc >= MIN_DISCOUNT and asin not in seen:
                    seen.add(asin)
                    price = float(prices[i]) if i < len(prices) else 0
                    deals.append({
                        "title": titles[i][:80],
                        "discount": disc,
                        "price": price,
                        "asin": asin,
                        "url": f"https://www.amazon.sa/dp/{asin}?tag={ASSOCIATE_TAG}"
                    })
            except:
                continue

        if not deals:
            div_pattern = r'<div[^>]*data-asin="([A-Z0-9]{10})"[^>]*>.*?(\d+)%\s*(?:off|خصم)'
            matches = re.findall(div_pattern, html, re.DOTALL)
            for asin, disc in matches[:20]:
                disc = int(disc)
                if disc >= MIN_DISCOUNT and asin not in seen:
                    seen.add(asin)
                    deals.append({
                        "title": f"عرض أمازون - {asin}",
                        "discount": disc,
                        "price": 0,
                        "asin": asin,
                        "url": f"https://www.amazon.sa/dp/{asin}?tag={ASSOCIATE_TAG}"
                    })
    except Exception as e:
        print(f"Scraping error: {e}")
    return deals

def fetch_deals_search():
    deals = []
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        for term in ["عروض", "تخفيضات", "deals"]:
            url = f"https://www.amazon.sa/s?k={term}&rh=p_n_pct-off-with-tax%3A5172720031"
            r = session.get(url, timeout=20)
            if r.status_code != 200:
                continue
            html = r.text
            asin_blocks = re.findall(
                r'data-asin="([A-Z0-9]{10})".*?'
                r'<span[^>]*class="[^"]*a-price-whole[^"]*"[^>]*>([^<]+)</span>.*?'
                r'<span[^>]*class="[^"]*savingsPercentage[^"]*"[^>]*>-(\d+)%</span>',
                html, re.DOTALL
            )
            for asin, price, disc in asin_blocks[:15]:
                disc = int(disc)
                if disc >= MIN_DISCOUNT:
                    deals.append({
                        "title": f"منتج أمازون #{asin}",
                        "discount": disc,
                        "price": float(price.replace(',', '').strip()) if price else 0,
                        "asin": asin,
                        "url": f"https://www.amazon.sa/dp/{asin}?tag={ASSOCIATE_TAG}"
                    })
            if deals:
                break
    except Exception as e:
        print(f"Search scraping error: {e}")
    return deals

def format_deal(deal):
    fire = "🔥" if deal["discount"] >= 70 else "⚡"
    price_text = f"\n💰 <b>{deal['price']:.2f} ر.س</b>" if deal.get("price", 0) > 0 else ""
    return (
        f"{fire} <b>{deal['title']}</b>\n"
        f"🏷️ خصم <b>{deal['discount']}%</b>{price_text}\n"
        f"🛒 <a href='{deal['url']}'>اشتري من أمازون السعودية</a>\n"
    )

def run_bot():
    print("🤖 بوت Amazonia SA يعمل...")
    test = send_telegram(
        "🛍️ <b>بوت Amazonia SA</b> يعمل الآن! 🔥\n\n"
        "سيتم نشر أفضل الصيدات بخصم +50% كل ساعة\n\n"
        "#صيدات #أمازون #السعودية"
    )
    print(f"Telegram test: {test}")

    while True:
        now = datetime.now().strftime('%H:%M:%S')
        print(f"\n[{now}] جاري جلب العروض...")
        deals = fetch_deals_goldbox()
        print(f"Goldbox deals: {len(deals)}")
        if not deals:
            deals = fetch_deals_search()
            print(f"Search deals: {len(deals)}")

        if deals:
            header = (
                f"🛍️ <b>صيدات أمازون السعودية</b>\n"
                f"🕐 {datetime.now().strftime('%I:%M %p')} | خصم +{MIN_DISCOUNT}%\n"
                f"{'─'*25}\n\n"
            )
            chunk = header
            sent = 0
            for deal in deals[:10]:
                line = format_deal(deal) + "\n"
                if len(chunk) + len(line) > 3800:
                    send_telegram(chunk + "\n#صيدات #أمازون #السعودية")
                    time.sleep(2)
                    chunk = line
                    sent += 1
                else:
                    chunk += line
            if chunk.strip():
                send_telegram(chunk + "\n#صيدات #أمازون #السعودية")
                sent += 1
            print(f"✅ تم نشر {len(deals)} صيدة في {sent} رسالة")
        else:
            print("❌ لم يتم العثور على صيدات")
            send_telegram("⏳ لم يتم العثور على صيدات حالياً، سيتم المحاولة مرة أخرى...")
            time.sleep(1800)
            continue

        print("⏰ انتظار ساعة...")
        time.sleep(3600)

if __name__ == "__main__":
    run_bot()
