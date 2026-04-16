import streamlit as st
import pandas as pd

# --- 1. DATA LOADING ---
def load_data():
    sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTDcviwtkVjuk2SZc9Ma4lxdRYAesg6vcHkVsoZwmmQAZ58LBP_hLGvjUDg5wziX7M6IAIHvF9N1yuU/pub?gid=91396847&single=true&output=csv"
    try:
        df = pd.read_csv(sheet_url)
        # Clean currency for logic
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
            
        # Weighted Matches
        if user_input['mode'] != "N/A" and row['Delivery Mode'] == user_input['mode']:
            score += 15
            match_flags.append("Mode")
        if user_input['country'] != "N/A" and row['Country'] == user_input['country']:
            score += 20
            match_flags.append("Country")
        
        # Budget Logic
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

# --- 3. PREMIUM UI ---
def main():
    st.set_page_config(page_title="EdPro Navigator", layout="wide", page_icon="🛡️")

    # Custom CSS for EdPro Brand Identity
    st.markdown("""
        <style>
        /* Background & Text Colors */
        .stApp { background-color: #F8FAFC; } /* Clean light grey background */
        h1 { color: #1E3A8A !important; font-weight: 800; text-align: center; } /* Navy Blue Title */
        .stSelectbox label { color: #1E3A8A !important; font-weight: bold; font-size: 16px; } /* Visible Labels */
        
        /* Centered Button Styling */
        .stButton>button { 
            width: 100%; border-radius: 12px; background-color: #1E3A8A; 
            color: white; height: 3.5em; font-weight: bold; font-size: 18px; 
            border: none; margin-top: 20px;
        }
        .stButton>button:hover { background-color: #172554; color: #FFFFFF; }

        /* Card Styling for Results */
        .stExpander { 
            border: 1px solid #CBD5E1; border-radius: 15px; 
            background-color: #FFFFFF !important; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)

    # Title Section
    st.markdown("<h1>🛡️ EdPro AI Navigator</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B; margin-bottom: 50px;'>Internal Consultant Decision Support Engine</p>", unsafe_allow_html=True)

    df = load_data()
    if df is None: return

    # --- CENTERED 4-OPTION INPUT LINE ---
    # We use a container and columns to align them in the middle
    input_container = st.container()
    with input_container:
        col1, col2, col3, col4 = st.columns(4)
        with col1: in_type = st.selectbox("Academic Goal", ["N/A", "Bridge", "Work-Ready"])
        with col2: in_country = st.selectbox("Country", ["N/A"] + sorted(df['Country'].unique().tolist()))
        with col3: in_mode = st.selectbox("Mode", ["N/A", "Offline", "Online", "Hybrid"])
        with col4: in_tier = st.selectbox("Budget Tier", ["N/A", "Tier 1 ($0-$3k)", "Tier 2 ($3k-$7k)", "Tier 3 ($7k-$12k)", "Tier 4 ($12k+)"])

    # Center-aligned Search Button
    _, mid_col, _ = st.columns([1, 2, 1])
    with mid_col:
        search_clicked = st.button("Find Matching Pathways")

    if search_clicked:
        recs = get_recommendations(df, {'type': in_type, 'country': in_country, 'mode': in_mode, 'tier': in_tier})
        
        if recs:
            st.markdown("### Optimized Results")
            for r in recs[:5]:
                with st.expander(f"✨ {r['Institution']} — {r['Program']}"):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Tuition", r['Cost'])
                    c2.metric("Visa Safety", r['Visa'])
                    c3.metric("Duration", f"{r['Duration']} Mo")
                    c4.metric("Location", r['Country'])
                    st.divider()
                    st.write(f"📅 **Intakes:** {r['Intake']} | 📝 **Requirements:** {r['Requirements']}")
                    st.caption(f"**Relevancy Factors:** {r['Factors']}")
        else:
            st.warning("No matches found. Try relaxing your filters.")

if __name__ == "__main__":
    main()
    
