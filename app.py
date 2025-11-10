# StartUpLens Web Application
# Team: Abhir Iyer [AI], Krishna Kishore [KK], Nandini Patel [NP]
# 
# AI Assistance: Application structure and Streamlit components created with 
# GitHub Copilot assistance, accessed on January 9, 2025

import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# [AI] Page configuration
st.set_page_config(
    page_title="StartUpLens",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# [AI] Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)

# [AI] MongoDB Connection
@st.cache_resource
def get_database():
    """Connect to MongoDB Atlas - uses environment variable or Streamlit secrets"""
    try:
        # Try Streamlit secrets first (for deployment)
        if hasattr(st, 'secrets') and 'mongo' in st.secrets:
            MONGO_URI = st.secrets['mongo']['uri']
        # Fallback to environment variable for local development
        elif os.getenv('MONGO_URI'):
            MONGO_URI = os.getenv('MONGO_URI')
        else:
            st.error("❌ MongoDB connection string not found!")
            st.info("Please set up .streamlit/secrets.toml for local development or add secrets in Streamlit Cloud.")
            st.stop()
        
        client = MongoClient(MONGO_URI)
        db = client["StartUpLensDB"]
        
        # Test connection
        client.server_info()
        return db
    except Exception as e:
        st.error(f"❌ Database connection failed: {str(e)}")
        st.info("Check your MongoDB connection string in .streamlit/secrets.toml or Streamlit Cloud secrets.")
        st.stop()

# [KK] Initialize database connection
db = get_database()
startups_collection = db["startups"]
investors_collection = db["investors"]

# Sidebar Navigation
st.sidebar.markdown("## 🚀 StartUpLens")
st.sidebar.markdown("### Navigation")

page = st.sidebar.radio(
    "Go to:",
    ["📊 Dashboard", "🔍 Search Startups", "➕ Add Startup", 
     "✏️ Update Startup", "🗑️ Delete Startup"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Team Members:**")
st.sidebar.markdown("• Abhir Iyer [AI]")
st.sidebar.markdown("• Krishna Kishore [KK]")
st.sidebar.markdown("• Nandini Patel [NP]")

# ==================== PAGE: DASHBOARD ====================
if page == "📊 Dashboard":
    st.markdown('<p class="main-header">📊 StartUpLens Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Exploring Global Startup Funding Networks</p>', unsafe_allow_html=True)
    
    # [NP] Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_startups = startups_collection.estimated_document_count()
        st.metric("Total Startups", f"{total_startups:,}")
    
    with col2:
        # [NP] Calculate total funding
        pipeline = [
            {"$unwind": "$funding_rounds"},
            {"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$funding_rounds.amount", 0]}}}}
        ]
        result = list(startups_collection.aggregate(pipeline))
        total_funding = result[0]['total'] if result else 0
        st.metric("Total Funding", f"${total_funding/1e9:.2f}B")
    
    with col3:
        # [NP] Count unique industries
        industries = startups_collection.distinct("industry")
        st.metric("Industries", len([i for i in industries if i]))
    
    with col4:
        # [NP] Count unique countries
        countries = startups_collection.distinct("country")
        st.metric("Countries", len([c for c in countries if c]))
    
    st.markdown("---")
    
    # [NP] Visualization 1: Funding by Industry (Top 10)
    st.subheader("💰 Total Funding by Industry (Top 10)")
    
    pipeline = [
        {"$unwind": "$funding_rounds"},
        {"$group": {
            "_id": {"$ifNull": ["$industry", "unknown"]},
            "totalRaised": {"$sum": {"$ifNull": ["$funding_rounds.amount", 0]}}
        }},
        {"$sort": {"totalRaised": -1}},
        {"$limit": 10}
    ]
    
    industry_data = list(startups_collection.aggregate(pipeline))
    
    if industry_data:
        df_industry = pd.DataFrame(industry_data)
        df_industry['totalRaised'] = df_industry['totalRaised'] / 1e9  # Convert to billions
        df_industry.columns = ['Industry', 'Total Raised ($B)']
        
        fig1 = px.bar(
            df_industry, 
            x='Industry', 
            y='Total Raised ($B)',
            title='Top 10 Industries by Total Funding',
            color='Total Raised ($B)',
            color_continuous_scale='Blues'
        )
        fig1.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)
    
    # [NP] Visualization 2 & 3 in columns
    col_left, col_right = st.columns(2)
    
    with col_left:
        # [NP] Visualization 2: Yearly Funding Trend
        st.subheader("📈 Yearly Funding Trend")
        
        pipeline = [
            {"$unwind": "$funding_rounds"},
            {"$addFields": {"year": {"$substr": ["$funding_rounds.date", 0, 4]}}},
            {"$match": {"year": {"$regex": "^[0-9]{4}$"}}},
            {"$group": {
                "_id": "$year",
                "total": {"$sum": {"$ifNull": ["$funding_rounds.amount", 0]}}
            }},
            {"$sort": {"_id": 1}},
            {"$limit": 30}  # Last 30 years
        ]
        
        yearly_data = list(startups_collection.aggregate(pipeline))
        
        if yearly_data:
            df_yearly = pd.DataFrame(yearly_data)
            df_yearly['total'] = df_yearly['total'] / 1e9
            df_yearly.columns = ['Year', 'Total ($B)']
            
            fig2 = px.line(
                df_yearly,
                x='Year',
                y='Total ($B)',
                title='Total Funding Over Time',
                markers=True
            )
            fig2.update_layout(height=350)
            st.plotly_chart(fig2, use_container_width=True)
    
    with col_right:
        # [NP] Visualization 3: Top 10 Countries
        st.subheader("🌍 Top 10 Countries by Funding")
        
        pipeline = [
            {"$unwind": "$funding_rounds"},
            {"$group": {
                "_id": {"$ifNull": ["$country", "unknown"]},
                "total": {"$sum": {"$ifNull": ["$funding_rounds.amount", 0]}}
            }},
            {"$sort": {"total": -1}},
            {"$limit": 10}
        ]
        
        country_data = list(startups_collection.aggregate(pipeline))
        
        if country_data:
            df_country = pd.DataFrame(country_data)
            df_country['total'] = df_country['total'] / 1e9
            df_country.columns = ['Country', 'Total ($B)']
            
            fig3 = px.bar(
                df_country,
                y='Country',
                x='Total ($B)',
                title='Top Countries by Total Funding',
                orientation='h',
                color='Total ($B)',
                color_continuous_scale='Viridis'
            )
            fig3.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig3, use_container_width=True)
    
    # [NP] Visualization 4: Round Type Distribution
    st.subheader("📊 Funding Round Distribution")
    
    pipeline = [
        {"$unwind": "$funding_rounds"},
        {"$group": {
            "_id": {"$toLower": {"$ifNull": ["$funding_rounds.round_type", "unknown"]}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 8}
    ]
    
    round_data = list(startups_collection.aggregate(pipeline))
    
    if round_data:
        df_rounds = pd.DataFrame(round_data)
        df_rounds.columns = ['Round Type', 'Count']
        
        fig4 = px.pie(
            df_rounds,
            values='Count',
            names='Round Type',
            title='Distribution of Funding Round Types',
            hole=0.4
        )
        fig4.update_layout(height=400)
        st.plotly_chart(fig4, use_container_width=True)

# ==================== PAGE: SEARCH STARTUPS ====================
elif page == "🔍 Search Startups":
    st.markdown('<p class="main-header">🔍 Search Startups</p>', unsafe_allow_html=True)
    
    # [KK] Search and Filter Section
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_name = st.text_input("🔎 Search by Name", placeholder="Enter startup name...")
    
    with col2:
        industries = ["All"] + sorted([i for i in startups_collection.distinct("industry") if i])
        selected_industry = st.selectbox("Industry Filter", industries)
    
    with col3:
        countries = ["All"] + sorted([c for c in startups_collection.distinct("country") if c])
        selected_country = st.selectbox("Country Filter", countries)
    
    # [KK] Build query
    query = {}
    
    if search_name:
        query["startup_name"] = {"$regex": search_name, "$options": "i"}
    
    if selected_industry != "All":
        query["industry"] = selected_industry
    
    if selected_country != "All":
        query["country"] = selected_country
    
    # [KK] Execute search
    results = list(startups_collection.find(query).limit(50))
    
    st.markdown(f"### Found {len(results)} startups")
    
    if results:
        for startup in results:
            with st.expander(f"🚀 {startup.get('startup_name', 'Unknown')} - {startup.get('industry', 'N/A')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Country:** {startup.get('country', 'N/A')}")
                    st.markdown(f"**Founded:** {startup.get('founded_year', 'N/A')}")
                    st.markdown(f"**Status:** {startup.get('status', 'N/A')}")
                    
                    founders = startup.get('founders', [])
                    if founders:
                        st.markdown(f"**Founders:** {', '.join(founders[:3])}")
                
                with col2:
                    funding_rounds = startup.get('funding_rounds', [])
                    if funding_rounds:
                        total_funding = sum(r.get('amount', 0) for r in funding_rounds)
                        st.markdown(f"**Total Funding:** ${total_funding:,.0f}")
                        st.markdown(f"**Funding Rounds:** {len(funding_rounds)}")
                        
                        latest_round = funding_rounds[-1]
                        st.markdown(f"**Latest Round:** {latest_round.get('round_type', 'N/A')}")
                        st.markdown(f"**Latest Amount:** ${latest_round.get('amount', 0):,.0f}")
    else:
        st.info("No startups found matching your criteria.")

# ==================== PAGE: ADD STARTUP ====================
elif page == "➕ Add Startup":
    st.markdown('<p class="main-header">➕ Add New Startup</p>', unsafe_allow_html=True)
    
    # [AI] Form for adding new startup
    with st.form("add_startup_form"):
        st.subheader("Basic Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            startup_name = st.text_input("Startup Name *", placeholder="e.g., TechVenture AI")
            industry = st.text_input("Industry *", placeholder="e.g., ai, software, biotech")
            country = st.text_input("Country Code *", placeholder="e.g., USA, GBR, IND")
        
        with col2:
            founded_year = st.number_input("Founded Year *", min_value=1900, max_value=2030, value=2024)
            status = st.selectbox("Status *", ["Seed", "Series A", "Series B", "Series C+", "Acquired", "Active"])
            founders_input = st.text_input("Founders (comma-separated)", placeholder="John Doe, Jane Smith")
        
        st.markdown("---")
        st.subheader("Initial Funding Round (Optional)")
        
        col3, col4, col5 = st.columns(3)
        
        with col3:
            round_type = st.selectbox("Round Type", ["", "Seed", "Angel", "Series A", "Series B", "Series C+", "Venture"])
        
        with col4:
            amount = st.number_input("Amount (USD)", min_value=0, value=0, step=100000)
        
        with col5:
            valuation = st.number_input("Valuation (USD)", min_value=0, value=0, step=1000000)
        
        funding_date = st.date_input("Funding Date", value=datetime.now())
        investors_input = st.text_input("Investors (comma-separated)", placeholder="Sequoia Capital, Y Combinator")
        
        # [AI] Submit button
        submitted = st.form_submit_button("Add Startup", type="primary", use_container_width=True)
        
        if submitted:
            # [AI] Validate required fields
            if not startup_name or not industry or not country:
                st.error("❌ Please fill in all required fields marked with *")
            else:
                # [AI] Prepare document
                new_startup = {
                    "startup_name": startup_name,
                    "industry": industry.lower(),
                    "country": country.upper(),
                    "founded_year": founded_year,
                    "status": status,
                    "founders": [f.strip() for f in founders_input.split(",")] if founders_input else [],
                    "funding_rounds": []
                }
                
                # [AI] Add funding round if provided
                if round_type and amount > 0:
                    funding_round = {
                        "round_type": round_type,
                        "amount": float(amount),
                        "date": funding_date.strftime("%Y-%m-%d"),
                        "valuation": float(valuation) if valuation > 0 else None,
                        "investors": [i.strip() for i in investors_input.split(",")] if investors_input else []
                    }
                    new_startup["funding_rounds"].append(funding_round)
                
                try:
                    # [AI] Insert into database
                    result = startups_collection.insert_one(new_startup)
                    st.success(f"✅ Successfully added startup: {startup_name}")
                    st.balloons()
                    st.info(f"Document ID: {result.inserted_id}")
                except Exception as e:
                    st.error(f"❌ Error adding startup: {str(e)}")

# ==================== PAGE: UPDATE STARTUP ====================
elif page == "✏️ Update Startup":
    st.markdown('<p class="main-header">✏️ Update Startup</p>', unsafe_allow_html=True)
    
    # [NP] Search for startup to update
    search_update = st.text_input("🔎 Search startup to update", placeholder="Enter startup name...")
    
    if search_update:
        # [NP] Find matching startups
        matches = list(startups_collection.find(
            {"startup_name": {"$regex": search_update, "$options": "i"}},
            limit=10
        ))
        
        if matches:
            startup_names = [s['startup_name'] for s in matches]
            selected_startup = st.selectbox("Select Startup", startup_names)
            
            if selected_startup:
                # [NP] Get full startup document
                startup = startups_collection.find_one({"startup_name": selected_startup})
                
                st.markdown("---")
                st.subheader(f"Updating: {startup['startup_name']}")
                
                # [NP] Update Status
                with st.form("update_status_form"):
                    st.markdown("#### Update Status")
                    new_status = st.selectbox(
                        "New Status",
                        ["Seed", "Series A", "Series B", "Series C+", "Acquired", "Inactive"],
                        index=["Seed", "Series A", "Series B", "Series C+", "Acquired", "Inactive"].index(startup.get('status', 'Seed')) if startup.get('status') in ["Seed", "Series A", "Series B", "Series C+", "Acquired", "Inactive"] else 0
                    )
                    
                    if st.form_submit_button("Update Status"):
                        try:
                            startups_collection.update_one(
                                {"startup_name": selected_startup},
                                {"$set": {"status": new_status}}
                            )
                            st.success(f"✅ Status updated to: {new_status}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                
                st.markdown("---")
                
                # [NP] Add New Funding Round
                with st.form("add_funding_round_form"):
                    st.markdown("#### Add New Funding Round")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        new_round_type = st.selectbox("Round Type", ["Seed", "Angel", "Series A", "Series B", "Series C+", "Venture"])
                    
                    with col2:
                        new_amount = st.number_input("Amount (USD)", min_value=0, value=1000000, step=100000)
                    
                    with col3:
                        new_valuation = st.number_input("Valuation (USD)", min_value=0, value=0, step=1000000)
                    
                    new_date = st.date_input("Funding Date", value=datetime.now())
                    new_investors = st.text_input("Investors (comma-separated)", placeholder="Investor A, Investor B")
                    
                    if st.form_submit_button("Add Funding Round"):
                        try:
                            new_round = {
                                "round_type": new_round_type,
                                "amount": float(new_amount),
                                "date": new_date.strftime("%Y-%m-%d"),
                                "valuation": float(new_valuation) if new_valuation > 0 else None,
                                "investors": [i.strip() for i in new_investors.split(",")] if new_investors else []
                            }
                            
                            startups_collection.update_one(
                                {"startup_name": selected_startup},
                                {"$push": {"funding_rounds": new_round}}
                            )
                            st.success(f"✅ Added {new_round_type} round of ${new_amount:,.0f}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("No matching startups found.")

# ==================== PAGE: DELETE STARTUP ====================
elif page == "🗑️ Delete Startup":
    st.markdown('<p class="main-header">🗑️ Delete Startup</p>', unsafe_allow_html=True)
    st.warning("⚠️ **Warning:** This action cannot be undone!")
    
    # [AI] Search for startup to delete
    search_delete = st.text_input("🔎 Search startup to delete", placeholder="Enter startup name...")
    
    if search_delete:
        # [AI] Find matching startups
        matches = list(startups_collection.find(
            {"startup_name": {"$regex": search_delete, "$options": "i"}},
            limit=10
        ))
        
        if matches:
            startup_names = [s['startup_name'] for s in matches]
            selected_delete = st.selectbox("Select Startup to Delete", [""] + startup_names)
            
            if selected_delete:
                # [AI] Show startup details
                startup = startups_collection.find_one({"startup_name": selected_delete})
                
                st.markdown("---")
                st.error(f"### You are about to delete: **{startup['startup_name']}**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Industry:** {startup.get('industry', 'N/A')}")
                    st.markdown(f"**Country:** {startup.get('country', 'N/A')}")
                    st.markdown(f"**Founded:** {startup.get('founded_year', 'N/A')}")
                
                with col2:
                    funding_rounds = startup.get('funding_rounds', [])
                    st.markdown(f"**Funding Rounds:** {len(funding_rounds)}")
                    total = sum(r.get('amount', 0) for r in funding_rounds)
                    st.markdown(f"**Total Funding:** ${total:,.0f}")
                
                st.markdown("---")
                
                # [AI] Confirmation
                confirm = st.text_input(
                    "Type the startup name to confirm deletion:",
                    placeholder=selected_delete
                )
                
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    if st.button("🗑️ Confirm Delete", type="primary", disabled=(confirm != selected_delete)):
                        try:
                            result = startups_collection.delete_one({"startup_name": selected_delete})
                            if result.deleted_count > 0:
                                st.success(f"✅ Successfully deleted: {selected_delete}")
                                st.balloons()
                            else:
                                st.error("❌ Failed to delete startup")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                
                with col2:
                    if confirm != selected_delete and confirm:
                        st.warning("⚠️ Name doesn't match. Delete button disabled.")
        else:
            st.info("No matching startups found.")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "StartUpLens © 2025 | Team: Abhir Iyer, Krishna Kishore, Nandini Patel | "
    "Applied Database Technologies Project"
    "</div>",
    unsafe_allow_html=True
)