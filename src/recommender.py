import pandas as pd
import numpy as np
import pickle
from sklearn.metrics.pairwise import cosine_similarity
import os
import time

class TourismRecommender:
    def __init__(self, data_path='data/processed', models_path='models'):
        """
        Inisialisasi Tourism Recommender System yang menggabungkan
        content-based, collaborative dan context-based filtering
        """
        # Load data yang sudah diproses
        self.tourism_df = pd.read_csv(f'{data_path}/tourism_processed.csv')
        self.rules_df = pd.read_csv(f'{data_path}/rules_data.csv')
        
        # Load encoder
        with open(f'{models_path}/encoder.pkl', 'rb') as f:
            self.encoder = pickle.load(f)
        
        # Siapkan data untuk rekomendasi yang cepat
        self.prepare_data()
    
    def prepare_data(self):
        """Siapkan struktur data untuk akses cepat"""
        # Pemetaan kategori ke objek wisata
        self.category_to_places = {}
        # Pemetaan kota ke objek wisata per kategori
        self.city_to_categories = {}
        
        # Buat mapping objek wisata per kategori
        for category in self.tourism_df['Category'].unique():
            places = self.tourism_df[self.tourism_df['Category'] == category]
            self.category_to_places[category] = places[['Place_Id', 'Place_Name', 'City', 'Description']].to_dict('records')
        
        # Buat mapping kategori per kota
        for city in self.tourism_df['City'].unique():
            city_places = self.tourism_df[self.tourism_df['City'] == city]
            
            # Simpan kategori dan jumlah objek wisata per kategori dalam kota ini
            category_counts = {}
            for category in city_places['Category'].unique():
                category_places = city_places[city_places['Category'] == category]
                category_counts[category] = len(category_places)
            
            # Simpan mapping kota ke kategori dan jumlah objek
            self.city_to_categories[city] = category_counts
        
        # Pemetaan kota ke objek wisata per kategori
        self.city_category_places = {}
        for city in self.tourism_df['City'].unique():
            self.city_category_places[city] = {}
            city_places = self.tourism_df[self.tourism_df['City'] == city]
            
            for category in city_places['Category'].unique():
                category_places = city_places[city_places['Category'] == category]
                self.city_category_places[city][category] = category_places[['Place_Id', 'Place_Name', 'City', 'Description']].to_dict('records')
    
    def get_category_recommendations(self, user_gender, user_age_group, n_categories=3):
        """
        Mendapatkan rekomendasi kategori berdasarkan profil pengguna
        menggunakan content-based filtering (cosine similarity)
        """
        if user_gender == "Tidak ingin menyebutkan":
            # Cari rules dengan age_group yang sama, tapi ambil yang Total_Users nya tertinggi
            # untuk setiap kategori (tidak peduli gender)
        matching_age_rules = self.rules_df[self.rules_df['Age_Group']
                                           == user_age_group]

        # Ambil rules terbaik per kategori (dengan Total_Users tertinggi)
        best_rules = matching_age_rules.sort_values('Total_Users', ascending=False) \
            .groupby('Category') \
            .first() \
            .reset_index() \
            .sort_values('Total_Users', ascending=False)

        # Set similarity = 1.0 karena age_group match
        best_rules['Similarity'] = 1.0

        return best_rules
    else:
        # Original code untuk gender standard
        # ...rest of the original code...
        # Buat vektor user
        user_df = pd.DataFrame([[user_gender, user_age_group]], columns=[
                               'Gender', 'Age_Group'])
        encoded_user = self.encoder.transform(user_df).toarray()

        # Transformasi fitur rules
        rule_features = self.encoder.transform(
            self.rules_df[['Gender', 'Age_Group']]).toarray()

        # Hitung similarity
        similarities = cosine_similarity(rule_features, encoded_user).flatten()

        # Tambahkan similarity ke dataframe rules
        rules_with_sim = self.rules_df.copy()
        rules_with_sim['Similarity'] = similarities

        # Ambil best rule untuk tiap kategori
        best_rules = rules_with_sim.sort_values('Similarity', ascending=False) \
            .groupby('Category') \
            .first() \
            .reset_index() \
            .sort_values('Similarity', ascending=False)

        # Ambil semua kategori dengan similarity-nya (tidak hanya top N)
        return best_rules
    
    def apply_context_boost(self, best_rules, user_trip_type):
        """
        Menerapkan context-based filtering dengan memberikan
        bobot tambahan berdasarkan tipe perjalanan
        """
        rules_with_boost = best_rules.copy()
        
        # Definisi bobot untuk tipe perjalanan per kategori
        trip_type_weights = {
            'Solo Trip': {
                'Cagar Alam': 0.3,
                'Bahari': 0.25,
                'Budaya': 0.2,
                'Taman Hiburan': 0.15,
                'Tempat Ibadah': 0.1,
                'Pusat Perbelanjaan': 0.05
            },
            'Family Trip': {
                'Taman Hiburan': 0.3,
                'Pusat Perbelanjaan': 0.25,
                'Bahari': 0.2,
                'Cagar Alam': 0.15,
                'Budaya': 0.1,
                'Tempat Ibadah': 0.05
            },
            'Couple Trip': {
                'Bahari': 0.3,
                'Budaya': 0.25,
                'Taman Hiburan': 0.2,
                'Pusat Perbelanjaan': 0.15,
                'Cagar Alam': 0.1,
                'Tempat Ibadah': 0.05
            },
            'Friends Trip': {
                'Taman Hiburan': 0.3, 
                'Bahari': 0.25,
                'Pusat Perbelanjaan': 0.2,
                'Cagar Alam': 0.15,
                'Budaya': 0.1,
                'Tempat Ibadah': 0.05
            }
        }
        
        # Terapkan boosting berdasarkan tipe perjalanan
        def get_trip_type_boost(row):
            category = row['Category']
            boost = 0
            
            # Boost berdasarkan kesesuaian tipe perjalanan dengan kategori
            category_weight = trip_type_weights.get(user_trip_type, {}).get(category, 0)
            boost += category_weight
            
            # Tambahan: boost jika tipe perjalanan cocok dengan yang ada di rules
            if row['Tipe_Perjalanan'] == user_trip_type:
                boost += 0.1
                
            return boost
        
        # Hitung boost score
        rules_with_boost['Boost'] = rules_with_boost.apply(get_trip_type_boost, axis=1)
        
        # Hitung final score
        rules_with_boost['Final_Score'] = rules_with_boost['Similarity'] + rules_with_boost['Boost']
        
        # Urutkan berdasarkan final score
        return rules_with_boost.sort_values('Final_Score', ascending=False)
    
    def get_places_for_category_in_city(self, category, city, n_places=3):
        """
        Mendapatkan objek wisata untuk kategori tertentu di kota tertentu.
        """
        # Generate seed unik untuk memastikan variasi
        seed = int(time.time() * 1000) % 2**32
        np.random.seed(seed)
        
        # Cek apakah kategori ada di kota target
        if city in self.city_category_places and category in self.city_category_places[city]:
            places_in_city = self.city_category_places[city][category]
            
            # Jika jumlah objek cukup, pilih secara acak
            if len(places_in_city) >= n_places:
                selected_indices = np.random.choice(len(places_in_city), n_places, replace=False)
                return [places_in_city[i] for i in selected_indices]
            
            # Jika tidak cukup, ambil semua yang ada
            return places_in_city
        
        # Jika tidak ada objek untuk kategori ini di kota target
        return []
    
    def get_recommendations(self, user_gender, user_age_group, target_city, user_trip_type, n_categories=3, n_places_per_category=3):
        """
        Generate rekomendasi lengkap untuk user.
        
        Args:
            user_gender: Jenis kelamin pengguna
            user_age_group: Kelompok usia pengguna
            target_city: Kota tujuan wisata
            user_trip_type: Tipe perjalanan pengguna
            n_categories: Jumlah kategori yang direkomendasikan
            n_places_per_category: Jumlah objek wisata per kategori
            
        Returns:
            List rekomendasi dengan kategori dan objek wisata
        """
        # 1. Dapatkan rekomendasi kategori berdasarkan content-based filtering (ambil semua kategori)
        all_categories = self.get_category_recommendations(user_gender, user_age_group)
        
        # 2. Terapkan context boosting berdasarkan tipe perjalanan
        boosted_categories = self.apply_context_boost(all_categories, user_trip_type)
        
        # 3. Filter kategori yang tersedia di kota tujuan
        available_categories = []
        unavailable_categories = []
        
        for _, row in boosted_categories.iterrows():
            category = row['Category']
            if target_city in self.city_category_places and category in self.city_category_places[target_city]:
                n_places = len(self.city_category_places[target_city][category])
                if n_places > 0:
                    available_categories.append((category, row, n_places))
                else:
                    unavailable_categories.append((category, row))
            else:
                unavailable_categories.append((category, row))
        
        # 4. Pilih kategori yang akan direkomendasikan
        selected_categories = []
        
        # Tambahkan kategori yang tersedia di kota tujuan
        for category, row, n_places in available_categories:
            if len(selected_categories) < n_categories:
                selected_categories.append((category, row))
            else:
                break
        
        # Jika masih kurang, tambahkan dari kategori yang tidak tersedia
        # (ini akan ditangani dengan mengambil dari kategori lain dengan similaritas tertinggi berikutnya)
        for category, row in unavailable_categories:
            if len(selected_categories) < n_categories:
                selected_categories.append((category, row))
            else:
                break
        
        # 5. Dapatkan objek wisata untuk setiap kategori
        recommendations = []
        categories_with_places = []
        
        for category, row in selected_categories:
            places = self.get_places_for_category_in_city(category, target_city, n_places=n_places_per_category)
            
            # Jika tidak ada objek wisata untuk kategori ini di kota tujuan,
            # tandai untuk diisi nanti dari kategori lain
            if len(places) == 0:
                recommendations.append({
                    'category': category,
                    'score': {
        'total': row['Final_Score'],
        'similarity': row['Similarity'],
        'boost': row['Boost']
    },
                    'similarity': row['Similarity'],
                    'boost': row['Boost'],
                    'user_match': {
                        'gender': row['Gender'],
                        'age_group': row['Age_Group'],
                        'trip_type': row['Tipe_Perjalanan']
                    },
                    'places': [],
                    'needs_places': n_places_per_category  # Flag untuk diisi dari kategori lain
                })
            else:
                # Jika tidak cukup, tandai berapa objek wisata yang masih dibutuhkan
                needs_more = max(0, n_places_per_category - len(places))
                
                recommendations.append({
                    'category': category,
                    'score': {
        'total': row['Final_Score'],
        'similarity': row['Similarity'],
        'boost': row['Boost']
    },
                    'similarity': row['Similarity'],
                    'boost': row['Boost'],
                    'user_match': {
                        'gender': row['Gender'],
                        'age_group': row['Age_Group'],
                        'trip_type': row['Tipe_Perjalanan']
                    },
                    'places': places,
                    'needs_places': needs_more
                })
                
                # Simpan kategori ini jika memiliki objek wisata (untuk digunakan nanti)
                if len(places) > 0:
                    categories_with_places.append(category)
        
        # 6. Cari kategori lain dengan skor tertinggi berikutnya untuk mengisi kategori yang kurang objek wisata
        # Ambil semua kategori yang tersedia di kota tujuan (yang memiliki objek wisata)
        available_city_categories = set()
        if target_city in self.city_category_places:
            for cat in self.city_category_places[target_city]:
                if len(self.city_category_places[target_city][cat]) > 0:
                    available_city_categories.add(cat)
        
        # Tambahkan objek wisata dari kategori lain untuk kategori yang kurang
        for i, rec in enumerate(recommendations):
            if rec['needs_places'] > 0:
                needed_places = rec['needs_places']
                
                # Ambil kategori lain dengan skor tertinggi berikutnya yang tersedia di kota tujuan
                # dan belum direkomendasikan
                for _, row in boosted_categories.iterrows():
                    alt_category = row['Category']
                    
                    # Skip jika kategori sudah direkomendasikan atau tidak tersedia di kota tujuan
                    if alt_category in [r['category'] for r in recommendations] or alt_category not in available_city_categories:
                        continue
                    
                    # Ambil objek wisata dari kategori alternatif
                    alt_places = self.get_places_for_category_in_city(alt_category, target_city, n_places=needed_places)
                    
                    if len(alt_places) > 0:
                        # Tambahkan ke rekomendasi
                        recommendations[i]['places'].extend(alt_places)
                        recommendations[i]['needs_places'] = max(0, needed_places - len(alt_places))
                        recommendations[i]['alternate_category'] = alt_category
                        
                        # Jika sudah cukup, break
                        if recommendations[i]['needs_places'] == 0:
                            break
        
        # 7. Hapus field 'needs_places' yang tidak perlu ditampilkan ke user
        for rec in recommendations:
            if 'needs_places' in rec:
                del rec['needs_places']
        
        return recommendations