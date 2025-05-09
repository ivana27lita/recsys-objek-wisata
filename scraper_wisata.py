import os
import time
import random
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm

# Gunakan daftar user agents statis sebagai pengganti fake-useragent
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
]

# File untuk menyimpan progress
PROGRESS_FILE = "progress.txt"
INPUT_FILE = "2/data/processed/tourism_processed.csv"  
OUTPUT_FILE = "2/data/processed/tourism_with_images.csv"  

# Tambahkan flag untuk melewati metode pencarian yang lambat jika perlu
USE_SELENIUM = True
USE_DUCKDUCKGO = False  # Set False untuk mempercepat proses
TIMEOUT = 15  # Timeout untuk operasi Selenium/Requests dalam detik
MAX_RETRIES = 2  # Jumlah percobaan ulang per metode

def get_last_processed_index():
    """Mendapatkan indeks terakhir yang diproses jika ada"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return int(f.read().strip())
    return 0

def save_progress(index):
    """Menyimpan progress ke file"""
    with open(PROGRESS_FILE, "w") as f:
        f.write(str(index))

def setup_driver():
    """Setup webdriver Chrome dengan opsi headless yang lebih kuat"""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Menggunakan headless baru
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--log-level=3")  # Hanya tampilkan fatal errors
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Set timeout secara global
    driver.set_page_load_timeout(TIMEOUT)
    driver.set_script_timeout(TIMEOUT)
    
    return driver

def get_images_direct_from_unsplash(query, num_images=3):
    """Coba ambil gambar langsung dari Unsplash - sumber alternatif yang bagus"""
    headers = {"User-Agent": random.choice(user_agents)}
    search_url = f"https://unsplash.com/s/photos/{query.replace(' ', '-')}"
    
    try:
        response = requests.get(search_url, headers=headers, timeout=TIMEOUT)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        image_urls = []
        img_tags = soup.select("figure img")
        
        for img in img_tags:
            if len(image_urls) >= num_images:
                break
            
            img_url = img.get('src')
            if img_url and img_url.startswith('https://') and "unsplash" in img_url:
                # Unsplash URLs sering memiliki parameter query, kita bisa mempertahankannya
                image_urls.append(img_url)
        
        print(f"Ditemukan {len(image_urls)} gambar dari Unsplash")
        return image_urls[:num_images]
    
    except Exception as e:
        print(f"Error dengan Unsplash: {e}")
        return []

def get_images_from_bing(query, num_images=3):
    """Mencari gambar dari Bing Images sebagai alternatif Google"""
    headers = {"User-Agent": random.choice(user_agents)}
    search_query = f"{query} tempat wisata"
    search_url = f"https://www.bing.com/images/search?q={search_query.replace(' ', '+')}"
    
    try:
        response = requests.get(search_url, headers=headers, timeout=TIMEOUT)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        image_urls = []
        # Bing menyimpan URL gambar dalam atribut data-src atau src
        img_tags = soup.select(".mimg")
        
        for img in img_tags:
            if len(image_urls) >= num_images:
                break
            
            img_url = img.get('src') or img.get('data-src')
            if img_url and img_url.startswith('http') and not img_url.startswith('data:'):
                image_urls.append(img_url)
        
        print(f"Ditemukan {len(image_urls)} gambar dari Bing")
        return image_urls[:num_images]
    
    except Exception as e:
        print(f"Error dengan Bing: {e}")
        return []

def get_images_from_google(query, num_images=3):
    """Scraping gambar dari Google Images menggunakan Selenium dengan perbaikan"""
    if not USE_SELENIUM:
        print("Selenium dilewati karena flag USE_SELENIUM=False")
        return []
        
    driver = None
    retry_count = 0
    
    while retry_count < MAX_RETRIES:
        try:
            driver = setup_driver()
            
            # Format query pencarian
            search_query = f"{query} tempat wisata indonesia"
            search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}&tbm=isch"
            
            # Buka halaman pencarian
            driver.get(search_url)
            
            # Gunakan pendekatan yang lebih sederhana untuk menangkap gambar
            # Fokus pada mendapatkan URL gambar yang valid daripada mencoba klik
            WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "img"))
            )
            
            # Scroll untuk memuat lebih banyak gambar
            driver.execute_script("window.scrollBy(0, 500)")
            time.sleep(1)
            
            # Ambil semua URL gambar yang terlihat
            image_urls = []
            image_elements = driver.find_elements(By.TAG_NAME, "img")
            
            for img in image_elements:
                if len(image_urls) >= num_images:
                    break
                    
                try:
                    img_url = img.get_attribute('src')
                    # Filter hanya URL yang valid (bukan base64 atau icon)
                    if (img_url and img_url.startswith('http') and 
                        not img_url.startswith('data:') and 
                        not "favicon" in img_url.lower() and
                        not "logo" in img_url.lower()):
                        # Ambil URL resolusi tinggi jika tersedia
                        high_res_url = img.get_attribute('data-src') or img_url
                        image_urls.append(high_res_url)
                except Exception:
                    continue
            
            print(f"Ditemukan {len(image_urls)} gambar dengan Selenium")
            return image_urls[:num_images]
            
        except Exception as e:
            print(f"Error dengan Selenium (percobaan {retry_count+1}/{MAX_RETRIES}): {e}")
            retry_count += 1
            
        finally:
            if driver:
                driver.quit()
    
    return []

def get_images_with_requests(query, num_images=3):
    """Backup method menggunakan requests dan BeautifulSoup - sederhana dan cepat"""
    headers = {"User-Agent": random.choice(user_agents)}
    search_query = f"{query} tempat wisata indonesia"
    search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}&tbm=isch"
    
    try:
        response = requests.get(search_url, headers=headers, timeout=TIMEOUT)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        image_urls = []
        img_tags = soup.find_all('img')
        
        for img in img_tags[1:]:  # Skip logo Google
            if len(image_urls) >= num_images:
                break
            
            img_url = img.get('src')
            if (img_url and img_url.startswith('http') and 
                not img_url.startswith('data:') and
                not "favicon" in img_url.lower()):
                image_urls.append(img_url)
        
        print(f"Ditemukan {len(image_urls)} gambar dengan requests")
        return image_urls[:num_images]
    
    except Exception as e:
        print(f"Error dengan requests method: {e}")
        return []

def search_images_duckduckgo(query, num_images=3):
    """Alternatif pencarian menggunakan DuckDuckGo"""
    if not USE_DUCKDUCKGO:
        print("DuckDuckGo dilewati karena flag USE_DUCKDUCKGO=False")
        return []
        
    headers = {"User-Agent": random.choice(user_agents)}
    search_query = f"{query} tempat wisata"
    search_url = f"https://duckduckgo.com/?q={search_query.replace(' ', '+')}&iax=images&ia=images"
    
    try:
        # Untuk DuckDuckGo, kita perlu Selenium karena kontennya dinamis
        driver = setup_driver()
        driver.get(search_url)
        
        # Tunggu hingga gambar muncul
        WebDriverWait(driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "img.tile--img__img"))
        )
        
        # Ambil URL gambar
        image_elements = driver.find_elements(By.CSS_SELECTOR, "img.tile--img__img")
        image_urls = []
        
        for img in image_elements[:num_images]:
            img_url = img.get_attribute('src')
            if img_url and img_url.startswith('http'):
                image_urls.append(img_url)
        
        driver.quit()
        print(f"Ditemukan {len(image_urls)} gambar dengan DuckDuckGo")
        return image_urls[:num_images]
    
    except Exception as e:
        print(f"Error dengan DuckDuckGo: {e}")
        if 'driver' in locals():
            driver.quit()
        return []

def main():
    # Pastikan direktori output ada
    output_dir = os.path.dirname(OUTPUT_FILE)
    if not os.path.exists(output_dir):
        print(f"Membuat direktori {output_dir}...")
        os.makedirs(output_dir, exist_ok=True)
    
    # Baca file CSV yang berisi daftar objek wisata
    try:
        df = pd.read_csv(INPUT_FILE)
        print(f"Berhasil membaca file {INPUT_FILE} dengan {len(df)} objek wisata.")
    except FileNotFoundError:
        print(f"File {INPUT_FILE} tidak ditemukan.")
        return
    
    # Cek apakah kolom image_urls sudah ada, jika belum, tambahkan
    if 'image_urls' not in df.columns:
        df['image_urls'] = None
    
    # Ambil indeks terakhir yang diproses
    last_index = get_last_processed_index()
    print(f"Melanjutkan dari indeks {last_index}")
    
    # Iterasi setiap objek wisata dan cari gambarnya
    for index, row in tqdm(df.iloc[last_index:].iterrows(), total=len(df.iloc[last_index:]), 
                          desc="Progress Scraping"):
        # Skip jika sudah ada URL gambar
        if pd.notna(row["image_urls"]) and row["image_urls"]:
            continue
            
        place_name = row["Place_Name"]
        city = row["City"] if pd.notna(row["City"]) else ""
        
        query = f"{place_name} {city}"
        print(f"\nMencari gambar untuk: {query}")
        
        # Mencoba beberapa metode pencarian dalam urutan dari yang tercepat ke yang lebih lambat
        image_urls = []
        
        # 1. Metode cepat: Requests dengan Google
        if not image_urls:
            try:
                image_urls = get_images_with_requests(query, num_images=3)
            except Exception as e:
                print(f"Error dengan metode requests: {e}")
        
        # 2. Metode alternatif: Bing
        if not image_urls:
            try:
                image_urls = get_images_from_bing(query, num_images=3)
            except Exception as e:
                print(f"Error dengan Bing: {e}")
        
        # 3. Metode alternatif: Unsplash
        if not image_urls:
            try:
                image_urls = get_images_direct_from_unsplash(query, num_images=3)
            except Exception as e:
                print(f"Error dengan Unsplash: {e}")
                
        # 4. Metode dengan Selenium: Google (lebih lambat tapi lebih baik)
        if not image_urls and USE_SELENIUM:
            try:
                image_urls = get_images_from_google(query, num_images=3)
            except Exception as e:
                print(f"Error dengan Selenium: {e}")
        
        # 5. Metode paling lambat: DuckDuckGo
        if not image_urls and USE_DUCKDUCKGO:
            try:
                image_urls = search_images_duckduckgo(query, num_images=3)
            except Exception as e:
                print(f"Error dengan DuckDuckGo: {e}")
        
        # Simpan URL gambar yang ditemukan
        if image_urls:
            df.at[index, "image_urls"] = "|".join(image_urls)
        else:
            print(f"Tidak dapat menemukan gambar untuk: {query}")
            # Tambahkan placeholder untuk objek tanpa gambar
            df.at[index, "image_urls"] = "https://via.placeholder.com/300x200?text=No+Image+Found"
        
        # Simpan progress dan hasil sementara
        save_progress(index + 1)
        df.to_csv(OUTPUT_FILE, index=False)
        
        # Delay acak untuk menghindari pemblokiran, tapi lebih singkat
        sleep_time = random.uniform(1, 2)
        time.sleep(sleep_time)

    print("\nProses scraping selesai!")
    print(f"Data telah disimpan ke {OUTPUT_FILE}")

if __name__ == "__main__":
    main()