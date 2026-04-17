import streamlit as st
import pandas as pd
import sys
import csv
import requests
import io

# --- 0. SYSTEM STABILITY FIX ---
# Prevents crash caused by long text in "Entry Requirements"
csv.field_size_limit(sys.maxsize)

# --- 1. DATA LOADING (Updated to New Google Sheet) ---
def load_data():
    # Using the NEW Google Sheet URL you provided
    sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRZ8Zfpv5Nb894hTEFla3MUvRO44trxtUJglUwHLMfRsV3TQr_wky0pilEqjYYozvznkkcsqYBlYl2r/pub?gid=0&single=true&output=csv"
    
    try:
        # Robust Fetch: Bypasses "EmptyDataError" and sync glitches
        response = requests.get(sheet_url)
        response.raise_for_status()
        
        # Engine='python' is required to handle the large text fields correctly
        df = pd.read_csv(io.StringIO(response.text), engine='python', on_bad_lines='warn')
        
        # --- ROBUST COST CLEANING (Fixes the '600 - 900' error) ---
        # 1. Remove symbols like $, *, and commas
        df['Total Tuition Cost (USD)'] = df['Total Tuition Cost (USD)'].astype(str).str.replace('[\$,\*]', '', regex=True)
        # 2. If it's a range (600-900), take the first number
        df['Total Tuition Cost (USD)'] = df['Total Tuition Cost (USD)'].str.split('-').str[0].str.strip()
        # 3. Convert to number
        df['Total Tuition Cost (USD)'] = pd.to_numeric(df['Total Tuition Cost (USD)'], errors='coerce').fillna(0)
        
        # Ensure Duration is numeric for Monthly calculation
        df['Duration (Months)'] = pd.to_numeric(df['Duration (Months)'], errors='coerce').fillna(1)
        
        return df
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return None

# --- 2. THE INTELLIGENT MATCHING ENGINE ---
def get_recommendations(df, user_input):
    results = []
    tier_limits = {"Tier 1 ($0-$3k)": 3000, "Tier 2 ($3k-$7k)": 7000, "Tier 3 ($7k-$12k)": 12000, "Tier 4 ($12k+)": 999999}

    for index, row in df.iterrows():
        score = 0
        match_flags = []
        title = str(row['Diploma Title']).lower()
        
        # A. SEARCH BAR / KEYWORD LOGIC
        if user_input['keyword']:
            keywords = user_input['keyword'].lower().split()
            if any(k in title for k in keywords):
                score += 60
                match_flags.append(f"Keyword Match")

        # B. SUBJECT DROPDOWN LOGIC
        requested_subject = user_input['subject'].lower()
        if requested_subject != "n/a":
            subj_keywords = [requested_subject]
            if requested_subject == "business": subj_keywords += ["management", "accounting", "commerce", "marketing"]
            if requested_subject == "tech": subj_keywords += ["ict", "computing", "software", "it", "computer"]
            if requested_subject == "engineering": subj_keywords += ["mechanical", "civil", "electrical"]
            
            if any(k in title for k in subj_keywords):
                score += 40 
                match_flags.append(f"Field Match")

        # C. GOAL FILTER
        if user_input['type'] != "N/A":
            if row['Diploma Type'] == user_input['type']:
                score += 30
                match_flags.append("Goal Match")
            else: continue

        # D. INCLUSIVE MODE LOGIC
        current_mode = row['Delivery Mode']
        requested_mode = user_input['mode']
        if requested_mode != "N/A":
            if current_mode == requested_mode:
                score += 20
                match_flags.append("Mode Match")
            elif requested_mode == "Hybrid" and current_mode in ["Online", "Offline"]:
                score += 10
                match_flags.append("Alt Mode")

        # E. INCLUSIVE BUDGET LOGIC
        cost = row['Total Tuition Cost (USD)']
        requested_tier = user_input['tier']
        if requested_tier != "N/A":
            max_budget = tier_limits[requested_tier]
            if cost <= max_budget:
                score += 30
                match_flags.append("Affordable")
            else: continue

        # F. LOCATION MATCH
        if user_input['country'] != "N/A" and row['Country'] == user_input['country']:
            score += 20
            match_flags.append("Location Match")
        
        # G. STRATEGIC WEIGHTING (Visa)
        score += (row['Visa Success Score'] * 3)

        # H. CALCULATE MONTHLY COST
        duration = row['Duration (Months)']
        monthly_cost = cost / duration if duration > 0 else cost
        
        results.append({
            "Institution": row['Institution Name'], "Program": row['Diploma Title'],
            "Cost": f"${int(cost):,}", "Monthly": f"${int(monthly_cost):,}",
            "Country": row['Country'], "Visa": f"{row['Visa Success Score']}/10", 
            "Duration": f"{int(duration)} Mo", "Intake": row['Intake Months'], 
            "Requirements": row['Entry Requirements'], "English": row['English Requirement'],
            "Score": score, "Factors": ", ".join(match_flags)
        })
        
    return sorted(results, key=lambda x: x['Score'], reverse=True)

# --- 3. UI LAYOUT ---
def main():
    st.set_page_config(page_title="EdPro Navigator", layout="centered", page_icon="🛡️")

    st.markdown("""
        <style>
        .stApp { background-color: #0A192F !important; }
        footer {visibility: hidden;} header {visibility: hidden;}
        h1, h2, h3, p, span, label, .stMarkdown { color: #FFFFFF !important; text-shadow: none !important; }
        .stSelectbox label p, .stTextInput label p { color: #FFFFFF !important; font-size: 19px !important; font-weight: bold !important; }

        .stButton>button { 
            width: 100%; border-radius: 12px; background-color: #FFB800; 
            color: #0A192F !important; height: 4.2em; font-weight: 800; 
            font-size: 22px; border: none; margin-top: 30px;
        }
        .stButton>button:hover { background-color: #FFD363; transform: translateY(-2px); }

        .secondary-btn>div>button {
            background-color: transparent !important;
            color: #FFB800 !important;
            border: 2px solid #FFB800 !important;
            height: 3.5em !important;
            font-size: 18px !important;
        }

        .stExpander {
            background-color: rgba(255, 255, 255, 0.08) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 15px; margin-bottom: 15px;
        }
        div[data-testid="stMetricValue"] { color: #FFB800 !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center;'>🛡️ EdPro AI Navigator</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; opacity: 0.7; margin-bottom: 40px;'>Internal Consultant Decision Support Engine</p>", unsafe_allow_html=True)

    df = load_data()
    if df is None: return

    # --- FORM INPUTS (Vertically Aligned) ---
    _, center_col, _ = st.columns([1, 4, 1])
    with center_col:
        in_keyword = st.text_input("🔍 Search Program Keyword", placeholder="e.g. Graphic, Software, Cabin...")
        in_subject = st.selectbox("📚 Field of Study", ["N/A", "Business", "Tech", "Engineering", "Arts", "Science"])
        in_type = st.selectbox("🎯 Academic Goal", ["N/A", "Bridge", "Work-Ready"])
        in_country = st.selectbox("🌍 Preferred Country", ["N/A"] + sorted(df['Country'].unique().tolist()))
        in_mode = st.selectbox("💻 Delivery Mode", ["N/A", "Offline", "Online", "Hybrid"])
        in_tier = st.selectbox("💰 Budget Tier", ["N/A", "Tier 1 ($0-$3k)", "Tier 2 ($3k-$7k)", "Tier 3 ($7k-$12k)", "Tier 4 ($12k+)"])
        
        if st.button("RUN MATCHING AGENT"):
            st.session_state.visible_count = 5
            st.session_state.current_results = get_recommendations(df, {
                'keyword': in_keyword, 'subject': in_subject, 'type': in_type, 
                'country': in_country, 'mode': in_mode, 'tier': in_tier
            })

    # --- RESULTS DISPLAY ---
    if 'current_results' in st.session_state and st.session_state.current_results:
        recs = st.session_state.current_results
        visible = st.session_state.visible_count
        
        st.markdown(f"<br><h3 style='text-align: center;'>🏆 Showing Top {min(visible, len(recs))} Matches</h3>", unsafe_allow_html=True)
        
        for r in recs[:visible]:
            with st.expander(f"✨ {r['Institution']} — {r['Program']}"):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Tuition", r['Cost'])
                c2.metric("Monthly Cost", r['Monthly']) # New Feature Added back
                c3.metric("Visa Safety", r['Visa'])
                c4.metric("Location", r['Country'])
                
                st.divider()
                st.write(f"📅 **Intakes:** {r['Intake']} | ⏳ **Duration:** {r['Duration']}")
                st.write(f"📝 **Academic Req:** {r['Requirements']}")
                st.write(f"🇬🇧 **English/SAT Req:** {r['English']}") # Displaying English/SAT Info

        if visible < len(recs):
            st.write(" ")
            _, btn_col, _ = st.columns([1, 2, 1])
            with btn_col:
                st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
                if st.button(f"SHOW 5 MORE RESULTS"):
                    st.session_state.visible_count += 5
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
    elif 'current_results' in st.session_state:
        st.warning("No matches found. Try relaxing the filters.")

if __name__ == "__main__":
    if 'visible_count' not in st.session_state:
        st.session_state.visible_count = 5
    main()
