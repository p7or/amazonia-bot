import requests
import time
from datetime import datetime

BOT_TOKEN = "8856681028:AAFhlhK86ykh5kmm6yax_wfBCtgkgO8ycQM"
CHAT_ID = "-1003718314738"
MIN_DISCOUNT = 20
ASSOCIATE_TAG = "sadealsbot-20"
RAPIDAPI_KEY = "83f7accaedmshd6aaf3e480061f7p19cb11jsne3c6c8dbfef0"

def send_photo(photo_url, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        r = requests.post(url, json={
            "chat_id": CHAT_ID,
            "photo": photo_url,
            "caption": caption,
            "parse_mode": "HTML"
        }, timeout=15)
        result = r.json()
        if not result.get("ok"):
            print(f"Photo error: {result}")
            send_message(caption)
        return result
    except Exception as e:
        print(f"Photo exception: {e}")
        return None

def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }, timeout=15)
        return r.json()
    except Exception as e:
        print(f"Message exception: {e}")
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
        print(f"Total deals: {len(deals)}")
        filtered = [d for d in deals if (d.get("savings_percentage") or 0) >= MIN_DISCOUNT]
        print(f"Deals +{MIN_DISCOUNT}%: {len(filtered)}")
        return filtered
    except Exception as e:
        print(f"API error: {e}")
        return []

def post_deal(deal):
    fire = "🔥" if (deal.get("savings_percentage") or 0) >= 70 else "⚡"
    title = deal.get("deal_title", "منتج أمازون")[:80]
    discount = deal.get("savings_percentage") or 0
    price = deal.get("deal_price", {}).get("amount", 0)
    original = deal.get("list_price", {}).get("amount", 0)
    currency = deal.get("deal_price", {}).get("currency", "SAR")
    asin = deal.get("product_asin", "")
    photo = deal.get("deal_photo", "")
    url = f"https://www.amazon.sa/dp/{asin}?tag={ASSOCIATE_TAG}" if asin else deal.get("deal_url", "")

    caption = (
        f"{fire} <b>{title}</b>\n\n"
        f"🏷️ خصم <b>{discount}%</b>\n"
        f"💰 <b>{price} {currency}</b> بدل <s>{original} {currency}</s>\n\n"
        f"🛒 <a href='{url}'>اشتري من أمازون السعودية</a>\n\n"
        f"#صيدات #أمازون #السعودية"
    )

    if photo:
        send_photo(photo, caption)
    else:
        send_message(caption)

def run_bot():
    print("🤖 بوت Amazonia SA يعمل...")
    send_message(
        "🛍️ <b>بوت Amazonia SA</b> يعمل الآن! 🔥\n\n"
        "سيتم نشر أفضل الصيدات بخصم كل ساعة\n\n"
        "#صيدات #أمازون #السعودية"
    )

    while True:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] جاري جلب العروض...")
        deals = fetch_deals()

        if deals:
            for i, deal in enumerate(deals[:10]):
                post_deal(deal)
                time.sleep(3)
            print(f"✅ تم نشر {min(len(deals), 10)} صيدة")
        else:
            print("❌ لا توجد صيدات الآن")
            send_message("⏳ لا توجد صيدات حالياً، سيتم المحاولة بعد ساعة...")

        print("⏰ انتظار ساعة...")
        time.sleep(3600)

if __name__ == "__main__":
    run_bot()
