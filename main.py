import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Aplikasi Pemeringkat Penerbangan", layout="wide")

st.title("✈️ Aplikasi Pemeringkat Penerbangan")
st.markdown("""
Aplikasi ini menggunakan metode **Weighted Product Model (WPM)** untuk memberikan peringkat pada opsi penerbangan berdasarkan preferensi Anda.

**Langkah-langkah**:
1. Tentukan bobot kriteria yang Anda anggap penting.
2. Atur preferensi waktu keberangkatan dan kedatangan.
3. Lihat hasil peringkat dan pilih opsi terbaik.
""")

try:
    df = pd.read_csv("flights.csv")
except FileNotFoundError:
    st.error("❌ File `flights.csv` tidak ditemukan. Pastikan file tersebut ada di folder yang sama.")
    st.stop()

with st.sidebar:
    st.header("⚙️ Pengaturan Preferensi")

    with st.expander("🎯 Bobot Kriteria"):
        st.markdown("Tentukan seberapa penting setiap kriteria. Total bobot akan dinormalisasi.")
        weight_price = st.slider("💰 Harga (semakin murah semakin baik)", 0.0, 1.0, 0.2)
        weight_duration = st.slider("🕒 Durasi Penerbangan (semakin singkat semakin baik)", 0.0, 1.0, 0.2)
        weight_days_left = st.slider("📅 Sisa Hari Menuju Keberangkatan (semakin cepat semakin baik)", 0.0, 1.0, 0.2)
        weight_stops = st.slider("🛑 Jumlah Transit (semakin sedikit semakin baik)", 0.0, 1.0, 0.1)
        weight_class = st.slider("💼 Kelas Penerbangan (lebih baik jika Business)", 0.0, 1.0, 0.1)
        weight_dep_time = st.slider("🕓 Waktu Keberangkatan (sesuai preferensi Anda)", 0.0, 1.0, 0.1)
        weight_arr_time = st.slider("🕙 Waktu Kedatangan (sesuai preferensi Anda)", 0.0, 1.0, 0.1)

    with st.expander("🕓 Preferensi Waktu Keberangkatan"):
        st.markdown("Berikan skor 1–5 pada tiap slot waktu. Semakin tinggi, semakin disukai.")
        dep_slots = ['Early_Morning', 'Morning', 'Afternoon', 'Evening', 'Night']
        dep_time_map = {}
        for slot in dep_slots:
            dep_time_map[slot] = st.slider(f"{slot}", 1, 5, 3, key=f"dep_{slot}")

    with st.expander("🕘 Preferensi Waktu Kedatangan"):
        st.markdown("Berikan skor 1–5 pada tiap slot waktu. Semakin tinggi, semakin disukai.")
        arr_time_map = {}
        for slot in dep_slots:
            arr_time_map[slot] = st.slider(f"{slot}", 1, 5, 3, key=f"arr_{slot}")

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

if weights.sum() == 0:
    st.error("⚠️ Bobot tidak boleh semuanya 0.")
    st.stop()

weights = weights / weights.sum()  

cost_indices = [0, 1, 2, 3]    
benefit_indices = [4, 5, 6]   

decision_matrix = pd.DataFrame({
    "price": df["price"],
    "duration": df["duration"],
    "days_left": df["days_left"],
    "stops": df["stops_mapped"],
    "class": df["class_mapped"],
    "dep_time": df["dep_time_score"],
    "arr_time": df["arr_time_score"]
})

epsilon = 1e-6
decision_matrix = decision_matrix.replace(0, epsilon)

wpm_matrix = decision_matrix.copy()

for i, col in enumerate(wpm_matrix.columns):
    if i in cost_indices:
        wpm_matrix[col] = wpm_matrix[col] ** (-weights[i])
    else:
        wpm_matrix[col] = wpm_matrix[col] ** (weights[i])

df["Skor WPM"] = wpm_matrix.prod(axis=1)

df["Peringkat"] = df["Skor WPM"].rank(ascending=False).astype(int)

df_sorted = df.sort_values("Skor WPM", ascending=False).reset_index(drop=True)

st.markdown("### 🏆 5 Opsi Penerbangan Terbaik")
top5 = df_sorted.head(5).copy()

def format_flight(row):
    return (
        f"#### ✈️ {row['airline']} - {row['flight']}\n"
        f"- Kelas: {row['class']}\n"
        f"- Harga: ₹{row['price']:,}\n"
        f"- Durasi: {row['duration']} jam\n"
        f"- Sisa Hari: {row['days_left']}\n"
        f"- Transit: {row['stops_mapped']}\n"
        f"- Berangkat: {row['departure_time']} → Tiba: {row['arrival_time']}\n"
        f"- Peringkat: {row['Peringkat']} | Skor: {round(row['Skor WPM'], 4)}"
    )


cols = st.columns(5)
for i in range(min(5, len(top5))):
    with cols[i]:
        st.markdown(format_flight(top5.iloc[i]))

with st.expander("📋 Lihat Semua Opsi Penerbangan Terurut"):
    st.markdown("Berikut adalah daftar lengkap semua penerbangan dengan skor dan peringkat:")
    st.dataframe(df_sorted[[
        "Peringkat", "airline", "flight", "departure_time", "arrival_time",
        "stops_mapped", "class", "duration", "days_left", "price", "Skor WPM"
    ]].rename(columns={"stops_mapped": "stops"}), use_container_width=True)

csv_download = df_sorted.to_csv(index=False)
st.download_button(
    label="📥 Unduh Hasil Peringkat (.csv)",
    data=csv_download,
    file_name="peringkat_penerbangan.csv",
    mime="text/csv"
)
