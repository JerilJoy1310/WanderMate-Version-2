import streamlit as st
import folium
from streamlit.components.v1 import html
from geopy.geocoders import Nominatim
import pandas as pd
import plotly.express as px
from forex_python.converter import CurrencyRates
from datetime import datetime
import openai
import os

# Page setup
st.set_page_config(page_title="WanderMate Travel Planner", layout="centered")
st.title("WanderMate - Smart Travel Planner")

# Input form
with st.form("trip_form"):
    origin = st.text_input("Origin City", "New Delhi")
    destination = st.text_input("Destination City, Country", "Paris, France")
    trip_type = st.selectbox("Trip Type", ["Honeymoon", "Solo", "Family", "Adventure"])
    dep_date = st.date_input("Departure Date", datetime.today())
    ret_date = st.date_input("Return Date", datetime.today())
    budget = st.number_input("Total Budget", min_value=100.0, step=50.0, value=1000.0)
    currency = st.selectbox("Currency", ["USD", "INR", "EUR", "GBP", "JPY"])
    taxi_choice = st.checkbox("Include taxi from airport")
    submitted = st.form_submit_button("Plan My Trip")

if submitted:
    # Geocode destination
    geolocator = Nominatim(user_agent="wandermate_v2")
    loc = geolocator.geocode(destination)
    m = folium.Map(location=[loc.latitude, loc.longitude], zoom_start=12)
    folium.Marker([loc.latitude, loc.longitude], popup=destination).add_to(m)

    st.subheader("Destination Map")
    html(m._repr_html_(), height=400)

    # Mock flight options
    flights = pd.DataFrame([
        {'From': origin, 'To': destination, 'Airline': 'Air Demo',   'Stops': 'Non-stop', 'Price (USD)': 800, 'Duration': '9h'},
        {'From': origin, 'To': destination, 'Airline': 'FlySample',  'Stops': '1 Stop',   'Price (USD)': 650, 'Duration': '12h'},
        {'From': origin, 'To': destination, 'Airline': 'TestWings',  'Stops': '2 Stops',  'Price (USD)': 580, 'Duration': '15h'},
    ])
    st.subheader("Available Flights")
    st.dataframe(flights)

    # Mock hotel options
    hotels = pd.DataFrame([
        {'Hotel': 'Dream Stay',     'Rating': 4.7, 'Nightly Rate (USD)': 220},
        {'Hotel': 'Comfort Suites', 'Rating': 4.3, 'Nightly Rate (USD)': 180},
        {'Hotel': 'Budget Inn',     'Rating': 4.0, 'Nightly Rate (USD)': 140},
    ])
    st.subheader("Hotel Options")
    st.dataframe(hotels)

    # Flight price trend
    trend = pd.DataFrame({
        'Date': pd.date_range(start=datetime.today().date(), periods=7),
        'Avg Fare (USD)': [800, 780, 820, 770, 790, 760, 805]
    })
    st.subheader("7-Day Flight Price Trend")
    fig = px.line(trend, x='Date', y='Avg Fare (USD)', title='Flight Price Trend')
    st.plotly_chart(fig)

    # Currency conversion
    c = CurrencyRates()
    try:
        rate = c.get_rate('USD', currency)
    except:
        st.warning("Currency conversion failed. Using default 1:1 rate.")
        rate = 1.0
    budget_usd = budget / rate
    st.success(f"Budget in USD: ${budget_usd:.2f}")

    # Budget estimation
    nights = (pd.to_datetime(ret_date) - pd.to_datetime(dep_date)).days
    avg_hotel_cost = hotels['Nightly Rate (USD)'].mean() * max(nights, 1)
    best_flight_price = flights['Price (USD)'].min()
    taxi_cost = 50 if taxi_choice else 0
    total_estimate_usd = avg_hotel_cost + best_flight_price + taxi_cost
    remaining_budget = budget_usd - total_estimate_usd

    st.subheader("Estimated Budget Breakdown")
    st.markdown(f"""
    - Flight: ${best_flight_price}  
    - Hotel ({nights} nights average): ${avg_hotel_cost:.2f}  
    - Taxi: ${taxi_cost}  
    - Total Estimate: ${total_estimate_usd:.2f}  
    - Remaining Budget: ${remaining_budget:.2f}
    """)

    # OpenAI travel tips
    st.subheader("AI Travel Tips")
    openai.api_key = os.getenv("OPENAI_API_KEY", "sk-your-openai-key")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": f"Give 3 practical travel tips for a {trip_type} trip from {origin} to {destination}."}
            ]
        )
        tips = response.choices[0].message.content
        st.write(tips)
    except Exception as e:
        st.error("OpenAI API failed. Please check your key or network.")
