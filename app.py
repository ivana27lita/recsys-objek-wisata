import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from PIL import Image
import os
import time
import random

from src.recommender import TourismRecommender
from src.utils import get_age_group

# Page configuration
st.set_page_config(
    page_title="Indonesia Tourism Recommender",
    page_icon="🏝️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS for improved appearance and mobile responsiveness
st.markdown("""
<style>
    /* Main styles with background gradient */
    body {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4eaff 100%);
        background-attachment: fixed;
    }
    
    .stApp {
        background: rgba(255, 255, 255, 0.1);
    }
    
    .main-header {
        font-size: 2.2rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }

    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        text-align: center;
    }

    /* Cards */
    .card {
        background-color: rgba(255, 255, 255, 0.85);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        backdrop-filter: blur(5px);
    }

    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
    }

    .category-header {
        font-size: 1.6rem;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
    }

    /* Place cards */
    .place-card {
        background-color: white;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 3px 6px rgba(0, 0, 0, 0.08);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
    }

    .place-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
    }

    .place-name {
        font-size: 1.3rem;
        font-weight: bold;
        margin-bottom: 0.6rem;
        color: #1976D2;
    }

    .place-location {
        display: flex;
        align-items: center;
        font-size: 0.9rem;
        color: #555;
        margin-bottom: 0.7rem;
    }

    .place-description {
        font-size: 0.95rem;
        color: #333;
        line-height: 1.5;
        flex-grow: 1;
    }
    
    /* Description with see more functionality */
    .short-description {
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        margin-bottom: 0.5rem;
    }
    
    .full-description {
        margin-bottom: 0.5rem;
    }
    
    .see-more-btn {
        color: #1976D2;
        cursor: pointer;
        display: inline-block;
        font-weight: 500;
        font-size: 0.85rem;
        margin-top: 0.5rem;
        text-decoration: underline;
        transition: color 0.2s;
    }
    
    .see-more-btn:hover {
        color: #1565C0;
    }
    
    /* Description toggle functionality */
    .collapsible-description[data-collapsed="true"] .full-description {
        display: none;
    }
    
    .collapsible-description[data-collapsed="false"] .short-description {
        display: none;
    }
    
    .collapsible-description[data-collapsed="false"] .see-more-btn::after {
        content: "Lihat lebih sedikit";
    }
    
    .collapsible-description[data-collapsed="true"] .see-more-btn::after {
        content: "Lihat selengkapnya";
    }

    /* Badges */
    .badge {
        background-color: #E3F2FD;
        color: #1565C0;
        padding: 0.3rem 0.7rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin-right: 0.6rem;
        display: inline-block;
        margin-bottom: 0.3rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    /* Sections */
    .section-divider {
        margin: 2rem 0;
        border-bottom: 1px solid #e0e0e0;
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.8rem;
        }

        .sub-header {
            font-size: 1.3rem;
        }

        .card {
            padding: 1rem;
        }

        .place-card {
            padding: 1rem;
        }

        .category-header {
            font-size: 1.4rem;
        }
    }
    
    /* Image carousel */
    .carousel {
        position: relative;
        width: 100%;
        overflow: hidden;
        border-radius: 10px;
        margin-bottom: 1rem;
        height: 200px; /* Fixed height for consistency */
    }
    
    .carousel img {
        width: 100%;
        height: 200px;
        object-fit: cover;
        border-radius: 10px;
    }
    
    /* Animation for skeleton loading */
    @keyframes shimmer {
        0% {
            background-position: -1000px 0;
        }
        100% {
            background-position: 1000px 0;
        }
    }
    
    .skeleton {
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 1000px 100%;
        animation: shimmer 2s infinite linear;
        border-radius: 10px;
        height: 200px;
        width: 100%;
        margin-bottom: 1rem;
    }
</style>

<script>
// JavaScript untuk toggle deskripsi
function toggleDescription(id) {
    const description = document.getElementById('description-' + id);
    const isCollapsed = description.getAttribute('data-collapsed') === 'true';
    description.setAttribute('data-collapsed', isCollapsed ? 'false' : 'true');
}
// Add event listeners after page loads
document.addEventListener('DOMContentLoaded', function() {
    const toggleButtons = document.querySelectorAll('.see-more-btn');
    toggleButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            toggleDescription(id);
        });
    });
});
</script>
""", unsafe_allow_html=True)

@st.cache_resource
def load_recommender():
    """Load the recommender model (cached)."""
    return TourismRecommender()

@st.cache_data
def load_tourism_data():
    """Load tourism data with images."""
    try:
        # Try to load from the specific path
        df = pd.read_csv('2/data/processed/tourism_with_images.csv')
        return df
    except FileNotFoundError:
        try:
            # Try alternative path
            df = pd.read_csv('data/processed/tourism_with_images.csv')
            return df
        except FileNotFoundError:
            # Fallback to basic tourism data
            st.warning("File tourism_with_images.csv tidak ditemukan. Menggunakan data dasar.")
            df = pd.read_csv('data/processed/tourism_processed.csv')
            # Add empty image_urls column if it doesn't exist
            if 'image_urls' not in df.columns:
                df['image_urls'] = ""
            return df

def get_place_images(place):
    """Get image URLs for a place."""
    if 'image_urls' in place and place['image_urls']:
        # Split by | to get multiple images
        image_urls = place['image_urls'].split('|')
        # Filter out empty URLs
        image_urls = [url for url in image_urls if url.strip()]
        return image_urls
    
    # Return a placeholder if no images
    return ["https://via.placeholder.com/400x300?text=No+Image+Available"]

def render_place_card(place, category, idx, use_columns=3):
    """Render a single place card with images and description."""
    place_id = place.get('Place_Id', 0)
    place_name = place['Place_Name']
    place_city = place['City']
    place_description = place.get('Description', 'Tidak ada deskripsi.')
    
    # Create unique ID for this description
    description_id = f"{category}-{place_id}-{idx}"
    
    # Get images for the place
    image_urls = get_place_images(place)
    
    # Use only the first image for the card
    primary_image = image_urls[0] if image_urls else "https://via.placeholder.com/400x300?text=No+Image+Available"
    
    # Create a card with hover effect and collapsible description
    st.markdown(f"""
    <div class="place-card">
        <div class="carousel">
            <img src="{primary_image}" alt="{place_name}">
        </div>
        <div class="place-name">{place_name}</div>
        <div class="place-location">📍 {place_city}</div>
    </div>
    """, unsafe_allow_html=True)

    # Now, use st.expander for the description part
    with st.expander("Lihat deskripsi"):
        st.write(place_description)
        
def get_gender_options():
    """Get gender options."""
    return ['Laki-laki', 'Perempuan']

def get_city_options():
    """Get city options."""
    return ['Jakarta', 'Bandung', 'Semarang', 'Yogyakarta', 'Surabaya']

def get_trip_type_options():
    """Get trip type options."""
    return ['Solo Trip', 'Couple Trip', 'Family Trip', 'Friends Trip']

def get_category_icon(category):
    """Get icon for each category."""
    icons = {
        'Bahari': '🌊',
        'Budaya': '🏛️',
        'Cagar Alam': '🌳',
        'Pusat Perbelanjaan': '🛍️',
        'Taman Hiburan': '🎡',
        'Tempat Ibadah': '🕌'
    }
    return icons.get(category, '🏞️')

def get_category_color(category):
    """Get color for each category."""
    colors = {
        'Bahari': '#2196F3',  # Blue
        'Budaya': '#FFC107',  # Amber
        'Cagar Alam': '#4CAF50',  # Green
        'Pusat Perbelanjaan': '#E91E63',  # Pink
        'Taman Hiburan': '#9C27B0',  # Purple
        'Tempat Ibadah': '#FF5722'  # Deep Orange
    }
    return colors.get(category, '#607D8B')  # Default: Blue Grey

def get_category_description(category):
    """Get description for each category."""
    descriptions = {
        'Bahari': 'Wisata bahari mencakup pantai, laut, dan aktivitas air.',
        'Budaya': 'Wisata budaya mencakup museum, situs sejarah, dan atraksi budaya lokal.',
        'Cagar Alam': 'Wisata alam mencakup taman nasional, gunung, dan kawasan konservasi.',
        'Pusat Perbelanjaan': 'Pusat perbelanjaan seperti mall, pasar tradisional, dan kawasan belanja.',
        'Taman Hiburan': 'Taman hiburan seperti taman bermain, wahana rekreasi, dan tempat hiburan.',
        'Tempat Ibadah': 'Tempat ibadah seperti masjid, gereja, pura, dan vihara bersejarah.'
    }
    return descriptions.get(category, 'Destinasi wisata populer di Indonesia.')

def initialize_session_state():
    """Initialize session state variables."""
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = {
            'gender': None,
            'age': None,
            'age_group': None,
            'city': None,
            'trip_type': None
        }

    if 'recommendations' not in st.session_state:
        st.session_state.recommendations = None

    if 'show_recommendations' not in st.session_state:
        st.session_state.show_recommendations = False

def render_header():
    """Render the application header."""
    st.markdown("<h1 class='main-header'>🏝️ Indonesia Tourism Recommender</h1>", unsafe_allow_html=True)
    st.markdown(
        """
        <p style='text-align: center; font-size: 1.2rem;'>
        Temukan destinasi wisata sesuai preferensi dan gaya perjalananmu!
        </p>
        """, 
        unsafe_allow_html=True
    )

def render_user_profile_form():
    """Render the user profile form."""
    st.markdown("<h2 class='sub-header'>👤 Profil User</h2>", unsafe_allow_html=True)
    
    with st.form("user_profile_form"):
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            gender = st.selectbox(
                "Jenis Kelamin",
                get_gender_options(),
                index=None,
                placeholder="Pilih jenis kelamin"
            )
            
            age = st.number_input(
                "Umur",
                min_value=18,
                max_value=60,
                step=1
            )
            
        with col2:
            city = st.selectbox(
                "Kota Tujuan Wisata",
                get_city_options(),
                index=None,
                placeholder="Pilih kota tujuan"
            )
            
            trip_type = st.selectbox(
                "Tipe Perjalanan",
                get_trip_type_options(),
                index=None,
                placeholder="Pilih tipe perjalanan"
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        submitted = st.form_submit_button("Dapatkan Rekomendasi", use_container_width=True)
        
        if submitted:
            if gender and age and city and trip_type:
                age_group = get_age_group(age)
                
                st.session_state.user_profile = {
                    'gender': gender,
                    'age': age,
                    'age_group': age_group,
                    'city': city,
                    'trip_type': trip_type
                }
                
                # Show loading spinner
                with st.spinner("Mencari rekomendasi terbaik untukmu..."):
                    # Generate recommendations
                    recommender = load_recommender()
                    recommendations = recommender.get_recommendations(
                        gender, age_group, city, trip_type,
                        n_categories=3, n_places_per_category=3
                    )
                    
                    # Load tourism data with images
                    tourism_data = load_tourism_data()
                    
                    # Enrich recommendations with image data
                    for category_rec in recommendations:
                        for place in category_rec['places']:
                            # Find image URLs for this place
                            place_id = place.get('Place_Id', 0)
                            matching_place = tourism_data[tourism_data['Place_Id'] == place_id]
                            if not matching_place.empty:
                                place['image_urls'] = matching_place.iloc[0].get('image_urls', '')
                                place['Category'] = category_rec['category']
                    
                    st.session_state.recommendations = recommendations
                    st.session_state.show_recommendations = True
                
                # Show success message
                st.success("Rekomendasi berhasil dibuat! Silakan lihat di bawah.")
            else:
                st.error("Mohon lengkapi semua profil user.")

def render_recommendations():
    """Render the recommendations."""
    if not st.session_state.show_recommendations or not st.session_state.recommendations:
        return
    
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    st.markdown("<h2 class='sub-header'>🎯 Rekomendasi Wisata Untukmu</h2>", unsafe_allow_html=True)
    
    # User profile summary
    user_profile = st.session_state.user_profile
    with st.expander("👤 Profil Pengunjung", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Jenis Kelamin:** {user_profile['gender']}")
            st.info(f"**Umur:** {user_profile['age']} ({user_profile['age_group']})")
        with col2:
            st.info(f"**Kota Tujuan:** {user_profile['city']}")
            st.info(f"**Tipe Perjalanan:** {user_profile['trip_type']}")
    
    # Recommendations
    for i, recommendation in enumerate(st.session_state.recommendations):
        category = recommendation['category']
        score = recommendation.get('score', {'similarity': 0, 'boost': 0})
        places = recommendation['places']
        user_match = recommendation['user_match']
        alternate_category = recommendation.get('alternate_category')
        
        # Title for card
        category_title = category
        if alternate_category:
            category_title = f"{category} + {alternate_category}"
        
        # Handle score format
        if isinstance(score, dict):
            similarity = score.get('similarity', 0)
            boost = score.get('boost', 0)
            final_score = similarity + boost
        else:
            similarity = 0
            boost = 0
            final_score = score
        
        st.markdown(f"""
    <div class='card' style='border-left: 5px solid {get_category_color(category)};'>
        <h3 class='category-header'>
            {get_category_icon(category)} {category_title} 
            <span style='font-size: 1rem; color: gray; margin-left: 10px;'>
                (Similarity: {score['similarity']:.2f}, Boost: {score['boost']:.2f})
            </span>
        </h3>
        <p>{get_category_description(category)}</p>
    </div>
""", unsafe_allow_html=True)

        
        # Tampilkan pesan jika kategori ini menggunakan objek wisata dari kategori lain
        if alternate_category:
            st.info(f"Karena jumlah objek wisata {category} di {user_profile['city']} terbatas, kami juga menampilkan beberapa objek wisata dari kategori {alternate_category} yang juga cocok dengan profil Anda.")
        
        # Tampilkan rekomendasi objek wisata
        if len(places) > 0:
            # Create columns for place cards - always use 3 columns or fewer if not enough places
            use_columns = min(3, len(places))
            cols = st.columns(use_columns)
            
            # Render place cards in columns
            for j, place in enumerate(places):
                with cols[j % use_columns]:
                    render_place_card(place, category, j, use_columns)
        else:
            st.warning(f"Tidak ditemukan objek wisata untuk kategori {category} di {user_profile['city']}. Silakan coba kota lain atau kategori lain.")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        if i < len(st.session_state.recommendations) - 1:
            st.markdown("<br>", unsafe_allow_html=True)

def render_about():
    """Render information about the application."""
    with st.expander("ℹ️ Tentang Aplikasi"):
        st.markdown("""
        **Indonesia Tourism Recommender** adalah aplikasi rekomendasi wisata yang menggunakan:
        
        1. **Content-based Filtering**: Merekomendasikan destinasi berdasarkan kategori dan karakteristik objek wisata
        2. **Collaborative Filtering**: Menggunakan pola preferensi dari pengguna lain dengan profil serupa
        3. **Context-based Filtering**: Mempertimbangkan konteks perjalanan untuk rekomendasi yang lebih personal
        
        Algoritma menggunakan cosine similarity untuk menghitung kesesuaian antara profil pengguna dengan pola preferensi
        yang telah diidentifikasi, serta memberikan bobot tambahan berdasarkan tipe perjalanan yang dipilih.
        """)

def main():
    """Main application."""
    initialize_session_state()
    render_header()
    render_about()
    render_user_profile_form()
    render_recommendations()
    
    # Add JavaScript for toggling descriptions
    st.markdown("""
    <script>
    function toggleDescription(id) {
        const description = document.getElementById('description-' + id);
        const isCollapsed = description.getAttribute('data-collapsed') === 'true';
        description.setAttribute('data-collapsed', isCollapsed ? 'false' : 'true');
    }
    // Ensure all toggle buttons work
    document.addEventListener('DOMContentLoaded', function() {
        const toggleButtons = document.querySelectorAll('.see-more-btn');
        toggleButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const id = this.getAttribute('data-id');
                toggleDescription(id);
            });
        });
    });
    // Re-add event listeners after Streamlit updates the DOM
    const observer = new MutationObserver(function(mutations) {
        const toggleButtons = document.querySelectorAll('.see-more-btn');
        toggleButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const id = this.getAttribute('data-id');
                toggleDescription(id);
            });
        });
    });
    observer.observe(document.body, { childList: true, subtree: true });
    </script>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
