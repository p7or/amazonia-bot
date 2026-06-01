import requests
import json
import time
import re
from datetime import datetime

BOT_TOKEN = "8850824192:AAFHWbn3CceUWWdtxaJvIF2mNtm_G4JXraw"
CHAT_ID = "-1003718314738"
MIN_DISCOUNT = 50

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ar-SA,ar;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
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
        r = requests.post(url, json=data, timeout=10)
        return r.json()
    except Exception as e:
        print(f"Telegram error: {e}")
        return None

def fetch_deals():
    deals = []
    try:
        url = "https://www.amazon.sa/gp/goldbox"
        r = requests.get(url, headers=HEADERS, timeout=15)
        html = r.text

        # Extract deal blocks
        pattern = r'"title"\s*:\s*"([^"]+)".*?"discountPercentage"\s*:\s*"(-?\d+)".*?"price"\s*:\s*\{"amount"\s*:\s*"([\d.]+)".*?"priceStrikethrough"\s*:\s*\{"amount"\s*:\s*"([\d.]+)".*?"dealId"\s*:\s*"([^"]+)"'
        matches = re.findall(pattern, html, re.DOTALL)

        for m in matches[:20]:
            title, discount, price, original, deal_id = m
            discount = abs(int(discount))
            if discount >= MIN_DISCOUNT:
                deals.append({
                    "title": title[:80],
                    "discount": discount,
                    "price": float(price),
                    "original": float(original),
                    "url": f"https://www.amazon.sa/dp/{deal_id}?tag=sadealsbot-20"
                })

    except Exception as e:
        print(f"Scraping error: {e}")

    # Fallback: try deals page differently
    if not deals:
        try:
            url = "https://www.amazon.sa/deals"
            r = requests.get(url, headers=HEADERS, timeout=15)
            html = r.text

            # Try to find percentage discounts
            titles = re.findall(r'class="[^"]*deal-title[^"]*"[^>]*>([^<]+)<', html)
            discounts = re.findall(r'(\d+)%\s*off', html)
            links = re.findall(r'href="(/dp/[A-Z0-9]+[^"]*)"', html)

            for i, disc in enumerate(discounts[:15]):
                if int(disc) >= MIN_DISCOUNT:
                    title = titles[i] if i < len(titles) else f"عرض أمازون #{i+1}"
                    link = f"https://www.amazon.sa{links[i]}?tag=sadealsbot-20" if i < len(links) else "https://www.amazon.sa/deals"
                    deals.append({
                        "title": title.strip()[:80],
                        "discount": int(disc),
                        "price": 0,
                        "original": 0,
                        "url": link
                    })
        except Exception as e:
            print(f"Fallback error: {e}")

    return deals

def format_deal(deal, index):
    fire = "🔥" if deal["discount"] >= 70 else "⚡"
    price_text = ""
    if deal["price"] > 0 and deal["original"] > 0:
        price_text = f"\n💰 <b>{deal['price']:.2f} ر.س</b> <s>{deal['original']:.2f} ر.س</s>"

    return (
        f"{fire} <b>{deal['title']}</b>\n"
        f"🏷️ خصم <b>{deal['discount']}%</b>{price_text}\n"
        f"🛒 <a href='{deal['url']}'>اشتري من أمازون</a>\n"
    )

def run_bot():
    print("🤖 بوت Amazonia SA يعمل...")
    send_telegram(
        "🛍️ <b>بوت Amazonia SA</b> يعمل الآن!\n"
        "سيتم نشر أفضل الصيدات كل ساعة 🔥\n"
        f"فلتر: خصم +{MIN_DISCOUNT}%"
    )

    while True:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] جاري جلب العروض...")
        deals = fetch_deals()

        if deals:
            header = f"🛍️ <b>صيدات أمازون السعودية</b> | {datetime.now().strftime('%I:%M %p')}\n خصم +{MIN_DISCOUNT}% |\n\n"
            messages = [header]
            for i, deal in enumerate(deals[:10]):
                messages.append(format_deal(deal, i+1))

            full_msg = "\n".join(messages) + "\n\n#صيدات #أمازون #السعودية"

            # Split if too long
            if len(full_msg) > 4000:
                chunks = []
                chunk = header
                for i, deal in enumerate(deals[:10]):
                    line = format_deal(deal, i+1) + "\n"
                    if len(chunk) + len(line) > 3800:
                        chunks.append(chunk)
                        chunk = line
                    else:
                        chunk += line
                chunks.append(chunk + "\n#صيدات #أمازون #السعودية")
                for c in chunks:
                    send_telegram(c)
                    time.sleep(1)
            else:
                send_telegram(full_msg)

            print(f"✅ تم نشر {len(deals)} صيدة")
        else:
            print("❌ لم يتم العثور على صيدات")
            send_telegram("⏳ جاري البحث عن الصيدات... سيتم النشر قريباً")

        print("⏰ انتظار ساعة...")
        time.sleep(3600)

if __name__ == "__main__":
    run_bot()
