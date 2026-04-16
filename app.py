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

# --- 2. ADVANCED MATCHING ENGINE ---
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
                match_flags.append(f"Keyword: {user_input['keyword']}")

        # B. SUBJECT DROPDOWN LOGIC
        requested_subject = user_input['subject'].lower()
        if requested_subject != "n/a":
            subj_keywords = [requested_subject]
            if requested_subject == "business": subj_keywords += ["management", "accounting", "commerce", "marketing"]
            if requested_subject == "tech": subj_keywords += ["ict", "computing", "software", "it", "computer"]
            if requested_subject == "engineering": subj_keywords += ["mechanical", "civil", "electrical"]
            if any(k in title for k in subj_keywords):
                score += 40 
                match_flags.append(f"Field: {user_input['subject']}")

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
                match_flags.append(f"Mode: {current_mode}")
            elif requested_mode == "Hybrid" and current_mode in ["Online", "Offline"]:
                score += 10
                match_flags.append(f"Alt Mode ({current_mode})")

        # E. INCLUSIVE BUDGET LOGIC
        cost = row['Total Tuition Cost (USD)']
        requested_tier = user_input['tier']
        if requested_tier != "N/A":
            max_budget = tier_limits[requested_tier]
            if cost <= max_budget:
                score += 30
                match_flags.append("Affordable")
                if cost <= max_budget * 0.5: score += 10
            else: continue

        # F. COUNTRY & VISA
        if user_input['country'] != "N/A" and row['Country'] == user_input['country']:
            score += 20
            match_flags.append("Preferred Country")
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

    st.markdown("""
        <style>
        .stApp { background-color: #0A192F !important; opacity: 1 !important; }
        footer {visibility: hidden;} header {visibility: hidden;}
        h1, h2, h3, p, span, label, .stMarkdown { color: #FFFFFF !important; text-shadow: none !important; }
        
        .stSelectbox label p, .stTextInput label p { 
            color: #FFFFFF !important; font-size: 19px !important; font-weight: bold !important; 
        }

        /* Gold Action Button */
        .stButton>button { 
            width: 100%; border-radius: 12px; background-color: #FFB800; 
            color: #0A192F !important; height: 4.2em; font-weight: 800; 
            font-size: 22px; border: none; margin-top: 30px;
            box-shadow: 0px 4px 20px rgba(255, 184, 0, 0.3);
        }
        .stButton>button:hover { background-color: #FFD363; transform: translateY(-2px); }

        /* Secondary Button (Show All) */
        .show-all-btn>div>button {
            background-color: transparent !important;
            color: #FFB800 !important;
            border: 2px solid #FFB800 !important;
            height: 3em !important;
            font-size: 16px !important;
        }

        .stExpander {
            background-color: rgba(255, 255, 255, 0.08) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 15px; margin-bottom: 15px;
        }
        div[data-testid="stMetricValue"] { color: #FFB800 !important; }
        
        /* Table Styling for All Matches */
        .stDataFrame { background-color: #FFFFFF; border-radius: 10px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center;'>🛡️ EdPro AI Navigator</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.1em; opacity: 0.7; margin-bottom: 40px;'>Internal Consultant Decision Support System</p>", unsafe_allow_html=True)

    df = load_data()
    if df is None: return

    # --- VERTICAL INPUT STACK ---
    _, center_col, _ = st.columns([1, 4, 1])
    with center_col:
        in_keyword = st.text_input("🔍 Search Specific Program or Keyword", placeholder="e.g. Aviation, Cyber, Nursing...")
        in_subject = st.selectbox("📚 Field of Study", ["N/A", "Business", "Tech", "Engineering", "Arts", "Science"])
        in_type = st.selectbox("🎯 Academic Goal", ["N/A", "Bridge", "Work-Ready"])
        in_country = st.selectbox("🌍 Preferred Country", ["N/A"] + sorted(df['Country'].unique().tolist()))
        in_mode = st.selectbox("💻 Delivery Mode", ["N/A", "Offline", "Online", "Hybrid"])
        in_tier = st.selectbox("💰 Budget Tier", ["N/A", "Tier 1 ($0-$3k)", "Tier 2 ($3k-$7k)", "Tier 3 ($7k-$12k)", "Tier 4 ($12k+)"])
        
        search_clicked = st.button("RUN MATCHING AGENT")

    if search_clicked or st.session_state.get('show_all', False):
        user_data = {'keyword': in_keyword, 'subject': in_subject, 'type': in_type, 'country': in_country, 'mode': in_mode, 'tier': in_tier}
        recs = get_recommendations(df, user_data)
        
        if recs:
            st.markdown("<br><h3 style='text-align: center;'>🏆 Top Recommendations</h3>", unsafe_allow_html=True)
            
            # Show Top 5 Curated Results
            for r in recs[:5]:
                with st.expander(f"✨ {r['Institution']} — {r['Program']}"):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Tuition", r['Cost'])
                    c2.metric("Visa Safety", r['Visa'])
                    c3.metric("Duration", f"{r['Duration']} Mo")
                    c4.metric("Location", r['Country'])
                    st.divider()
                    st.write(f"📅 **Intakes:** {r['Intake']} | 📝 **Requirements:** {r['Requirements']}")
            
            # Show All Matches Button
            if len(recs) > 5:
                st.write(" ")
                _, btn_col, _ = st.columns([1, 2, 1])
                with btn_col:
                    st.markdown('<div class="show-all-btn">', unsafe_allow_html=True)
                    if st.button(f"SHOW ALL {len(recs)} MATCHES"):
                        st.session_state.show_all = True
                    st.markdown('</div>', unsafe_allow_html=True)

                if st.session_state.get('show_all', False):
                    st.markdown("### 📋 Full Matching List")
                    all_df = pd.DataFrame(recs).drop(columns=['Score', 'Factors'])
                    st.dataframe(all_df, use_container_width=True)
        else:
            st.warning("No matches found. Try relaxing the filters.")

if __name__ == "__main__":
    if 'show_all' not in st.session_state:
        st.session_state.show_all = False
    main()
