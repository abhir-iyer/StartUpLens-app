# StartUpLens Web Application

**Team Members:** Abhir Iyer [AI], Krishna Kishore [KK], Nandini Patel [NP]  
**Course:** Applied Database Technologies  
**Database:** MongoDB Atlas (StartUpLensDB)

## 📋 Project Overview

StartUpLens is a web-based application for exploring global startup funding networks. It connects to a MongoDB database containing 21,485+ startup documents with comprehensive funding and investor information.

### Features

✅ **Dashboard** - Interactive visualizations of funding trends, top industries, and geographic distribution  
✅ **Search** - Filter and search startups by name, industry, and country  
✅ **Create** - Add new startups with funding information  
✅ **Update** - Modify startup status and add new funding rounds  
✅ **Delete** - Remove startups with confirmation safeguards  

## 🚀 Quick Start (Local Development)

### Prerequisites

- Python 3.9 or higher
- MongoDB Atlas account (already configured)
- Git

### Installation

1. **Clone or download the project files:**

```bash
mkdir startuplens-app
cd startuplens-app
```

2. **Create these files in your project directory:**

```
startuplens-app/
├── app.py                    # Main application (provided above)
├── requirements.txt          # Dependencies (provided above)
├── .streamlit/
│   └── secrets.toml         # MongoDB credentials (provided above)
└── README.md                # This file
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Set up secrets:**

Create `.streamlit/secrets.toml` with your MongoDB URI:

```toml
[mongo]
uri = "mongodb+srv://<username>:<password>@startuplenscluster.p5eyklh.mongodb.net/"
```

5. **Run the application:**

```bash
streamlit run app.py
```

6. **Open browser:**

The app will automatically open at `http://localhost:8501`

## 🌐 Deployment to Streamlit Cloud (Recommended)

### Step 1: Prepare Repository

1. **Create a GitHub repository:**
   - Go to https://github.com/new
   - Name it `startuplens-app`
   - Make it **public** or **private**

2. **Push your code:**

```bash
git init
git add app.py requirements.txt README.md
git commit -m "Initial commit: StartUpLens web app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/startuplens-app.git
git push -u origin main
```

⚠️ **IMPORTANT:** Do NOT commit `.streamlit/secrets.toml` to GitHub!

### Step 2: Deploy on Streamlit Cloud

1. **Go to:** https://share.streamlit.io/

2. **Sign in** with your GitHub account

3. **Click "New app"**

4. **Configure deployment:**
   - **Repository:** Select your `startuplens-app` repo
   - **Branch:** `main`
   - **Main file path:** `app.py`

5. **Add secrets:**
   - Click "Advanced settings"
   - In the "Secrets" section, paste:

```toml
[mongo]
uri = "mongodb+srv://<username>:<password>@startuplenscluster.p5eyklh.mongodb.net/"
```

6. **Click "Deploy"**

7. **Wait 2-3 minutes** for deployment to complete

8. **Your app will be live at:**
   ```
   https://YOUR_USERNAME-startuplens-app-XXXXX.streamlit.app
   ```

## 📊 Application Structure

### Page 1: Dashboard (📊)
**Contributor: [NP] - Nandini Patel**

- **Key Metrics Cards:** Total startups, funding, industries, countries
- **Visualization 1:** Bar chart - Top 10 industries by funding
- **Visualization 2:** Line chart - Yearly funding trend
- **Visualization 3:** Horizontal bar - Top 10 countries
- **Visualization 4:** Pie chart - Round type distribution

### Page 2: Search Startups (🔍)
**Contributor: [KK] - Krishna Kishore**

- Text search by startup name (regex, case-insensitive)
- Filter by industry dropdown
- Filter by country dropdown
- Display results with expandable cards
- Show funding details, founders, status

### Page 3: Add Startup (➕)
**Contributor: [AI] - Abhir Iyer**

- Form with validation for required fields
- Basic info: name, industry, country, founded year, status
- Optional founders list
- Optional initial funding round
- Success confirmation with document ID

### Page 4: Update Startup (✏️)
**Contributor: [NP] - Nandini Patel**

- Search and select startup
- Update status dropdown
- Add new funding rounds
- Real-time updates to database
- Form validation

### Page 5: Delete Startup (🗑️)
**Contributor: [AI] - Abhir Iyer**

- Search and select startup
- Preview startup details before deletion
- Type-to-confirm safety mechanism
- Confirmation messages

## 🔧 Technology Stack

- **Frontend:** Streamlit 1.31.0
- **Database:** MongoDB Atlas (cloud-hosted)
- **Driver:** PyMongo 4.6.1
- **Visualization:** Plotly 5.18.0
- **Data Processing:** Pandas 2.1.4

## 📝 Authorship & Contributions

### Abhir Iyer [AI]
- **Tasks:** Database connection setup, Add Startup page, Delete Startup page, application structure
- **Hours:** 7 hours

### Krishna Kishore [KK]
- **Tasks:** Search & Filter functionality, READ operations, query optimization
- **Hours:** 7 hours

### Nandini Patel [NP]
- **Tasks:** Dashboard visualizations, Update Startup page, aggregation pipelines
- **Hours:** 7 hours

## 🎯 Meeting Project Requirements

### ✅ CRUD Operations

1. **CREATE** - Add Startup page (form-based insertion)
2. **READ** - Search page + Dashboard (queries with filters)
3. **UPDATE** - Update Startup page (status updates, push funding rounds)
4. **DELETE** - Delete Startup page (with confirmation)

### ✅ Analytical Visualizations

1. Total funding by industry (bar chart)
2. Yearly funding trend (line chart)
3. Geographic distribution (horizontal bar)
4. Round type distribution (pie chart)

### ✅ Database Connection

- Uses existing MongoDB Atlas cluster
- Connection pooling with `@st.cache_resource`
- Error handling and connection testing

## 🔒 Security Notes

- MongoDB credentials stored in Streamlit secrets (not in code)
- No hardcoded passwords in repository
- `.streamlit/secrets.toml` added to `.gitignore`

## 📚 External Resources

### AI Assistance
Application structure, Streamlit components, and visualization layouts were developed with assistance from GitHub Copilot, accessed on January 9, 2025.

### Documentation Referenced
- Streamlit documentation: https://docs.streamlit.io
- PyMongo documentation: https://pymongo.readthedocs.io
- Plotly documentation: https://plotly.com/python/

## 🐛 Troubleshooting

### Local Development Issues

**Issue:** `ModuleNotFoundError: No module named 'streamlit'`
```bash
pip install -r requirements.txt
```

**Issue:** `Database connection failed`
- Check MongoDB Atlas is accessible
- Verify connection string in `.streamlit/secrets.toml`
- Ensure IP address is whitelisted in MongoDB Atlas

**Issue:** App not loading data
- Verify database name is `StartUpLensDB`
- Check collections exist: `startups`, `investors`

### Deployment Issues

**Issue:** App crashes on Streamlit Cloud
- Check secrets are correctly added in Advanced settings
- Review logs in Streamlit Cloud dashboard
- Verify all dependencies in `requirements.txt`

## 📞 Support

For issues or questions:
- **Abhir Iyer:** abhiyer@iu.edu
- **Krishna Kishore:** kmadath@iu.edu
- **Nandini Patel:** nantpate@iu.edu

## 📄 License

This project is submitted as coursework for Applied Database Technologies at Indiana University Bloomington.

---

**Last Updated:** January 9, 2025  
**Version:** 1.0.0
