import streamlit as st
import pandas as pd

from src.recommender import TourismRecommender
from src.utils import get_age_group

# Page configuration
st.set_page_config(
    page_title="Indonesia Tourism Recommender",
    page_icon="🏝️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS for improved appearance
st.markdown("""
<style>
    /* Main styles with background gradient */
    body {
        background: linear-gradient(135deg, #e0f2ff 0%, #d5deff 50%, #e4d5ff 100%);
        background-attachment: fixed;
    }
    .stApp {
        background: rgba(255, 255, 255, 0.1);
    }
    .main-header {
    font-size: 2.4rem;
    background: -webkit-linear-gradient(45deg, #1976D2, #5E35B1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 1.2rem;
    text-shadow: 0px 2px 3px rgba(0,0,0,0.1);
    font-weight: 800;
}
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        text-align: center;
    }
    /* Category cards */
    .category-card {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        backdrop-filter: blur(5px);
    }
    .category-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
    }
    .category-header {
        font-size: 1.6rem;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
    }

    /* Tourism place cards */
    .place-card-wrapper {
        background-color: white;
        border-radius: 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        margin-bottom: 1.5rem;
        overflow: hidden;
        height: 100%;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        display: flex;
        flex-direction: column;
    }
    .place-card-wrapper:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
    }

    /* Place image and info section */
    .place-image {
        width: 100%;
        height: 180px;
        object-fit: cover;
    }
    .place-info {
        padding: 1rem;
    }
    .place-name {
        color: #1976D2;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        line-height: 1.3;
    }
    .place-location {
        display: flex;
        align-items: center;
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }

    /* Fix Streamlit expander styling to integrate better with card */
    .stExpander {
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
        margin: 0 !important;
    }
    .streamlit-expanderHeader {
        background-color: transparent !important;
        color: #1976D2 !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        padding: 0.5rem 1rem !important;
        border-top: 1px solid #f0f0f0 !important;
        border-bottom: none !important;
    }
    .streamlit-expanderContent {
        border: none !important;
        padding: 0 1rem 1rem 1rem !important;
    }

    /* Description content */
    .place-description {
        color: #444;
        font-size: 0.95rem;
        line-height: 1.5;
    }

    /* Override Streamlit form inputs */
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
    div[data-baseweb="input"] > div {
        background-color: white !important;
    }
    div[data-baseweb="input"] input {
        color: black !important;
    }

    /* Submit button */
    .stButton > button {
        background-color: #1976D2 !important;
        color: white !important;
        border: none !important;
        border-radius: 30px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background-color: #1565C0 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
    }

    /* Alert messages */
    .custom-success {
        padding: 0.75rem 1.25rem;
        margin-bottom: 1rem;
        border: 1px solid transparent;
        border-radius: 8px;
        background-color: #d4edda !important;
        border-color: #c3e6cb !important;
        color: #155724 !important;
    }
    .custom-error {
        padding: 0.75rem 1.25rem;
        margin-bottom: 1rem;
        border: 1px solid transparent;
        border-radius: 8px;
        background-color: #f8d7da !important;
        border-color: #f5c6cb !important;
        color: #721c24 !important;
    }
    .custom-info {
        padding: 0.75rem 1.25rem;
        margin-bottom: 1rem;
        border: 1px solid transparent;
        border-radius: 8px;
        background-color: #e3f2fd !important;
        border-color: #bee5eb !important;
        color: #004085 !important;
    }
    .custom-warning {
        padding: 0.75rem 1.25rem;
        margin-bottom: 1rem;
        border: 1px solid transparent;
        border-radius: 8px;
        background-color: #fff3cd !important;
        border-color: #ffeaa7 !important;
        color: #856404 !important;
    }

    .place-rating {
        display: flex;
        align-items: center;
        color: #ff6b35;
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
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

    /* Section divider */
    .section-divider {
        margin: 2rem 0;
        border-bottom: 1px solid #e0e0e0;
    }

    /* Override default streamlit spacing */
    .element-container {
        margin-bottom: 0 !important;
    }

    /* Custom styling for iframes */
    iframe {
        border: none !important;
        background-color: transparent !important;
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.8rem;
        }
        .sub-header {
            font-size: 1.3rem;
        }
        .category-card {
            padding: 1rem;
        }
        .place-info {
            padding: 0.8rem;
        }
        .place-name {
            font-size: 1.2rem;
        }
        .category-header {
            font-size: 1.4rem;
        }
    }
</style>
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
        df = pd.read_csv('data/processed/tourism_with_images.csv')
        return df
    except FileNotFoundError:
        try:
            # Try alternative path
            df = pd.read_csv('data/processed/tourism_with_images.csv')
            return df
        except FileNotFoundError:
            # Fallback to basic tourism data
            st.warning(
                "File tourism_with_images.csv tidak ditemukan. Menggunakan data dasar.")
            df = pd.read_csv('data/processed/tourism_processed.csv')
            return df


def get_place_images(place):
    """Get image URLs for a place."""
    if 'image_urls' in place and place['image_urls']:
        # Split by | to get multiple images
        image_urls = place['image_urls'].split('|')
        return image_urls
    # Return a placeholder if no images
    return ["https://via.placeholder.com/800x400?text=Tidak+Ada+Gambar"]


def render_place_card(place):
    """Render a place card with image outside expander."""
    place_name = place['Place_Name']
    place_city = place['City']
    place_description = place.get('Description', 'Tidak ada deskripsi.')
    avg_rating = place.get('Avg_Rating', 0)
    rating_count = place.get('Rating_Count', 0)

    # Get image URLs - mengambil gambar dari data
    # tourism_with_images.csv yang sudah diproses
    image_urls = get_place_images(place)

    main_image = image_urls[0] if image_urls else "https://desmacenter.com/assets/pages/img/works/informasi-menyambut%20wonderful%20indonesia-post_1553164416_logo_wonderful_indonesia.jpg"

    # Membuat card untuk tempat wisata
    st.markdown(f"""
        <div class="place-card-wrapper">
            <img src="{main_image}" class="place-image" alt="{place_name}">
            <div class="place-info">
                <div class="place-name">{place_name}</div>
                <div class="place-location">📍 {place_city}</div>
                <div class="place-rating" style="color: #ff6b35; font-weight: 600; margin-bottom: 0.5rem;" 
                     title="Rating dari pengunjung dengan profil serupa">
                    Rating dari profil serupa: ⭐ {avg_rating:.1f} /5
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Menampilkan deskripsi tempat wisata
    with st.expander("Lihat Deskripsi " + place_name):
        st.markdown(
            f'<div class="place-description">{place_description}</div>', unsafe_allow_html=True)


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
        'Taman Hiburan': 'Taman hiburan seperti taman kota, taman rekreasi, dan tempat hiburan.',
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


def custom_warning(message):
    """Custom warning message that's not affected by theme."""
    st.markdown(f"""
    <div class="custom-warning">
        {message}
    </div>
    """, unsafe_allow_html=True)


def render_header():
    """Render the application header."""
    st.markdown("<h1 class='main-header'>Indonesia Tourism Recommender</h1>",
                unsafe_allow_html=True)
    st.markdown(
        """
        <p style='text-align: center; font-size: 1.2rem;'>
        Temukan destinasi wisata sesuai preferensi dan gaya perjalananmu!
        </p>
        """,
        unsafe_allow_html=True
    )


def render_about():
    """Render information about the application."""
    with st.expander("ℹ️ Tentang Aplikasi"):
        st.markdown("""
        🎯 Cara Kerja Aplikasi
                    
        **Indonesia Tourism Recommender** adalah aplikasi rekomendasi wisata yang menggunakan:
        1. **Content-based Filtering**: Merekomendasikan destinasi berdasarkan kategori dan karakteristik objek wisata
        2. **Collaborative Filtering**: Menggunakan pola preferensi dari pengguna lain dengan profil serupa
        3. **Context-aware Filtering**: Mempertimbangkan konteks perjalanan untuk rekomendasi yang lebih personal

        Algoritma cosine similarity digunakan untuk menghitung kesesuaian antara profil pengguna dengan pola preferensi
        yang telah diidentifikasi, serta memberikan bobot tambahan berdasarkan tipe perjalanan yang dipilih.
       
        📊 Hasil Rekomendasi    
                                    
        Aplikasi menampilkan semua kategori wisata yang diurutkan berdasarkan tingkat kesesuaian dengan profil dan konteks 
        perjalanan Anda. Setiap kategori menunjukkan skor final dan menampilkan 3 objek wisata terbaik yang diurutkan berdasarkan 
        rating tertinggi dari wisatawan dengan profil demografis serupa.
        """)


def render_user_profile_form():
    """Render the user profile form."""
    st.markdown("<h2 class='sub-header'>👤 Profil User</h2>",
                unsafe_allow_html=True)

    with st.form("user_profile_form"):
        st.markdown(
            "<p>Isi profil Anda untuk mendapatkan rekomendasi</p>", unsafe_allow_html=True)

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
            st.caption("""
            **Detail kelompok usia:**
            Teen/College (18-22 tahun);
            Young Adult (23-27 tahun);
            Adult (28-32 tahun);
            Mature Adult (di atas 32 tahun)
            """)

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
        submitted = st.form_submit_button(
            "Dapatkan Rekomendasi", use_container_width=True)
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
                        n_categories=6, n_places_per_category=3
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
                                place['image_urls'] = matching_place.iloc[0].get(
                                    'image_urls', '')
                                place['Category'] = category_rec['category']

                    st.session_state.recommendations = recommendations
                    st.session_state.show_recommendations = True

                # Show custom success message
                custom_success(
                    "Rekomendasi berhasil dibuat! Silakan lihat di bawah.")
            else:
                custom_error("Mohon lengkapi semua profil user.")
        


def render_recommendations():
    """Render the recommendations."""
    if not st.session_state.show_recommendations or not st.session_state.recommendations:
        return

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    st.markdown("<h2 class='sub-header'>🎯 Rekomendasi Wisata Untukmu</h2>",
                unsafe_allow_html=True)

    # User profile summary
    user_profile = st.session_state.user_profile
    with st.expander("👤 Profil Pengunjung", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Jenis Kelamin:** {user_profile['gender']}")
            st.info(
                f"**Umur:** {user_profile['age']} ({user_profile['age_group']})")
        with col2:
            st.info(f"**Kota Tujuan:** {user_profile['city']}")
            st.info(f"**Tipe Perjalanan:** {user_profile['trip_type']}")
        

    # Recommendations
    for recommendation in st.session_state.recommendations:
        category = recommendation['category']
        score = recommendation.get('score', {})
        places = recommendation['places']
        places_found = recommendation.get('places_found', 0)
        places_requested = recommendation.get('places_requested', 3)

        # Get values for each component
        collaborative_score = score.get('collaborative_score', 0.0)
        context_score = score.get('context_score', 0.0)
        final_score = score.get('final_score', 0.0)
        similarity = score.get('similarity', 0.0)

        # Menampilkan hasil scoring dengan terminologi yang diperbaiki
        st.markdown(
            f"""
            <div class='category-card' style='border-left: 5px solid {get_category_color(category)};'>
            <h3 class='category-header'>
                {get_category_icon(category)} {category}
                <span style='font-size: 1rem; color: #666; margin-left: 10px; font-weight: normal;'>
                Final Score: {final_score:.1f}
                </span>
            </h3>
            <div style='margin-bottom: 1rem; font-size: 0.9rem;'>
                <div style='display: flex; gap: 15px; margin-bottom: 0.5rem;'>
                <span style='background: #e3f2fd; color: #1976d2; padding: 4px 10px; border-radius: 12px;'>
                    📊 Content-Based: {similarity:.3f}
                </span>
                <span style='background: #e8f5e8; color: #2e7d32; padding: 4px 10px; border-radius: 12px;'>
                    👥 Popularity Weight: {collaborative_score:.0f}
                </span>
                <span style='background: #fff3e0; color: #f57c00; padding: 4px 10px; border-radius: 12px;'>
                    🧭 Trip Type Weight: {context_score:.0f}
                </span>
                </div>
                <div style='font-size: 0.8em; color: #666; font-style: italic;'>
                * Final Score = Popularity Weight ({collaborative_score:.0f}) + Trip Type Weight ({context_score:.0f}) = {final_score:.1f}
                </div>
            </div>
            <p>{get_category_description(category)}</p>
            </div>
            """, unsafe_allow_html=True)

        # Tampilkan pesan jika data objek wisata terbatas
        if places_found < places_requested:
            if places_found == 0:
                custom_warning(
                    f"⚠️ Tidak ditemukan objek wisata untuk kategori {category} di {user_profile['city']}. "
                    f"Silakan coba kota lain atau lihat kategori lainnya."
                )
            else:
                custom_info(
                    f"ℹ️ Karena data objek wisata {category} di {user_profile['city']} terbatas, "
                    f"hanya menampilkan {places_found} dari {places_requested} objek wisata yang diminta."
                )

        # Tampilkan rekomendasi objek wisata
        if len(places) > 0:
            # Create columns for place cards - always use 3 columns or fewer if not enough places
            use_columns = min(3, len(places))
            cols = st.columns(use_columns)

            # Render place cards in columns
            for j, place in enumerate(places):
                with cols[j % use_columns]:
                    render_place_card(place)


def main():
    """Main application."""
    initialize_session_state()
    render_header()
    render_about()
    render_user_profile_form()
    render_recommendations()


if __name__ == "__main__":
    main()
