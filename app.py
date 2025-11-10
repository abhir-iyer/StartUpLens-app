# StartUpLens Web Application
# Team: Abhir Iyer [AI], Krishna Kishore [KK], Nandini Patel [NP]
#
# AI Assistance: Application structure and Streamlit components created with
# GitHub Copilot assistance, accessed on January 9, 2025
#
# NOTE: This build removes pandas (for Streamlit Cloud on Python 3.13) and
# adds explicit TLS CA (certifi) for Atlas connections.

import os
from datetime import datetime

import streamlit as st
from pymongo import MongoClient
import plotly.graph_objects as go


# ===================== PAGE CONFIG =====================
st.set_page_config(
    page_title="StartUpLens",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styles
st.markdown(
    """
    <style>
      .main-header { font-size: 3rem; font-weight: 800; color: #1f77b4; text-align: center; margin-bottom: .75rem; }
      .sub-header  { font-size: 1.25rem; color: #666; text-align: center; margin-bottom: 1.5rem; }
      .metric-card { background-color: #f0f2f6; padding: 1.25rem; border-radius: .5rem; border-left: 5px solid #1f77b4; }
    </style>
    """,
    unsafe_allow_html=True
)


# ===================== DATABASE =====================
@st.cache_resource
def get_database():
    """Connect to MongoDB Atlas using Streamlit secrets or env, with explicit TLS CA."""
    import certifi

    # Pull URI
    if hasattr(st, "secrets") and "mongo" in st.secrets:
        MONGO_URI = st.secrets["mongo"].get("uri")
    else:
        MONGO_URI = os.getenv("MONGO_URI")

    if not MONGO_URI:
        st.error("❌ MongoDB connection string not found!")
        st.info("Add it to .streamlit/secrets.toml (local) or Streamlit Cloud → Secrets.")
        st.stop()

    try:
        client = MongoClient(
            MONGO_URI,
            tls=True,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=20000,
            socketTimeoutMS=20000,
            appname="StartUpLens",
        )
        # Verify TLS/network
        client.admin.command("ping")
        # If DB not in URI, we default to this logical name:
        db = client["StartUpLensDB"]
        return db
    except Exception as e:
        st.error("❌ Database connection failed (TLS/DNS/Network).")
        st.code(str(e))
        st.info(
            "Checklist:\n"
            "• Atlas → Network Access: temporarily allow 0.0.0.0/0 for Streamlit Cloud.\n"
            "• Use mongodb+srv:// URI, include /StartUpLensDB and ?retryWrites=true&w=majority&appName=StartUpLens.\n"
            "• requirements.txt includes certifi and dnspython.\n"
            "• Username/password are correct (URL-encode special characters)."
        )
        st.stop()


db = get_database()
startups_collection = db["startups"]
investors_collection = db["investors"]


# ===================== SIDEBAR NAV =====================
st.sidebar.markdown("## 🚀 StartUpLens\n### Navigation")
page = st.sidebar.radio(
    "Go to:",
    ["📊 Dashboard", "🔍 Search Startups", "➕ Add Startup", "✏️ Update Startup", "🗑️ Delete Startup"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Team Members:**\n\n• Abhir Iyer [AI]\n\n• Krishna Kishore [KK]\n\n• Nandini Patel [NP]")


# ----------------- Helper funcs (no pandas) -----------------
def agg_to_xy(records, key="_id", value="total"):
    """Convert a list of { '_id': ..., 'total': ... } to x,y lists for plotting."""
    x = [str(r.get(key, "unknown")) for r in records]
    y = [float(r.get(value, 0) or 0) for r in records]
    return x, y


def safe_num(x, default=0.0):
    try:
        return float(x or 0)
    except Exception:
        return default


# ===================== PAGE: DASHBOARD =====================
if page == "📊 Dashboard":
    st.markdown('<p class="main-header">📊 StartUpLens Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Exploring Global Startup Funding Networks</p>', unsafe_allow_html=True)

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_startups = startups_collection.estimated_document_count()
        st.metric("Total Startups", f"{total_startups:,}")

    with col2:
        # Sum of funding_rounds.amount
        pipeline_total = [
            {"$unwind": "$funding_rounds"},
            {"$group": {"_id": None, "total": {"$sum": {"$ifNull": ["$funding_rounds.amount", 0]}}}}
        ]
        res_total = list(startups_collection.aggregate(pipeline_total))
        total_funding = res_total[0]["total"] if res_total else 0
        st.metric("Total Funding", f"${total_funding/1e9:.2f}B")

    with col3:
        industries = [i for i in startups_collection.distinct("industry") if i]
        st.metric("Industries", len(industries))

    with col4:
        countries = [c for c in startups_collection.distinct("country") if c]
        st.metric("Countries", len(countries))

    st.markdown("---")

    # 1) Total Funding by Industry (Top 10)
    st.subheader("💰 Total Funding by Industry (Top 10)")
    pipeline_industry = [
        {"$unwind": "$funding_rounds"},
        {"$group": {
            "_id": {"$ifNull": ["$industry", "unknown"]},
            "total": {"$sum": {"$ifNull": ["$funding_rounds.amount", 0]}}
        }},
        {"$sort": {"total": -1}},
        {"$limit": 10},
    ]
    industry_data = list(startups_collection.aggregate(pipeline_industry))
    if industry_data:
        x, y = agg_to_xy(industry_data, key="_id", value="total")
        y_bil = [v / 1e9 for v in y]
        fig1 = go.Figure(
            data=[go.Bar(x=x, y=y_bil, marker=dict(color=y_bil, colorscale="Blues"))]
        )
        fig1.update_layout(
            title="Top 10 Industries by Total Funding ($B)",
            xaxis_title="Industry",
            yaxis_title="Total Raised ($B)",
            height=420,
            showlegend=False,
            margin=dict(l=20, r=20, t=60, b=20),
        )
        st.plotly_chart(fig1, use_container_width=True)

    # 2) Yearly Funding Trend  |  3) Top Countries (side-by-side)
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📈 Yearly Funding Trend")
        pipeline_yearly = [
            {"$unwind": "$funding_rounds"},
            {"$addFields": {"year": {"$substr": ["$funding_rounds.date", 0, 4]}}},
            {"$match": {"year": {"$regex": "^[0-9]{4}$"}}},
            {"$group": {"_id": "$year", "total": {"$sum": {"$ifNull": ["$funding_rounds.amount", 0]}}}},
            {"$sort": {"_id": 1}},
            {"$limit": 30},
        ]
        yearly_data = list(startups_collection.aggregate(pipeline_yearly))
        if yearly_data:
            years, totals = agg_to_xy(yearly_data, key="_id", value="total")
            totals_bil = [t / 1e9 for t in totals]
            fig2 = go.Figure(
                data=[go.Scatter(x=years, y=totals_bil, mode="lines+markers")]
            )
            fig2.update_layout(
                title="Total Funding Over Time ($B)",
                xaxis_title="Year",
                yaxis_title="Total ($B)",
                height=360,
                margin=dict(l=20, r=20, t=60, b=20),
            )
            st.plotly_chart(fig2, use_container_width=True)

    with col_right:
        st.subheader("🌍 Top 10 Countries by Funding")
        pipeline_country = [
            {"$unwind": "$funding_rounds"},
            {"$group": {
                "_id": {"$ifNull": ["$country", "unknown"]},
                "total": {"$sum": {"$ifNull": ["$funding_rounds.amount", 0]}}
            }},
            {"$sort": {"total": -1}},
            {"$limit": 10},
        ]
        country_data = list(startups_collection.aggregate(pipeline_country))
        if country_data:
            countries_x, totals_y = agg_to_xy(country_data, key="_id", value="total")
            totals_bil = [t / 1e9 for t in totals_y]
            fig3 = go.Figure(
                data=[go.Bar(x=totals_bil, y=countries_x, orientation="h",
                             marker=dict(color=totals_bil, colorscale="Viridis"))]
            )
            fig3.update_layout(
                title="Top Countries by Total Funding ($B)",
                xaxis_title="Total ($B)",
                yaxis_title="Country",
                height=360,
                showlegend=False,
                margin=dict(l=20, r=20, t=60, b=20),
            )
            st.plotly_chart(fig3, use_container_width=True)

    # 4) Round Type Distribution (Pie)
    st.subheader("📊 Funding Round Distribution")
    pipeline_rounds = [
        {"$unwind": "$funding_rounds"},
        {"$group": {
            "_id": {"$toLower": {"$ifNull": ["$funding_rounds.round_type", "unknown"]}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 8},
    ]
    round_data = list(startups_collection.aggregate(pipeline_rounds))
    if round_data:
        labels = [r.get("_id", "unknown") for r in round_data]
        values = [int(r.get("count", 0) or 0) for r in round_data]
        fig4 = go.Figure(
            data=[go.Pie(labels=labels, values=values, hole=0.4)]
        )
        fig4.update_layout(
            title="Distribution of Funding Round Types",
            height=420,
            margin=dict(l=20, r=20, t=60, b=20),
        )
        st.plotly_chart(fig4, use_container_width=True)


# ===================== PAGE: SEARCH =====================
elif page == "🔍 Search Startups":
    st.markdown('<p class="main-header">🔍 Search Startups</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        search_name = st.text_input("🔎 Search by Name", placeholder="Enter startup name...")
    with col2:
        industry_opts = ["All"] + sorted([i for i in startups_collection.distinct("industry") if i])
        selected_industry = st.selectbox("Industry Filter", industry_opts)
    with col3:
        country_opts = ["All"] + sorted([c for c in startups_collection.distinct("country") if c])
        selected_country = st.selectbox("Country Filter", country_opts)

    query = {}
    if search_name:
        query["startup_name"] = {"$regex": search_name, "$options": "i"}
    if selected_industry != "All":
        query["industry"] = selected_industry
    if selected_country != "All":
        query["country"] = selected_country

    results = list(startups_collection.find(query).limit(50))
    st.markdown(f"### Found {len(results)} startups")

    if results:
        for s in results:
            title = f"🚀 {s.get('startup_name', 'Unknown')} - {s.get('industry', 'N/A')}"
            with st.expander(title):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Country:** {s.get('country', 'N/A')}")
                    st.markdown(f"**Founded:** {s.get('founded_year', 'N/A')}")
                    st.markdown(f"**Status:** {s.get('status', 'N/A')}")
                    founders = s.get("founders", [])
                    if founders:
                        st.markdown(f"**Founders:** {', '.join(founders[:3])}")
                with c2:
                    rounds = s.get("funding_rounds", [])
                    total = sum(safe_num(r.get("amount")) for r in rounds)
                    st.markdown(f"**Total Funding:** ${total:,.0f}")
                    st.markdown(f"**Funding Rounds:** {len(rounds)}")
                    if rounds:
                        latest = rounds[-1]
                        st.markdown(f"**Latest Round:** {latest.get('round_type', 'N/A')}")
                        st.markdown(f"**Latest Amount:** ${safe_num(latest.get('amount')):,.0f}")
    else:
        st.info("No startups found matching your criteria.")


# ===================== PAGE: ADD =====================
elif page == "➕ Add Startup":
    st.markdown('<p class="main-header">➕ Add New Startup</p>', unsafe_allow_html=True)

    with st.form("add_startup_form"):
        st.subheader("Basic Information")
        c1, c2 = st.columns(2)
        with c1:
            startup_name = st.text_input("Startup Name *", placeholder="e.g., TechVenture AI")
            industry = st.text_input("Industry *", placeholder="e.g., ai, software, biotech")
            country = st.text_input("Country Code *", placeholder="e.g., USA, GBR, IND")
        with c2:
            founded_year = st.number_input("Founded Year *", min_value=1900, max_value=2030, value=2024)
            status = st.selectbox("Status *", ["Seed", "Series A", "Series B", "Series C+", "Acquired", "Active"])
            founders_input = st.text_input("Founders (comma-separated)", placeholder="John Doe, Jane Smith")

        st.markdown("---")
        st.subheader("Initial Funding Round (Optional)")
        c3, c4, c5 = st.columns(3)
        with c3:
            round_type = st.selectbox("Round Type", ["", "Seed", "Angel", "Series A", "Series B", "Series C+", "Venture"])
        with c4:
            amount = st.number_input("Amount (USD)", min_value=0, value=0, step=100000)
        with c5:
            valuation = st.number_input("Valuation (USD)", min_value=0, value=0, step=1000000)
        funding_date = st.date_input("Funding Date", value=datetime.now())
        investors_input = st.text_input("Investors (comma-separated)", placeholder="Sequoia Capital, Y Combinator")

        submitted = st.form_submit_button("Add Startup", type="primary", use_container_width=True)
        if submitted:
            if not startup_name or not industry or not country:
                st.error("❌ Please fill in all required fields marked with *")
            else:
                doc = {
                    "startup_name": startup_name,
                    "industry": industry.lower(),
                    "country": country.upper(),
                    "founded_year": int(founded_year),
                    "status": status,
                    "founders": [f.strip() for f in founders_input.split(",")] if founders_input else [],
                    "funding_rounds": [],
                }
                if round_type and amount > 0:
                    doc["funding_rounds"].append({
                        "round_type": round_type,
                        "amount": float(amount),
                        "date": funding_date.strftime("%Y-%m-%d"),
                        "valuation": float(valuation) if valuation > 0 else None,
                        "investors": [i.strip() for i in investors_input.split(",")] if investors_input else [],
                    })
                try:
                    res = startups_collection.insert_one(doc)
                    st.success(f"✅ Successfully added startup: {startup_name}")
                    st.balloons()
                    st.info(f"Document ID: {res.inserted_id}")
                except Exception as e:
                    st.error(f"❌ Error adding startup: {str(e)}")


# ===================== PAGE: UPDATE =====================
elif page == "✏️ Update Startup":
    st.markdown('<p class="main-header">✏️ Update Startup</p>', unsafe_allow_html=True)

    search_update = st.text_input("🔎 Search startup to update", placeholder="Enter startup name...")
    if search_update:
        matches = list(startups_collection.find(
            {"startup_name": {"$regex": search_update, "$options": "i"}}, limit=10
        ))
        if matches:
            names = [m["startup_name"] for m in matches]
            selected = st.selectbox("Select Startup", names)
            if selected:
                s = startups_collection.find_one({"startup_name": selected})
                st.markdown("---")
                st.subheader(f"Updating: {s['startup_name']}")

                # Update Status
                with st.form("update_status_form"):
                    st.markdown("#### Update Status")
                    status_opts = ["Seed", "Series A", "Series B", "Series C+", "Acquired", "Inactive"]
                    current = s.get("status", "Seed")
                    idx = status_opts.index(current) if current in status_opts else 0
                    new_status = st.selectbox("New Status", status_opts, index=idx)
                    if st.form_submit_button("Update Status"):
                        try:
                            startups_collection.update_one(
                                {"startup_name": selected}, {"$set": {"status": new_status}}
                            )
                            st.success(f"✅ Status updated to: {new_status}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")

                st.markdown("---")

                # Add New Funding Round
                with st.form("add_funding_round_form"):
                    st.markdown("#### Add New Funding Round")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        new_round_type = st.selectbox(
                            "Round Type", ["Seed", "Angel", "Series A", "Series B", "Series C+", "Venture"]
                        )
                    with c2:
                        new_amount = st.number_input("Amount (USD)", min_value=0, value=1000000, step=100000)
                    with c3:
                        new_valuation = st.number_input("Valuation (USD)", min_value=0, value=0, step=1000000)
                    new_date = st.date_input("Funding Date", value=datetime.now())
                    new_investors = st.text_input("Investors (comma-separated)", placeholder="Investor A, Investor B")
                    if st.form_submit_button("Add Funding Round"):
                        try:
                            round_doc = {
                                "round_type": new_round_type,
                                "amount": float(new_amount),
                                "date": new_date.strftime("%Y-%m-%d"),
                                "valuation": float(new_valuation) if new_valuation > 0 else None,
                                "investors": [i.strip() for i in new_investors.split(",")] if new_investors else [],
                            }
                            startups_collection.update_one(
                                {"startup_name": selected}, {"$push": {"funding_rounds": round_doc}}
                            )
                            st.success(f"✅ Added {new_round_type} round of ${new_amount:,.0f}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("No matching startups found.")


# ===================== PAGE: DELETE =====================
elif page == "🗑️ Delete Startup":
    st.markdown('<p class="main-header">🗑️ Delete Startup</p>', unsafe_allow_html=True)
    st.warning("⚠️ **Warning:** This action cannot be undone!")

    search_delete = st.text_input("🔎 Search startup to delete", placeholder="Enter startup name...")
    if search_delete:
        matches = list(startups_collection.find(
            {"startup_name": {"$regex": search_delete, "$options": "i"}}, limit=10
        ))
        if matches:
            names = [m["startup_name"] for m in matches]
            selected = st.selectbox("Select Startup to Delete", [""] + names)
            if selected:
                s = startups_collection.find_one({"startup_name": selected})
                st.markdown("---")
                st.error(f"### You are about to delete: **{s['startup_name']}**")

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Industry:** {s.get('industry', 'N/A')}")
                    st.markdown(f"**Country:** {s.get('country', 'N/A')}")
                    st.markdown(f"**Founded:** {s.get('founded_year', 'N/A')}")
                with c2:
                    rounds = s.get("funding_rounds", [])
                    total = sum(safe_num(r.get("amount")) for r in rounds)
                    st.markdown(f"**Funding Rounds:** {len(rounds)}")
                    st.markdown(f"**Total Funding:** ${total:,.0f}")

                st.markdown("---")
                confirm = st.text_input("Type the startup name to confirm deletion:", placeholder=selected)

                c1, c2 = st.columns([1, 3])
                with c1:
                    disabled = (confirm != selected)
                    if st.button("🗑️ Confirm Delete", type="primary", disabled=disabled):
                        try:
                            res = startups_collection.delete_one({"startup_name": selected})
                            if res.deleted_count > 0:
                                st.success(f"✅ Successfully deleted: {selected}")
                                st.balloons()
                            else:
                                st.error("❌ Failed to delete startup")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                with c2:
                    if confirm and confirm != selected:
                        st.warning("⚠️ Name doesn't match. Delete button disabled.")
        else:
            st.info("No matching startups found.")


# ===================== FOOTER =====================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "StartUpLens © 2025 | Team: Abhir Iyer, Krishna Kishore, Nandini Patel | "
    "Applied Database Technologies Project"
    "</div>",
    unsafe_allow_html=True
)
