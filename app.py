import streamlit as st
import pandas as pd

# --- 1. DATA LOADING ---
def load_data():
    sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTDcviwtkVjuk2SZc9Ma4lxdRYAesg6vcHkVsoZwmmQAZ58LBP_hLGvjUDg5wziX7M6IAIHvF9N1yuU/pub?gid=91396847&single=true&output=csv"
    try:
        df = pd.read_csv(sheet_url)
        df['Total Tuition Cost (USD)'] = df['Total Tuition Cost (USD)'].replace('[\$,]', '', regex=True).astype(float)
        return df
    except Exception as e:
        st.error(f"Data Sync Error: {e}")
        return None

# --- 2. LOGIC ENGINE ---
def get_recommendations(df, user_input):
    results = []
    for index, row in df.iterrows():
        score = 0
        match_flags = []
        if user_input['type'] != "N/A":
            if row['Diploma Type'] == user_input['type']:
                score += 35
                match_flags.append("🎯 Goal Match")
            else: continue
        if user_input['mode'] != "N/A" and row['Delivery Mode'] == user_input['mode']:
            score += 15
            match_flags.append("💻 Mode Match")
        if user_input['country'] != "N/A" and row['Country'] == user_input['country']:
            score += 20
            match_flags.append("🌍 Country Match")
        
        cost = row['Total Tuition Cost (USD)']
        tier = user_input['tier']
        in_tier = False
        if tier == "Tier 1 ($0-$3k)" and cost <= 3000: in_tier = True
        elif tier == "Tier 2 ($3k-$7k)" and 3000 < cost <= 7000: in_tier = True
        elif tier == "Tier 3 ($7k-$12k)" and 7000 < cost <= 12000: in_tier = True
        elif tier == "Tier 4 ($12k+)" and cost > 12000: in_tier = True
        
        if in_tier:
            score += 30
            match_flags.append("💰 Budget Match")
        elif tier != "N/A": score -= 5
        
        score += (row['Visa Success Score'] * 3)
        results.append({
            "Institution": row['Institution Name'], "Program": row['Diploma Title'],
            "Cost": f"${int(cost):,}", "Country": row['Country'],
            "Visa": f"{row['Visa Success Score']}/10", "Duration": row['Duration (Months)'],
            "Intake": row['Intake Months'], "Requirements": row['Entry Requirements'],
            "Score": score, "Relevancy": ", ".join(match_flags)
        })
    return sorted(results, key=lambda x: x['Score'], reverse=True)

# --- 3. PREMIUM UI ---
def main():
    st.set_page_config(page_title="EdPro Navigator", layout="wide", page_icon="🛡️")

    # Custom "Premium" CSS
    st.markdown("""
        <style>
        .stApp { background-color: #FFFFFF; }
        .main-header { font-size: 42px; font-weight: 800; color: #1E3A8A; text-align: center; margin-bottom: 0px; }
        .sub-header { font-size: 18px; color: #64748B; text-align: center; margin-bottom: 40px; }
        div[data-testid="stMetricValue"] { color: #1E3A8A; font-size: 24px; }
        .stButton>button { width: 100%; border-radius: 8px; background-color: #1E3A8A; color: white; height: 3em; font-weight: bold; }
        .stExpander { border: 1px solid #E2E8F0; border-radius: 12px; background-color: #F8FAFC !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<p class="main-header">🛡️ EdPro AI Navigator</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Internal Consultant Decision Engine — v1.0 Live</p>', unsafe_allow_html=True)

    df = load_data()
    if df is None: return

    # --- MAIN SCREEN INPUTS (GRID LAYOUT) ---
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        with col1: in_type = st.selectbox("🎯 Academic Goal", ["N/A", "Bridge", "Work-Ready"])
        with col2: in_country = st.selectbox("🌍 Preferred Country", ["N/A"] + sorted(df['Country'].unique().tolist()))
        with col3: in_mode = st.selectbox("💻 Delivery Mode", ["N/A", "Offline", "Online", "Hybrid"])
        with col4: in_tier = st.selectbox("💰 Budget Tier", ["N/A", "Tier 1 ($0-$3k)", "Tier 2 ($3k-$7k)", "Tier 3 ($7k-$12k)", "Tier 4 ($12k+)"])

    st.write(" ") # Spacer
    if st.button("Generate Tailored Recommendations"):
        recs = get_recommendations(df, {'type': in_type, 'country': in_country, 'mode': in_mode, 'tier': in_tier})
        
        if recs:
            st.markdown(f"### Found {len(recs)} Optimized Pathways")
            for r in recs[:5]:
                with st.expander(f"✨ {r['Institution']} — {r['Program']}"):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Tuition", r['Cost'])
                    c2.metric("Visa Safety", r['Visa'])
                    c3.metric("Duration", f"{r['Duration']} Mo")
                    c4.metric("Location", r['Country'])
                    st.divider()
                    st.write(f"📅 **Intakes:** {r['Intake']} | 📝 **Requirements:** {r['Requirements']}")
                    st.caption(f"**Relevancy Factors:** {r['Relevancy']}")
        else:
            st.warning("No matches found. Please adjust filters.")

if __name__ == "__main__":
    main()