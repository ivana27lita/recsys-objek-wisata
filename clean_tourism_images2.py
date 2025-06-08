import pandas as pd
import os
import re
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import time

def extract_wikimedia_image_url(wiki_url):
    """
    Mengekstrak URL gambar langsung dari halaman Wikipedia atau Wikimedia Commons
    
    Args:
        wiki_url (str): URL halaman Wikipedia atau Wikimedia Commons yang berisi gambar
        
    Returns:
        str: URL gambar langsung atau None jika gagal
    """
    try:
        # Periksa apakah ini adalah URL Wikipedia atau Wikimedia Commons
        is_wikipedia = 'wikipedia.org/wiki/' in wiki_url and ('Berkas:' in wiki_url or 'File:' in wiki_url)
        is_wikimedia_commons = 'commons.wikimedia.org/wiki/File:' in wiki_url
        
        if not (is_wikipedia or is_wikimedia_commons):
            return None
            
        # Request halaman
        response = requests.get(wiki_url, timeout=10)
        if response.status_code != 200:
            return None
            
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Cari elemen gambar atau div yang berisi gambar
        img_div = soup.find('div', class_='fullImageLink')
        if img_div:
            # Cari tag img di dalam div
            img_tag = img_div.find('img')
            if img_tag and 'src' in img_tag.attrs:
                # Dapatkan URL gambar dan pastikan lengkap
                img_url = img_tag['src']
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                return img_url
        
        # Cara kedua: cari langsung tag img berukuran besar
        for img in soup.select('img.mw-mmv-dialog-thumbnail, img.mw-file-element'):
            if 'src' in img.attrs:
                img_url = img['src']
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                return img_url
        
        # Cara ketiga: coba ekstrak dengan regex dari konten halaman
        # Cari pola yang mengarah ke upload.wikimedia.org
        match = re.search(r'(https://upload\.wikimedia\.org/[^"\'>\s]+)', response.text)
        if match:
            return match.group(1)
            
        return None
    except Exception as e:
        print(f"Error mengekstrak URL gambar dari {wiki_url}: {e}")
        return None

def fix_wikimedia_urls():
    """
    Mengganti URL Wikipedia dan Wikimedia Commons dengan URL gambar langsung dalam file CSV
    """
    # Path file
    file_path = "2/data/processed/tourism_with_images.csv"
    
    # Cek apakah file ada
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} tidak ditemukan.")
        return
    
    print(f"Membaca file {file_path}...")
    df = pd.read_csv(file_path)
    
    # Buat backup
    backup_path = file_path + ".wikimedia_backup"
    df.to_csv(backup_path, index=False)
    print(f"Backup dibuat di {backup_path}")
    
    # Inisialisasi counter untuk statistik
    total_wiki_urls = 0
    replaced_wiki_urls = 0
    rows_with_wiki = 0
    
    # Loop melalui setiap baris
    print("Memperbaiki URL gambar Wikipedia dan Wikimedia Commons...")
    for idx, row in tqdm(df.iterrows(), total=len(df)):
        # Skip jika tidak ada URL gambar
        if pd.isna(row['image_urls']) or not row['image_urls'] or row['image_urls'] == "":
            continue
            
        # Pisahkan URL berdasarkan pemisah |
        url_list = row['image_urls'].split('|')
        url_changed = False
        
        # Proses setiap URL
        for i, url in enumerate(url_list):
            url = url.strip()
            
            # Cek apakah URL dari Wikipedia atau Wikimedia Commons
            is_wikipedia = 'wikipedia.org/wiki/' in url and ('Berkas:' in url or 'File:' in url)
            is_wikimedia_commons = 'commons.wikimedia.org/wiki/File:' in url
            
            if is_wikipedia or is_wikimedia_commons:
                total_wiki_urls += 1
                
                # Coba ekstrak URL gambar langsung
                direct_url = extract_wikimedia_image_url(url)
                if direct_url:
                    url_list[i] = direct_url
                    replaced_wiki_urls += 1
                    url_changed = True
                    print(f"Berhasil mengganti URL: {url} -> {direct_url}")
                else:
                    # Jika gagal, tandai untuk dihapus (dengan string kosong)
                    url_list[i] = ""
                    print(f"Gagal mendapatkan URL gambar langsung dari: {url}")
        
        # Jika ada perubahan URL, perbarui DataFrame
        if url_changed:
            rows_with_wiki += 1
            # Filter out empty strings
            url_list = [u for u in url_list if u.strip()]
            
            if len(url_list) == 0:
                # Jika semua URL dihapus, gunakan placeholder
                df.at[idx, 'image_urls'] = "https://via.placeholder.com/800x400?text=Tidak+Ada+Gambar"
            else:
                # Simpan URL yang tersisa/diganti
                df.at[idx, 'image_urls'] = "|".join(url_list)
        
        # Tunggu sebentar untuk menghindari overload server
        time.sleep(0.5)
    
    # Simpan hasil ke file asli
    df.to_csv(file_path, index=False)
    
    # Tampilkan statistik
    print("\n===== HASIL PERBAIKAN URL WIKIMEDIA =====")
    print(f"Total baris diperiksa: {len(df)}")
    print(f"Baris yang mengandung URL Wikipedia/Commons: {rows_with_wiki}")
    print(f"Total URL Wikipedia/Commons yang ditemukan: {total_wiki_urls}")
    print(f"URL yang berhasil diganti: {replaced_wiki_urls}")
    print(f"URL yang gagal diganti: {total_wiki_urls - replaced_wiki_urls}")
    print("===========================================")
    print(f"\nFile telah diperbarui: {file_path}")
    print(f"Backup tersimpan di: {backup_path}")

if __name__ == "__main__":
    fix_wikimedia_urls()