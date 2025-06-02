import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Flight Ranking App", layout="wide")

st.title("✈️ Flight Ranking App")
st.markdown("This app uses the **Weighted Product Model (WPM)** to rank flight options based on your preferences.")

with st.sidebar:
    st.header("📂 Upload Your Flight CSV")
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

    st.markdown("---")
    st.header("🧮 Set Weights (Importance)")
    st.caption("Higher weight → more influence in ranking. All weights are normalized.")

    weight_price = st.slider("💰 Price (prefer cheaper)", 0.0, 1.0, 0.2)
    weight_duration = st.slider("🕒 Duration (prefer shorter)", 0.0, 1.0, 0.2)
    weight_days_left = st.slider("📅 Days Left (prefer sooner)", 0.0, 1.0, 0.2)
    weight_stops = st.slider("🛑 Stops (prefer fewer)", 0.0, 1.0, 0.1)
    weight_class = st.slider("💼 Class (prefer Business)", 0.0, 1.0, 0.1)
    weight_dep_time = st.slider("🕓 Departure Time", 0.0, 1.0, 0.1)
    weight_arr_time = st.slider("🕙 Arrival Time", 0.0, 1.0, 0.1)

    st.markdown("---")
    st.header("🕑 Time Preferences")
    st.caption("Assign preference scores (1–5) to time slots. Higher = better.")

    st.markdown("**Departure Time Preferences**")
    dep_slots = ['Early_Morning', 'Morning', 'Afternoon', 'Evening', 'Night']
    dep_time_map = {}
    for slot in dep_slots:
        dep_time_map[slot] = st.slider(f"{slot}", 1, 5, 3, key=f"dep_{slot}")

    st.markdown("**Arrival Time Preferences**")
    arr_time_map = {}
    for slot in dep_slots:
        arr_time_map[slot] = st.slider(f"{slot}", 1, 5, 3, key=f"arr_{slot}")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    stops_map = {'zero': 0, 'one': 1, 'two_or_more': 2}
    df['stops_mapped'] = df['stops'].map(stops_map)

    class_map = {'Economy': 0, 'Business': 1}
    df['class_mapped'] = df['class'].map(class_map)

    df['dep_time_score'] = df['departure_time'].map(dep_time_map)
    df['arr_time_score'] = df['arrival_time'].map(arr_time_map)

    weights = np.array([
        weight_price, weight_duration, weight_days_left,
        weight_stops, weight_class, weight_dep_time, weight_arr_time
    ])
    weights = weights / weights.sum()

    decision_matrix = pd.DataFrame({
        "price": df["price"],
        "duration": df["duration"],
        "days_left": df["days_left"],
        "stops": df["stops_mapped"],
        "class": df["class_mapped"],
        "dep_time": df["dep_time_score"],
        "arr_time": df["arr_time_score"]
    })

    cost_indices = [0, 1, 2, 3]
    benefit_indices = [4, 5, 6]

    norm_matrix = decision_matrix.copy()
    for i, col in enumerate(norm_matrix.columns):
        if i in cost_indices:
            norm_matrix[col] = norm_matrix[col].min() / norm_matrix[col]
        else:
            norm_matrix[col] = norm_matrix[col] / norm_matrix[col].max()

    product_scores = np.prod(norm_matrix ** weights, axis=1)
    df["WPM Score"] = product_scores
    df["Rank"] = df["WPM Score"].rank(ascending=False).astype(int)

    df_sorted = df.sort_values("WPM Score", ascending=False).reset_index(drop=True)

    st.markdown("### 🏆 Top 5 Flight Options")
    top5 = df_sorted.head(5).copy()

    def format_flight(row):
        return (
            f"**✈️ {row['airline']} - {row['flight']}**\n"
            f"- Class: {row['class']}\n"
            f"- Price: ₹{row['price']}\n"
            f"- Duration: {row['duration']} hrs\n"
            f"- Days Left: {row['days_left']}\n"
            f"- Dep: {row['departure_time']} → Arr: {row['arrival_time']}\n"
            f"- Rank: {row['Rank']} | Score: {round(row['WPM Score'], 4)}"
        )

    cols = st.columns(5)
    for i in range(min(5, len(top5))):
        with cols[i]:
            st.markdown(format_flight(top5.iloc[i]))

    st.markdown("### 📄 All Ranked Flights")
    st.dataframe(df_sorted[[
        "Rank", "airline", "flight", "departure_time", "arrival_time",
        "class", "duration", "days_left", "price", "WPM Score"
    ]], use_container_width=True)

else:
    st.warning("⚠️ Please upload a valid flight CSV file to start.")
