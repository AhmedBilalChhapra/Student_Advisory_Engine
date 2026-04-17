import streamlit as st
import pandas as pd
import csv
import sys

# --- 0. SYSTEM STABILITY FIX ---
csv.field_size_limit(10**7) 

# --- 1. DATA LOADING ---
def load_data():
    sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRZ8Zfpv5Nb894hTEFla3MUvRO44trxtUJglUwHLMfRsV3TQr_wky0pilEqjYYozvznkkcsqYBlYl2r/pub?gid=0&single=true&output=csv"
    try:
        df = pd.read_csv(sheet_url, low_memory=False)
        # Clean currency
        df['Total Tuition Cost (USD)'] = df['Total Tuition Cost (USD)'].replace('[\$,]', '', regex=True).astype(float)
        df['Duration (Months)'] = pd.to_numeric(df['Duration (Months)'], errors='coerce')
        # English Score Parser
        df['IELTS_Num'] = df['English Requirement'].str.extract(r'(\d+\.\d+|\d+)').astype(float).fillna(0)
        return df
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return None

# --- 2. THE MASTER MATCHING ENGINE ---
def get_recommendations(df, user_input):
    results = []
    tier_limits = {"Tier 1 ($0-$3k)": 3000, "Tier 2 ($3k-$7k)": 7000, "Tier 3 ($7k-$12k)": 12000, "Tier 4 ($12k+)": 999999}

    for index, row in df.iterrows():
        score = 0
        match_flags = []
        title = str(row['Diploma Title']).lower()
        
        # A. ELIGIBILITY: English Requirement
        if user_input['student_ielts'] < row['IELTS_Num']:
            continue 

        # B. POWER SEARCH: Keywords
        if user_input['keyword']:
            if any(k in title for k in user_input['keyword'].lower().split()):
                score += 60
                match_flags.append("Keyword Match")

        # C. SUBJECT MAPPING
        requested_subject = user_input['subject'].lower()
        if requested_subject != "n/a":
            subj_keywords = [requested_subject]
            if requested_subject == "business": subj_keywords += ["management", "accounting", "marketing"]
            if requested_subject == "tech": subj_keywords += ["ict", "computing", "it", "software"]
            if any(k in title for k in subj_keywords):
                score += 40

        # D. GOAL & MODE FILTERS
        if user_input['type'] != "N/A" and row['Diploma Type'] != user_input['type']:
            continue
        
        if user_input['mode'] != "N/A":
            if row['Delivery Mode'] == user_input['mode']: score += 20
            elif user_input['mode'] == "Hybrid": score += 10 # Inclusive match

        # E. BUDGET TIER (Cumulative)
        cost = row['Total Tuition Cost (USD)']
        if user_input['tier'] != "N/A" and cost > tier_limits[user_input['tier']]:
            continue

        # F. FINANCIALS & VISA RISK
        duration = row['Duration (Months)']
        monthly_cost = cost / duration if duration > 0 else 0
        visa_score = row['Visa Success Score']
        
        if visa_score >= 8: badge_color = "#22C55E" # Green
        elif visa_score >= 5: badge_color = "#F59E0B" # Amber
        else: badge_color = "#EF4444" # Red
        
        results.append({
            "Institution": row['Institution Name'], "Program": row['Diploma Title'],
            "Total": f"${int(cost):,}", "Monthly": f"${int(monthly_cost):,}",
            "Country": row['Country'], "Visa": visa_score, "VisaColor": badge_color,
            "Duration": f"{int(duration)} Mo", "Intake": row['Intake Months'], 
            "Academic": row['Entry Requirements'], "English": row['English Requirement'],
            "Score": score + (visa_score * 3)
        })
        
    return sorted(results, key=lambda x: x['Score'], reverse=True)

# --- 3. UI LAYOUT ---
def main():
    st.set_page_config(page_title="EdPro Navigator", layout="centered", page_icon="🛡️")

    st.markdown("""
        <style>
        .stApp { background-color: #0A192F !important; }
        footer {visibility: hidden;} header {visibility: hidden;}
        h1, h2, h3, p, span, label, .stMarkdown { color: #FFFFFF !important; }
        .stSelectbox label p, .stTextInput label p, .stSlider label p { color: #FFFFFF !important; font-size: 18px !important; font-weight: bold !important; }
        .stButton>button { width: 100%; border-radius: 12px; background-color: #FFB800; color: #0A192F !important; height: 4.2em; font-weight: 800; font-size: 22px; border: none; margin-top: 20px; }
        .stExpander { background-color: rgba(255, 255, 255, 0.08) !important; border: 1px solid rgba(255, 255, 255, 0.2) !important; border-radius: 15px; margin-bottom: 15px; }
        div[data-testid="stMetricValue"] { color: #FFB800 !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center;'>🛡️ EdPro AI Navigator</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; opacity: 0.7; margin-bottom: 30px;'>Internal Consultant Decision Support Engine — V2.0 Final</p>", unsafe_allow_html=True)

    df = load_data()
    if df is None: return

    _, center_col, _ = st.columns([1, 4, 1])
    with center_col:
        in_keyword = st.text_input("🔍 Search Keyword", placeholder="e.g. IT, Business...")
        in_ielts = st.slider("🎓 Student IELTS / Equivalent Score", 4.0, 9.0, 6.0, 0.5)
        
        c1, c2 = st.columns(2)
        with c1: in_subject = st.selectbox("📚 Field", ["N/A", "Business", "Tech", "Engineering", "Arts"])
        with c2: in_type = st.selectbox("🎯 Goal", ["N/A", "Bridge", "Work-Ready"])
        
        c3, c4 = st.columns(2)
        with c3: in_mode = st.selectbox("💻 Mode", ["N/A", "Offline", "Online", "Hybrid"])
        with c4: in_tier = st.selectbox("💰 Budget", ["N/A", "Tier 1", "Tier 2", "Tier 3", "Tier 4"])
        
        if st.button("RUN MATCHING AGENT"):
            st.session_state.visible_count = 5
            st.session_state.current_results = get_recommendations(df, {
                'keyword': in_keyword, 'subject': in_subject, 'student_ielts': in_ielts, 
                'tier': in_tier, 'type': in_type, 'mode': in_mode
            })

    # --- RESULTS ---
    if 'current_results' in st.session_state and st.session_state.current_results:
        recs = st.session_state.current_results
        st.markdown(f"<h3 style='text-align: center;'>🏆 Top Matches</h3>", unsafe_allow_html=True)
        
        for r in recs[:st.session_state.visible_count]:
            with st.expander(f"✨ {r['Institution']} — {r['Program']}"):
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Tuition", r['Total'])
                m2.metric("Monthly Cost", r['Monthly'])
                m3.markdown(f"<div style='text-align:center;'><p style='margin-bottom:0px; font-weight:bold;'>Visa Safety</p><h2 style='color:{r['VisaColor']}; margin-top:0px;'>{r['Visa']}/10</h2></div>", unsafe_allow_html=True)
                
                st.divider()
                st1, st2, st3 = st.columns(3)
                st1.metric("Location", r['Country'])
                st2.metric("Duration", r['Duration'])
                st3.write(f"📅 **Intakes:**\n{r['Intake']}")
                
                st.write(f"📝 **Academic Req:** {r['Academic']}")
                st.write(f"🇬🇧 **English Req:** {r['English']}")

        if st.session_state.visible_count < len(recs):
            if st.button("SHOW 5 MORE"):
                st.session_state.visible_count += 5
                st.rerun()

if __name__ == "__main__":
    if 'visible_count' not in st.session_state: st.session_state.visible_count = 5
    main()
    
