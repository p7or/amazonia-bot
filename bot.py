import requests
import time
import json
from datetime import datetime

BOT_TOKEN = "8856681028:AAFhlhK86ykh5kmm6yax_wfBCtgkgO8ycQM"
CHAT_ID = "-1003718314738"
MIN_DISCOUNT = 20
ASSOCIATE_TAG = "sadealsbot-20"
RAPIDAPI_KEY = "83f7accaedmshd6aaf3e480061f7p19cb11jsne3c6c8dbfef0"

UPSTASH_URL = "https://apparent-mustang-140877.upstash.io"
UPSTASH_TOKEN = "gQAAAAAAAiZNAAIgcDFmNzY2MDFiMWEwYTE0NWI1ODc3NmVkZjQyZjMwMzczNQ"

def redis_get(key):
    try:
        r = requests.get(
            f"{UPSTASH_URL}/get/{key}",
            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
            timeout=10
        )
        result = r.json().get("result")
        return json.loads(result) if result else []
    except:
        return []

def redis_set(key, value):
    try:
        requests.post(
            f"{UPSTASH_URL}/set/{key}",
            headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
            json={"value": json.dumps(value)},
            timeout=10
        )
    except Exception as e:
        print(f"Redis error: {e}")

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
    all_deals = []
    headers = {
        "x-rapidapi-host": "real-time-amazon-data.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    for page in range(1, 6):
        params = {
            "country": "SA",
            "min_product_star_rating": "ALL",
            "price_range": "ALL",
            "discount_range": "ALL",
            "num_pages": page
        }
        try:
            r = requests.get(
                "https://real-time-amazon-data.p.rapidapi.com/deals-v2",
                headers=headers,
                params=params,
                timeout=20
            )
            data = r.json()
            deals = data.get("data", {}).get("deals", [])
            if not deals:
                break
            all_deals.extend(deals)
            time.sleep(1)
        except Exception as e:
            print(f"API error page {page}: {e}")
            break

    filtered = [d for d in all_deals if (d.get("savings_percentage") or 0) >= MIN_DISCOUNT]
    print(f"Total: {len(all_deals)} | +{MIN_DISCOUNT}%: {len(filtered)}")
    return filtered

def post_deal(deal):
    discount = deal.get("savings_percentage") or 0
    title = deal.get("deal_title", "منتج أمازون")[:80]
    price = deal.get("deal_price", {}).get("amount", 0)
    original = deal.get("list_price", {}).get("amount", 0)
    currency = deal.get("deal_price", {}).get("currency", "SAR")
    asin = deal.get("product_asin", "")
    photo = deal.get("deal_photo", "")
    url = f"https://www.amazon.sa/dp/{asin}?tag={ASSOCIATE_TAG}" if asin else deal.get("deal_url", "")

    if discount >= 45:
        caption = (
            f"🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴\n"
            f"🚨 <b>تنبيه صيدة نارية!</b> 🚨\n"
            f"🔴🔴🔴🔴🔴🔴🔴🔴🔴🔴\n\n"
            f"🛍️ <b>{title}</b>\n\n"
            f"💥 خصم <b>{discount}%</b>\n"
            f"💰 <b>{price} {currency}</b> بدل <s>{original} {currency}</s>\n\n"
            f"⏰ العرض محدود — لا تفوّته!\n\n"
            f"🛒 <a href='{url}'>اشتري الآن من أمازون</a>\n\n"
            f"#صيدة_نارية #صيدات #أمازون #السعودية"
        )
    else:
        caption = (
            f"⚡ <b>{title}</b>\n\n"
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
        "سيتم نشر العروض الجديدة كل 5 دقائق\n\n"
        "#صيدات #أمازون #السعودية"
    )

    while True:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] جاري جلب العروض...")
        
        seen = set(redis_get("seen_deals"))
        deals = fetch_deals()
        new_deals = [d for d in deals if d.get("deal_id") not in seen]
        print(f"عروض جديدة: {len(new_deals)}")

        if new_deals:
            for deal in new_deals:
                post_deal(deal)
                seen.add(deal.get("deal_id"))
                time.sleep(3)
            redis_set("seen_deals", list(seen))
            print(f"✅ تم نشر {len(new_deals)} صيدة جديدة")
        else:
            print("لا توجد عروض جديدة")

        print("⏰ انتظار ساعة...")
        time.sleep(3600)

if __name__ == "__main__":
    run_bot()
