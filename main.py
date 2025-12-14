import time
import random
import os
import google.generativeai as genai
from playwright.sync_api import sync_playwright

# --- KONFIGURASI ---
TARGET_USERNAME = "@ptcrystalbirumeuligo" # <--- GANTI DENGAN USERNAME PROFIL (Pakai @)
GEMINI_API_KEY = "AIzaSyACe8O6W7M90Yf8S28xd4EpOdD5tzNvFwU"
KEYWORDS = ["sukses"]
DELAY_MINUTES = 5 
CHECK_LATEST_COUNT = 3 

# --- SETUP ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')
HISTORY_FILE = "replied_comments.txt"

def load_history():
    if not os.path.exists(HISTORY_FILE): return set()
    with open(HISTORY_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_history(comment_text):
    with open(HISTORY_FILE, "a") as f:
        f.write(f"{comment_text}\n")
        
def get_ai_reply(user_comment):
    try:
        # Prompt singkat agar tidak terdeteksi bot panjang
        prompt = f"Jawab komentar TikTok ini dengan singkat, gaul, dan ramah (max 1 kalimat). Arahkan ke Link Bio atau DM jika nanya harga. Komentar user: '{user_comment}'"
        response = model.generate_content(prompt)
        return response.text.strip().replace('"', '')
    except:
        return "Cek link di bio ya kak! 🔥"

def run_bot():
    replied_set = load_history()

    with sync_playwright() as p:
        # headless=True jika ingin berjalan tanpa layar (background)
        # headless=False jika ingin melihat prosesnya
        browser = p.chromium.launch(headless=False) 
        context = browser.new_context(storage_state="auth.json")
        page = context.new_page()

        while True:
            print(f"\n🌍 Membuka Profil: {TARGET_USERNAME}...")
            try:
                page.goto(f"https://www.tiktok.com/{TARGET_USERNAME}")
                time.sleep(3)
                
                # --- LANGKAH 1: AMBIL DAFTAR VIDEO TERBARU ---
                # Cari elemen link video di profil
                # Selector ini mencari tag <a> yang punya href ke video
                video_links = page.locator('a[href*="/video/"]').all()
                
                # Ambil URL unik (karena kadang ada duplikat elemen)
                found_urls = []
                for link in video_links:
                    url = link.get_attribute('href')
                    if url and "/video/" in url and url not in found_urls:
                        found_urls.append(url)
                    if len(found_urls) >= CHECK_LATEST_COUNT:
                        break # Cukup ambil X video teratas
                
                print(f"📹 Menemukan {len(found_urls)} video terbaru untuk discan.")

                # --- LANGKAH 2: LOOPING KE SETIAP VIDEO ---
                for video_url in found_urls:
                    print(f"\n   👉 Memeriksa Video: {video_url}")
                    page.goto(video_url)
                    time.sleep(3)
                    
                    # Scroll dikit buat load komentar
                    page.mouse.wheel(0, 600)
                    time.sleep(2)

                    # --- SCAN KOMENTAR (LOGIKA SAMA SEPERTI SEBELUMNYA) ---
                    comments = page.locator('div[class*="DivCommentItemContainer"]').all()
                    
                    if not comments:
                        print("      (Sepi / Belum ada komentar baru)")

                    for comment in comments:
                        try:
                            # Ambil Text
                            text_el = comment.locator('span[data-e2e="comment-level-1"]').first
                            if not text_el.count(): continue
                            
                            text = text_el.inner_text().strip()
                            text_lower = text.lower()

                            # Cek Keyword & History
                            keyword_match = any(k in text_lower for k in KEYWORDS)
                            
                            if keyword_match and text not in replied_set:
                                print(f"      ✅ TARGET DITEMUKAN: {text}")
                                
                                # Jeda sebelum membalas (Penting!)
                                print(f"      ⏳ Menunggu antrian 10 detik...") 
                                time.sleep(10) # Testing mode. Ubah jadi DELAY_MINUTES*60 nanti.

                                # Generate AI
                                reply_text = get_ai_reply(text)
                                print(f"      🤖 AI: {reply_text}")

                                # Klik Reply
                                reply_btn = comment.locator('span:text("Reply"), span:text("Balas")').first
                                if reply_btn.count() > 0:
                                    reply_btn.click()
                                    time.sleep(1.5)

                                    # Ketik & Enter
                                    input_box = page.locator('div[contenteditable="true"]').first
                                    if input_box.count() > 0:
                                        input_box.fill(reply_text)
                                        time.sleep(1)
                                        input_box.press("Enter")
                                        
                                        print("      🚀 Terkirim!")
                                        save_history(text)
                                        replied_set.add(text)
                                        time.sleep(3) # Jeda antar komentar
                                    else:
                                        print("      ❌ Gagal mengetik.")
                        except Exception as e:
                            continue # Lanjut ke komentar berikutnya jika error
                    
                    # Jeda antar video agar tidak terlalu cepat
                    time.sleep(5)

            except Exception as e:
                print(f"❌ Error Utama: {e}")
            
            print(f"\n💤 Selesai satu putaran profil. Tidur {DELAY_MINUTES} menit...")
            # Ini jeda antar putaran pengecekan profil
            time.sleep(DELAY_MINUTES * 60) 

if __name__ == "__main__":
    run_bot()


# --- KODE BARU (BENAR UNTUK RAILWAY) ---
browser = p.chromium.launch(
    headless=True,  # <--- Wajib True (Jalan tanpa layar)
    args=[
        "--no-sandbox", 
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage"
    ]
)
