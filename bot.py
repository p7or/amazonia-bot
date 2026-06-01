import requests
import time
from datetime import datetime

BOT_TOKEN = "8856681028:AAFhlhK86ykh5kmm6yax_wfBCtgkgO8ycQM"
CHAT_ID = "-1003718314738"
MIN_DISCOUNT = 50
ASSOCIATE_TAG = "sadealsbot-20"
RAPIDAPI_KEY = "83f7accaedmshd6aaf3e480061f7p19cb11jsne3c6c8dbfef0"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }, timeout=15)
        return r.json()
    except Exception as e:
        print(f"Telegram error: {e}")
        return None

def fetch_deals():
    url = "https://real-time-amazon-data.p.rapidapi.com/deals-v2"
    params = {
        "country": "SA",
        "min_product_star_rating": "ALL",
        "price_range": "ALL",
        "discount_range": "ALL"
    }
    headers = {
        "x-rapidapi-host": "real-time-amazon-data.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    try:
        r = requests.get(url, headers=headers, params=params, timeout=20)
        data = r.json()
        deals = data.get("data", {}).get("deals", [])
        print(f"Total deals from API: {len(deals)}")
        filtered = [d for d in deals if d.get("savings_percentage", 0) >= MIN_DISCOUNT]
        print(f"Deals with +{MIN_DISCOUNT}% discount: {len(filtered)}")
        return filtered
    except Exception as e:
        print(f"API error: {e}")
        return []

def format_deal(deal):
    fire = "🔥" if deal["savings_percentage"] >= 70 else "⚡"
    title = deal.get("deal_title", "منتج أمازون")[:80]
    discount = deal.get("savings_percentage", 0)
    price = deal.get("deal_price", {}).get("amount", 0)
    original = deal.get("list_price", {}).get("amount", 0)
    currency = deal.get("deal_price", {}).get("currency", "SAR")
    asin = deal.get("product_asin", "")
    url = f"https://www.amazon.sa/dp/{asin}?tag={ASSOCIATE_TAG}" if asin else deal.get("deal_url", "")

    price_text = ""
    if price and original:
        price_text = f"\n💰 <b>{price} {currency}</b> بدل {original} {currency}"

    return (
        f"{fire} <b>{title}</b>\n"
        f"🏷️ خصم <b>{discount}%</b>{price_text}\n"
        f"🛒 <a href='{url}'>اشتري من أمازون</a>\n"
    )

def run_bot():
    print("🤖 بوت Amazonia SA يعمل...")
    send_telegram(
        "🛍️ <b>بوت Amazonia SA</b> يعمل الآن! 🔥\n\n"
        "سيتم نشر أفضل الصيدات بخصم +50% كل ساعة\n\n"
        "#صيدات #أمازون #السعودية"
    )

    while True:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] جاري جلب العروض...")
        deals = fetch_deals()

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
            print(f"✅ تم نشر {len(deals)} صيدة")
        else:
            print("❌ لا توجد صيدات بخصم +50% الآن")
            send_telegram("⏳ لا توجد صيدات بخصم +50% حالياً، سيتم المحاولة بعد ساعة...")

        print("⏰ انتظار ساعة...")
        time.sleep(3600)

if __name__ == "__main__":
    run_bot()
