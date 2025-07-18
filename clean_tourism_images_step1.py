import pandas as pd
import os
import requests
from requests.exceptions import RequestException
import time
from tqdm import tqdm

def validate_url(url, timeout=5):
    """Cek apakah URL valid dan dapat diakses"""
    # Skip URL dari asset.kompas.com - langsung anggap tidak valid
    if "asset.kompas.com" in url:
        return False
        
    try:
        # Hanya melakukan HEAD request untuk kecepatan
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return 200 <= response.status_code < 300
    except:
        return False

def clean_invalid_urls():
    """Menghapus URL yang tidak valid dan URL dari asset.kompas.com"""
    
    # Path file
    file_path = "2/data/processed/tourism_with_images.csv"
    
    # Cek apakah file ada
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} tidak ditemukan.")
        return
    
    print(f"Membaca file {file_path}...")
    df = pd.read_csv(file_path)
    
    # Buat backup
    backup_path = file_path + ".backup"
    df.to_csv(backup_path, index=False)
    print(f"Backup dibuat di {backup_path}")
    
    # Buat daftar untuk menyimpan statistik
    total_urls = 0
    valid_urls = 0
    kompas_urls = 0
    other_invalid_urls = 0
    rows_updated = 0
    
    # Loop melalui setiap baris
    print("Memvalidasi dan menghapus URL yang tidak valid...")
    for idx, row in tqdm(df.iterrows(), total=len(df)):
        # Skip jika tidak ada URL gambar
        if pd.isna(row['image_urls']) or not row['image_urls'] or row['image_urls'] == "":
            df.at[idx, 'image_urls'] = "https://via.placeholder.com/800x400?text=Tidak+Ada+Gambar"
            rows_updated += 1
            continue
            
        # Pisahkan URL berdasarkan pemisah |
        url_list = row['image_urls'].split('|')
        total_urls += len(url_list)
        
        # Filter hanya URL yang valid dan bukan dari asset.kompas.com
        valid_url_list = []
        for url in url_list:
            url = url.strip()
            if not url:
                continue
                
            if "asset.kompas.com" in url:
                kompas_urls += 1
                continue  # Skip URL dari kompas
                
            if validate_url(url):
                valid_url_list.append(url)
                valid_urls += 1
            else:
                other_invalid_urls += 1
        
        # Jika semua URL tidak valid, gunakan placeholder
        if not valid_url_list:
            df.at[idx, 'image_urls'] = "https://via.placeholder.com/800x400?text=Tidak+Ada+Gambar"
        else:
            # Simpan hanya URL yang valid
            df.at[idx, 'image_urls'] = "|".join(valid_url_list)
            
        rows_updated += 1
        
        # Tunggu sebentar untuk menghindari overload server
        time.sleep(0.1)
    
    # Simpan hasil ke file asli
    df.to_csv(file_path, index=False)
    
    # Tampilkan statistik
    print("\n===== HASIL PEMBERSIHAN URL =====")
    print(f"Total baris diproses: {rows_updated}")
    print(f"Total URL diperiksa: {total_urls}")
    print(f"URL valid: {valid_urls}")
    print(f"URL dari asset.kompas.com (dihapus): {kompas_urls}")
    print(f"URL invalid lainnya (dihapus): {other_invalid_urls}")
    print(f"Total URL dihapus: {kompas_urls + other_invalid_urls}")
    if total_urls > 0:
        print(f"Persentase URL valid: {valid_urls/total_urls*100:.2f}%")
    print("=================================")
    print(f"\nFile telah diperbarui: {file_path}")
    print(f"Backup tersimpan di: {backup_path}")

if __name__ == "__main__":
    clean_invalid_urls()
