import os
import sqlite3
from io import BytesIO
import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# -------------------- Page Setup --------------------
st.set_page_config(page_title="TravelPulse Sri Lanka", layout="wide")

# -------------------- Path Setup --------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "Assets")

reviews_xlsx = os.path.join(BASE_DIR, "Final_Cleaned_Tourist_Reviews.xlsx")
activities_csv = os.path.join(BASE_DIR, "Rural_Activities_Expanded.csv")

ITINERARY_MAP = os.path.join(ASSETS_DIR, "sri-lankan-travel-map.jpg")
ABOUT_IMG = os.path.join(ASSETS_DIR, "511564047_3690789407732651_2711082666974816646_n.jpg")
ABOUT_SIDE_IMG = os.path.join(ASSETS_DIR, "jaffna-aesthetic.jpeg")

# -------------------- Load Excel Data --------------------
@st.cache_data
def load_excel_data():
    try:
        df = pd.read_excel(reviews_xlsx)
    except FileNotFoundError:
        st.error("⚠ Final_Cleaned_Tourist_Reviews.xlsx not found.")
        df = pd.DataFrame()
    return df

reviews_df = load_excel_data()

# -------------------- Load Activities Data --------------------
@st.cache_data
def load_activities_data():
    try:
        df = pd.read_csv(activities_csv)  # CSV must use commas
        df.columns = df.columns.str.strip()  # remove any hidden spaces
        df['Activity Category'] = df['Activity Category'].astype(str).str.title().str.strip()
        df['Activity'] = df['Activity'].astype(str).str.strip()
        df['District'] = df['District'].astype(str).str.title().str.strip()
    except FileNotFoundError:
        st.error("⚠ Rural_Activities_Expanded.csv not found.")
        df = pd.DataFrame()
    return df

activities_df = load_activities_data()

# -------------------- Data Cleaning --------------------
if not reviews_df.empty:
    reviews_df.columns = reviews_df.columns.str.strip()
    reviews_df['Cleaned_Review'] = reviews_df['Cleaned_Review'].astype(str)
    reviews_df['Sentiment'] = reviews_df['Sentiment'].astype(str).str.title()
    reviews_df['District'] = reviews_df['District'].astype(str).str.title().str.strip()
    reviews_df['Destination'] = reviews_df['Destination'].astype(str).str.title().str.strip()
    reviews_df = reviews_df[reviews_df['Sentiment'].isin(['Positive', 'Neutral', 'Negative'])]
    reviews_df['Latitude'] = pd.to_numeric(reviews_df['Latitude'], errors='coerce')
    reviews_df['Longitude'] = pd.to_numeric(reviews_df['Longitude'], errors='coerce')

# -------------------- Database Setup --------------------
conn = sqlite3.connect(os.path.join(BASE_DIR, "tourism.db"))
cursor = conn.cursor()
cursor.execute("DROP TABLE IF EXISTS reviews")
conn.commit()

if not reviews_df.empty:
    reviews_df.to_sql("reviews", conn, if_exists="replace", index=False)

# -------------------- Navbar as Boxes --------------------
pages = ["Home", "Explore", "Itinerary", "About"]

# Initialize page in session state
if "page" not in st.session_state:
    st.session_state.page = "Home"

# Create a row of buttons for navigation
cols = st.columns(len(pages))
for i, page in enumerate(pages):
    if cols[i].button(page):
        st.session_state.page = page

# Highlight the selected page using custom CSS
st.markdown(
    f"""
    <style>
    .stButton button {{
        width: 100%;
        padding: 15px;
        font-size: 1rem;
        border-radius: 10px;
        margin-bottom: 5px;
        background-color: #f0f0f0;
        transition: all 0.3s ease;
    }}
    .stButton button:hover {{
        background-color: #4CAF50;
        color: white;
    }}
    .stButton button:focus {{
        outline: 3px solid #4CAF50;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------- General CSS --------------------
st.markdown(
    """
    <style>
    h1, h2, h3, h4, h5, h6 {
        font-weight: bold !important;
    }
    .stMarkdown p {
        font-size: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------- Home Page --------------------
if st.session_state.page == "Home":
    home_bg_url = "https://ceylonsrilankan.com/_next/image?url=%2Fimg%2Fdemodara-bridge.jpeg&w=3840&q=75"
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url('{home_bg_url}');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .home-overlay {{
            background: rgba(0, 0, 0, 0.4);
            padding: 150px 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .home-overlay h1, .home-overlay p {{
            color: white !important;
            text-shadow: 2px 2px 8px rgba(0,0,0,0.7);
        }}
        </style>
        <div class="home-overlay">
            <h1 style="font-size:4rem;">🌏 TravelPulse Sri Lanka</h1>
            <p style="font-size:1.5rem;">
            Discover destinations through data-driven insights and plan your journey smartly.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

# -------------------- Explore Page --------------------
elif st.session_state.page == "Explore":
    st.title("🔍 Explore Sentiment Insights")
    conn = sqlite3.connect(os.path.join(BASE_DIR, "tourism.db"))
    reviews = pd.read_sql("SELECT * FROM reviews", conn)
    conn.close()

    if not reviews.empty:
        st.sidebar.header("🔎 Filter Reviews")
        filter_mode = st.sidebar.selectbox("Filter Mode", ["Show All", "Select Sentiment", "Select District"])
        filtered_df = reviews.copy()

        if filter_mode == "Select Sentiment":
            sentiment_choice = st.sidebar.radio("Choose Sentiment", ["Positive", "Neutral", "Negative"])
            filtered_df = reviews[reviews["Sentiment"] == sentiment_choice]
        elif filter_mode == "Select District":
            district_choice = st.sidebar.selectbox("Choose District", sorted(reviews["District"].dropna().unique()))
            filtered_df = reviews[reviews["District"] == district_choice]

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Reviews", len(reviews))
        col2.metric("Unique Destinations", reviews['Destination'].nunique())
        col3.metric("Districts Covered", reviews['District'].nunique())
        st.markdown("---")

        urban_districts = ["Colombo", "Kandy", "Galle", "Jaffna", "Negombo", "Matara", "Kurunegala"]
        reviews['Area_Type'] = reviews['District'].apply(lambda x: 'Urban' if x in urban_districts else 'Rural')
        filtered_df['Area_Type'] = filtered_df['District'].apply(lambda x: 'Urban' if x in urban_districts else 'Rural')

        # Pie chart
        area_counts = filtered_df['Area_Type'].value_counts().reset_index()
        area_counts.columns = ['Area Type', 'Review Count']
        fig_area = px.pie(area_counts, names='Area Type', values='Review Count', hole=0.4,
                          color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_area.update_traces(textinfo='percent+label')
        st.subheader("📊 Review Distribution by Area")
        st.plotly_chart(fig_area, use_container_width=True)

        # Top Positive Rural Destinations
        st.subheader("🌟 Top Positive Rural Destinations")
        top_rural = filtered_df[(filtered_df['Area_Type'] == 'Rural') & (filtered_df['Sentiment'] == 'Positive')]
        top_rural_counts = top_rural['Destination'].value_counts().head(10).reset_index()
        top_rural_counts.columns = ['Destination', 'Positive Review Count']
        fig_top_rural = px.bar(top_rural_counts, x='Destination', y='Positive Review Count', color='Positive Review Count',
                               color_continuous_scale='viridis')
        st.plotly_chart(fig_top_rural, use_container_width=True)

        # Word Clouds
        st.subheader("☁ Word Cloud by Sentiment")
        def generate_wordcloud(sentiment):
            text = " ".join(filtered_df[filtered_df['Sentiment'] == sentiment]['Cleaned_Review'].dropna())
            return WordCloud(width=800, height=300, background_color='white').generate(text)

        tabs = st.tabs(['🌟 Positive', '😐 Neutral', '💢 Negative'])
        for i, sentiment in enumerate(['Positive', 'Neutral', 'Negative']):
            with tabs[i]:
                wc = generate_wordcloud(sentiment)
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.imshow(wc, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig)

        # Map
        st.subheader("🗺 Tourist Review Locations by Sentiment")
        map_df = filtered_df.dropna(subset=['Latitude', 'Longitude'])
        if not map_df.empty:
            fig_map = px.scatter_mapbox(
                map_df, lat='Latitude', lon='Longitude', color='Sentiment',
                hover_name='Destination', hover_data={'District': True, 'Cleaned_Review': True},
                zoom=6, height=500,
                color_discrete_map={'Positive': 'green', 'Neutral': 'orange', 'Negative': 'red'}
            )
            fig_map.update_layout(mapbox_style="open-street-map")
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("⚠ No geolocation data available.")

        # Urban vs Rural Sentiment
        st.subheader("📊 Urban vs Rural Sentiment Comparison")
        sentiment_comparison = filtered_df.groupby(['Area_Type', 'Sentiment']).size().reset_index(name='Count')
        fig_urban_rural = px.bar(
            sentiment_comparison,
            x='Sentiment',
            y='Count',
            color='Area_Type',
            barmode='group',
            text='Count',
            color_discrete_map={'Urban': 'blue', 'Rural': 'green'},
            title="Sentiment Comparison: Urban vs Rural Destinations"
        )
        fig_urban_rural.update_layout(xaxis_title="Sentiment", yaxis_title="Number of Reviews", legend_title="Area Type")
        st.plotly_chart(fig_urban_rural, use_container_width=True)

# -------------------- Itinerary Page --------------------
elif st.session_state.page == "Itinerary":
    st.markdown("<h1>🧳 Personalized Travel Itinerary</h1>", unsafe_allow_html=True)
    pdf_bytes = None
    col1, col2 = st.columns([2, 1])

    with col1:
        if not reviews_df.empty and not activities_df.empty:
            with st.form("itinerary_form"):
                num_days = st.slider("🗓 Trip Duration (in days)", 1, 10, 3)
                preferred_district = st.selectbox(
                    "📍 Preferred District", options=["Any"] + sorted(reviews_df['District'].dropna().unique())
                )
                preferred_activity = st.multiselect(
                    "🎯 Preferred Activity Category", options=["Any"] + sorted(activities_df['Activity Category'].dropna().unique())
                )
                start_city = st.text_input("🚐 Start City", "Colombo")
                end_city = st.text_input("🏁 End City", "Kandy")
                submitted = st.form_submit_button("Generate Itinerary")

            if submitted:
                itinerary_df = reviews_df.drop_duplicates(subset=['Destination'])
                if preferred_district != "Any":
                    itinerary_df = itinerary_df[itinerary_df['District'] == preferred_district]
                if preferred_activity and "Any" not in preferred_activity:
                    activity_filtered = activities_df[activities_df['Activity Category'].isin(preferred_activity)]
                else:
                    activity_filtered = activities_df.copy()

                itinerary_df = itinerary_df.merge(
                    activity_filtered[['District', 'Activity Category', 'Activity']], on='District', how='left'
                )

                if start_city:
                    start_row = itinerary_df[itinerary_df['Destination'].str.contains(start_city, case=False)]
                    if not start_row.empty:
                        itinerary_df = pd.concat([start_row, itinerary_df.drop(start_row.index)])
                if end_city:
                    end_row = itinerary_df[itinerary_df['Destination'].str.contains(end_city, case=False)]
                    if not end_row.empty:
                        itinerary_df = pd.concat([itinerary_df.drop(end_row.index), end_row])

                itinerary_df = itinerary_df.reset_index(drop=True)
                destinations_per_day = max(1, len(itinerary_df) // num_days)
                st.markdown("### 🗺 Your Travel Itinerary")
                itinerary_text = ""

                for day in range(num_days):
                    day_plan = itinerary_df.iloc[day * destinations_per_day:(day + 1) * destinations_per_day]
                    if not day_plan.empty:
                        st.markdown(f"<div><h3>📅 Day {day + 1}</h3>", unsafe_allow_html=True)
                        for _, row in day_plan.iterrows():
                            activity_info = f"{row['Activity Category']} - {row['Activity']}" if pd.notna(row['Activity Category']) else "N/A"
                            line = (f"- **Destination:** {row['Destination']} ({row['District']})  \n"
                                    f"  **Sentiment:** {row['Sentiment']}  \n"
                                    f"  **Activity:** {activity_info}")
                            st.markdown(line, unsafe_allow_html=True)
                            itinerary_text += line + "\n"
                        st.markdown("</div>", unsafe_allow_html=True)
                        itinerary_text += "\n"

                # PDF Export
                pdf_buffer = BytesIO()
                c = canvas.Canvas(pdf_buffer, pagesize=letter)
                width, height = letter
                y = height - 50
                for line in itinerary_text.split("\n"):
                    c.drawString(50, y, line)
                    y -= 15
                    if y < 50:
                        c.showPage()
                        y = height - 50
                c.save()
                pdf_bytes = pdf_buffer.getvalue()

            if pdf_bytes:
                st.download_button(
                    label="📥 Download Itinerary as PDF",
                    data=pdf_bytes,
                    file_name="travel_itinerary.pdf",
                    mime="application/pdf"
                )

    with col2:
        st.image(ITINERARY_MAP, width='stretch')

# -------------------- About Page --------------------
elif st.session_state.page == "About":
    col1, col2 = st.columns([2, 1])
    about_text = """
    <h1>🍃 About TravelPulse Sri Lanka</h1>
    <p>
    TravelPulse Sri Lanka is more than just a travel guide; it is a data-driven platform designed to help travelers discover the island in a way that is meaningful, authentic, and sustainable. By applying advanced sentiment analysis to thousands of genuine tourist reviews, TravelPulse reveals what visitors truly value about Sri Lanka, from the vibrant pulse of its bustling cities to the tranquil beauty of its untouched rural landscapes. Every insight is drawn from real experiences, making TravelPulse a trusted companion for travelers who want more than just recommendations — they want journeys that matter.
    </p>
    <p>
    Our mission is to promote responsible tourism that not only creates unforgettable memories for travelers but also strengthens local communities, protects cultural traditions, and safeguards the island’s natural treasures for generations to come. To achieve this, TravelPulse goes beyond being a simple guidebook — it acts as a bridge between travelers and authentic experiences. By highlighting both world-renowned attractions and hidden gems, including rural destinations that are often overlooked, the platform helps distribute tourism more evenly across the island. This approach eases pressure on popular hotspots while also empowering smaller communities and supporting sustainable development, ensuring that travel benefits everyone.
    </p>
    <h3>🌏 Discover Experiences by Category</h3>
    <ul>
        <li><b>Adventure & Outdoor</b> – Hike misty mountain trails, dive into thrilling water sports, embark on safaris, or soar high in a hot air balloon.</li>
        <li><b>Cultural & Historical</b> – Step into the past through temples, colonial landmarks, museums, and traditional cultural performances.</li>
        <li><b>Religious & Spiritual</b> – Find inner peace at sacred Buddhist and Hindu temples, meditation retreats, and pilgrimage sites.</li>
        <li><b>Nature & Scenic</b> – Wander across emerald tea plantations, visit lush botanical gardens and cascading waterfalls, or ride the world-famous scenic train through the highlands.</li>
        <li><b>Beach & Relaxation</b> – Soothe your soul with sun-kissed beaches, spa treatments, or rejuvenating yoga by the ocean.</li>
        <li><b>Food & Culinary</b> – Experience Sri Lanka’s rich flavors with street food tours, immersive cooking classes, and tea-tasting journeys.</li>
        <li><b>Rural & Village Experiences</b> – Connect with authentic lifestyles through village stays, farming, and traditional handicraft workshops.</li>
    </ul>
    <p>
    ✨ With TravelPulse Sri Lanka, every trip becomes more than just a holiday — it is an opportunity to travel with purpose, live like a local, and create memories that leave a lasting impact on both you and the island itself.
    </p>
    """
    with col1:
        st.markdown(about_text, unsafe_allow_html=True)
    with col2:
        st.image(ABOUT_SIDE_IMG, width='stretch')





