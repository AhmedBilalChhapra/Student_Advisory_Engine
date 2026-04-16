import streamlit as st
import pandas as pd

# --- 1. DATA LOADING ---
def load_data():
    sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTDcviwtkVjuk2SZc9Ma4lxdRYAesg6vcHkVsoZwmmQAZ58LBP_hLGvjUDg5wziX7M6IAIHvF9N1yuU/pub?gid=91396847&single=true&output=csv"
    try:
        df = pd.read_csv(sheet_url)
        # Clean currency
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
        if user_input['type'] != "N/A":
            if row['Diploma Type'] == user_input['type']:
                score += 35
                match_flags.append("Goal Match")
            else: continue
        if user_input['mode'] != "N/A" and row['Delivery Mode'] == user_input['mode']:
            score += 15
            match_flags.append("Mode")
        if user_input['country'] != "N/A" and row['Country'] == user_input['country']:
            score += 20
            match_flags.append("Country")
        
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

# --- 3. UI LAYOUT ---
def main():
    st.set_page_config(page_title="EdPro Navigator", layout="centered", page_icon="🛡️")

    # CUSTOM CSS: Midnight Blue + Gold Button + Ghosting Fix
    st.markdown("""
        <style>
        /* Midnight Blue Background & Text Visibility Fix */
        .stApp { 
            background-color: #0A192F !important; 
            opacity: 1 !important;
        }
        
        /* Eliminate any background 'ghosting' by hiding default elements */
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        h1, h2, h3, p, span, label, .stMarkdown { 
            color: #FFFFFF !important; 
            text-shadow: none !important; /* Fixes potential ghosting look */
        }

        .stSelectbox label p {
            color: #FFFFFF !important;
            font-size: 20px !important;
            font-weight: bold !important;
        }

        /* PREMIUM GOLD BUTTON (Matching Agent) */
        .stButton>button { 
            width: 100%; 
            border-radius: 12px; 
            background-color: #FFB800; /* Gold/Amber */
            color: #0A192F !important; 
            height: 4.2em; 
            font-weight: 800; 
            font-size: 22px; 
            border: none;
            margin-top: 30px;
            transition: all 0.3s ease;
            box-shadow: 0px 4px 20px rgba(255, 184, 0, 0.3);
        }
        .stButton>button:hover {
            background-color: #FFD363;
            transform: translateY(-2px);
            box-shadow: 0px 6px 25px rgba(255, 184, 0, 0.5);
        }

        /* Clean Results Expanders */
        .stExpander {
            background-color: rgba(255, 255, 255, 0.08) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 15px;
            margin-bottom: 15px;
        }
        
        div[data-testid="stMetricValue"] { color: #FFB800 !important; }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("<h1 style='text-align: center;'>🛡️ EdPro AI Navigator</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.1em; opacity: 0.7; margin-bottom: 40px;'>Internal Consultant Decision Support System</p>", unsafe_allow_html=True)

    df = load_data()
    if df is None: return

    # --- VERTICAL STACK INPUTS ---
    _, center_col, _ = st.columns([1, 4, 1])
    
    with center_col:
        in_type = st.selectbox("🎯 Academic Goal", ["N/A", "Bridge", "Work-Ready"])
        in_country = st.selectbox("🌍 Preferred Country", ["N/A"] + sorted(df['Country'].unique().tolist()))
        in_mode = st.selectbox("💻 Delivery Mode", ["N/A", "Offline", "Online", "Hybrid"])
        in_tier = st.selectbox("💰 Budget Tier", ["N/A", "Tier 1 ($0-$3k)", "Tier 2 ($3k-$7k)", "Tier 3 ($7k-$12k)", "Tier 4 ($12k+)"])
        
        search_clicked = st.button("RUN MATCHING AGENT")

    # --- RESULTS ---
    if search_clicked:
        recs = get_recommendations(df, {'type': in_type, 'country': in_country, 'mode': in_mode, 'tier': in_tier})
        
        if recs:
            st.markdown("<br><h3 style='text-align: center;'>🏆 Top Recommendations</h3>", unsafe_allow_html=True)
            for r in recs[:5]:
                with st.expander(f"✨ {r['Institution']} — {r['Program']}"):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Tuition", r['Cost'])
                    c2.metric("Visa Safety", r['Visa'])
                    c3.metric("Duration", f"{r['Duration']} Mo")
                    c4.metric("Location", r['Country'])
                    st.divider()
                    st.write(f"📅 **Intakes:** {r['Intake']} | 📝 **Requirements:** {r['Requirements']}")
        else:
            st.warning("No matches found. Try relaxing the filters.")

if __name__ == "__main__":
    main()
    
