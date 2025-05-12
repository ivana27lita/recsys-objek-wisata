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

# Apply custom CSS for improved appearance (without Bootstrap)
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
        background-color: white !important;
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
    .place-image-container {
        width: 100%;
        height: 200px;
        overflow: hidden;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .place-image {
        width: 100%;
        height: 200px;
        object-fit: cover;
        border-radius: 10px;
    }
    /* Override Streamlit selectbox */
    div[data-baseweb="select"] > div > div {
        background-color: white !important;
        color: black !important;
    }
    div[data-baseweb="select"] > div > div input {
        color: black !important;
    }
    div[data-baseweb="select"] > div > div > div {
        color: black !important;
    }
    /* Override Streamlit number input */
    div[data-baseweb="input"] > div {
        background-color: white !important;
    }
    div[data-baseweb="input"] input {
        color: black !important;
    }
    /* Override Streamlit form submit button */
    .stButton > button {
        background-color: #1976D2 !important;
        color: white !important;
        border: none !important;
    }
    .stButton > button:hover {
        background-color: #1565C0 !important;
    }
    /* Override Streamlit info messages */
    div[data-testid="stAlert"] {
        background-color: #e3f2fd !important;
        color: #004085 !important;
        border: 1px solid #bee5eb !important;
    }
    /* Custom Success/Error messages */
    .custom-success {
        padding: 0.75rem 1.25rem;
        margin-bottom: 1rem;
        border: 1px solid transparent;
        border-radius: 0.375rem;
        background-color: #d4edda !important;
        border-color: #c3e6cb !important;
        color: #155724 !important;
    }
    .custom-error {
        padding: 0.75rem 1.25rem;
        margin-bottom: 1rem;
        border: 1px solid transparent;
        border-radius: 0.375rem;
        background-color: #f8d7da !important;
        border-color: #f5c6cb !important;
        color: #721c24 !important;
    }
    .custom-info {
        padding: 0.75rem 1.25rem;
        margin-bottom: 1rem;
        border: 1px solid transparent;
        border-radius: 0.375rem;
        background-color: #e3f2fd !important;
        border-color: #bee5eb !important;
        color: #004085 !important;
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
<<<<<<< HEAD
=======

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
>>>>>>> 0c6634cd358f0e225bf2b0111e61ac2cf347feeb
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
            df = pd.read_csv('2/data/processed/tourism_processed.csv')
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
        image_urls = [url.strip() for url in image_urls if url.strip()]
        return image_urls
    # Return a placeholder if no images
    return ["https://via.placeholder.com/400x300?text=No+Image+Available"]

def render_place_card(place, category, idx, use_columns=3):
    """Render a single place card with single image and description in expander."""
    place_id = place.get('Place_Id', 0)
    place_name = place['Place_Name']
    place_city = place['City']
    place_description = place.get('Description', 'Tidak ada deskripsi.')
    # Get images for the place (only use the first one)
    image_urls = get_place_images(place)
    primary_image = image_urls[0] if image_urls else "https://via.placeholder.com/400x300?text=No+Image+Available"
    # Create a card with single image
    st.markdown(f"""
    <div class="place-card">
        <div class="place-image-container">
            <img src="{primary_image}" class="place-image" alt="{place_name}">
        </div>
        <div class="place-name">{place_name}</div>
        <div class="place-location">📍 {place_city}</div>
    </div>
    """, unsafe_allow_html=True)
    # Add expander for description
    with st.expander("Lihat deskripsi"):
        st.write(place_description)

    # Now, use st.expander for the description part
    with st.expander("Lihat deskripsi"):
        st.write(place_description)
        
def get_gender_options():
    """Get gender options."""
    return ['Laki-laki', 'Perempuan', 'Tidak ingin menyebutkan']

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
        'Pusat Perbelanjaan': 'Pusat perbelanjaan seperti mall, pasar tradisional, dan kawasan belanja serta kuliner.',
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

def custom_success(message):
    """Custom success message that's not affected by theme."""
    st.markdown(f"""
    <div class="custom-success">
        {message}
    </div>
    """, unsafe_allow_html=True)

def custom_error(message):
    """Custom error message that's not affected by theme."""
    st.markdown(f"""
    <div class="custom-error">
        {message}
    </div>
    """, unsafe_allow_html=True)

def custom_info(message):
    """Custom info message that's not affected by theme."""
    st.markdown(f"""
    <div class="custom-info">
        {message}
    </div>
    """, unsafe_allow_html=True)

def render_header():
    """Render the application header."""
    st.markdown("<h1 class='main-header'>Indonesia Tourism Recommender</h1>", unsafe_allow_html=True)
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
<<<<<<< HEAD
=======
    
>>>>>>> 0c6634cd358f0e225bf2b0111e61ac2cf347feeb
    with st.form("user_profile_form"):
        st.markdown("<p>Isi profil Anda untuk mendapatkan rekomendasi</p>", unsafe_allow_html=True)
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
                # Show custom success message
                custom_success("Rekomendasi berhasil dibuat! Silakan lihat di bawah.")
            else:
<<<<<<< HEAD
                custom_error("Mohon lengkapi semua profil user.")
=======
                st.error("Mohon lengkapi semua profil user.")
>>>>>>> 0c6634cd358f0e225bf2b0111e61ac2cf347feeb

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
        </h3>
        <p>{get_category_description(category)}</p>
    </div>
""", unsafe_allow_html=True)
        # Tampilkan pesan jika kategori ini menggunakan objek wisata dari kategori lain
        if alternate_category:
            custom_info(f"Karena jumlah objek wisata {category} di {user_profile['city']} terbatas, kami juga menampilkan beberapa objek wisata dari kategori {alternate_category} yang juga cocok dengan profil Anda.")
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
<<<<<<< HEAD
=======
    
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
>>>>>>> 0c6634cd358f0e225bf2b0111e61ac2cf347feeb

if __name__ == "__main__":
    main()
