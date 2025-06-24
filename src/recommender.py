import pandas as pd
import numpy as np
import pickle
from sklearn.metrics.pairwise import cosine_similarity
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
        self.avg_place_ratings = pd.read_csv(f'{data_path}/avg_place_ratings.csv')

        # Manggabungkan deskripsi objek wisata ke dalam avg_place_ratings
        self.avg_place_ratings = self.avg_place_ratings.merge(
        self.tourism_df[['Place_Id', 'Description']], 
        on='Place_Id', 
        how='left'
    )

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
    
    def get_category_recommendations(self, user_gender, user_age_group):
        """
        Mendapatkan rekomendasi kategori berdasarkan profil pengguna
        menggunakan content-based filtering (cosine similarity)
        """
        if user_gender == "Tidak ingin menyebutkan":
            # Pendekatan vektor untuk "Tidak ingin menyebutkan"
            # Dapatkan representasi vektor untuk kedua gender
            male_df = pd.DataFrame([["Laki-laki", user_age_group]], columns=['Gender', 'Age_Group'])
            female_df = pd.DataFrame([["Perempuan", user_age_group]], columns=['Gender', 'Age_Group'])

            encoded_male = self.encoder.transform(male_df).toarray()
            encoded_female = self.encoder.transform(female_df).toarray()

            # Buat vektor representasi netral dengan mengambil rata-rata
            # Ini memberikan probabilitas 0.5 untuk setiap gender
            encoded_neutral = (encoded_male + encoded_female) / 2

            # Transformasi fitur rules
            rule_features = self.encoder.transform(self.rules_df[['Gender', 'Age_Group']]).toarray()

            # Hitung similarity dengan vektor netral
            similarities = cosine_similarity(rule_features, encoded_neutral).flatten()
        else:
            # Original code untuk gender standard
            user_df = pd.DataFrame([[user_gender, user_age_group]], columns=['Gender', 'Age_Group'])
            encoded_user = self.encoder.transform(user_df).toarray()

            # Transformasi fitur rules
            rule_features = self.encoder.transform(self.rules_df[['Gender', 'Age_Group']]).toarray()

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
                              .sort_values('Total_Users', ascending=False)
        
        # Tambahkan kolom Collaborative_Score berdasarkan urutan Total_Users
        collaborative_scores = []
        
        for i in range(len(best_rules)):
            # Skor dimulai dari 6 untuk urutan pertama, turun sampai minimum 1
            score = max(1, 6 - i)
            collaborative_scores.append(score)
        
        best_rules['Collaborative_Score'] = collaborative_scores

        return best_rules
    
    def apply_context_boost(self, best_rules, user_trip_type):
        """
        Menerapkan context-based filtering dengan memberikan
        bobot tambahan berdasarkan tipe perjalanan
        """

        # Buat salinan dari best_rules untuk menambahkan kolom boost
        rules_with_boost = best_rules.copy()
        
        # Definisi bobot untuk tipe perjalanan per kategori
        trip_type_weights = {
            'Solo Trip': {
                'Cagar Alam': 6,
                'Tempat Ibadah': 5,
                'Budaya': 4,
                'Bahari': 3,
                'Taman Hiburan': 2,
                'Pusat Perbelanjaan': 1
            },
            'Family Trip': {
                'Taman Hiburan': 6,
                'Pusat Perbelanjaan': 5,
                'Bahari': 4,
                'Budaya': 3,
                'Cagar Alam': 2,
                'Tempat Ibadah': 1
            },
            'Couple Trip': {
                'Bahari': 6,
                'Budaya': 5,
                'Taman Hiburan': 4,
                'Cagar Alam': 3,
                'Pusat Perbelanjaan': 2,
                'Tempat Ibadah': 1
            },
            'Friends Trip': {
                'Taman Hiburan': 6, 
                'Budaya': 5,
                'Cagar Alam': 4,
                'Pusat Perbelanjaan': 3,
                'Bahari': 2,
                'Tempat Ibadah': 1
            }
        }
        
        # Terapkan boosting berdasarkan tipe perjalanan
        def get_trip_type_boost(row):
            category = row['Category']
            boost = 0
            
            # Boost berdasarkan kesesuaian tipe perjalanan dengan kategori
            category_weight = trip_type_weights.get(user_trip_type, {}).get(category, 0)
            boost += category_weight
                
            return boost
        
        # Hitung boost score
        rules_with_boost['Context_Score'] = rules_with_boost.apply(get_trip_type_boost, axis=1)

        # Hitung final score
        rules_with_boost['Final_Score'] = (
            rules_with_boost['Collaborative_Score'] + 
            rules_with_boost['Context_Score']
        )

        # Urutkan berdasarkan final score
        return rules_with_boost.sort_values('Final_Score', ascending=False)
    
    def get_places_for_category_in_city(self, category, city, user_gender, user_age_group, n_places=3):
        """
        Mendapatkan objek wisata untuk kategori tertentu di kota tertentu 
        berdasarkan rating tertinggi dari user dengan demografis serupa.
        """
        if user_gender == "Tidak ingin menyebutkan":
        # Ambil top places dari kedua gender dengan age_group serupa
            male_places = self.avg_place_ratings[
                (self.avg_place_ratings['Gender'] == 'Laki-laki') &
                (self.avg_place_ratings['Age_Group'] == user_age_group) &
                (self.avg_place_ratings['Category'] == category) &
                (self.avg_place_ratings['City'] == city)
            ].head(n_places)
            
            female_places = self.avg_place_ratings[
                (self.avg_place_ratings['Gender'] == 'Perempuan') &
                (self.avg_place_ratings['Age_Group'] == user_age_group) &
                (self.avg_place_ratings['Category'] == category) &
                (self.avg_place_ratings['City'] == city)
            ].head(n_places)
            
            # Gabungkan dan sort berdasarkan rating
            combined_places = pd.concat([male_places, female_places]).drop_duplicates('Place_Id')
            combined_places = combined_places.sort_values(['Avg_Rating', 'Rating_Count'], ascending=[False, False]).head(n_places)
            
            # Convert ke format yang dibutuhkan
            places_list = []
            for _, place in combined_places.iterrows():
                places_list.append({
                    'Place_Id': place['Place_Id'],
                    'Place_Name': place['Place_Name'],
                    'City': place['City'],
                    'Description': place.get('Description', 'Tidak ada deskripsi.'),
                    'Avg_Rating': place['Avg_Rating'],
                    'Rating_Count': place['Rating_Count']
                })
            
            return places_list
        else:
            # Filter berdasarkan demografis user yang spesifik
            filtered_places = self.avg_place_ratings[
                (self.avg_place_ratings['Gender'] == user_gender) &
                (self.avg_place_ratings['Age_Group'] == user_age_group) &
                (self.avg_place_ratings['Category'] == category) &
                (self.avg_place_ratings['City'] == city)
            ].head(n_places)
            
            # Convert ke format yang dibutuhkan
            places_list = []
            for _, place in filtered_places.iterrows():
                places_list.append({
                    'Place_Id': place['Place_Id'],
                    'Place_Name': place['Place_Name'],
                    'City': place['City'],
                    'Description': place.get('Description', 'Tidak ada deskripsi.'),
                    'Avg_Rating': place['Avg_Rating'],
                    'Rating_Count': place['Rating_Count']
                })
            
            return places_list
    
    def get_recommendations(self, user_gender, user_age_group, target_city, user_trip_type, n_categories=6, n_places_per_category=3):
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
        
        # 3. Ambil semua kategori dengan skor tertinggi (6 kategori)
        top_categories = boosted_categories.head(n_categories)

        # 4. Dapatkan objek wisata untuk setiap kategori
        recommendations = []

        for _, row in top_categories.iterrows():
            category = row['Category']
            places = self.get_places_for_category_in_city(category, target_city, user_gender, user_age_group, n_places=n_places_per_category)
            
            recommendations.append({
                'category': category,
                'score': {
                    'similarity': row['Similarity'],
                    'collaborative_score': row['Collaborative_Score'], 
                    'context_score': row['Context_Score'],
                    'final_score': row['Final_Score']
                },
                'user_match': {
                    'gender': row['Gender'],
                    'age_group': row['Age_Group'],
                    'trip_type': user_trip_type
                },
                'places': places,
                'places_found': len(places),  
                'places_requested': n_places_per_category  
            })
    
        return recommendations