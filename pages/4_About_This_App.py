# 4_About_This_App.py

import streamlit as st

# ------------------------------------------------
# 📚 Title & Hero Text
# ------------------------------------------------
st.title("📚 About PandasPlayground")

st.success("An interactive data visualization dashboard powered by Streamlit and Plotly.")

# ------------------------------------------------
# 📋 Overview Section
# ------------------------------------------------
st.markdown("---")
st.markdown("### 🚀 Key Highlights")

st.markdown("""
- ✅ **Cleaned and merged datasets** from a complete preprocessing pipeline
- 📊 **Advanced interactive charts** built with Plotly Express
- 🎛️ **Dynamic sidebar filters** for real-time data exploration
- 📈 **KPI cards** summarizing top-level metrics
- 📁 **Multi-page modular layout** for seamless navigation
""")

# ------------------------------------------------
# 🧠 Purpose Section
# ------------------------------------------------
st.markdown("---")
st.markdown("### 🧠 Why This App Exists")

st.markdown("""
This project was designed to:
- 🔍 Explore patterns in sales, profits, and health metrics
- 📦 Build a one-stop reference for Pandas and Plotly visualization workflows
- 🧱 Serve as a reproducible template for future data science dashboards
""")

# ------------------------------------------------
# 💡 Tech Stack Section
# ------------------------------------------------
st.markdown("---")
st.markdown("### 🛠️ Built With")

st.markdown("""
- `Streamlit` — for rapid frontend development
- `Pandas` — for data wrangling
- `Plotly` — for expressive, interactive visualizations
- `Python` — because of course 🐍
""")

# ------------------------------------------------
# 🙌 Final Note
# ------------------------------------------------
st.markdown("---")
st.markdown("### 🙌 Thanks for Visiting!")
st.info("Explore the pages using the sidebar. Each section offers a unique lens into the dataset. Happy analyzing!")
