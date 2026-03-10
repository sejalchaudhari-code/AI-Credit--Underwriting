import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import feedparser
import pdfplumber

from io import BytesIO
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import TableStyle
from reportlab.lib import colors

from model import predict_default


# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="AI Credit Decision Engine", layout="wide")

st.title("🏦 AI Credit Underwriting Dashboard")


# ---------------- DATABASE ----------------
conn = sqlite3.connect("applications.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS applications (
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT,
phone TEXT,
revenue REAL,
debt REAL,
networth REAL,
score REAL,
decision TEXT,
date TEXT
)
""")

conn.commit()


# ---------------- PDF FUNCTION ----------------
def generate_pdf(b):

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(Paragraph(f"Credit Report - {b['name']}", styles["Heading1"]))
    elements.append(Spacer(1,20))

    data = [
        ["Name", b["name"]],
        ["Phone", b["phone"]],
        ["Revenue", b["revenue"]],
        ["Debt", b["debt"]],
        ["Net Worth", b["networth"]],
        ["Score", b["score"]],
        ["Decision", b["decision"]],
        ["Date", b["date"]]
    ]

    table = Table(data)

    table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),1,colors.black)
    ]))

    elements.append(table)

    doc.build(elements)

    buffer.seek(0)

    return buffer


# ---------------- NEWS FUNCTION ----------------
def get_company_news(company):

    query = company.replace(" ","+")
    url = f"https://news.google.com/rss/search?q={query}"

    feed = feedparser.parse(url)

    news = []

    for entry in feed.entries[:5]:

        news.append({
            "title": entry.title,
            "link": entry.link
        })

    return news


# ---------------- FETCH DATA ----------------
def fetch_all():
    return pd.read_sql("SELECT * FROM applications", conn)


# ---------------- SIDEBAR ----------------
page = st.sidebar.selectbox(

"Select Page",

[
"Entity Onboarding",
"Document Upload",
"Credit Analysis",
"Application History",
"Portfolio Analytics"
]

)


# =================================================
# ENTITY ONBOARDING
# =================================================

if page == "Entity Onboarding":

    st.header("🏢 Entity Onboarding")

    company = st.text_input("Company Name")
    cin = st.text_input("CIN")
    pan = st.text_input("PAN")

    sector = st.selectbox(
        "Sector",
        ["Manufacturing","IT","Finance","Retail"]
    )

    turnover = st.number_input("Annual Turnover")

    st.subheader("Loan Details")

    loan_type = st.selectbox(
        "Loan Type",
        ["Working Capital","Term Loan","Business Loan"]
    )

    loan_amount = st.number_input("Loan Amount")

    if st.button("Save Entity"):
        st.success("Entity saved successfully")


# =================================================
# DOCUMENT UPLOAD
# =================================================

elif page == "Document Upload":

    st.header("📂 Upload Documents")

    annual = st.file_uploader("Upload Annual Report", type=["pdf"])

    if annual:

        with pdfplumber.open(annual) as pdf:

            text = ""

            for p in pdf.pages:
                text += p.extract_text()

        st.subheader("Extracted Text")

        st.text(text[:1000])


# =================================================
# CREDIT ANALYSIS
# =================================================

elif page == "Credit Analysis":

    st.sidebar.header("Borrower Details")

    name = st.sidebar.text_input("Name")
    phone = st.sidebar.text_input("Phone")

    revenue = st.sidebar.number_input("Revenue")
    debt = st.sidebar.number_input("Debt")
    networth = st.sidebar.number_input("Net Worth")

    if st.sidebar.button("Run Credit Analysis"):

        default_prob = predict_default(revenue,debt,networth)

        score = (revenue - debt + networth) / 3

        if default_prob < 0.2:
            decision = "Approved"
            risk = "Low Risk"
        elif default_prob < 0.5:
            decision = "Conditional Approval"
            risk = "Moderate Risk"
        else:
            decision = "Rejected"
            risk = "High Risk"


        b = {
            "name":name,
            "phone":phone,
            "revenue":revenue,
            "debt":debt,
            "networth":networth,
            "score":score,
            "decision":decision,
            "date":datetime.now().strftime("%Y-%m-%d")
        }


        c.execute(

        "INSERT INTO applications (name,phone,revenue,debt,networth,score,decision,date) VALUES (?,?,?,?,?,?,?,?)",

        (name,phone,revenue,debt,networth,score,decision,b["date"])

        )

        conn.commit()


        st.subheader(name)

        st.metric("Score", round(score,1))
        st.metric("Default Probability", f"{default_prob*100:.1f}%")
        st.metric("Risk", risk)


# ---------------- GAUGE ----------------

        fig = go.Figure(go.Indicator(

        mode="gauge+number",

        value=default_prob*100,

        title={'text':"Risk Meter"},

        gauge={
        'axis':{'range':[0,100]},
        'steps':[
        {'range':[0,20],'color':'green'},
        {'range':[20,50],'color':'yellow'},
        {'range':[50,100],'color':'red'}
        ]
        }

        ))

        st.plotly_chart(fig,use_container_width=True)


# ---------------- NEWS ----------------

        st.subheader("📰 Company News")

        news = get_company_news(name)

        for n in news:

            st.write("🔹",n["title"])
            st.write(n["link"])


# ---------------- SWOT ----------------

        st.subheader("SWOT Analysis")

        swot = {

        "Strength":"Good revenue growth",
        "Weakness":"Debt exposure",
        "Opportunity":"Market expansion",
        "Threat":"Economic slowdown"

        }

        st.table(swot)


# ---------------- CHART ----------------

        fig2,ax = plt.subplots()

        ax.bar(["Revenue","Debt","NetWorth"],[revenue,debt,networth])

        st.pyplot(fig2)


# ---------------- PDF ----------------

        pdf = generate_pdf(b)

        st.download_button(

        "Download Report",

        pdf,

        file_name=f"{name}_report.pdf"

        )


# =================================================
# APPLICATION HISTORY
# =================================================

elif page == "Application History":

    st.header("Application History")

    df = fetch_all()

    if df.empty:
        st.info("No data yet")
    else:
        st.dataframe(df)


# =================================================
# PORTFOLIO ANALYTICS
# =================================================

elif page == "Portfolio Analytics":

    st.header("Portfolio Analytics")

    df = fetch_all()

    if df.empty:
        st.warning("No data available")

    else:

        fig = go.Figure(

        data=[go.Pie(

        labels=df["decision"],
        values=df["score"],
        hole=0.4

        )]

        )

        st.plotly_chart(fig,use_container_width=True)

        fig2,ax = plt.subplots()

        ax.bar(df["name"],df["score"])

        st.pyplot(fig2)