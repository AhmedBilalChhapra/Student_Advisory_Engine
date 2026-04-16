import streamlit as st
import pandas as pd

# --- 1. DATA LOADING ---
def load_data():
    sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTDcviwtkVjuk2SZc9Ma4lxdRYAesg6vcHkVsoZwmmQAZ58LBP_hLGvjUDg5wziX7M6IAIHvF9N1yuU/pub?gid=91396847&single=true&output=csv"
    try:
        df = pd.read_csv(sheet_url)
        # Convert cost to numeric for logic
        df['Total Tuition Cost (USD)'] = df['Total Tuition Cost (USD)'].replace('[\$,]', '', regex=True).astype(float)
        return df
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return None

# --- 2. LOGIC ENGINE ---
def get_recommendations(df, user_input):
    results = []
    for index, row in df.iterrows():
        score = 0
        match_flags = []
        
        # Hard Filter for Goal
        if user_input['type'] != "N/A":
            if row['Diploma Type'] == user_input['type']:
                score += 35
                match_flags.append("Goal Match")
            else: continue
            
        # Matches
        if user_input['mode'] != "N/A" and row['Delivery Mode'] == user_input['mode']:
            score += 15
            match_flags.append("Mode")
        if user_input['country'] != "N/A" and row['Country'] == user_input['country']:
            score += 20
            match_flags.append("Country")
        
        # Budget Tiering
        cost = row['Total Tuition Cost (USD)']
        tier = user_input['tier']
        in_tier = False
        if tier == "Tier 1 ($0-$3k)" and cost <= 3000: in_tier = True
        elif tier == "Tier 2 ($3k-$7k)" and 3000 < cost <= 7000: in_tier = True
        elif tier == "Tier 3 ($7k-$12k)" and 7000 < cost <= 12000: in_tier = True
        elif tier == "Tier 4 ($12k+)" and cost > 12000: in_tier = True
        
        if in_tier:
            score += 30
            match_flags.append("Budget")
        elif tier != "N/A": score -= 5
        
        score += (row['Visa Success Score'] * 3)
        
        results.append({
            "Institution": row['Institution Name'], "Program": row['Diploma Title'],
            "Cost": f"${int(cost):,}", "Country": row['Country'],
            "Visa": f"{row['Visa Success Score']}/10", "Duration": row['Duration (Months)'],
            "Intake": row['Intake Months'], "Requirements": row['Entry Requirements'],
            "Score": score, "Factors": ", ".join(match_flags)
        })
    return sorted(results, key=lambda x: x['Score'], reverse=True)

# --- 3. THE PREMIUM INTERFACE ---
def main():
    st.set_page_config(page_title="EdPro Navigator", layout="wide", page_icon="🛡️")

    # CUSTOM CSS: EdPro Navy Theme + High Visibility
    st.markdown("""
        <style>
        /* Force Background to EdPro Navy */
        .stApp { 
            background-color: #1E3A8A !important; 
        }
        
        /* Force All Text to White */
        h1, h2, h3, p, span, label, .stMarkdown { 
            color: #FFFFFF !important; 
        }

        /* Styling Dropdown Labels specifically for visibility */
        .stSelectbox label p {
            color: #FFFFFF !important;
            font-size: 18px !important;
            font-weight: bold !important;
        }

        /* Search Button Styling */
        .stButton>button { 
            width: 100%; 
            border-radius: 10px; 
            background-color: #FFFFFF; 
            color: #1E3A8A !important; 
            height: 3.5em; 
            font-weight: bold; 
            font-size: 18px; 
            border: none;
            margin-top: 25px;
        }
        .stButton>button:hover {
            background-color: #E2E8F0;
            color: #1E3A8A !important;
        }

        /* Results Card Background */
        .stExpander {
            background-color: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            border-radius: 12px;
        }
        
        /* Metric values inside cards */
        div[data-testid="stMetricValue"] {
            color: #FFFFFF !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Title Section
    st.markdown("<h1 style='text-align: center; margin-bottom: 0px;'>🛡️ EdPro AI Navigator</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2em; opacity: 0.8; margin-bottom: 50px;'>Internal Consultant Decision Support Engine</p>", unsafe_allow_html=True)

    df = load_data()
    if df is None: return

    # --- CENTERED 4-OPTION INPUT LINE ---
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        with col1: in_type = st.selectbox("🎯 Academic Goal", ["N/A", "Bridge", "Work-Ready"])
        with col2: in_country = st.selectbox("🌍 Country", ["N/A"] + sorted(df['Country'].unique().tolist()))
        with col3: in_mode = st.selectbox("💻 Mode", ["N/A", "Offline", "Online", "Hybrid"])
        with col4: in_tier = st.selectbox("💰 Budget Tier", ["N/A", "Tier 1 ($0-$3k)", "Tier 2 ($3k-$7k)", "Tier 3 ($7k-$12k)", "Tier 4 ($12k+)"])

    # Center Button
    _, mid_col, _ = st.columns([1, 1, 1])
    with mid_col:
        search_clicked = st.button("RUN MATCHING ENGINE")

    if search_clicked:
        recs = get_recommendations(df, {'type': in_type, 'country': in_country, 'mode': in_mode, 'tier': in_tier})
        
        if recs:
            st.markdown("---")
            st.markdown("### 🏆 Optimized Pathway Recommendations")
            for r in recs[:5]:
                with st.expander(f"✨ {r['Institution']} — {r['Program']}"):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Tuition", r['Cost'])
                    c2.metric("Visa Safety", r['Visa'])
                    c3.metric("Duration", f"{r['Duration']} Mo")
                    c4.metric("Location", r['Country'])
                    st.write(f"📅 **Intakes:** {r['Intake']} | 📝 **Requirements:** {r['Requirements']}")
                    st.caption(f"**Factors:** {r['Factors']}")
        else:
            st.warning("No matches found. Try setting more options to N/A.")

if __name__ == "__main__":
    main()
