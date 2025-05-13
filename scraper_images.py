import os
import time
import random
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import re

# Daftar user agents
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
]

# File untuk menyimpan progress
PROGRESS_FILE = "progress.txt"
INPUT_FILE = "data/processed/tourism_processed.csv"  
OUTPUT_FILE = "data/processed/tourism_with_images.csv"

# Pengaturan timeout
TIMEOUT = 20  # Ditingkatkan timeout untuk Google Maps yang bisa lambat
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

def get_images_from_google_direct(query, num_images=3):
    """Mencari gambar dari Google Images menggunakan requests (tidak perlu Selenium)"""
    headers = {"User-Agent": random.choice(user_agents)}
    search_query = f"{query} tempat wisata Indonesia"
    search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}&tbm=isch"
    
    try:
        print(f"Mencari di Google Images: {search_query}")
        response = requests.get(search_url, headers=headers, timeout=TIMEOUT)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Mencari tag gambar dan URL gambar dengan kualitas yang baik
        image_urls = []
        
        # Metode 1: Cari tag img
        for img in soup.find_all('img'):
            if len(image_urls) >= num_images:
                break
                
            src = img.get('src')
            if src and src.startswith('http') and not src.startswith('data:'):
                # Filter hanya gambar dengan ukuran yang wajar (bukan ikon kecil)
                if 'google' not in src and 'gstatic' not in src:
                    image_urls.append(src)
        
        # Metode 2: Coba cari link gambar dalam atribut data
        if len(image_urls) < num_images:
            # Cari pattern URL gambar di dalam script atau JSON
            content = str(soup)
            img_pattern = r'(https://[^"]+\.(?:jpg|jpeg|png|webp))'
            found_urls = re.findall(img_pattern, content)
            
            for url in found_urls:
                if len(image_urls) >= num_images:
                    break
                    
                if 'google' not in url and 'gstatic' not in url:
                    image_urls.append(url)
        
        print(f"Ditemukan {len(image_urls)} gambar dari Google Images")
        return image_urls[:num_images]
    
    except Exception as e:
        print(f"Error dengan Google Images: {e}")
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
        
        # Coba berbagai metode untuk mendapatkan gambar
        image_urls = []
        
        # 1. Metode Google Images direct (tanpa Selenium)
        if not image_urls:
            try:
                image_urls = get_images_from_google_direct(query, num_images=3)
            except Exception as e:
                print(f"Error dengan metode Google Images direct: {e}")
        
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
        
        # Delay acak untuk menghindari pemblokiran
        sleep_time = random.uniform(1, 3)
        time.sleep(sleep_time)

    print("\nProses scraping selesai!")
    print(f"Data telah disimpan ke {OUTPUT_FILE}")

if __name__ == "__main__":
    main()