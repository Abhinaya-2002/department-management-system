import streamlit as st
import sqlite3
import hashlib
import os
from datetime import date, datetime, time as dt_time
import time
import pandas as pd
import base64
import streamlit.components.v1 as components
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import matplotlib.pyplot as plt
import json
import random
from typing import List, Dict
import plotly.express as px
import plotly.graph_objects as go 
from PIL import Image
from datetime import timedelta
import re
# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Department Management System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.markdown("<div id='top'></div>", unsafe_allow_html=True)
# ---------------- PATHS ----------------
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
UPLOAD_DIR = os.path.abspath("uploads")

TIMETABLE_DIR = "timetable_pdfs"
os.makedirs(TIMETABLE_DIR, exist_ok=True)

FEES_DIR = "fees_images"
os.makedirs(FEES_DIR, exist_ok=True)

IMAGE_DIR = "achievement_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

# ---------- DATABASE CONNECTION ----------
conn = sqlite3.connect(
    "dms.db",
    check_same_thread=False,
    timeout=30
)
cur = conn.cursor()
cur.execute("PRAGMA journal_mode=WAL;")
conn.commit()
cur.execute("PRAGMA table_info(syllabus)")
cols = [c[1] for c in cur.fetchall()]

def add_col(col, dtype):
    if col not in cols:
        cur.execute(f"ALTER TABLE syllabus ADD COLUMN {col} {dtype}")

add_col("degree", "TEXT")
add_col("year", "TEXT")
add_col("semester", "TEXT")
add_col("syllabus_type", "TEXT")
add_col("download_count", "INTEGER DEFAULT 0")

conn.commit()
DEGREE_SHORT = {
    "BCA": "bca",
    "B.Sc Computer Science": "bsc_comp_sci",
    "B.Sc Computer Science (AI)": "bsc_comp_sci_ai",
    "B.Sc Information Technology": "bsc_it",
    "M.Sc Computer Science": "msc_cs"
}
# ================= LAB DATABASE FIX =================

def add_column_if_not_exists(table, column, datatype):
    cur.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cur.fetchall()]
    if column not in columns:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {datatype}")
        print(f"Added column {column} to {table}")
        conn.commit()

# Fix lab_sessions table
add_column_if_not_exists("lab_sessions", "lab_room", "TEXT")

# Fix lab_attendance table
add_column_if_not_exists("lab_attendance", "lab_room", "TEXT")
# ---------- LAB CONFIG ----------
LAB_CLASSES = [
    "BSc CS",
    "BSc CS(AI)",
    "BSc IT",
    "BCA",
    "BCom",
    "BCom (IT)",
    "BCom (CA & IT)",
    "English",
    "Tamil",
    "Zoology",
    "History"
]
LAB_YEARS = ["1 YEAR", "2 YEAR", "3 YEAR"]
LAB_ROOMS = [
    "🖥️ Lab 01",
    "🖥️ Lab 02",
    "🖥️ IT Lab 3"
]
TOTAL_SYSTEMS_PER_LAB = {
    "🖥️ Lab 01": 40,
    "🖥️ Lab 02": 35,
    "🖥️ IT Lab 3": 30
}
# ---------------- SESSION ----------------
if "user" not in st.session_state:
    st.session_state.user = None

if "page" not in st.session_state:
    st.session_state.page = "home"

if "show_menu" not in st.session_state:
    st.session_state.show_menu = False

if "logout_clicked" not in st.session_state:
    st.session_state.logout_clicked = False

if "logout_success" not in st.session_state:
    st.session_state.logout_success = False

if "login_time" not in st.session_state:
    st.session_state.login_time = "-"

if "session_duration" not in st.session_state:
    st.session_state.session_duration = "-"
# ---------- SESSION STATE INITIALIZATION ----------
if "user_role" not in st.session_state:
    st.session_state.user_role = None 
# ---------- PUBLIC MENU (BEFORE LOGIN) ----------
public_menu = [
    ("🏠 Home", "home"),
    ("✍️ User Enrollment", "enrollment"),
    ("🔓 Sign In", "login"),
    ("📚 E-Materials", "materials"),
    ("📘 Academic Syllabus", "syllabus"),
    ("🎓 Alumni Meet", "alumni_meet"),
    ("🎤 TED Talk", "ted_talk"),
    ("🧩 Club Activities", "clubs"),
    ("💰 Payment Structure", "fees"),
    ("🕒 Schedule", "schedule"),
    ("📝 Support Desk", "support")
]
# ================= ROLE BASED MENUS =================
admin_menu = [
    ("🏠 Home", "home"),
    ("✍️ User Enrollment", "enrollment"),
    ("📚 E-Materials", "materials"),
    ("📘 Syllabus", "syllabus"),
    ("📝 Assignments", "assignments"),
    ("🧪 Lab Register", "lab_register"),
    ("📊 Daily Lab Report", "daily_lab_report"),
    ("🏆 Excellence Gallery", "excellence_gallery"),
    ("🎓 Alumni", "alumni_meet"),
    ("🎤 TED Talk", "ted_talk"),
    ("🏭 Industrial Academic Venture", "industrial"),
    ("🧩 Club Activity", "clubs"),
    ("📊 Attendance Summary","attendance_summary"),
    ("🕒 Schedule", "schedule"),
    ("💰 Payment Structure", "fees"),
    ("📝 Support Desk", "support"),
    ("🔚 Sign Out", "logout")
]
faculty_menu = [
    ("🏠 Home", "home"),
    ("📚 E-Materials", "materials"),
    ("📘 Syllabus", "syllabus"),
    ("📝 Assignments", "assignments"),
    ("🧪 Lab Register", "lab_register"),
    ("📊 Daily Lab Report", "daily_lab_report"),
    ("🏆 Excellence Gallery", "excellence_gallery"),
    ("🎓 Alumni", "alumni_meet"),
    ("🎤 TED Talk", "ted_talk"),
    ("🏭 Industrial Academic Venture", "industrial"),
    ("🧩 Club Activity", "clubs"),
    ("📊 Attendance Summary","attendance_summary"),
    ("🕒 Schedule", "schedule"),
    ("💰 Payment Structure", "fees"),
    ("📝 Support Desk", "support"),
    ("🔚 Sign Out", "logout")
]
student_menu = [
    ("🏠 Home", "home"),
    ("📚 E-Materials", "materials"),
    ("📘 Syllabus", "syllabus"),
    ("📝 Assignments", "assignments"),
    ("🏆 Excellence Gallery", "excellence_gallery"),
    ("🎓 Alumni", "alumni_meet"),
    ("🎤 TED Talk", "ted_talk"),
    ("🧩 Club Activity", "clubs"),
    ("📊 Attendance Summary","attendance_summary"),
    ("🕒 Schedule", "schedule"),
    ("💰 Payment Structure", "fees"),
    ("📝 Support Desk", "support"),
    ("🔚 Sign Out", "logout")
]
def get_menu_by_role(role):
    if role == "Admin":
        return admin_menu
    elif role == "Faculty":
        return faculty_menu
    elif role == "Student":
        return student_menu
    else:
        return [("🏠 Home", "home")]
# ---------- MENU SELECTION ----------
if st.session_state.get("user_role"):
    menu = get_menu_by_role(st.session_state.user_role)
else:
    menu = public_menu
# ---------------- TABLES----- ----------------
cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    phone TEXT PRIMARY KEY,
    name TEXT,
    password TEXT,
    role TEXT,
    degree TEXT,
    year INTEGER,
    designation TEXT,
    department TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS documents(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    degree TEXT,
    subject TEXT,
    author TEXT,
    filename TEXT,
    uploaded_by TEXT,
    uploaded_on TEXT,
    uploaded_by_role TEXT,
    uploaded_by_phone TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS syllabus_subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    degree TEXT,
    subject TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS student_uploads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    degree TEXT,
    subject TEXT,
    filename TEXT,
    student_phone TEXT,
    status TEXT DEFAULT 'Pending',
    notification TEXT,
    uploaded_on TEXT
)
""")
# Enable foreign key support (VERY IMPORTANT)
cur.execute("PRAGMA foreign_keys = ON;")

cur.execute("""
CREATE TABLE IF NOT EXISTS syllabus (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    degree TEXT NOT NULL,
    syllabus_type TEXT NOT NULL,

    file_path TEXT NOT NULL,

    download_count INTEGER DEFAULT 0,

    uploaded_by TEXT NOT NULL,
    uploaded_date TEXT NOT NULL
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS syllabus_downloads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    syllabus_id INTEGER NOT NULL,
    downloaded_by TEXT,
    downloaded_by_name TEXT,
    downloaded_by_role TEXT,
    download_date TEXT,

    FOREIGN KEY (syllabus_id)
        REFERENCES syllabus(id)
        ON DELETE CASCADE
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS likes (
    doc_id INTEGER,
    phone TEXT,
    UNIQUE(doc_id, phone)
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS comments(
    doc_id INTEGER,
    phone TEXT,
    comment TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS attendance_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    department TEXT,
    year TEXT,
    present INTEGER,
    total_strength INTEGER
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    role TEXT,
    title TEXT,
    category TEXT,
    event_name TEXT,
    level TEXT,
    date TEXT,
    description TEXT,
    image_path TEXT
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    degree TEXT NOT NULL,
    year INTEGER NOT NULL,
    deadline TEXT NOT NULL,
    max_marks INTEGER DEFAULT 100,
    assignment_type TEXT,
    attachment_path TEXT,
    created_by TEXT NOT NULL,
    created_date TEXT NOT NULL
)
""")
cur.execute("""
    CREATE TABLE IF NOT EXISTS assignment_submissions (
        assignment_id INTEGER,
        student_phone TEXT,
        file_path TEXT,
        submitted_on TEXT,
        marks INTEGER,
        feedback TEXT,
        graded_date TEXT,
        PRIMARY KEY (assignment_id, student_phone)
    )
    """)
cur.execute('''
CREATE TABLE IF NOT EXISTS lab_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_date DATE NOT NULL,
    session_name TEXT NOT NULL,
    lab_room TEXT NOT NULL,
    class TEXT NOT NULL,
    year TEXT NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    hours REAL NOT NULL,
    staff_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_date, lab_room, start_time, class, year)
)
''')
cur.execute('''
CREATE TABLE IF NOT EXISTS lab_attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lab_date DATE NOT NULL,
    session_id INTEGER NOT NULL,
    register_no TEXT NOT NULL,
    student_name TEXT NOT NULL,
    class TEXT NOT NULL,
    year TEXT NOT NULL,
    lab_room TEXT NOT NULL,
    system_no INTEGER NOT NULL,
    hours REAL NOT NULL,
    overtime TEXT DEFAULT 'No',
    staff_name TEXT NOT NULL,
    marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, register_no),
    UNIQUE(session_id, lab_room, system_no),
    FOREIGN KEY (session_id) REFERENCES lab_sessions (id)
)
''')
cur.execute('''
CREATE TABLE IF NOT EXISTS lab_staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    staff_name TEXT NOT NULL,
    class TEXT NOT NULL,
    year TEXT NOT NULL,
    lab_subject TEXT NOT NULL,
    lab_name TEXT NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(lab_name, class, year, lab_subject)
)
''')
cur.execute('''
CREATE TABLE IF NOT EXISTS lab_internal_marks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    register_no TEXT NOT NULL,
    student_name TEXT NOT NULL,
    class TEXT NOT NULL,
    year TEXT NOT NULL,
    lab_subject TEXT NOT NULL,
    mark REAL NOT NULL,
    max_mark REAL DEFAULT 10,
    staff_name TEXT NOT NULL,
    evaluated_date DATE DEFAULT CURRENT_DATE,
    remarks TEXT,
    UNIQUE(register_no, lab_subject)
)
''')    
cur.execute('''
CREATE TABLE IF NOT EXISTS lab_equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lab_name TEXT NOT NULL,
    equipment_name TEXT NOT NULL,
    equipment_id TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'Working',
    last_maintenance DATE,
    next_maintenance DATE,
    notes TEXT
)
''')
cur.execute("""
CREATE TABLE IF NOT EXISTS fees_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_path TEXT
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS timetable_pdf (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course TEXT,
    year TEXT,
    file_name TEXT,
    upload_date TEXT,
    timetable_type TEXT
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_phone TEXT,
    category TEXT,
    student_message TEXT,
    faculty_reply TEXT,
    status TEXT DEFAULT 'Open',
    created_at TEXT
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS students (
    register_no TEXT PRIMARY KEY,
    student_name TEXT,
    degree TEXT,
    class TEXT
)
""")
cur.execute("""
    CREATE TABLE IF NOT EXISTS club_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_title TEXT NOT NULL,
        event_date DATE NOT NULL,
        club_name TEXT NOT NULL,
        venue TEXT NOT NULL,
        event_type TEXT,
        faculty_coordinator TEXT,
        hod_name TEXT,
        principal_name TEXT,
        student_coordinators TEXT,
        organized_by TEXT,
        description TEXT,
        highlights TEXT,
        report_path TEXT,
        poster_path TEXT,
        college_header TEXT,
        created_by TEXT,
        status TEXT DEFAULT 'Published',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
cur.execute("""
    CREATE TABLE IF NOT EXISTS club_gallery (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        image_path TEXT NOT NULL,
        uploaded_by TEXT,
        upload_date DATE,
        FOREIGN KEY (event_id) REFERENCES club_reports(id)
    )
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT,          -- Alumni / TED / Club
    title TEXT,
    description TEXT,
    date TEXT,
    venue TEXT,
    image_path TEXT,
    created_by TEXT
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS alumni_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT,
    title TEXT,
    description TEXT,
    date DATE,
    venue TEXT,
    image_path TEXT,
    capacity INTEGER,
    registration_fee REAL,
    contact_person TEXT,
    contact_email TEXT,
    website_url TEXT,
    hashtag TEXT,
    status TEXT DEFAULT 'Upcoming',
    created_by TEXT,
    created_date DATETIME
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS alumni_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_phone TEXT UNIQUE,
    student_name TEXT,
    department TEXT,
    batch_year TEXT,
    email TEXT,
    company TEXT,
    designation TEXT,
    location TEXT,
    linkedin TEXT,
    skills TEXT,
    github TEXT,
    portfolio TEXT,
    interests TEXT,
    achievements TEXT,
    profile_completion INTEGER DEFAULT 0,
    is_visible INTEGER DEFAULT 1,
    created_date DATETIME,
    updated_on DATETIME
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS mentorship_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mentor_id INTEGER,
    mentee_id INTEGER,
    mentee_name TEXT,
    mentee_email TEXT,
    mentee_phone TEXT,
    mentee_year TEXT,
    mentee_department TEXT,
    mentorship_area TEXT,
    status TEXT DEFAULT 'Pending',
    message TEXT,
    created_date DATETIME,
    FOREIGN KEY (mentor_id) REFERENCES alumni_profiles (id),
    FOREIGN KEY (mentee_id) REFERENCES users (phone)
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS job_postings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    posted_by INTEGER,
    company TEXT,
    position TEXT,
    location TEXT,
    job_type TEXT,
    experience_level TEXT,
    salary_range TEXT,
    description TEXT,
    requirements TEXT,
    application_link TEXT,
    posted_date DATETIME,
    expiry_date DATE,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (posted_by) REFERENCES alumni_profiles (id)
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS event_registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    alumni_id INTEGER,
    name TEXT,
    email TEXT,
    phone TEXT,
    batch_year TEXT,
    registration_date DATETIME,
    attendance_status TEXT DEFAULT 'Registered',
    payment_status TEXT DEFAULT 'Pending',
    FOREIGN KEY (event_id) REFERENCES alumni_events (id),
    FOREIGN KEY (alumni_id) REFERENCES alumni_profiles (id)
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS alumni_connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alumni_id INTEGER,
    connected_to_id INTEGER,
    connection_date DATETIME,
    status TEXT DEFAULT 'Connected',
    FOREIGN KEY (alumni_id) REFERENCES alumni_profiles (id),
    FOREIGN KEY (connected_to_id) REFERENCES alumni_profiles (id),
    UNIQUE(alumni_id, connected_to_id)
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS success_stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alumni_id INTEGER,
    title TEXT,
    story TEXT,
    achievement_type TEXT,
    date_achieved DATE,
    featured INTEGER DEFAULT 0,
    approved INTEGER DEFAULT 0,
    created_date DATETIME,
    FOREIGN KEY (alumni_id) REFERENCES alumni_profiles (id)
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS ted_talks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    speaker TEXT NOT NULL,
    duration TEXT,
    talk_category TEXT,
    target_audience TEXT,
    language TEXT,
    max_attendees INTEGER DEFAULT 100,
    recording_consent BOOLEAN DEFAULT 1,
    qna_session BOOLEAN DEFAULT 1,
    networking BOOLEAN DEFAULT 1,
    hashtag TEXT,
    registration_link TEXT,
    poster_path TEXT,
    speaker_path TEXT,
    slides_path TEXT,
    key_points TEXT,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS industrial_ventures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venture_type TEXT,       -- Industrial Visit / MoU / Guest Lecture / Internship
    title TEXT,
    industry_name TEXT,
    description TEXT,
    date TEXT,
    venue TEXT,
    image_path TEXT,
    created_by TEXT
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS announcements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT,
    announce_date TEXT,
    is_new INTEGER DEFAULT 1
)
""")
def add_col(table, col, dtype):
    cur.execute(f"PRAGMA table_info({table})")
    cols = [c[1] for c in cur.fetchall()]
    if col not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {dtype}")
        conn.commit()

add_col("announcements", "pinned", "INTEGER DEFAULT 0")
add_col("announcements", "expiry_date", "TEXT")
add_col("announcements", "alert_sent", "INTEGER DEFAULT 0")
conn.commit()
def strip_html_tags(text):
    if not text:
        return ""
    # Remove everything after first <
    if "<" in text:
        text = text.split("<")[0]
    return text.strip()
def generate_comprehensive_report(report_date, selected_lab, conn):
    """Generate a comprehensive lab report"""
    
    with st.spinner("🔍 Analyzing lab data..."):
        # ================= OVERVIEW SECTION =================
        st.markdown("## 📋 Executive Summary")
        
        # Get overall statistics
        if selected_lab == "All Labs":
            overview_query = """
                SELECT 
                    COUNT(DISTINCT register_no) as total_students,
                    COUNT(DISTINCT session_id) as total_sessions,
                    ROUND(SUM(hours), 2) as total_hours,
                    COUNT(DISTINCT lab_room) as labs_used,
                    COUNT(DISTINCT system_no) as systems_used
                FROM lab_attendance 
                WHERE lab_date = ?
            """
            params = (str(report_date),)
        else:
            overview_query = """
                SELECT 
                    COUNT(DISTINCT register_no) as total_students,
                    COUNT(DISTINCT session_id) as total_sessions,
                    ROUND(SUM(hours), 2) as total_hours,
                    COUNT(DISTINCT system_no) as systems_used
                FROM lab_attendance 
                WHERE lab_date = ? AND lab_room = ?
            """
            params = (str(report_date), selected_lab)
        
        overview_df = pd.read_sql(overview_query, conn, params=params)
        
        if overview_df.empty or overview_df.iloc[0]["total_students"] == 0:
            st.warning(f"No lab activity found for {report_date}")
            return
        
        # Display metrics
        metric_cols = st.columns(5 if selected_lab == "All Labs" else 4)
        
        metrics = [
            ("👨‍🎓 Total Students", overview_df.iloc[0]["total_students"]),
            ("📅 Total Sessions", overview_df.iloc[0]["total_sessions"]),
            ("⏱️ Total Hours", f"{overview_df.iloc[0]['total_hours']:.1f}"),
            ("💻 Systems Used", overview_df.iloc[0]["systems_used"])
        ]
        
        if selected_lab == "All Labs":
            metrics.append(("🏫 Labs Used", overview_df.iloc[0]["labs_used"]))
        
        for idx, (label, value) in enumerate(metrics):
            with metric_cols[idx]:
                st.metric(label, value)
        
        # ================= DETAILED BREAKDOWN =================
        st.markdown("## 📊 Detailed Analysis")
        
        # Get detailed data
        if selected_lab == "All Labs":
            detail_query = """
                SELECT 
                    lab_room as "Lab",
                    class as "Class",
                    year as "Year",
                    COUNT(DISTINCT register_no) as "Students",
                    COUNT(DISTINCT session_id) as "Sessions",
                    ROUND(SUM(hours), 2) as "Hours",
                    COUNT(DISTINCT system_no) as "Systems Used",
                    ROUND((COUNT(DISTINCT system_no) * 100.0 / 60), 1) as "Utilization %"
                FROM lab_attendance 
                WHERE lab_date = ?
                GROUP BY lab_room, class, year
                ORDER BY lab_room, class, year
            """
            detail_df = pd.read_sql(detail_query, conn, params=(str(report_date),))
        else:
            detail_query = """
                SELECT 
                    class as "Class",
                    year as "Year",
                    COUNT(DISTINCT register_no) as "Students",
                    COUNT(DISTINCT session_id) as "Sessions",
                    ROUND(SUM(hours), 2) as "Hours",
                    COUNT(DISTINCT system_no) as "Systems Used",
                    ROUND((COUNT(DISTINCT system_no) * 100.0 / 60), 1) as "Utilization %"
                FROM lab_attendance 
                WHERE lab_date = ? AND lab_room = ?
                GROUP BY class, year
                ORDER BY class, year
            """
            detail_df = pd.read_sql(detail_query, conn, params=(str(report_date), selected_lab))
        
        # Display detailed table
        st.dataframe(detail_df, use_container_width=True)
        
        # ================= VISUALIZATIONS =================
        st.markdown("## 📈 Data Visualizations")
        
        viz_tabs = st.tabs(["📊 Bar Charts", "🥧 Pie Charts", "📈 Trends"])
        
        with viz_tabs[0]:
            # Bar charts
            col1, col2 = st.columns(2)
            
            with col1:
                if selected_lab == "All Labs":
                    # Students per lab
                    lab_students = detail_df.groupby("Lab")["Students"].sum().reset_index()
                    fig = px.bar(lab_students, x="Lab", y="Students",
                                title="Students per Lab",
                                color="Lab",
                                color_discrete_sequence=px.colors.qualitative.Set3)
                else:
                    # Students per class
                    fig = px.bar(detail_df, x="Class", y="Students",
                                title=f"Students per Class - {selected_lab}",
                                color="Class",
                                color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Hours distribution
                if selected_lab == "All Labs":
                    lab_hours = detail_df.groupby("Lab")["Hours"].sum().reset_index()
                    fig = px.bar(lab_hours, x="Lab", y="Hours",
                                title="Hours per Lab",
                                color="Lab",
                                color_discrete_sequence=px.colors.qualitative.Set2)
                else:
                    fig = px.bar(detail_df, x="Class", y="Hours",
                                title=f"Hours per Class - {selected_lab}",
                                color="Class",
                                color_discrete_sequence=px.colors.qualitative.Pastel1)
                st.plotly_chart(fig, use_container_width=True)
        
        with viz_tabs[1]:
            # Pie charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Students distribution
                if selected_lab == "All Labs":
                    total_students = detail_df.groupby("Lab")["Students"].sum()
                    fig = px.pie(values=total_students.values, 
                                names=total_students.index,
                                title="Student Distribution by Lab",
                                hole=0.4)
                else:
                    fig = px.pie(detail_df, values="Students", names="Class",
                                title=f"Student Distribution - {selected_lab}",
                                hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Hours distribution
                if selected_lab == "All Labs":
                    total_hours = detail_df.groupby("Lab")["Hours"].sum()
                    fig = px.pie(values=total_hours.values, 
                                names=total_hours.index,
                                title="Hours Distribution by Lab",
                                hole=0.4)
                else:
                    fig = px.pie(detail_df, values="Hours", names="Class",
                                title=f"Hours Distribution - {selected_lab}",
                                hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
        
        with viz_tabs[2]:
            # Utilization trends
            if selected_lab == "All Labs":
                # Lab utilization comparison
                fig = px.bar(detail_df, x="Lab", y="Utilization %",
                            color="Class",
                            title="Lab Utilization by Class",
                            barmode="group")
                st.plotly_chart(fig, use_container_width=True)
            else:
                # Class utilization
                fig = px.bar(detail_df, x="Class", y="Utilization %",
                            color="Year",
                            title=f"Utilization by Class & Year - {selected_lab}",
                            barmode="group")
                st.plotly_chart(fig, use_container_width=True)
        
        # ================= TIME ANALYSIS =================
        st.markdown("## 🕒 Time Analysis")
        
        # Get hourly distribution
        if selected_lab == "All Labs":
            time_query = """
                SELECT 
                    strftime('%H:00', s.start_time) as Hour,
                    COUNT(DISTINCT a.register_no) as Students,
                    COUNT(DISTINCT a.session_id) as Sessions
                FROM lab_attendance a
                JOIN lab_sessions s ON a.session_id = s.id
                WHERE a.lab_date = ?
                GROUP BY strftime('%H', s.start_time)
                ORDER BY Hour
            """
            time_df = pd.read_sql(time_query, conn, params=(str(report_date),))
        else:
            time_query = """
                SELECT 
                    strftime('%H:00', s.start_time) as Hour,
                    COUNT(DISTINCT a.register_no) as Students,
                    COUNT(DISTINCT a.session_id) as Sessions
                FROM lab_attendance a
                JOIN lab_sessions s ON a.session_id = s.id
                WHERE a.lab_date = ? AND a.lab_room = ?
                GROUP BY strftime('%H', s.start_time)
                ORDER BY Hour
            """
            time_df = pd.read_sql(time_query, conn, params=(str(report_date), selected_lab))
        
        if not time_df.empty:
            fig = px.line(time_df, x="Hour", y="Students",
                         title="Hourly Student Distribution",
                         markers=True)
            st.plotly_chart(fig, use_container_width=True)
        
        # ================= SYSTEM ANALYSIS =================
        st.markdown("## 💻 System Utilization Analysis")
        
        # Get system usage pattern
        if selected_lab == "All Labs":
            system_query = """
                SELECT 
                    lab_room as Lab,
                    system_no as System,
                    COUNT(*) as Usage_Count
                FROM lab_attendance 
                WHERE lab_date = ?
                GROUP BY lab_room, system_no
                ORDER BY lab_room, system_no
            """
            system_df = pd.read_sql(system_query, conn, params=(str(report_date),))
            
            if not system_df.empty:
                # Heatmap of system usage
                pivot_df = system_df.pivot_table(values='Usage_Count', 
                                                index='System', 
                                                columns='Lab', 
                                                fill_value=0)
                
                fig = px.imshow(pivot_df,
                              title="System Usage Heatmap",
                              labels=dict(x="Lab", y="System Number", color="Usage Count"),
                              color_continuous_scale="Viridis")
                st.plotly_chart(fig, use_container_width=True)
        else:
            system_query = """
                SELECT 
                    system_no as System,
                    COUNT(*) as Usage_Count,
                    class as Class
                FROM lab_attendance 
                WHERE lab_date = ? AND lab_room = ?
                GROUP BY system_no, class
                ORDER BY system_no
            """
            system_df = pd.read_sql(system_query, conn, params=(str(report_date), selected_lab))
            
            if not system_df.empty:
                # Most used systems
                fig = px.bar(system_df.nlargest(10, 'Usage_Count'), 
                           x='System', y='Usage_Count', color='Class',
                           title=f"Top 10 Most Used Systems - {selected_lab}")
                st.plotly_chart(fig, use_container_width=True)
        
        # ================= EXPORT SECTION =================
        st.markdown("## 📥 Export Report")
        
        # Create Excel report
        excel_file = f"Lab_Report_{report_date}_{selected_lab.replace(' ', '_')}.xlsx"
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # Summary sheet
            overview_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Detailed sheet
            detail_df.to_excel(writer, sheet_name='Detailed', index=False)
            
            # Time analysis sheet
            if not time_df.empty:
                time_df.to_excel(writer, sheet_name='Time Analysis', index=False)
            
            # System analysis sheet
            if 'system_df' in locals() and not system_df.empty:
                system_df.to_excel(writer, sheet_name='System Analysis', index=False)
            
            # Raw data sheet
            if selected_lab == "All Labs":
                raw_query = """
                    SELECT 
                        a.lab_date as Date,
                        a.lab_room as Lab,
                        a.class as Class,
                        a.year as Year,
                        a.register_no as Register_No,
                        a.student_name as Student_Name,
                        a.system_no as System_No,
                        a.hours as Hours,
                        s.session_name as Subject,
                        s.start_time as Start_Time,
                        s.end_time as End_Time,
                        a.staff_name as Staff
                    FROM lab_attendance a
                    JOIN lab_sessions s ON a.session_id = s.id
                    WHERE a.lab_date = ?
                    ORDER BY a.lab_room, a.class, a.year
                """
                raw_df = pd.read_sql(raw_query, conn, params=(str(report_date),))
            else:
                raw_query = """
                    SELECT 
                        a.lab_date as Date,
                        a.class as Class,
                        a.year as Year,
                        a.register_no as Register_No,
                        a.student_name as Student_Name,
                        a.system_no as System_No,
                        a.hours as Hours,
                        s.session_name as Subject,
                        s.start_time as Start_Time,
                        s.end_time as End_Time,
                        a.staff_name as Staff
                    FROM lab_attendance a
                    JOIN lab_sessions s ON a.session_id = s.id
                    WHERE a.lab_date = ? AND a.lab_room = ?
                    ORDER BY a.class, a.year
                """
                raw_df = pd.read_sql(raw_query, conn, params=(str(report_date), selected_lab))
            
            raw_df.to_excel(writer, sheet_name='Raw Data', index=False)
        
        # Download button
        with open(excel_file, "rb") as f:
            st.download_button(
                label="📥 Download Complete Report (Excel)",
                data=f,
                file_name=excel_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        # Also provide CSV option
        csv_data = detail_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Summary (CSV)",
            data=csv_data,
            file_name=f"lab_summary_{report_date}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    st.success(f"✅ Report generated successfully for {report_date}")
def get_lab_occupancy(lab_room, session_id, conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT system_no
        FROM lab_attendance
        WHERE lab_room=? AND session_id=?
    """, (lab_room, session_id))
    return {r[0] for r in cur.fetchall()}
def show_pdf_preview(file_path):
    """Function to display PDF preview"""
    try:
        if os.path.exists(file_path):
            # Display PDF using base64 encoding
            with open(file_path, "rb") as f:
                base64_pdf = base64.b64encode(f.read()).decode('utf-8')
            
            # PDF display with download option
            pdf_display = f"""
            <div class="pdf-viewer">
                <iframe src="data:application/pdf;base64,{base64_pdf}" 
                        width="100%" 
                        height="600px" 
                        style="border: none;">
                </iframe>
            </div>
            """
            st.markdown(pdf_display, unsafe_allow_html=True)
            
            # Download button
            with open(file_path, "rb") as file:
                st.download_button(
                    label="📥 Download This PDF",
                    data=file,
                    file_name=os.path.basename(file_path),
                    mime="application/pdf",
                    use_container_width=True
                )
        else:
            st.error("File not found. It may have been deleted.")
    except Exception as e:
        st.error(f"Error displaying PDF: {str(e)}")
def extract_from_description(description, field, default):
    """Extract field value from description text"""
    try:
        if field in description:
            lines = description.split('\n')
            for line in lines:
                if line.startswith(f"**{field}**") or line.startswith(field):
                    return line.replace(f"**{field}**", "").replace(field, "").strip()
        return default
    except:
        return default
# ================= UI UTILITY FUNCTIONS =================
def create_card(icon, title, content, button_text=None, button_action=None):
    """Create a modern card component"""
    button_html = ""
    if button_text:
        if button_action:
            button_html = f"""
            <button onclick="{button_action}" class="primary-btn" style="margin-top: 1rem; width: 100%;">
                {button_text}
            </button>
            """
        else:
            button_html = f"""
            <button class="primary-btn" style="margin-top: 1rem; width: 100%;">
                {button_text}
            </button>
            """
    
    html = f"""
    <div class="custom-card">
        <div class="card-header">
            <span class="card-icon">{icon}</span>
            <h3 class="card-title">{title}</h3>
        </div>
        <div class="card-content">{content}</div>
        {button_html}
    </div>
    """
    return html

def create_header(title, subtitle=None):
    """Create a modern header section"""
    subtitle_html = f'<p>{subtitle}</p>' if subtitle else ''
    html = f"""
    <div class="main-header">
        <h1>{title}</h1>
        {subtitle_html}
    </div>
    """
    return html
    # ---------- ANNOUNCEMENTS SECTION ----------
    with col_ann:

        st.subheader("📢 Latest Announcements")

        cur.execute("""
            SELECT message, announce_date, pinned, expiry_date 
            FROM announcements 
            WHERE (expiry_date IS NULL OR expiry_date >= date('now'))
            ORDER BY pinned DESC, announce_date DESC 
            LIMIT 5
        """)
        announcements = cur.fetchall()

        if announcements:
            for msg, date_val, pinned, expiry in announcements:

                clean_msg = strip_html_tags(str(msg))
                clean_expiry = strip_html_tags(str(expiry)) if expiry else None

                icon = "📌" if pinned else "📢"

                with st.container():
                    st.markdown(f"### {icon} {clean_msg}")
                    st.caption(f"📅 {date_val}")

                    if clean_expiry:
                        st.caption(f"⏳ Expires: {clean_expiry}")

                    st.divider()

        else:
            st.info("No announcements at this time.")
    # ---------- ACHIEVEMENTS SECTION ----------
    with col_ach:
        st.markdown("""
            <div style="margin-bottom: 1.5rem;">
                <h2 style="color: #1e40af; font-size: 28px; font-weight: 800; 
                    background: linear-gradient(90deg, #1e40af, #2563eb);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    display: inline-block;
                    animation: fadeInDown 0.8s ease-out 0.3s both;">
                    🏆 Recent Achievements
                </h2>
                <p style="color: #64748b; margin-top: 5px; animation: fadeInUp 0.8s ease-out 0.4s both;">
                    Click on any achievement to view details
                </p>
            </div>
        """, unsafe_allow_html=True)

        # Initialize session state for achievement details
        if 'selected_achievement' not in st.session_state:
            st.session_state.selected_achievement = None

        # Level icons and colors
        level_colors = {
            "International": "#8b5cf6",
            "National": "#3b82f6", 
            "State": "#10b981",
            "District": "#f59e0b",
            "College": "#6b7280"
        }
        
        level_icons = {
            "International": "🌍",
            "National": "🇮🇳",
            "State": "🗺️",
            "District": "🏙️",
            "College": "🏛️"
        }

        # Fetch recent achievements
        cur.execute("""
            SELECT id, name, role, title, category, event_name, level, date, description, image_path
            FROM achievements 
            ORDER BY date DESC 
            LIMIT 3
        """)
        recent_achievements = cur.fetchall()

        if recent_achievements:
            for idx, ach in enumerate(recent_achievements):
                ach_id, name, role, title, category, event_name, level, ach_date, description, image_path = ach
                
                # Strip HTML tags from all text fields
                clean_name = strip_html_tags(str(name))
                clean_role = strip_html_tags(str(role))
                clean_title = strip_html_tags(str(title))
                clean_category = strip_html_tags(str(category))
                clean_level = strip_html_tags(str(level))
                
                color = level_colors.get(level, "#3b82f6")
                level_icon = level_icons.get(level, "🏆")
                
                # Achievement card
                st.markdown(f"""
                <div class="achievement-mini-card" style="border-left-color: {color}; animation-delay: {0.1 * idx}s;">
                    <div style="display: flex; align-items: flex-start; gap: 12px;">
                        <div style="font-size: 32px;">{level_icon}</div>
                        <div style="flex: 1;">
                            <span class="level-badge" style="background: {color}15; color: {color};">{clean_level}</span>
                            <div class="achievement-title">{clean_title[:60]}{'...' if len(clean_title) > 60 else ''}</div>
                            <div style="color: #475569; font-size: 13px; font-weight: 500;">
                                {clean_name} • {clean_role}
                            </div>
                            <div class="achievement-meta">
                                <span>📅 {ach_date}</span>
                                <span>📂 {clean_category}</span>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # View details button
                if st.button(f"🔍 View Details", key=f"ach_btn_{ach_id}", use_container_width=True):
                    st.session_state.selected_achievement = ach_id
                    st.rerun()
            
            # Show achievement details if one is selected
            if st.session_state.selected_achievement:
                cur.execute("""
                    SELECT name, role, title, category, event_name, level, date, description, image_path
                    FROM achievements WHERE id = ?
                """, (st.session_state.selected_achievement,))
                full_ach = cur.fetchone()
                
                if full_ach:
                    name, role, title, category, event_name, level, ach_date, description, image_path = full_ach
                    
                    # Strip HTML tags from all text fields
                    clean_name = strip_html_tags(str(name))
                    clean_role = strip_html_tags(str(role))
                    clean_title = strip_html_tags(str(title))
                    clean_category = strip_html_tags(str(category))
                    clean_level = strip_html_tags(str(level))
                    clean_event_name = strip_html_tags(str(event_name)) if event_name else ""
                    clean_description = strip_html_tags(str(description)) if description else ""
                    
                    level_icon = level_icons.get(level, "🏆")
                    color = level_colors.get(level, "#3b82f6")
                    
                    # Create image HTML if exists
                    image_html = ""
                    if image_path and os.path.exists(image_path):
                        try:
                            img = Image.open(image_path)
                            # Resize image for better display
                            max_size = (400, 300)
                            img.thumbnail(max_size, Image.Resampling.LANCZOS)
                            
                            # Save to bytes for display
                            from io import BytesIO
                            img_bytes = BytesIO()
                            img.save(img_bytes, format='PNG')
                            img_bytes = img_bytes.getvalue()
                            img_base64 = base64.b64encode(img_bytes).decode()
                            
                            image_html = f"""
                            <div class="detail-section">
                                <h4>🖼️ Achievement Image</h4>
                                <div class="achievement-image-container">
                                    <img src="data:image/png;base64,{img_base64}" alt="Achievement Image" style="width: 100%; border-radius: 10px;">
                                </div>
                            </div>
                            """
                        except Exception as e:
                            print(f"Error loading image: {e}")
                    
                    st.markdown(f"""
                    <div class="achievement-detail">
                        <div class="detail-header">
                            <div class="detail-icon">{level_icon}</div>
                            <div style="flex: 1;">
                                <h3 class="detail-title">{clean_title}</h3>
                                <p class="detail-subtitle">{clean_category} Achievement • {clean_level} Level</p>
                            </div>
                        </div>
                        
                        <div class="detail-grid">
                            <div class="detail-item">
                                <div class="detail-item-label">👤 Name</div>
                                <div class="detail-item-value">{clean_name}</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-item-label">🎓 Role</div>
                                <div class="detail-item-value">{clean_role}</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-item-label">📅 Date</div>
                                <div class="detail-item-value">{ach_date}</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-item-label">🏆 Level</div>
                                <div class="detail-item-value" style="color: {color};">{clean_level}</div>
                            </div>
                        </div>
                        
                        {f'<div class="detail-item" style="grid-column: span 2;"><div class="detail-item-label">🎯 Event</div><div class="detail-item-value">{clean_event_name}</div></div>' if clean_event_name else ''}
                        
                        <div class="detail-section">
                            <h4>📋 Achievement Description</h4>
                            <p style="color: #475569; line-height: 1.6; margin: 0;">{clean_description}</p>
                        </div>
                        
                        {image_html}
                        
                        <div style="text-align: center; margin-top: 1.5rem;">
                            <button class="close-button" onclick="document.getElementById('close_ach').click()">Close</button>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Close", key="close_ach", use_container_width=True):
                        st.session_state.selected_achievement = None
                        st.rerun()
            
            # View all button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🌟 View All Achievements", type="primary", use_container_width=True):
                    st.session_state.page = "excellence_gallery"
                    st.rerun()
        else:
            st.info("No achievements added yet. Be the first to achieve!")

    # Also update the ticker section:
    # Fetch latest announcements for ticker
    cur.execute("""
        SELECT message FROM announcements 
        WHERE (expiry_date IS NULL OR expiry_date >= date('now'))
        ORDER BY pinned DESC, announce_date DESC 
        LIMIT 10
    """)
    ticker_announcements = cur.fetchall()

    if ticker_announcements:
        ticker_html = '<div class="announcement-ticker"><div class="ticker-content">'
        
        for msg in ticker_announcements:
            clean_msg = strip_html_tags(str(msg[0]))
            ticker_html += f'<span class="ticker-item">📢 {clean_msg}</span>'
        
        ticker_html += '</div></div>'
        st.markdown(ticker_html, unsafe_allow_html=True)

    # And update the admin recent announcements section:
    with col2:
        st.subheader("Recent Announcements")
        cur.execute("""
            SELECT message, announce_date, pinned 
            FROM announcements 
            ORDER BY announce_date DESC 
            LIMIT 5
        """)
        recent = cur.fetchall()
        if recent:
            for msg, dte, pinned in recent:
                pin_icon = "📌 " if pinned else "📢 "
                clean_msg = strip_html_tags(str(msg))
                st.info(f"{pin_icon}**{dte}:** {clean_msg[:100]}...")
        else:
            st.info("No recent announcements")
def create_welcome_banner(name, role):
    return f"""
    <div class="welcome-banner">
        <h3>👋 Welcome back, {name}!</h3>
        <p>You are logged in as <strong>{role}</strong>. Access all department features below.</p>
    </div>
    """
# Add this at the very beginning of your ted_talk page, after establishing database connection
def initialize_ted_talks_table():
    """Add missing columns to events table for TED Talks"""
    try:
        # Check if columns exist and add them if they don't
        cur.execute("PRAGMA table_info(events)")
        existing_columns = [column[1] for column in cur.fetchall()]
        
        columns_to_add = {
            "capacity": "INTEGER DEFAULT 0",
            "reg_fee": "REAL DEFAULT 0",
            "contact_person": "TEXT",
            "contact_email": "TEXT",
            "website_url": "TEXT",
            "hashtag": "TEXT",
            "extra_data": "TEXT"
        }
        
        for col_name, col_type in columns_to_add.items():
            if col_name not in existing_columns:
                try:
                    cur.execute(f"ALTER TABLE events ADD COLUMN {col_name} {col_type}")
                    conn.commit()
                    print(f"✅ Added column: {col_name}")
                except Exception as e:
                    print(f"⚠️ Could not add column {col_name}: {e}")
        
        # Also check if we need to add extra_data_json alias or other specific columns
        if "extra_data_json" not in existing_columns and "extra_data" not in existing_columns:
            cur.execute("ALTER TABLE events ADD COLUMN extra_data TEXT")
            conn.commit()
            print("✅ Added column: extra_data")
            
    except Exception as e:
        print(f"❌ Error initializing TED Talks table: {e}")

# Call this function at the start of your ted_talk page
initialize_ted_talks_table()
# ---------- ALUMNI HELPER FUNCTIONS ----------
def calculate_profile_completion(profile_data):
    """Calculate profile completion percentage"""
    completion = 0
    fields = [
        ('student_name', 15),
        ('department', 15),
        ('batch_year', 15),
        ('email', 10),
        ('company', 15),
        ('designation', 15),
        ('location', 10),
        ('linkedin', 5)
    ]
    
    for field, weight in fields:
        if profile_data.get(field):
            completion += weight
    
    return min(completion, 100)

def get_alumni_statistics():
    """Get comprehensive alumni statistics"""
    stats = {}
    
    # Total alumni
    cur.execute("SELECT COUNT(*) FROM alumni_profiles WHERE is_visible = 1")
    stats['total_alumni'] = cur.fetchone()[0]
    
    # Active profiles
    cur.execute("SELECT COUNT(*) FROM alumni_profiles WHERE updated_on >= date('now', '-6 months')")
    stats['active_alumni'] = cur.fetchone()[0]
    
    # Departments
    cur.execute("SELECT COUNT(DISTINCT department) FROM alumni_profiles WHERE department IS NOT NULL")
    stats['departments'] = cur.fetchone()[0]
    
    # Companies
    cur.execute("SELECT COUNT(DISTINCT company) FROM alumni_profiles WHERE company IS NOT NULL")
    stats['companies'] = cur.fetchone()[0]
    
    # Locations
    cur.execute("SELECT COUNT(DISTINCT location) FROM alumni_profiles WHERE location IS NOT NULL")
    stats['locations'] = cur.fetchone()[0]
    
    # LinkedIn profiles
    cur.execute("SELECT COUNT(*) FROM alumni_profiles WHERE linkedin IS NOT NULL")
    stats['linkedin_profiles'] = cur.fetchone()[0]
    
    # Profile completion average
    cur.execute("SELECT AVG(profile_completion) FROM alumni_profiles")
    stats['avg_completion'] = round(cur.fetchone()[0] or 0, 1)
    
    return stats

def get_top_companies():
    """Get top companies where alumni work"""
    cur.execute("""
        SELECT company, COUNT(*) as count
        FROM alumni_profiles
        WHERE company IS NOT NULL AND company != ''
        GROUP BY company
        ORDER BY count DESC
        LIMIT 8
    """)
    return cur.fetchall()

def get_success_stories(limit=4):
    """Get featured success stories"""
    cur.execute("""
        SELECT p.student_name, p.department, p.batch_year, 
               p.company, p.designation, p.location, s.title, s.story
        FROM alumni_profiles p
        LEFT JOIN success_stories s ON p.id = s.alumni_id
        WHERE s.featured = 1 OR s.approved = 1
        ORDER BY s.date_achieved DESC
        LIMIT ?
    """, (limit,))
    return cur.fetchall()

def export_alumni_data(format='csv'):
    """Export alumni data in specified format"""
    cur.execute("""
        SELECT student_name, department, batch_year, email, 
               company, designation, location, linkedin
        FROM alumni_profiles
        WHERE is_visible = 1
        ORDER BY updated_on DESC
    """)
    
    data = cur.fetchall()
    df = pd.DataFrame(data, columns=['Name', 'Department', 'Batch', 'Email', 
                                     'Company', 'Designation', 'Location', 'LinkedIn'])
    
    if format == 'csv':
        return df.to_csv(index=False)
    elif format == 'excel':
        return df.to_excel(index=False)
    elif format == 'json':
        return df.to_json(orient='records')
    
    return df.to_string(index=False)

# ================= HELPER FUNCTIONS =================
def hash_pwd(p):
    return hashlib.sha256(p.encode()).hexdigest()

def safe_image(path, width=None, use_container_width=False):
    if os.path.exists(path):
        st.image(path, width=width, use_container_width=use_container_width)
    else:
        st.warning(f"⚠️ Image not found: {os.path.basename(path)}")

def img_to_base64(img_path):
    if not os.path.exists(img_path):
        return ""
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()
def clean_html(text):
    """Remove unwanted span tags if already stored in DB"""
    if not text:
        return ""
    return (
        text.replace('<span class="ticker-item">', '')
            .replace('</span>', '')
            .strip()
    )
# =============================
def display_achievements_gallery(conn, cur, max_items=6):
    """
    Display achievements gallery on homepage
    """
    st.markdown("---")
    
    # Header with styling
    st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <h2 style="color: #2E86AB; margin-bottom: 5px;">🏆 Excellence Gallery</h2>
            <p style="color: #666; font-size: 16px;">Celebrating Success & Achievements</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Fetch achievements from database
    cur.execute("""
        SELECT id, name, role, title, category, 
               event_name, level, date, description, image_path
        FROM achievements 
        ORDER BY date DESC 
        LIMIT ?
    """, (max_items,))
    rows = cur.fetchall()
    
    if not rows:
        st.info("🎯 No achievements added yet. Be the first to achieve!")
        return
    
    # Create columns for the gallery
    cols = st.columns(3)
    
    # Color palette for different categories
    category_colors = {
        "Academic": "#4A90E2",
        "Sports": "#50C878",
        "Cultural": "#FF6B6B",
        "Technical": "#FFA500",
        "Other": "#9B59B6"
    }
    
    # Level icons
    level_icons = {
        "College": "🏛️",
        "District": "🏙️",
        "State": "🗺️",
        "National": "🇮🇳",
        "International": "🌍"
    }
    
    for idx, r in enumerate(rows):
        with cols[idx % 3]:
            # Create card container
            with st.container():
                # Card styling
                st.markdown(f"""
                    <div style="
                        border-radius: 12px;
                        padding: 20px;
                        margin-bottom: 20px;
                        background: white;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                        border-left: 5px solid {category_colors.get(r[4], '#4A90E2')};
                        transition: transform 0.3s ease;
                        height: 100%;
                    ">
                """, unsafe_allow_html=True)
                
                # Achievement image or placeholder
                if r[9] and os.path.exists(r[9]):
                    try:
                        img = Image.open(r[9])
                        # Create modal for image
                        img_key = f"img_modal_{r[0]}"
                        if st.button(f"🏆 View Achievement", key=f"view_{r[0]}"):
                            st.session_state[img_key] = not st.session_state.get(img_key, False)
                        
                        if st.session_state.get(img_key, False):
                            with st.expander("📸 Achievement Details", expanded=True):
                                st.image(img, use_column_width=True)
                                st.markdown(f"""
                                    <div style="padding: 15px; background: #f8f9fa; border-radius: 8px; margin-top: 10px;">
                                        <h4 style="color: #2c3e50;">{r[3]}</h4>
                                        <p><strong>👤 Name:</strong> {r[1]}</p>
                                        <p><strong>🎓 Role:</strong> {r[2]}</p>
                                        <p><strong>📅 Date:</strong> {r[7]}</p>
                                        <p>{r[8]}</p>
                                    </div>
                                """, unsafe_allow_html=True)
                    except:
                        st.image("https://via.placeholder.com/300x200/4A90E2/FFFFFF?text=Achievement", 
                                use_column_width=True)
                else:
                    # Colorful placeholder based on category
                    color = category_colors.get(r[4], "#4A90E2")
                    st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, {color}, {color}99);
                            height: 180px;
                            border-radius: 10px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            margin-bottom: 15px;
                        ">
                            <span style="font-size: 48px; color: white;">🏆</span>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Achievement title
                st.markdown(f"""
                    <h4 style="
                        color: #2c3e50;
                        margin-top: 0;
                        margin-bottom: 10px;
                        font-size: 18px;
                        line-height: 1.4;
                    ">{r[3]}</h4>
                """, unsafe_allow_html=True)
                
                # Achievement details
                st.markdown(f"""
                    <div style="color: #666; font-size: 14px; line-height: 1.5;">
                        <p style="margin: 5px 0;"><strong>👤</strong> {r[1]}</p>
                        <p style="margin: 5px 0;">
                            <span style="
                                background: {category_colors.get(r[4], '#4A90E2')}15;
                                color: {category_colors.get(r[4], '#4A90E2')};
                                padding: 2px 8px;
                                border-radius: 12px;
                                font-size: 12px;
                            ">📂 {r[4]}</span>
                        </p>
                        <p style="margin: 5px 0;">
                            {level_icons.get(r[6], '🏆')} <strong>{r[6]}</strong>
                        </p>
                        <p style="margin: 5px 0; color: #888; font-size: 13px;">
                            📅 {r[7]}
                        </p>
                    </div>
                """, unsafe_allow_html=True)
                
                # View more button with modal
                if len(str(r[8])) > 100:
                    desc = str(r[8])[:100] + "..."
                    view_key = f"view_more_{r[0]}"
                    
                    if st.button("📖 Read More", key=f"read_{r[0]}", type="secondary"):
                        st.session_state[view_key] = not st.session_state.get(view_key, False)
                    
                    if st.session_state.get(view_key, False):
                        st.markdown(f"""
                            <div style="
                                background: #f8f9fa;
                                padding: 12px;
                                border-radius: 8px;
                                margin-top: 10px;
                                border-left: 3px solid {category_colors.get(r[4], '#4A90E2')};
                            ">
                                <p style="margin: 0; color: #555;">{r[8]}</p>
                            </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
    
    # View all achievements button
    st.markdown("""
        <div style="text-align: center; margin-top: 30px;">
    """, unsafe_allow_html=True)
    
    if st.button("📚 View All Achievements", type="primary"):
        st.session_state.page = "🏆 Excellence Gallery"
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
# Add these helper functions before the ted_talk page or at the top of your file

def get_distinct_values(table, column):
    """Get distinct values from a table column"""
    try:
        cur.execute(f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL AND {column} != '' ORDER BY {column}")
        return [row[0] for row in cur.fetchall()]
    except:
        return []

def attendance_summary_page():
    """Placeholder for attendance summary page"""
    st.info("Attendance Summary Page - Coming Soon")
# ================= SIGN OUT PAGE =================
def sign_out_page():
    st.markdown("""
    <style>
    /* Main container styling */
    .logout-container {
        min-height: 85vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 2rem;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 20px;
        margin: 1rem;
    }
    
    /* Title styling */
    .logout-title {
        font-size: 3.5rem;
        font-weight: 800;
        color: #2c3e50;
        margin-bottom: 1rem;
        text-align: center;
        background: linear-gradient(45deg, #3498db, #2c3e50);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Icon animation */
    .logout-icon {
        font-size: 5rem;
        margin: 2rem 0;
        animation: pulse 2s infinite;
        color: #e74c3c;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    
    /* User info card */
    .user-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin: 2rem 0;
        text-align: center;
        max-width: 400px;
    }
    
    .user-avatar {
        width: 80px;
        height: 80px;
        background: linear-gradient(45deg, #3498db, #2c3e50);
        border-radius: 50%;
        margin: 0 auto 15px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 2rem;
        font-weight: bold;
    }
    
    .user-name {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 5px;
    }
    
    .user-role {
        font-size: 1rem;
        color: #7f8c8d;
        padding: 5px 15px;
        background: #ecf0f1;
        border-radius: 20px;
        display: inline-block;
    }
    
    /* Warning message styling */
    .warning-message {
        background: linear-gradient(45deg, #f39c12, #e67e22);
        color: white;
        padding: 20px 30px;
        border-radius: 15px;
        margin: 2rem auto;
        text-align: center;
        max-width: 500px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <div class="logout-icon">🔚</div>
            <h1 class="logout-title">Sign Out</h1>
        </div>
        """, unsafe_allow_html=True)
        
        # Show user info if logged in
        if st.session_state.user:
            user_name = st.session_state.user.get("name", "Vidhya Bharathi")
            user_initial = user_name[0].upper()
            user_role = st.session_state.user_role or "FACULTY"
            
            st.markdown(f"""
            <div class="user-card">
                <div class="user-avatar">{user_initial}</div>
                <div class="user-name">{user_name}</div>
                <div class="user-role">{user_role}</div>
                <p style="color: #7f8c8d; margin-top: 10px;">Login Time: Today</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Warning message
        st.markdown("""
        <div class="warning-message">
            <strong>⚠️ Important Notice</strong><br>
            You are about to sign out of the system. Any unsaved work will be lost.<br><br>
            After signing out, you'll need to log in again to access your documents and settings.
        </div>
        """, unsafe_allow_html=True)
        
        # Confirmation
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <h3 style="color: #2c3e50;">Are you sure you want to logout? 😊</h3>
            <p style="color: #7f8c8d;">You'll need to sign in again to access department features</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Buttons with unique keys
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Yes, Logout", type="primary", use_container_width=True, key="logout_yes_button"):
                # Clear session
                st.session_state.user = None
                st.session_state.user_role = None
                st.session_state.page = "home"
                st.success("✅ Successfully logged out!")
                st.rerun()
            
            if st.button("Go Back", use_container_width=True, key="logout_back_button"):
                st.session_state.page = "home"
                st.rerun()
# STATISTICS SECTION
def display_achievement_stats(conn, cur):
    """
    Display achievement statistics
    """
    # Fetch all achievements for stats
    cur.execute("""
        SELECT category, level, COUNT(*) as count 
        FROM achievements 
        GROUP BY category, level
    """)
    stats_data = cur.fetchall()
    
    if stats_data:
        # Create stats cards
        col1, col2, col3, col4 = st.columns(4)
        
        total = sum([row[2] for row in stats_data])
        categories = len(set([row[0] for row in stats_data]))
        national_plus = sum([row[2] for row in stats_data if row[1] in ["National", "International"]])
        
        with col1:
            st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px;
                    border-radius: 10px;
                    color: white;
                    text-align: center;
                ">
                    <h3 style="margin: 0; font-size: 32px;">{total}</h3>
                    <p style="margin: 5px 0; opacity: 0.9;">Total Achievements</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    padding: 20px;
                    border-radius: 10px;
                    color: white;
                    text-align: center;
                ">
                    <h3 style="margin: 0; font-size: 32px;">{categories}</h3>
                    <p style="margin: 5px 0; opacity: 0.9;">Categories</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    padding: 20px;
                    border-radius: 10px;
                    color: white;
                    text-align: center;
                ">
                    <h3 style="margin: 0; font-size: 32px;">{national_plus}</h3>
                    <p style="margin: 5px 0; opacity: 0.9;">National+ Level</p>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                    padding: 20px;
                    border-radius: 10px;
                    color: white;
                    text-align: center;
                ">
                    <h3 style="margin: 0; font-size: 32px;">👨‍🎓</h3>
                    <p style="margin: 5px 0; opacity: 0.9;">Students & Faculty</p>
                </div>
            """, unsafe_allow_html=True)
def excellence_gallery_page(conn, cur):
    """
    Enhanced excellence gallery page with filters
    """
    if not st.session_state.user:
        st.warning("🔐 Login required")
        st.stop()

    st.header("🏆 Excellence Gallery")
    
    # Filters section
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        filter_category = st.selectbox(
            "Filter by Category",
            ["All"] + ["Academic", "Sports", "Cultural", "Technical", "Other"]
        )
    with col2:
        filter_level = st.selectbox(
            "Filter by Level",
            ["All"] + ["College", "District", "State", "National", "International"]
        )
    with col3:
        filter_role = st.selectbox(
            "Filter by Role",
            ["All", "Student", "Faculty"]
        )
    with col4:
        sort_by = st.selectbox(
            "Sort by",
            ["Date (Newest)", "Date (Oldest)", "Title A-Z", "Level"]
        )
    
    # Build query based on filters
    query = """
        SELECT id, name, role, title, category, 
               event_name, level, date, description, image_path
        FROM achievements
        WHERE 1=1
    """
    params = []
    
    if filter_category != "All":
        query += " AND category = ?"
        params.append(filter_category)
    
    if filter_level != "All":
        query += " AND level = ?"
        params.append(filter_level)
    
    if filter_role != "All":
        query += " AND role = ?"
        params.append(filter_role)
    
    # Add sorting
    if sort_by == "Date (Newest)":
        query += " ORDER BY date DESC"
    elif sort_by == "Date (Oldest)":
        query += " ORDER BY date ASC"
    elif sort_by == "Title A-Z":
        query += " ORDER BY title ASC"
    elif sort_by == "Level":
        level_order = {"International": 1, "National": 2, "State": 3, "District": 4, "College": 5}
        # This would require custom sorting
    
    cur.execute(query, params)
    rows = cur.fetchall()
    # Display filtered results using the same gallery component
    display_achievements_gallery(conn, cur, max_items=len(rows))
# ====================== HELPER FUNCTIONS ======================
def create_lab_card(title, content, icon="🖥️", color="#3498DB"):
    """Create a beautiful card component"""
    return f"""
    <div class="lab-card fade-in">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <span style="font-size: 2rem; margin-right: 1rem;">{icon}</span>
            <h3 style="margin: 0; color: {color}; flex-grow: 1;">{title}</h3>
        </div>
        {content}
    </div>
    """

def create_metric_card(value, label, icon="👨‍🎓", color="#667eea"):
    """Create a metric card"""
    return f"""
    <div class="metric-card" style="background: linear-gradient(135deg, {color} 0%, {color}88 100%);">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">{icon}</div>
        <h3>{value}</h3>
        <p>{label}</p>
    </div>
    """

def get_lab_occupancy(lab_room, session_id, conn):
    """Get current occupancy of a lab for a session"""
    cur = conn.cursor()
    cur.execute("""
        SELECT system_no FROM lab_attendance 
        WHERE lab_room=? AND session_id=?
    """, (lab_room, session_id))
    occupied_systems = [row[0] for row in cur.fetchall()]
    return occupied_systems

def get_lab_status(lab_room, conn):
    """Get current lab status (Available/Partial/Occupied)"""
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(DISTINCT session_id) as active_sessions
        FROM lab_attendance 
        WHERE lab_room=? AND lab_date=DATE('now')
    """, (lab_room,))
    active_sessions = cur.fetchone()[0]
    
    if active_sessions == 0:
        return "Available", "#27AE60"
    elif active_sessions < 3:  # Assuming max 3 sessions per day
        return "Partial", "#F39C12"
    else:
        return "Occupied", "#E74C3C"
    # Add this at the top of your app (outside this module) for notifications
    if 'user' in st.session_state and st.session_state.user:
        role = st.session_state.user["role"].strip().lower()
        if role != "student":
            # Check for new queries every 30 seconds
            if 'last_query_check' not in st.session_state:
                st.session_state.last_query_check = time.time()
                st.session_state.last_query_count = 0
        
            current_time = time.time()
            if current_time - st.session_state.last_query_check > 30:  # 30 seconds
                cur.execute("SELECT COUNT(*) FROM feedback WHERE status='Open'")
                new_count = cur.fetchone()[0]
                if new_count > st.session_state.last_query_count:
                    # Show notification
                    notification_placeholder = st.empty()
                    with notification_placeholder:
                        st.toast(f"🔔 New query received! Total open queries: {new_count}", icon="📩")
                    # Update count
                        st.session_state.last_query_count = new_count
                        st.session_state.last_query_check = current_time
st.markdown("""
<style>

/* ================= GOOGLE FONTS (ONLY ONCE) ================= */
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

/* ================= ROOT VARIABLES ================= */
:root {
    --primary: #2563eb;
    --primary-dark: #1e40af;
    --secondary: #7c3aed;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --light: #f8fafc;
    --dark: #1e293b;
    --gray: #64748b;

    --shadow-sm: 0 2px 8px rgba(0,0,0,0.08);
    --shadow-md: 0 4px 16px rgba(0,0,0,0.12);
    --shadow-lg: 0 8px 30px rgba(0,0,0,0.15);

    --radius-sm: 6px;
    --radius-md: 12px;
    --radius-lg: 16px;

    --transition: all 0.3s ease;
}

/* ================= GLOBAL RESET ================= */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
    color: var(--dark);
    line-height: 1.6;
    scroll-behavior: smooth;
}

/* ================= STREAMLIT LAYOUT ================= */
.stApp {
    background: transparent !important;
}

.main .block-container {
    padding-top: 1rem !important;
    padding-bottom: 3rem !important;
    max-width: 1400px !important;
}

/* ================= HEADINGS ================= */
h1, h2, h3, h4, .stHeader, .stSubheader {
    font-family: 'Poppins', sans-serif !important;
    color: var(--primary-dark) !important;
}

/* ================= COLLEGE LOGO ================= */
.college-logo {
    width: 120px;
    height: 120px;
    object-fit: contain;
    transition: var(--transition);
}

.college-logo:hover {
    transform: scale(1.05);
}

@media (max-width: 768px) {
    .college-logo {
        width: 80px;
        height: 80px;
    }
}

/* ================= GRADIENT TYPEWRITER ================= */
.gradient-typewriter {
    font-size: clamp(18px, 2vw, 28px);
    font-weight: 700;
    text-align: center;
    letter-spacing: 1px;
    font-family: 'Poppins', sans-serif;
    background: linear-gradient(90deg, #ff9800, #ffeb3b, #009688, #9c27b0);
    background-size: 300% 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradientShift 5s ease infinite, typing 3.5s steps(60, end) forwards;
    white-space: nowrap;
    overflow: hidden;
    display: inline-block;
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

@keyframes typing {
    from { width: 0; }
    to { width: 100%; }
}

/* ================= BUTTONS (ONLY ONE MASTER STYLE) ================= */
.stButton > button {
    background: linear-gradient(135deg, var(--primary), var(--primary-dark)) !important;
    color: white !important;
    border: none !important;
    border-radius: var(--radius-md) !important;
    padding: 0.8rem 2rem !important;
    font-weight: 600 !important;
    transition: var(--transition) !important;
    cursor: pointer !important;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg) !important;
}

/* ================= CARDS ================= */
.custom-card,
.event-card,
.alumni-card,
.lab-card {
    background: white;
    border-radius: var(--radius-lg);
    padding: 1.8rem;
    box-shadow: var(--shadow-md);
    border: 1px solid #e2e8f0;
    transition: var(--transition);
    margin-bottom: 1.5rem;
}

.custom-card:hover,
.event-card:hover,
.alumni-card:hover,
.lab-card:hover {
    transform: translateY(-5px);
    box-shadow: var(--shadow-lg);
}

/* ================= FORMS ================= */
.stForm {
    background: #f8fafc;
    border-radius: var(--radius-lg);
    padding: 2rem;
    border: 1px solid #e2e8f0;
}

.stTextInput input,
.stTextArea textarea,
.stSelectbox select {
    border-radius: var(--radius-md) !important;
    border: 2px solid #e2e8f0 !important;
    padding: 0.8rem !important;
}

/* ================= DATAFRAME ================= */
.stDataFrame {
    border-radius: var(--radius-lg);
    overflow: hidden;
    box-shadow: var(--shadow-md);
}

.dataframe th {
    background: linear-gradient(135deg, var(--primary-dark), var(--primary));
    color: white;
    padding: 1rem;
}

.dataframe td {
    padding: 0.8rem;
}

/* ================= ANNOUNCEMENT BAR ================= */
.announcement-bar {
    background: linear-gradient(135deg, var(--primary-dark), var(--primary));
    color: white;
    padding: 1rem 1.5rem;
    border-radius: var(--radius-md);
    margin: 2rem 0;
    box-shadow: var(--shadow-md);
}

/* ================= SCROLL TO TOP ================= */
.scroll-top-btn {
    position: fixed;
    bottom: 30px;
    right: 20px;
    width: 52px;
    height: 52px;
    background: var(--primary);
    color: white;
    border-radius: 50%;
    font-size: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--shadow-lg);
    cursor: pointer;
    transition: var(--transition);
}

.scroll-top-btn:hover {
    background: var(--primary-dark);
    transform: scale(1.1);
}

/* ================= WHATSAPP FLOAT ================= */
.whatsapp-float {
    position: fixed;
    bottom: 110px;
    right: 20px;
    width: 60px;
    height: 60px;
    background: #25D366;
    color: white;
    border-radius: 50%;
    font-size: 26px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--shadow-lg);
    transition: var(--transition);
}

.whatsapp-float:hover {
    transform: scale(1.1);
}

/* ================= FOOTER ================= */
.footer {
    background: linear-gradient(135deg, var(--primary-dark), var(--primary));
    color: white;
    padding: 3rem 2rem;
    margin-top: 4rem;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    text-align: center;
}

.footer-copy {
    margin-top: 2rem;
    font-size: 0.9rem;
    opacity: 0.85;
}

</style>
""", unsafe_allow_html=True)
# ================= MAIN NAVIGATION =================
col1, col2, col3 = st.columns([1, 6, 1])

with col1:
    if st.button("☰", key="hamburger", use_container_width=True):
        st.session_state.show_menu = not st.session_state.show_menu
with col2:
    st.markdown("""
    <div style="text-align: center; padding: 10px 0;">
        <h2 style="margin: 0; color: #0da30f; font-weight: 700;">
            Department Management System
        </h2>
        <p style="margin: 5px 0 0 0; color: #fa0fc7;">
            Michael Job College of Arts & Science for Women
        </p>
    </div>
    """, unsafe_allow_html=True)
# Show menu if toggled
if st.session_state.show_menu:
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    for label, route in menu:
        if st.button(
            label,
            key=f"menu_{route}",   # 🔑 unique key
            use_container_width=True
        ):
            st.session_state.page = route
            st.session_state.show_menu = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
# ================= CURRENT PAGE =================
page = st.session_state.page
# ================= WELCOME BANNER (if logged in) =================
if st.session_state.user and page == "home":
    user = st.session_state.user
    st.markdown(create_welcome_banner(user.get("name", "User"), user.get("role", "")), unsafe_allow_html=True)
# ================= HOME PAGE =================
if page == "home":
    # 🔧 FIX: sync user_role from user dict
    if "user" in st.session_state and st.session_state.user:
        st.session_state.user_role = st.session_state.user.get("role")
    # ---------- HEADER ----------
    col1, col2, col3 = st.columns([1, 6, 1])

    with col1:
        st.markdown(
            f"<img src='data:image/png;base64,{img_to_base64(os.path.join(ASSETS_DIR,'leftlogo.png'))}' class='college-logo'>",
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("""
            <div class="gradient-typewriter">
            MICHAEL JOB COLLEGE OF ARTS AND SCIENCE FOR WOMEN
            </div>
            <p style="text-align:center; margin-top:8px; color:#475569;">
                Approved by UGC, Affiliated to Bharathiar University<br>
                Recognized by UGC under Section 2(f), ISO 9001:2015 & 21001:2018 certified<br>
                Near Sulur Boat Lake, Ravathur, Coimbatore – 641 402
            </p>
            """, unsafe_allow_html=True)
            
    with col3:
        st.markdown(
            f"<img src='data:image/png;base64,{img_to_base64(os.path.join(ASSETS_DIR,'rightlogo.png'))}' class='college-logo'>",
            unsafe_allow_html=True
        )

    st.divider()
    
    # ---------- FADE BANNER (AUTO-SCALABLE) - SLOWER ----------
    banner_data = [
        ("college_banner.jpg", "Michael Job College Campus"),
        ("college1.jpg", "Arts Building"),
        ("college2.jpg", "College Campus"),
        ("college3.jpg", "Cultural Programme"),
        ("photo5.jpg", "Value Added Courses"),
        ("photo6.jpg", "Industrial Visit"),
        ("photo7.jpg", "Industrial Visit"),
        ("photo10.jpg", "Industrial Visit"),
        ("photo8.jpg", "Village Visit"),
        ("photo9.jpg", "Alumnae Meet "),
        ("welcome1.jpeg","CS Deptstaff"),
        ("welcome2.jpeg","CS Deptstaff"),
        ("photo13.jpg", "Department Staff"),
        ("onamcelebration.jpg", "Onam Celebration"),
        ("photo11.jpg", "2024 Batch Students"),
        ("photo12.jpg", "Onam Celebration 2025"),
        ("photo14.jpg", "Inter-Collegiate Meet"),
        ("photo15.jpg", "Students Presentation"),
        ("photo17.jpg", "Club Activity"),
        ("photo18.jpg", "Inter Collegiate Meet"),
        ("photo19.jpg", "Farewell"),
        ("photo22.jpg", "Graduation Ceremony"),
    ]

    slides = ""
    delay = 0
    
    for img, title in banner_data:
        img_path = os.path.join(ASSETS_DIR, img)
        if os.path.exists(img_path):
            img64 = img_to_base64(img_path)
            slides += f"""
            <div class="slide" style="animation-delay:{delay}s">
                <img src="data:image/jpeg;base64,{img64}">
                <div class="banner-caption">{title}</div>
            </div>
            """
            delay += 5

    banner_html = f"""
    <style>
    .slider {{
        position: relative;
        width: 100%;
        height: 320px;
        overflow: hidden;
        border-radius: 18px;
        background: #000;
        box-shadow: 0 12px 30px rgba(0,0,0,0.2);
        margin: 1.5rem 0;
    }}

    .slide {{
        position: absolute;
        inset: 0;
        opacity: 0;
        animation: fadeBanner {delay}s infinite;
    }}

    .slide img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 15s ease;
    }}

    .slide:hover img {{
        transform: scale(1.05);
    }}

    @keyframes fadeBanner {{
        0% {{ opacity: 0; transform: scale(1.1); }}
        5% {{ opacity: 1; transform: scale(1); }}
        20% {{ opacity: 1; transform: scale(1); }}
        25% {{ opacity: 0; transform: scale(1.1); }}
        100% {{ opacity: 0; transform: scale(1.1); }}
    }}

    .banner-caption {{
        position: absolute;
        bottom: 20px;
        left: 20px;
        right: 20px;
        padding: 12px 16px;
        background: linear-gradient(90deg, rgba(0,0,0,0.8), rgba(0,0,0,0.6));
        color: white;
        border-radius: 12px;
        font-size: 18px;
        font-weight: 600;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
    }}
    </style>

    <div class="slider">
        {slides}
    </div>
    """

    components.html(banner_html, height=340)

    # ---------- ANNOUNCEMENTS TICKER (TOP) ----------
    st.markdown("""
        <style>
        @keyframes tickerMove {
            0% { transform: translateX(100%); }
            100% { transform: translateX(-100%); }
        }
        
        .announcement-ticker {
            background: linear-gradient(135deg, #2563eb, #1e40af);
            padding: 12px 0;
            border-radius: 12px;
            margin: 1.5rem 0;
            overflow: hidden;
            position: relative;
            box-shadow: 0 4px 20px rgba(37, 99, 235, 0.3);
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .ticker-content {
            display: inline-block;
            white-space: nowrap;
            animation: tickerMove 40s linear infinite;
            padding-left: 100%;
            color: white;
            font-size: 1.1rem;
            font-weight: 500;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .ticker-content:hover {
            animation-play-state: paused;
        }
        
        .ticker-item {
            display: inline-block;
            margin-right: 50px;
        }
        </style>
    """, unsafe_allow_html=True)
    # ---------- ROLE-BASED QUICK ACCESS CARDS ----------
    st.markdown("""
        <style>
        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .role-card {
            background: white;
            border-radius: 20px;
            padding: 1.8rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
            border: 1px solid #e2e8f0;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            text-align: center;
            height: 100%;
            position: relative;
            overflow: hidden;
            animation: fadeInUp 0.8s ease-out both;
        }
        
        .role-card:nth-child(1) { animation-delay: 0.1s; }
        .role-card:nth-child(2) { animation-delay: 0.2s; }
        .role-card:nth-child(3) { animation-delay: 0.3s; }
        
        .role-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 5px;
            background: linear-gradient(90deg, #3b82f6, #8b5cf6, #10b981);
            transform: translateX(-100%);
            transition: transform 0.5s ease;
        }
        
        .role-card:hover::before {
            transform: translateX(0);
        }
        
        .role-card:hover {
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 25px 30px -10px rgba(0, 0, 0, 0.15);
            border-color: #3b82f6;
        }
        
        .role-card .card-icon {
            font-size: 3.5rem;
            margin-bottom: 1rem;
            transition: transform 0.3s ease;
        }
        
        .role-card:hover .card-icon {
            transform: scale(1.1) rotate(5deg);
        }
        
        .role-card h3 {
            color: #1e40af;
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
        
        .role-card p {
            color: #64748b;
            font-size: 0.95rem;
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }
        
        .role-badge {
            position: absolute;
            top: 15px;
            right: 15px;
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: white;
            padding: 5px 15px;
            border-radius: 25px;
            font-size: 12px;
            font-weight: 600;
            animation: pulse 2s infinite;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="margin: 2.5rem 0 1rem 0; text-align: center;">
            <h2 style="color: #1e40af; font-size: 28px; font-weight: 800; 
                background: linear-gradient(90deg, #1e40af, #2563eb);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                display: inline-block;
                animation: fadeInDown 0.8s ease-out;">
                🚀 Quick Access
            </h2>
            <p style="color: #64748b; margin-top: 5px; animation: fadeInUp 0.8s ease-out 0.2s both;">
                Fast access to frequently used features based on your role
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    user_role = st.session_state.get("user_role")
    
    if not user_role:  # Not logged in
        cols = st.columns(2)
        with cols[0]:
            st.markdown("""
            <div class="role-card">
                <span class="role-badge">New</span>
                <div class="card-icon">👤</div>
                <h3>New User?</h3>
                <p>Create your account to access all department services. Registration takes less than 2 minutes.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Register Now", key="reg_card", use_container_width=True):
                st.session_state.page = "enrollment"
                st.rerun()
        
        with cols[1]:
            st.markdown("""
            <div class="role-card">
                <span class="role-badge">Welcome</span>
                <div class="card-icon">🔓</div>
                <h3>Existing User</h3>
                <p>Login to access your personalized dashboard, materials, assignments, and more.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Sign In", key="login_card", use_container_width=True):
                st.session_state.page = "login"
                st.rerun()
                
    elif user_role == "Student":
        cols = st.columns(3)
        quick_items = [
            ("📚", "E-Materials", "Access study materials, notes, and presentations", "materials"),
            ("📝", "Assignments", "Submit assignments, check deadlines, and view submissions", "assignments"),
            ("📘", "Syllabus", "Download course syllabus and academic curriculum", "syllabus"),
            ("🖥️", "Lab Register", "Mark lab attendance and view lab sessions", "lab_register"),
            ("📝", "Support Desk", "Submit queries and get support from faculty", "support"),
            ("🕒", "Schedule", "View class timetable and exam schedules", "schedule")
        ]
        for idx, (icon, title, desc, route) in enumerate(quick_items):
            with cols[idx % 3]:
                st.markdown(f"""
                <div class="role-card" style="animation-delay: {0.1 * idx}s;">
                    <div class="card-icon">{icon}</div>
                    <h3>{title}</h3>
                    <p>{desc}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Go to {title}", key=f"stu_{route}", use_container_width=True):
                    st.session_state.page = route
                    st.rerun()
    
    elif user_role == "Faculty":
        cols = st.columns(3)
        quick_items = [
            ("📤", "Upload Materials", "Upload study materials, notes, and resources", "materials"),
            ("📝", "Assignments", "Create assignments, manage submissions, and grade", "assignments"),
            ("📊", "Attendance", "Enter and manage daily attendance records", "attendance_summary"),
            ("🏆", "Achievements", "Add student and faculty achievements", "achievements"),
            ("📋", "Lab Management", "Manage lab sessions, attendance, and reports", "lab_register"),
            ("💬", "Student Queries", "Respond to student queries and support requests", "support")
        ]
        for idx, (icon, title, desc, route) in enumerate(quick_items):
            with cols[idx % 3]:
                st.markdown(f"""
                <div class="role-card" style="animation-delay: {0.1 * idx}s;">
                    <div class="card-icon">{icon}</div>
                    <h3>{title}</h3>
                    <p>{desc}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Go to {title}", key=f"fac_{route}", use_container_width=True):
                    st.session_state.page = route
                    st.rerun()
    
    elif user_role == "Admin":
        cols = st.columns(3)
        quick_items = [
            ("👥", "User Management", "Manage user accounts, roles, and permissions", "enrollment"),
            ("📢", "Announcements", "Create and manage department announcements", "announcements"),
            ("📊", "Reports", "Generate department reports and analytics", "attendance_summary"),
            ("🏆", "Achievements", "Manage achievements gallery", "achievements"),
            ("📋", "Lab Oversight", "Monitor lab activities and generate reports", "lab_register"),
            ("💰", "Fees", "Manage fee structure and documents", "fees")
        ]
        for idx, (icon, title, desc, route) in enumerate(quick_items):
            with cols[idx % 3]:
                st.markdown(f"""
                <div class="role-card" style="animation-delay: {0.1 * idx}s;">
                    <div class="card-icon">{icon}</div>
                    <h3>{title}</h3>
                    <p>{desc}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Go to {title}", key=f"admin_{route}", use_container_width=True):
                    st.session_state.page = route
                    st.rerun()

    # ---------- ANNOUNCEMENTS AND ACHIEVEMENTS SIDE BY SIDE ----------
    st.markdown("""
        <style>
        @keyframes slideInLeft {
            from { opacity: 0; transform: translateX(-30px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(30px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        @keyframes glowPulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.5); }
            50% { box-shadow: 0 0 20px 5px rgba(59, 130, 246, 0.3); }
        }
        
        .announcement-container {
            background: linear-gradient(135deg, #f8fafc, #f1f5f9);
            border-radius: 20px;
            padding: 2rem;
            margin: 2rem 0;
            border: 1px solid #e2e8f0;
            position: relative;
            overflow: hidden;
            animation: slideInLeft 0.8s ease-out;
        }
        
        .announcement-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #3b82f6, #8b5cf6, #10b981);
        }
        
        .announcement-item {
            background: white;
            border-radius: 12px;
            padding: 1.2rem;
            margin-bottom: 1rem;
            border-left: 4px solid #3b82f6;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            transition: all 0.3s ease;
            animation: slideInLeft 0.5s ease-out both;
            position: relative;
            overflow: hidden;
        }
        
        .announcement-item:hover {
            transform: translateX(5px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }
        
        .announcement-item.pinned {
            border-left-color: #f59e0b;
            background: linear-gradient(135deg, #fff, #fffbeb);
            animation: glowPulse 2s infinite;
        }
        
        .announcement-item.pinned::after {
            content: '📌 PINNED';
            position: absolute;
            top: 8px;
            right: 8px;
            background: #f59e0b;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 10px;
            font-weight: 600;
        }
        
        .announcement-date {
            display: inline-block;
            background: #e2e8f0;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            color: #475569;
            font-weight: 600;
        }
        
        .new-badge {
            display: inline-block;
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 8px;
            animation: pulse 1.5s infinite;
        }
        
        .announcement-icon {
            font-size: 24px;
            margin-right: 12px;
            float: left;
        }
        
        .achievement-mini-card {
            background: linear-gradient(135deg, white, #f8fafc);
            border-radius: 16px;
            padding: 1.2rem;
            margin-bottom: 1rem;
            border: 1px solid #e2e8f0;
            border-left: 5px solid;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            animation: slideInRight 0.6s ease-out both;
            position: relative;
            overflow: hidden;
            cursor: pointer;
        }
        
        .achievement-mini-card:hover {
            transform: translateY(-5px) scale(1.02);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        }
        
        .achievement-mini-card::before {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 100px;
            height: 100px;
            background: linear-gradient(135deg, currentColor 0%, transparent 100%);
            opacity: 0.1;
            border-radius: 50%;
            transform: translate(30px, -30px);
        }
        
        .level-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .achievement-title {
            color: #1e293b;
            font-size: 16px;
            font-weight: 700;
            margin: 8px 0 4px 0;
            line-height: 1.4;
        }
        
        .achievement-meta {
            color: #64748b;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 8px;
        }
        
        .achievement-detail {
            background: white;
            border-radius: 20px;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            border: 2px solid #e2e8f0;
            animation: slideInUp 0.5s ease-out;
        }
        
        @keyframes slideInUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .detail-header {
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #e2e8f0;
        }
        
        .detail-icon {
            font-size: 4rem;
        }
        
        .detail-title {
            color: #1e40af;
            font-size: 1.8rem;
            font-weight: 800;
            margin: 0;
        }
        
        .detail-subtitle {
            color: #64748b;
            font-size: 1rem;
            margin-top: 5px;
        }
        
        .detail-section {
            background: #f8fafc;
            border-radius: 12px;
            padding: 1.2rem;
            margin: 1rem 0;
        }
        
        .detail-section h4 {
            color: #1e40af;
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 0.8rem;
        }
        
        .detail-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 1rem 0;
        }
        
        .detail-item {
            background: white;
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid #e2e8f0;
        }
        
        .detail-item-label {
            color: #64748b;
            font-size: 0.85rem;
            margin-bottom: 0.3rem;
        }
        
        .detail-item-value {
            color: #1e293b;
            font-size: 1.1rem;
            font-weight: 600;
        }
        
        .close-button {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
            border: none;
            padding: 0.5rem 2rem;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .close-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(239, 68, 68, 0.3);
        }
        
        .achievement-image-container {
            width: 100%;
            max-height: 400px;
            overflow: hidden;
            border-radius: 12px;
            margin: 1rem 0;
        }
        
        .achievement-image-container img {
            width: 100%;
            height: auto;
            object-fit: cover;
            transition: transform 0.3s ease;
        }
        
        .achievement-image-container img:hover {
            transform: scale(1.02);
        }
        </style>
    """, unsafe_allow_html=True)

    # Create two columns for announcements and achievements
    col_ann, col_ach = st.columns([1, 1])

    # ---------- ANNOUNCEMENTS SECTION ----------
    with col_ann:
        st.markdown("""
            <div style="margin-bottom: 1.5rem;">
                <h2 style="color: #1e40af; font-size: 28px; font-weight: 800; 
                    background: linear-gradient(90deg, #1e40af, #2563eb);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    display: inline-block;
                    animation: fadeInDown 0.8s ease-out;">
                    📢 Latest Announcements
                </h2>
                <p style="color: #64748b; margin-top: 5px; animation: fadeInUp 0.8s ease-out 0.2s both;">
                    Important updates from the department
                </p>
            </div>
            
            <div class="announcement-container">
        """, unsafe_allow_html=True)

        # Fetch announcements from database
        cur.execute("""
            SELECT message, announce_date, pinned, expiry_date 
            FROM announcements 
            WHERE (expiry_date IS NULL OR expiry_date >= date('now'))
            ORDER BY pinned DESC, announce_date DESC 
            LIMIT 5
        """)
        announcements = cur.fetchall()

        if announcements:
            for idx, (msg, date_val, pinned, expiry) in enumerate(announcements):
                # Simple text - no HTML escaping needed for display
                safe_msg = str(msg)
                
                # Check if announcement is recent
                announce_date = date.fromisoformat(date_val) if date_val else date.today()
                days_old = (date.today() - announce_date).days
                is_new = days_old < 7
                
                pinned_class = "pinned" if pinned else ""
                new_badge = '<span class="new-badge">NEW</span>' if is_new else ''
                
                st.markdown(f"""
                <div class="announcement-item {pinned_class}" style="animation-delay: {0.1 * idx}s;">
                    <div style="display: flex; align-items: flex-start;">
                        <span class="announcement-icon">{'📌' if pinned else '📢'}</span>
                        <div style="flex: 1;">
                            <p style="margin: 0 0 8px 0; color: #1e293b; font-size: 15px; line-height: 1.5;">
                                {safe_msg}
                            </p>
                            <div>
                                <span class="announcement-date">
                                    📅 {date_val}
                                </span>
                                {new_badge}
                                {f'<span style="margin-left: 8px; color: #64748b;">⏳ Expires: {expiry}</span>' if expiry else ''}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No announcements at this time.")

        st.markdown("</div>", unsafe_allow_html=True)

    # ---------- ACHIEVEMENTS SECTION ----------
    with col_ach:
        st.markdown("""
            <div style="margin-bottom: 1.5rem;">
                <h2 style="color: #1e40af; font-size: 28px; font-weight: 800; 
                    background: linear-gradient(90deg, #1e40af, #2563eb);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    display: inline-block;
                    animation: fadeInDown 0.8s ease-out 0.3s both;">
                    🏆 Recent Achievements
                </h2>
                <p style="color: #64748b; margin-top: 5px; animation: fadeInUp 0.8s ease-out 0.4s both;">
                    Click on any achievement to view details
                </p>
            </div>
        """, unsafe_allow_html=True)

        # Initialize session state for achievement details
        if 'selected_achievement' not in st.session_state:
            st.session_state.selected_achievement = None

        # Level icons and colors
        level_colors = {
            "International": "#8b5cf6",
            "National": "#3b82f6", 
            "State": "#10b981",
            "District": "#f59e0b",
            "College": "#6b7280"
        }
        
        level_icons = {
            "International": "🌍",
            "National": "🇮🇳",
            "State": "🗺️",
            "District": "🏙️",
            "College": "🏛️"
        }

        # Fetch recent achievements
        cur.execute("""
            SELECT id, name, role, title, category, event_name, level, date, description, image_path
            FROM achievements 
            ORDER BY date DESC 
            LIMIT 3
        """)
        recent_achievements = cur.fetchall()

        if recent_achievements:
            for idx, ach in enumerate(recent_achievements):
                ach_id, name, role, title, category, event_name, level, ach_date, description, image_path = ach
                
                # Simple text - no HTML escaping needed for display
                safe_name = str(name)
                safe_role = str(role)
                safe_title = str(title)
                safe_category = str(category)
                safe_level = str(level)
                
                color = level_colors.get(level, "#3b82f6")
                level_icon = level_icons.get(level, "🏆")
                
                # Achievement card
                st.markdown(f"""
                <div class="achievement-mini-card" style="border-left-color: {color}; animation-delay: {0.1 * idx}s;">
                    <div style="display: flex; align-items: flex-start; gap: 12px;">
                        <div style="font-size: 32px;">{level_icon}</div>
                        <div style="flex: 1;">
                            <span class="level-badge" style="background: {color}15; color: {color};">{safe_level}</span>
                            <div class="achievement-title">{safe_title[:60]}{'...' if len(safe_title) > 60 else ''}</div>
                            <div style="color: #475569; font-size: 13px; font-weight: 500;">
                                {safe_name} • {safe_role}
                            </div>
                            <div class="achievement-meta">
                                <span>📅 {ach_date}</span>
                                <span>📂 {safe_category}</span>
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # View details button
                if st.button(f"🔍 View Details", key=f"ach_btn_{ach_id}", use_container_width=True):
                    st.session_state.selected_achievement = ach_id
                    st.rerun()
            
            # Show achievement details if one is selected
            if st.session_state.selected_achievement:
                cur.execute("""
                    SELECT name, role, title, category, event_name, level, date, description, image_path
                    FROM achievements WHERE id = ?
                """, (st.session_state.selected_achievement,))
                full_ach = cur.fetchone()
                
                if full_ach:
                    name, role, title, category, event_name, level, ach_date, description, image_path = full_ach
                    
                    # Simple text - no HTML escaping needed for display
                    safe_name = str(name)
                    safe_role = str(role)
                    safe_title = str(title)
                    safe_category = str(category)
                    safe_level = str(level)
                    safe_event_name = str(event_name) if event_name else ""
                    safe_description = str(description) if description else ""
                    
                    level_icon = level_icons.get(level, "🏆")
                    color = level_colors.get(level, "#3b82f6")
                    
                    # Create image HTML if exists
                    image_html = ""
                    if image_path and os.path.exists(image_path):
                        try:
                            img = Image.open(image_path)
                            # Resize image for better display
                            max_size = (400, 300)
                            img.thumbnail(max_size, Image.Resampling.LANCZOS)
                            
                            # Save to bytes for display
                            from io import BytesIO
                            img_bytes = BytesIO()
                            img.save(img_bytes, format='PNG')
                            img_bytes = img_bytes.getvalue()
                            img_base64 = base64.b64encode(img_bytes).decode()
                            
                            image_html = f"""
                            <div class="detail-section">
                                <h4>🖼️ Achievement Image</h4>
                                <div class="achievement-image-container">
                                    <img src="data:image/png;base64,{img_base64}" alt="Achievement Image" style="width: 100%; border-radius: 10px;">
                                </div>
                            </div>
                            """
                        except Exception as e:
                            print(f"Error loading image: {e}")
                    
                    st.markdown(f"""
                    <div class="achievement-detail">
                        <div class="detail-header">
                            <div class="detail-icon">{level_icon}</div>
                            <div style="flex: 1;">
                                <h3 class="detail-title">{safe_title}</h3>
                                <p class="detail-subtitle">{safe_category} Achievement • {safe_level} Level</p>
                            </div>
                        </div>
                        
                        <div class="detail-grid">
                            <div class="detail-item">
                                <div class="detail-item-label">👤 Name</div>
                                <div class="detail-item-value">{safe_name}</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-item-label">🎓 Role</div>
                                <div class="detail-item-value">{safe_role}</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-item-label">📅 Date</div>
                                <div class="detail-item-value">{ach_date}</div>
                            </div>
                            <div class="detail-item">
                                <div class="detail-item-label">🏆 Level</div>
                                <div class="detail-item-value" style="color: {color};">{safe_level}</div>
                            </div>
                        </div>
                        
                        {f'<div class="detail-item" style="grid-column: span 2;"><div class="detail-item-label">🎯 Event</div><div class="detail-item-value">{safe_event_name}</div></div>' if safe_event_name else ''}
                        
                        <div class="detail-section">
                            <h4>📋 Achievement Description</h4>
                            <p style="color: #475569; line-height: 1.6; margin: 0;">{safe_description}</p>
                        </div>
                        
                        {image_html}
                        
                        <div style="text-align: center; margin-top: 1.5rem;">
                            <button class="close-button" onclick="document.getElementById('close_ach').click()">Close</button>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Close", key="close_ach", use_container_width=True):
                        st.session_state.selected_achievement = None
                        st.rerun()
            
            # View all button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🌟 View All Achievements", type="primary", use_container_width=True):
                    st.session_state.page = "excellence_gallery"
                    st.rerun()
        else:
            st.info("No achievements added yet. Be the first to achieve!")

    # ---------- DEPARTMENT INFORMATION SECTIONS ----------
    st.markdown("""
        <style>
        @keyframes floatIn {
            0% { opacity: 0; transform: translateY(30px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        
        .info-section {
            animation: floatIn 0.8s ease-out both;
            background: linear-gradient(135deg, #ffffff, #f8fafc);
            border-radius: 20px;
            padding: 2rem;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }
        
        .info-section:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        }
        
        .info-title {
            color: #1e40af;
            font-size: 24px;
            font-weight: 800;
            margin-bottom: 1rem;
            background: linear-gradient(90deg, #1e40af, #2563eb);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .info-text {
            color: #475569;
            font-size: 16px;
            line-height: 1.7;
        }
        
        .section-img-wrapper {
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            transition: all 0.5s ease;
            animation: floatIn 0.8s ease-out both;
        }
        
        .section-img-wrapper:hover {
            transform: scale(1.02);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.15);
        }
        
        .section-img-wrapper img {
            width: 100%;
            height: auto;
            transition: transform 0.5s ease;
        }
        
        .section-img-wrapper:hover img {
            transform: scale(1.1);
        }
        
        .fade-delay-1 { animation-delay: 0.1s; }
        .fade-delay-2 { animation-delay: 0.2s; }
        .fade-delay-3 { animation-delay: 0.3s; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="margin: 3rem 0 1.5rem 0; text-align: center;">
            <h2 style="color: #1e40af; font-size: 28px; font-weight: 800; 
                background: linear-gradient(90deg, #1e40af, #2563eb);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                display: inline-block;
                animation: floatIn 0.8s ease-out;">
                🎓 About Our Department
            </h2>
            <p style="color: #64748b; margin-top: 5px; animation: floatIn 0.8s ease-out 0.1s both;">
                Computer Science | Information Technology | BCA | Artificial Intelligence
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Section 1
    c1, c2 = st.columns([2, 3])
    with c1:
        img_path = os.path.join(ASSETS_DIR, "about_department.jpg")
        if os.path.exists(img_path):
            img64 = img_to_base64(img_path)
            st.markdown(
                f"""
                <div class="section-img-wrapper fade-delay-1">
                    <img src="data:image/jpeg;base64,{img64}">
                </div>
                <p style="text-align:center;margin-top:8px;color:#475569; font-weight: 500;">
                    Department Faculty & Activities
                </p>
                """,
                unsafe_allow_html=True
            )
        else:
            st.warning("⚠️ about_department.jpg not found")

    with c2:
        st.markdown("""
        <div class="info-section fade-delay-2">
            <div class="info-title">🚀 Our Mission</div>
            <div class="info-text">
                To create an integrated digital platform that enhances academic
                efficiency and learning outcomes for Computer Science,
                Information Technology, and BCA programmes. We aim to provide
                state-of-the-art facilities, industry-relevant curriculum, and
                holistic development opportunities for our students.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Section 2
    c1, c2 = st.columns([3, 2])
    with c1:
        st.markdown("""
        <div class="info-section fade-delay-3">
            <div class="info-title">📚 Academic Excellence</div>
            <div class="info-text">
                Our department offers comprehensive UG and PG programmes with
                modern curriculum aligned with industry requirements. We focus on
                practical learning, project-based assessments, and continuous
                skill development. Our faculty members are experienced professionals
                dedicated to mentoring and guiding students.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        img_path = os.path.join(ASSETS_DIR, "academic_resources.jpg")
        if os.path.exists(img_path):
            img64 = img_to_base64(img_path)
            st.markdown(
                f"""
                <div class="section-img-wrapper fade-delay-1">
                    <img src="data:image/jpeg;base64,{img64}">
                </div>
                <p style="text-align:center;margin-top:8px;color:#475569; font-weight: 500;">
                    Student Learning Sessions
                </p>
                """,
                unsafe_allow_html=True
            )
        else:
            st.warning("⚠️ academic_resources.jpg not found")

    # ---------- STATISTICS SECTION ----------
    st.markdown("""
        <style>
        @keyframes countUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .stat-container {
            background: linear-gradient(135deg, #ffffff, #f8fafc);
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
            animation: countUp 0.8s ease-out both;
            height: 100%;
        }
        
        .stat-container:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            border-color: #3b82f6;
        }
        
        .stat-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: 800;
            color: #1e40af;
            line-height: 1.2;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            color: #64748b;
            font-size: 1rem;
            font-weight: 500;
        }
        </style>
    """, unsafe_allow_html=True)

    # ---------- STATISTICS SECTION ----------
    st.markdown("""
        <style>
        /* Center the statistics section */
        .statistics-header {
            text-align: center;
            margin: 3rem 0 1.5rem 0;
        }
        
        /* Center the metric cards */
        [data-testid="column"] {
            text-align: center !important;
            display: flex !important;
            justify-content: center !important;
        }
        
        /* Style for metric cards (your original style) */
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
            color: white;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 250px;
            margin: 0 auto;
        }
        
        .metric-card .metric-icon {
            font-size: 3rem;
            margin-bottom: 0.5rem;
        }
        
        .metric-card h3 {
            font-size: 2.5rem;
            font-weight: 800;
            margin: 0.5rem 0;
            color: white;
        }
        
        .metric-card p {
            font-size: 1rem;
            margin: 0;
            opacity: 0.9;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="statistics-header">
            <h2 style="color: #1e40af; font-size: 28px; font-weight: 800; 
                background: linear-gradient(90deg, #1e40af, #2563eb);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                display: inline-block;
                margin-bottom: 1rem;">
                📊 Department Statistics
            </h2>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📊 Department Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-icon">👨‍🎓</div>
            <h3>120+</h3>
            <p>Students</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-icon">👩‍🏫</div>
            <h3>10+</h3>
            <p>Faculty</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-icon">📈</div>
            <h3>50+</h3>
            <p>Achievements</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-icon">📚</div>
            <h3>200+</h3>
            <p>Resources</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    # ---------- ADMIN FUNCTIONS (Only visible to Faculty/Admin) ----------
    if user_role in ["Faculty", "Admin"]:
        st.markdown("""
            <style>
            @keyframes slideUp {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .admin-section {
                background: linear-gradient(135deg, #1e293b, #0f172a);
                border-radius: 20px;
                padding: 2rem;
                margin: 2rem 0;
                color: white;
                animation: slideUp 0.8s ease-out;
            }
            
            .admin-section h2 {
                color: white !important;
                -webkit-text-fill-color: white !important;
            }
            
            .admin-expander {
                background: rgba(255,255,255,0.1);
                border-radius: 12px;
                padding: 1rem;
                margin: 1rem 0;
                backdrop-filter: blur(10px);
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div class="admin-section">
                <h2 style="color: white; font-size: 28px; font-weight: 800; margin-bottom: 0.5rem;">
                    🛠️ Admin Functions
                </h2>
                <p style="color: #94a3b8; margin-bottom: 1.5rem;">
                    Manage department announcements and other administrative tasks
                </p>
            </div>
        """, unsafe_allow_html=True)

        with st.expander("📢 Manage Announcements", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                with st.form("announcement_form"):
                    message = st.text_area("Announcement Message", placeholder="Enter announcement details...")
                    pin = st.checkbox("Pin this announcement (will appear at the top)")
                    expiry = st.date_input("Expiry Date (optional)", value=None)
                    submit = st.form_submit_button("📢 Post Announcement", type="primary", use_container_width=True)
                    
                    if submit and message:
                        expiry_val = str(expiry) if expiry else None
                        cur.execute("""
                            INSERT INTO announcements 
                            (message, announce_date, expiry_date, pinned)
                            VALUES (?, ?, ?, ?)
                        """, (message, str(date.today()), expiry_val, int(pin)))
                        conn.commit()
                        st.success("✅ Announcement posted successfully!")
                        st.balloons()
                        st.rerun()
            
            with col2:
                st.subheader("Recent Announcements")
                cur.execute("""
                    SELECT message, announce_date, pinned 
                    FROM announcements 
                    ORDER BY announce_date DESC 
                    LIMIT 5
                """)
                recent = cur.fetchall()
                if recent:
                    for msg, dte, pinned in recent:
                        pin_icon = "📌 " if pinned else "📢 "
                        safe_msg = str(msg)
                        st.info(f"{pin_icon}**{dte}:** {safe_msg[:100]}...")
                else:
                    st.info("No recent announcements")

    # ---------- FOOTER ----------
    components.html(
        """
        <style>
        @keyframes fadeInFooter {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .footer {
            background: linear-gradient(135deg, #ffffff, #f8fafc);
            border-top: 4px solid #2563eb;
            padding: 40px 30px;
            margin-top: 60px;
            font-family: 'Inter', sans-serif;
            animation: fadeInFooter 0.8s ease-out;
            box-shadow: 0 -10px 25px -5px rgba(0, 0, 0, 0.05);
        }

        .footer-content {
            display: flex;
            gap: 40px;
            align-items: flex-start;
            flex-wrap: wrap;
        }

        .footer-left {
            flex: 1;
        }

        .footer-title {
            font-size: 22px;
            font-weight: 800;
            color: #1e40af;
            margin-bottom: 15px;
            background: linear-gradient(90deg, #1e40af, #2563eb);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .footer-text {
            font-size: 15px;
            color: #334155;
            line-height: 1.7;
        }

        .footer-media {
            display: flex;
            gap: 20px;
        }

        .footer-media iframe {
            width: 260px;
            height: 170px;
            border-radius: 12px;
            border: none;
            box-shadow: 0 8px 18px rgba(0,0,0,0.15);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .footer-media iframe:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.2);
        }

        .footer-copy {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            font-size: 14px;
            color: #64748b;
        }

        @media (max-width:768px) {
            .footer-content {
                flex-direction: column;
            }
            .footer-media {
                flex-direction: column;
            }
            .footer-media iframe {
                width: 100%;
                height: 220px;
            }
        }
        </style>

        <div class="footer">
            <div class="footer-content">
                <div class="footer-left">
                    <div class="footer-title">
                        🎓 Michael Job College of Arts & Science for Women
                    </div>
                    <div class="footer-text">
                        Near Sulur Boat Lake, Ravathur,<br>
                        Coimbatore – 641 402<br>
                        Affiliated to Bharathiar University<br>
                        ISO 9001:2015 & 21001:2018 Certified Institution
                    </div>
                </div>

                <div class="footer-media">
                    <iframe 
                        src="https://www.youtube.com/embed/-RVxNU-bxR0"
                        allowfullscreen>
                    </iframe>
                    <iframe
                        src="https://www.google.com/maps?q=Michael+Job+College+of+Arts+and+Science+for+Women,+Sulur&output=embed"
                        loading="lazy"
                        referrerpolicy="no-referrer-when-downgrade">
                    </iframe>
                </div>
            </div>

            <div class="footer-copy">
                © 2025 Michael Job College of Arts & Science for Women. All Rights Reserved.
            </div>
        </div>
        """,
        height=540
    )
# ================= REGISTRATION PAGE =================
elif page == "enrollment":
    st.markdown(create_header("👤 User Registration", "Create your account to access department services"), unsafe_allow_html=True)
    # Removed the extra ) at the end
    
    with st.container():
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            phone = st.text_input("📱 Phone Number", placeholder="Enter 10-digit phone number")
            name = st.text_input("👤 Full Name", placeholder="Enter your full name")
            password = st.text_input("🔒 Password", type="password", placeholder="Create a strong password")
            confirm_password = st.text_input("✓ Confirm Password", type="password", placeholder="Re-enter your password")
        
        with col2:
            role = st.selectbox("👥 Role", ["Student", "Faculty", "Admin"])
            
            if role == "Student":
                degree = st.selectbox("🎓 Degree", ["BSc CS", "BSc IT", "BCA", "BSc CS(AI)", "MSc CS"])
                year = st.selectbox("📅 Year", [1, 2, 3])
            else:
                degree = None
                year = None
                designation = st.selectbox("💼 Designation", ["Assistant Professor", "Associate Professor", "Professor", "HOD"])
                department = st.selectbox("🏢 Department", [
                    "Computer Science", "Information Technology", "Mathematics", 
                    "Commerce", "English", "Tamil", "History", "Zoology"
                ])
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.button("📝 Register Account", type="primary", use_container_width=True):
            if not all([phone, name, password]):
                st.error("❌ Please fill all required fields")
            elif password != confirm_password:
                st.error("❌ Passwords do not match")
            else:
                cur.execute("SELECT phone FROM users WHERE phone=?", (phone,))
                if cur.fetchone():
                    st.error("❌ Phone number already registered")
                else:
                    try:
                        cur.execute("""
                            INSERT INTO users 
                            (phone, name, password, role, degree, year, designation, department)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            phone, name, hash_pwd(password), role,
                            degree, year, designation if role != "Student" else None,
                            department if role != "Student" else None
                        ))
                        conn.commit()
                        st.success("✅ Registration successful! Please login.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"❌ Registration failed: {str(e)}")
# ================= LOGIN PAGE =================
elif page == "login":
    st.markdown(
        create_header("🔐 Sign In", "Access your department account"),
        unsafe_allow_html=True
    )

    with st.container():
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1])

        # ================= LEFT COLUMN (LOGIN FORM) =================
        with col1:
            phone = st.text_input(
                "📱 Phone Number",
                placeholder="Enter registered phone number"
            )
            password = st.text_input(
                "🔒 Password",
                type="password",
                placeholder="Enter your password"
            )

            if st.button("🚀 Sign In", type="primary", use_container_width=True):
                if not phone or not password:
                    st.error("❌ Please enter both phone and password")
                else:
                    cur.execute("""
                        SELECT phone, name, role, degree, year
                        FROM users
                        WHERE phone=? AND password=?
                    """, (phone, hash_pwd(password)))

                    user = cur.fetchone()

                    if user:
                        # ✅ STEP 3 FIX (CORRECT USER STRUCTURE)
                        st.session_state.user = {
                            "phone": user[0],
                            "name": user[1],
                            "role": user[2],
                            "degree": user[3],
                            "year": user[4]
                        }
                        st.session_state.user_role = user[2]
                        st.session_state.page = "home"

                        st.success(f"✅ Welcome {user[1]}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")
# ================= ENHANCED E-MATERIALS MODULE =================
elif page == "materials":
    # ---------- LOGIN CHECK ----------
    if not st.session_state.user:
        st.markdown("""
        <div class="custom-card" style="text-align: center; padding: 3rem;">
            <div style="font-size: 64px; margin-bottom: 1rem;">🔐</div>
            <h2 style="color: #1e40af;">Login Required</h2>
            <p style="color: #64748b; margin: 1rem 0;">
                Please login to access E-Study Materials
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.stop()
    
    # ================= SUBJECT LIST =================
    SUBJECTS_BY_DEGREE = {
        "BSc CS(AI)": [
            "Language-I","English-I","Programming in C","Data Structures",
            "Discrete Mathematics","Programming Lab-C","Environmental Studies",
            "Language-II","English-II","Programming in C++","Programming Lab C++",
            "Internet Basics Lab","Introduction to Statistics",
            "Value Education-Human Rights","Language-III","English-III",
            "Java Programming","Java Programming Lab","Artificial Intelligence",
            "Software Engineering","Operating System","Women's Rights",
            "Language-IV","English-IV","Python Programming",
            "Introduction to Machine Learning","Python Programming Lab",
            "Design and Analysis of Algorithms",
            "Capstone Project Work (AI & ML) Lab","General Awareness",
            "Advanced Machine Learning Using Python",
            "Advanced Machine Learning Using Python Lab",
            "Fuzzy Logic and Neural Networks",
            "Fundamentals of Robotics / Business Data Analytics / Social Network Analysis",
            "Database Management Systems","R Programming","R Programming Lab",
            "Project Work Lab","Deep Learning / Web Application Security / Software Agents",
            "Natural Language Processing / Client Server Computing / Reinforcement Learning",
            "Oracle and SQL Lab"
        ],
        "BSc CS": [
            "Language-I","English-I","Computing Fundamentals and C Programming",
            "Digital Computer Fundamentals","Programming Lab-C",
            "Mathematical Structures for Computer Science","Environmental Studies",
            "Language-II","English-II","Object Oriented Programming with Java",
            "Programming Lab-Java","Internet Basics","Discrete Mathematics",
            "Value Education-Human Rights","Language-III","English-III",
            "Data Structures","Python Programming","Programming Lab-Python",
            "Machine Learning","Software Engineering","Women's Rights",
            "Language-IV","English-IV","Operating Systems",
            "Linux and Shell Programming","Information Technology Service Management",
            "Software Project Management Lab","General Awareness",
            "RDBMS Programming","Cyber Security","Programming Lab-RDBMS",
            "Linux and Shell Programming Lab","Web Programming",
            "Graphics and Multimedia","Graphics and Multimedia Lab",
            "Network Security and Cryptography/Artificial Intelligence and Expert Systems/Web Technology","Data Mining/Open Source Software/Internet of things","Web Programming Lab"
        ],
        "BSc IT": [
            "Language-I","English-I","Programming Concepts in C",
            "Digital Fundamentals and Computer Architecture",
            "Mathematical Structures for Computer Science",
            "Programming Lab-C","Environmental Studies",
            "Language-II","English-II","OOPs with Java Programming",
            "Programming Lab-Java","Office Automation and Internet",
            "Discrete Mathematics","Human Rights",
            "Language-III","English-III","Data Structures",
            "RDBMS Programming","Programming Lab-RDBMS",
            "Women's Rights","Microprocessor and its Applications",
            "Web Application Development",
            "Language-IV","English-IV","Operating System",
            "Linux and Shell Programming","Internet of Things",
            "Linux and Shell Programming Lab","General Awareness",
            "Python Programming","Programming Lab-Python",
            "Cyber Security","Data Analytics",
            "Software Engineering / Client Server Computing / Distributed Computing",
            "Capstone Project Work Lab",
            "Multimedia and its Applications","Programming Lab-Multimedia",
            "Artificial Intelligence / Business Intelligence / Computational Intelligence",
            "Middleware Technologies / Cloud Computing / Ethical Hacking"
        ],
        "BCA": [
            "Language-I","English-I","Programming Concepts with C and C++",
            "Programming Lab-C and C++","Digital Fundamentals and Computer Architecture",
            "Environmental Studies","Language-II","English-II",
            "Mathematical Structures for Computer Science","Java Programming",
            "Programming Lab-Java","Office Automation and Internet",
            "Human Rights","Language-III","English-III",
            "Programming Lab-RDBMS","Discrete Mathematics",
            "Data Structures","RDBMS","Women's Rights",
            "Language-IV","English-IV","Animation Techniques",
            "Web Application Development","Operating System",
            "Linux and Shell Programming","Linux and Shell Programming Lab",
            "General Awareness","Software Engineering",
            "Python Programming","Programming Lab-Python",
            "Capstone Project Work Lab-Phase I",
            "Cyber Security","Artificial Intelligence and Machine Learning",
            "Project Work Lab-Final Phase",
            "Data Mining and R Programming",
            "Oracle and SQL","AI & ML Lab using Python"
        ],
        "MSc CS": [
            "Analysis and Design of Algorithms",
            "Object Oriented Analysis and Design & C++",
            "Python Programming","Advanced Software Engineering",
            "Algorithm and OOPS Lab","Python Programming Lab",
            "Data Mining and Warehousing","Advanced Operating Systems",
            "Advanced Java Programming","Advanced Java Programming Lab",
            "Artificial Intelligence and Machine Learning",
            "Multimedia & Its Applications / Embedded Systems / IoT",
            "Cloud Computing","Cloud Computing Lab",
            "Network Security and Cryptography",
            "Digital Image Processing","Digital Image Processing Lab",
            "Data Mining Lab using R","Data Science and Analytics",
            "Mobile Computing / Blockchain / Web Services / RPA",
            "Web Application Development & Hosting","Project Work"
        ]
    }

    user = st.session_state.user
    role = user["role"]
    phone = user["phone"]

    st.header("📚 E-Study Materials")
    
    # ---------- DEGREE ----------
    degree = (
        st.selectbox("🎓 Degree", list(SUBJECTS_BY_DEGREE.keys()))
        if role in ["Admin", "Faculty"]
        else user["degree"]
    )
    subjects = SUBJECTS_BY_DEGREE.get(degree, [])
    
    # ---------- FILTER ----------
    col1, col2 = st.columns(2)
    with col1:
        subject_filter = st.selectbox("📘 Subject", ["All"] + subjects, key="subject_filter")
    with col2:
        search = st.text_input("🔍 Search by keyword", key="material_search")

    # ---------- UPLOAD (ADMIN / FACULTY) ----------
    if role in ["Admin", "Faculty"]:
        with st.expander("➕ Upload New Material", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                up_subject = st.selectbox("Subject", subjects)
            with col2:
                up_author = st.text_input("Author Name")
            with col3:
                up_file = st.file_uploader(
                    "Choose File", 
                    type=["pdf", "ppt", "pptx", "doc", "docx"]
                )

            if st.button("🚀 Upload Material", type="primary") and not st.session_state.upload_lock:
                st.session_state.upload_lock = True
                if up_file and up_subject and up_author:
                    fname = f"{int(datetime.now().timestamp())}_{up_file.name}"
                    path = os.path.join(UPLOAD_DIR, fname)

                    with open(path, "wb") as f:
                        f.write(up_file.getbuffer())

                    cur.execute("""
                        INSERT INTO documents
                        (degree, subject, author, filename,
                         uploaded_by_role, uploaded_by_phone, uploaded_on)
                        VALUES (?,?,?,?,?,?,?)
                    """, (
                        degree, up_subject, up_author, fname,
                        role, phone,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))
                    conn.commit()

                    st.success("✅ Material uploaded successfully")
                    st.session_state.upload_lock = False
                    st.rerun()
                else:
                    st.error("Please fill all fields")
                    st.session_state.upload_lock = False

    # ---------- STUDENT PPT UPLOAD ----------
    if role == "Student":
        with st.expander("📤 Submit Presentation", expanded=False):
            ppt_subject = st.selectbox("Presentation Subject", subjects)
            ppt_file = st.file_uploader("Upload PPT", type=["ppt", "pptx"])

            if st.button("📤 Submit Presentation") and not st.session_state.upload_lock:
                st.session_state.upload_lock = True
                if ppt_file:
                    fname = f"STU_{phone}_{int(datetime.now().timestamp())}_{ppt_file.name}"
                    path = os.path.join(UPLOAD_DIR, fname)

                    with open(path, "wb") as f:
                        f.write(ppt_file.getbuffer())

                    cur.execute("""
                        INSERT INTO documents
                        (degree, subject, author, filename,
                         uploaded_by_role, uploaded_by_phone, uploaded_on)
                        VALUES (?,?,?,?,?,?,?)
                    """, (
                        degree, ppt_subject, "Student PPT",
                        fname, "Student", phone,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))
                    conn.commit()

                    st.success("✅ Presentation submitted")
                    st.session_state.upload_lock = False
                    st.rerun()

    # ---------- FETCH MATERIALS ----------
    query = """
        SELECT id, subject, author, filename,
               uploaded_by_role, uploaded_by_phone, uploaded_on
        FROM documents WHERE degree=?
    """
    params = [degree]

    if subject_filter != "All":
        query += " AND subject=?"
        params.append(subject_filter)
    if search:
        query += " AND (subject LIKE ? OR author LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY uploaded_on DESC"
    cur.execute(query, params)
    docs = cur.fetchall()

    # ---------- DISPLAY IN TABULAR FORMAT ----------
    st.markdown("### 📋 Materials List")
    
    if docs:
        # Create table headers
        col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 1.5, 1, 1, 1])
        with col1:
            st.markdown("**📘 Subject**")
        with col2:
            st.markdown("**👤 Author**")
        with col3:
            st.markdown("**📅 Uploaded On**")
        with col4:
            st.markdown("**👍 Likes**")
        with col5:
            st.markdown("**⬇️ Download**")
        with col6:
            st.markdown("**⚡ Actions**")
        
        st.markdown("---")
        
        # Display each material in a row
        for idx, d in enumerate(docs):
            doc_id, subject, author, filename, u_role, u_phone, uploaded_on = d
            path = os.path.join(UPLOAD_DIR, filename)
            
            # Get like count
            cur.execute("SELECT COUNT(*) FROM likes WHERE doc_id=?", (doc_id,))
            like_count = cur.fetchone()[0]
            
            # Format date to show only date part
            upload_date = uploaded_on.split()[0] if uploaded_on else "N/A"
            
            # Create row columns
            cols = st.columns([2, 2, 1.5, 1, 1, 1])
            
            with cols[0]:  # Subject
                st.write(subject)
            
            with cols[1]:  # Author
                st.write(author)
            
            with cols[2]:  # Uploaded On
                st.write(upload_date)
            
            with cols[3]:  # Likes
                st.write(f"👍 {like_count}")
            
            with cols[4]:  # Download button
                if os.path.isfile(path):
                    with open(path, "rb") as f:
                        file_data = f.read()
                    st.download_button(
                        "📥",
                        file_data,
                        file_name=filename,
                        key=f"dl_{doc_id}",
                        help="Download file"
                    )
                else:
                    st.write("❌")
            
            with cols[5]:  # Action buttons
                if role == "Student":
                    if st.button("👍", key=f"like_{doc_id}", help="Like this material"):
                        cur.execute(
                            "INSERT OR IGNORE INTO likes (doc_id, phone) VALUES (?,?)",
                            (doc_id, phone)
                        )
                        conn.commit()
                        st.rerun()
                
                if role in ["Admin", "Faculty"] or (role == "Student" and u_role == "Student" and u_phone == phone):
                    if st.button("🗑️", key=f"del_{doc_id}", help="Delete material"):
                        if os.path.isfile(path):
                            os.remove(path)
                        cur.execute("DELETE FROM documents WHERE id=?", (doc_id,))
                        cur.execute("DELETE FROM likes WHERE doc_id=?", (doc_id,))
                        cur.execute("DELETE FROM comments WHERE doc_id=?", (doc_id,))
                        conn.commit()
                        st.success("Material deleted")
                        st.rerun()
            
            # Add a subtle separator between rows
            if idx < len(docs) - 1:
                st.markdown("---")
        
        # Summary statistics
        st.markdown("---")
        st.info(f"📊 Total Materials: {len(docs)} | 📘 Subject: {subject_filter if subject_filter != 'All' else 'All Subjects'}")
    
    else:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background: #f8fafc; border-radius: 10px;">
            <div style="font-size: 48px; margin-bottom: 1rem;">📭</div>
            <h3 style="color: #1e293b;">No Materials Found</h3>
            <p style="color: #64748b;">
                No study materials available for the selected filters.
            </p>
        </div>
        """, unsafe_allow_html=True)
# ---------------------------------------
elif page == "syllabus":

    import os, time
    from datetime import datetime

    user = st.session_state.user
    if not user:
        st.warning("🔐 Please login to access syllabus")
        st.stop()

    role = user.get("role")

    # ================= DEGREE SHORT NAME =================
    DEGREE_SHORT = {
        "BCA": "bca",
        "B.Sc Computer Science": "bsc_comp_sci",
        "B.Sc Computer Science (AI)": "bsc_comp_sci_ai",
        "B.Sc Information Technology": "bsc_it",
        "M.Sc Computer Science": "msc_cs"
    }

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_DIR = "uploads"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # ================= FACULTY UPLOAD =================
    if role == "Faculty":
        with st.expander("📤 Upload Syllabus"):
            with st.form("upload_syllabus"):
                up_degree = st.selectbox(
                    "Degree",
                    [
                        "B.Sc Computer Science",
                        "B.Sc Information Technology",
                        "B.Sc Computer Science (AI)",
                        "BCA",
                        "M.Sc Computer Science"
                    ]
                )

                up_type = st.selectbox("Type", ["UG", "PG"])
                up_file = st.file_uploader("Upload Syllabus PDF", type=["pdf"])

                submit = st.form_submit_button("Upload")

                if submit:
                    if not up_file:
                        st.error("❌ Please upload syllabus PDF")
                    else:
                        filename = f"{int(time.time())}_{up_file.name}"
                        save_path = os.path.join(UPLOAD_DIR, filename)

                        with open(save_path, "wb") as f:
                            f.write(up_file.getbuffer())

                        cur.execute("""
                            INSERT INTO syllabus (
                                degree, syllabus_type,
                                file_path, download_count,
                                uploaded_by, uploaded_date
                            ) VALUES (?, ?, ?, 0, ?, ?)
                        """, (
                            up_degree,
                            up_type,
                            save_path,
                            user.get("name"),
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ))
                        conn.commit()
                        st.success("✅ Syllabus uploaded successfully")

    # ================= FILTERS =================
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        filter_degree = st.selectbox(
            "Degree",
            [
                "All",
                "B.Sc Computer Science",
                "B.Sc Information Technology",
                "B.Sc Computer Science (AI)",
                "BCA",
                "M.Sc Computer Science"
            ]
        )

    with col2:
        st.selectbox("Year", ["All"])

    with col3:
        filter_type = st.selectbox("Type", ["All", "UG", "PG"])

    with col4:
        st.selectbox("Course", ["All"])

    # ================= STATS =================
    cur.execute("SELECT COUNT(*) FROM syllabus")
    total_syllabi = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT degree) FROM syllabus")
    course_count = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(download_count),0) FROM syllabus")
    total_downloads = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT uploaded_by) FROM syllabus")
    contributors = cur.fetchone()[0]

    stats = [
        ("📘", total_syllabi, "Total Syllabi"),
        ("🎓", course_count, "Courses"),
        ("⬇️", total_downloads, "Downloads"),
        ("👥", contributors, "Contributors")
    ]

    cols = st.columns(4)
    for i, (icon, val, label) in enumerate(stats):
        with cols[i]:
            st.markdown(f"""
            <div style="text-align:center;padding:1.5rem;border-radius:15px;
                        background:#f8fafc;border:2px solid #10b981">
                <div style="font-size:32px">{icon}</div>
                <h2>{val}</h2>
                <p>{label}</p>
            </div>
            """, unsafe_allow_html=True)

    # ================= QUERY =================
    query = """
        SELECT
            id,degree,syllabus_type,file_path,download_count,uploaded_by,uploaded_date FROM syllabus WHERE 1=1"""
    params = []

    if filter_degree != "All":
        query += " AND degree = ?"
        params.append(filter_degree)

    if filter_type != "All":
        query += " AND syllabus_type = ?"
        params.append(filter_type)

    query += " ORDER BY uploaded_date DESC"
    cur.execute(query, params)
    syllabi = cur.fetchall()

    # ================= DISPLAY =================
    if not syllabi:
        st.info("📭 No syllabus found for selected filters")
    else:
        for s in syllabi:
            sid, degree, syllabus_type, file_path, download_count, uploaded_by, uploaded_date = s

            st.markdown(f"""
            <div class="custom-card">
                <h4>Syllabus</h4>
                <p style="color:#64748b">
                    {degree} | {syllabus_type}
                </p>
                <p style="font-size:13px">⬇️ {download_count} downloads</p>
            </div>
            """, unsafe_allow_html=True)

            absolute_path = os.path.join(BASE_DIR, file_path)

            colA, colB = st.columns([3, 1])

            with colA:
                if os.path.exists(absolute_path):
                    with open(absolute_path, "rb") as f:
                        if st.download_button(
                            "📥 Download Syllabus",
                            f,
                            file_name=f"{DEGREE_SHORT.get(degree,'syllabus')}_2025_26.pdf",
                            mime="application/pdf",
                            key=f"dl_{sid}"
                        ):
                            cur.execute(
                                "UPDATE syllabus SET download_count = download_count + 1 WHERE id=?",
                                (sid,)
                            )

                            cur.execute("""
                                INSERT INTO syllabus_downloads (
                                    syllabus_id,
                                    downloaded_by,
                                    downloaded_by_name,
                                    downloaded_by_role,
                                    download_date
                                )
                                VALUES (?, ?, ?, ?, ?)
                            """, (
                                sid,
                                user.get("phone"),
                                user.get("name"),
                                role,
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ))
                            conn.commit()

            # ================= FACULTY DELETE =================
            if role == "Faculty":
                with colB:
                    if st.button("🗑 Delete", key=f"del_{sid}"):
                        # delete file
                        if os.path.exists(absolute_path):
                            os.remove(absolute_path)

                        # delete db record
                        cur.execute("DELETE FROM syllabus WHERE id = ?", (sid,))
                        conn.commit()

                        st.success("🗑 Syllabus deleted successfully")
                        st.rerun()

    # ================= DOWNLOAD HISTORY =================
    with st.expander("📥 My Download History"):
        cur.execute("""
            SELECT s.degree, d.download_date
            FROM syllabus_downloads d
            JOIN syllabus s ON s.id = d.syllabus_id
            WHERE d.downloaded_by = ?
            ORDER BY d.download_date DESC
        """, (user.get("phone"),))

        rows = cur.fetchall()
        if not rows:
            st.info("No downloads yet")
        else:
            for deg, dt in rows:
                st.write(f"• **{deg}** – {dt}")
#----------------------------------------------------
elif page == "assignments":
    st.markdown("""
    <style>
    /* Assignment Card Animations */
    @keyframes assignmentCardAppear {
        0% {
            opacity: 0;
            transform: translateY(30px) scale(0.95);
            filter: blur(5px);
        }
        100% {
            opacity: 1;
            transform: translateY(0) scale(1);
            filter: blur(0);
        }
    }
    
    .assignment-card-animation {
        animation: assignmentCardAppear 0.6s ease-out forwards;
    }
    
    /* Deadline Pulse Animation */
    @keyframes deadlinePulse {
        0%, 100% { 
            box-shadow: 0 0 10px rgba(239, 68, 68, 0.3),
                        inset 0 0 5px rgba(255,255,255,0.3);
        }
        50% { 
            box-shadow: 0 0 20px rgba(239, 68, 68, 0.6),
                        0 0 30px rgba(239, 68, 68, 0.4),
                        inset 0 0 10px rgba(255,255,255,0.5);
        }
    }
    
    .deadline-pulse {
        animation: deadlinePulse 2s infinite;
    }
    
    /* Upload Animation */
    @keyframes uploadFloat {
        0% {
            transform: translateY(0) scale(1);
            opacity: 0.8;
        }
        50% {
            transform: translateY(-10px) scale(1.05);
            opacity: 1;
        }
        100% {
            transform: translateY(0) scale(1);
            opacity: 0.8;
        }
    }
    
    .upload-float {
        animation: uploadFloat 3s ease-in-out infinite;
    }
    
    /* Checkmark Animation */
    @keyframes checkmarkPop {
        0% {
            transform: scale(0);
            opacity: 0;
        }
        70% {
            transform: scale(1.2);
            opacity: 1;
        }
        100% {
            transform: scale(1);
            opacity: 1;
        }
    }
    
    .checkmark-pop {
        animation: checkmarkPop 0.5s ease-out forwards;
    }
    
    /* Submission Status Colors */
    .submitted-badge {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
    }
    
    .pending-badge {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3);
    }
    
    .overdue-badge {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
    }
    
    /* Progress Bar Animation */
    @keyframes progressFill {
        0% { width: 0%; }
        100% { width: var(--progress); }
    }
    
    .assignment-progress-bar {
        height: 6px;
        background: #e2e8f0;
        border-radius: 3px;
        overflow: hidden;
        margin: 10px 0;
        position: relative;
    }
    
    .assignment-progress-fill {
        position: absolute;
        height: 100%;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        border-radius: 3px;
        animation: progressFill 1.5s ease-out forwards;
        width: 0%;
    }
    
    /* File Card Design */
    .file-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        border: 2px solid #e2e8f0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .file-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 5px;
        height: 100%;
        background: linear-gradient(to bottom, #3b82f6, #8b5cf6);
    }
    
    .file-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
        border-color: #3b82f6;
    }
    
    /* Grading Star Animation */
    @keyframes starTwinkle {
        0%, 100% { 
            transform: scale(1) rotate(0deg);
            opacity: 1;
        }
        50% { 
            transform: scale(1.1) rotate(10deg);
            opacity: 0.8;
        }
    }
    
    .star-twinkle {
        animation: starTwinkle 2s infinite;
        display: inline-block;
    }
    
    /* Assignment Countdown */
    .countdown-timer {
        font-family: 'Courier New', monospace;
        font-weight: bold;
        padding: 8px 15px;
        border-radius: 10px;
        background: linear-gradient(135deg, #1e293b, #334155);
        color: white;
        display: inline-block;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    /* Floating Paper Animation */
    @keyframes paperFloat {
        0% {
            transform: translateY(0) rotate(0deg);
        }
        25% {
            transform: translateY(-20px) rotate(5deg);
        }
        50% {
            transform: translateY(-40px) rotate(0deg);
        }
        75% {
            transform: translateY(-20px) rotate(-5deg);
        }
        100% {
            transform: translateY(0) rotate(0deg);
        }
    }
    
    .paper-float {
        animation: paperFloat 6s ease-in-out infinite;
    }
    
    /* Upload Success Celebration */
    .assignment-celebration {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 10000;
    }
    
    .confetti {
        position: absolute;
        width: 10px;
        height: 20px;
        animation: confettiFall 3s linear forwards;
    }
    
    @keyframes confettiFall {
        0% {
            transform: translateY(-100px) rotate(0deg);
            opacity: 1;
        }
        100% {
            transform: translateY(100vh) rotate(720deg);
            opacity: 0;
        }
    }
    
    .paper-plane-assignment {
        position: absolute;
        font-size: 24px;
        animation: assignmentPaperFly 4s linear forwards;
    }
    
    @keyframes assignmentPaperFly {
        0% {
            transform: translateX(-100px) translateY(100vh) rotate(0deg);
            opacity: 1;
        }
        100% {
            transform: translateX(100vw) translateY(-100px) rotate(720deg);
            opacity: 0;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    # ---------- LOGIN CHECK ----------
    if not st.session_state.get("user"):
        st.warning("🔐 Please login to access assignments")
        st.stop()

    user = st.session_state.user
    role = user["role"]
    phone = user["phone"]

    # ==================================================
    # HEADER
    # ==================================================
    st.markdown("""
    <h1 style="font-size:3rem;font-weight:900;
               background:linear-gradient(90deg,#f59e0b,#ef4444,#8b5cf6);
               -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
        📝 Assignment Management
    </h1>
    <p style="color:#64748b;font-size:1.2rem;">
        Create, submit, and manage academic assignments
    </p>
    """, unsafe_allow_html=True)

    # ==================================================
    # 👩‍🏫 FACULTY VIEW
    # ==================================================
    if role == "Faculty":

        # ---------- CREATE ASSIGNMENT ----------
        st.subheader("📤 Create New Assignment")

        with st.form("create_assignment"):
            col1, col2 = st.columns(2)

            with col1:
                title = st.text_input("📝 Assignment Title")
                degree = st.selectbox("🎓 Degree", ["BSc CS", "BSc IT", "BCA", "BSc CS(AI)", "MSc CS"])
                deadline = st.date_input("⏰ Deadline", min_value=date.today())

            with col2:
                year = st.selectbox("📅 Year", [1, 2, 3, 4])
                max_marks = st.number_input("⭐ Maximum Marks", min_value=0, max_value=100, value=100)
                assignment_type = st.selectbox("📄 Assignment Type",
                                               ["Project", "Homework", "Lab Work", "Report", "Presentation"])

            description = st.text_area("📋 Detailed Instructions", height=150)
            attachment = st.file_uploader("📎 Reference Material (Optional)",
                                           type=["pdf", "doc", "docx", "ppt", "pptx"])

            submit = st.form_submit_button("🚀 Create Assignment")

            if submit:
                if not title or not description:
                    st.error("❌ Title and description required")
                else:
                    attachment_path = None
                    if attachment:
                        fname = f"REF_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{attachment.name}"
                        attachment_path = os.path.join(UPLOAD_DIR, fname)
                        with open(attachment_path, "wb") as f:
                            f.write(attachment.getbuffer())

                    cur.execute("""
                        INSERT INTO assignments
                        (title, description, degree, year, deadline,
                         max_marks, assignment_type, attachment_path,
                         created_by, created_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        title, description, degree, year,
                        str(deadline), max_marks,
                        assignment_type, attachment_path,
                        phone, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))
                    conn.commit()
                    st.success("✅ Assignment created successfully")
                    st.rerun()

        st.divider()

        # ---------- MANAGE ASSIGNMENTS ----------
        st.subheader("🛠️ Manage Assignments")

        cur.execute("""
            SELECT id, title, description, degree, year, deadline,
                   max_marks, assignment_type, created_date
            FROM assignments
            WHERE created_by=?
            ORDER BY deadline
        """, (phone,))
        assignments = cur.fetchall()

        if not assignments:
            st.info("📭 No assignments created yet")
        else:
            for a in assignments:
                (a_id, title, desc, degree, year, deadline,
                 max_marks, a_type, created_date) = a

                with st.expander(f"📌 {title} ({degree} - Year {year})"):
                    st.write(desc)
                    st.write(f"⭐ Max Marks: {max_marks}")
                    st.write(f"📄 Type: {a_type}")
                    st.write(f"⏰ Deadline: {deadline}")

                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("🗑 Delete Assignment", key=f"del_{a_id}"):
                            cur.execute("DELETE FROM assignment_submissions WHERE assignment_id=?", (a_id,))
                            cur.execute("DELETE FROM assignments WHERE id=?", (a_id,))
                            conn.commit()
                            st.warning("🗑 Assignment deleted")
                            st.rerun()

    # ==================================================
    # 👩‍🎓 STUDENT VIEW
    # ==================================================
    else:
        st.subheader("📚 Your Assignments")

        degree = user["degree"]
        year = user["year"]

        cur.execute("""
            SELECT a.id, a.title, a.description, a.deadline,
                   a.max_marks, a.assignment_type, a.attachment_path,
                   s.file_path, s.marks, s.feedback
            FROM assignments a
            LEFT JOIN assignment_submissions s
                ON a.id = s.assignment_id AND s.student_phone=?
            WHERE a.degree=? AND a.year=?
            ORDER BY a.deadline
        """, (phone, degree, year))

        rows = cur.fetchall()

        if not rows:
            st.info("🎉 No assignments available")
        else:
            for r in rows:
                (a_id, title, desc, deadline, max_marks,
                 a_type, attachment_path, sub_file, marks, feedback) = r

                with st.expander(f"📄 {title}"):
                    st.write(desc)
                    st.write(f"⭐ Max Marks: {max_marks}")
                    st.write(f"⏰ Deadline: {deadline}")

                    if marks is not None:
                        st.success(f"⭐ Marks: {marks}/{max_marks}")
                        if feedback:
                            st.info(f"💬 Feedback: {feedback}")

                    if attachment_path and os.path.exists(attachment_path):
                        with open(attachment_path, "rb") as f:
                            st.download_button("📎 Reference Material", f,
                                               file_name=os.path.basename(attachment_path))

                    if not sub_file:
                        upload = st.file_uploader("📤 Submit Assignment",
                                                  key=f"up_{a_id}",
                                                  type=["pdf", "doc", "docx", "ppt", "pptx", "zip"])
                        if upload and st.button("🚀 Submit", key=f"sub_{a_id}"):
                            fname = f"{phone}_{a_id}_{upload.name}"
                            path = os.path.join(UPLOAD_DIR, fname)
                            with open(path, "wb") as f:
                                f.write(upload.getbuffer())

                            cur.execute("""
                                INSERT OR REPLACE INTO assignment_submissions
                                (assignment_id, student_phone, file_path, submitted_on)
                                VALUES (?, ?, ?, ?)
                            """, (
                                a_id, phone, path,
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ))
                            conn.commit()
                            st.success("✅ Assignment submitted")
                            st.rerun()
elif page == "lab_register":

    LAB_CLASSES = [
    "BSc CS",
    "BSc CS(AI)",
    "BSc IT",
    "BCA",
    "BCom",
    "BCom (IT)",
    "BCom (CA & IT)",
    "English",
    "Tamil",
    "Zoology",
    "History"
    ]
    LAB_YEARS = ["1 YEAR", "2 YEAR", "3 YEAR"]
    LAB_ROOMS = [
        "🖥️ Lab 01",
        "🖥️ Lab 02",
        "🖥️ IT Lab 3"
    ]
    TOTAL_SYSTEMS_PER_LAB = {
        "🖥️ Lab 01": 40,
        "🖥️ Lab 02": 35,
        "🖥️ IT Lab 3": 30
    }

    if not st.session_state.user:
        st.error("🔐 Please login to access Lab Register")
        st.stop()

    user = st.session_state.user
    role = st.session_state.user_role

    tabs = st.tabs(
        ["📅 Manage Sessions", "👥 Lab In-Charge", "📊 Live Dashboard", "🔧 Tools & Reports"]
        if role in ["Faculty", "Admin"]
        else ["📝 Mark Attendance", "📈 My History", "📊 My Performance"]
    )

    # ==========================================================
    # FACULTY / ADMIN
    # ==========================================================
    if role in ["Faculty", "Admin"]:

        # ----------------- MANAGE SESSIONS -----------------
        with tabs[0]:
            st.subheader("📅 Create Lab Session")

            with st.form("create_session", clear_on_submit=True):
                col1, col2 = st.columns(2)

                with col1:
                    subject = st.text_input("Lab Subject *")
                    lab_room = st.selectbox("Lab Room", LAB_ROOMS)
                    lab_class = st.selectbox("Class", LAB_CLASSES)

                with col2:
                    lab_year = st.selectbox("Year", LAB_YEARS)
                    start_time = st.time_input("Start Time", dt_time(10, 0))
                    end_time = st.time_input("End Time", dt_time(12, 0))
                    session_date = st.date_input("Session Date", date.today())

                submit = st.form_submit_button("➕ Create Session")

                if submit:
                    if not subject.strip():
                        st.error("❌ Lab subject required")
                    elif end_time <= start_time:
                        st.error("❌ End time must be after start time")
                    else:
                        hours = round(
                            (datetime.combine(date.today(), end_time) -
                             datetime.combine(date.today(), start_time)).seconds / 3600, 2
                        )
                        try:
                            cur.execute("""
                                INSERT INTO lab_sessions
                                (session_date, session_name, lab_room, class, year,
                                 start_time, end_time, hours, staff_name)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                str(session_date), subject, lab_room,
                                lab_class, lab_year,
                                str(start_time), str(end_time),
                                hours, user["name"]
                            ))
                            conn.commit()
                            st.success("✅ Session created successfully")
                        except sqlite3.IntegrityError:
                            st.error("⚠️ Session already exists")

            st.subheader("📋 All Sessions")
            df = pd.read_sql("SELECT * FROM lab_sessions ORDER BY session_date DESC", conn)
            st.dataframe(df, use_container_width=True)

        # ----------------- LAB IN-CHARGE -----------------
        with tabs[1]:
            st.subheader("👥 Assign Lab In-Charge")

            with st.form("add_incharge", clear_on_submit=True):
                staff = st.text_input("Staff Name *")
                lab = st.selectbox("Lab", LAB_ROOMS)
                cls = st.selectbox("Class", LAB_CLASSES)
                yr = st.selectbox("Year", LAB_YEARS)
                sub = st.text_input("Lab Subject *")

                if st.form_submit_button("Assign"):
                    if not staff or not sub:
                        st.error("❌ All fields required")
                    else:
                        cur.execute("""
                            INSERT OR IGNORE INTO lab_staff
                            (staff_name, lab_name, class, year, lab_subject, created_date)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """, (staff, lab, cls, yr, sub, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
                        st.success("✅ Lab In-Charge Assigned")

            st.dataframe(
                pd.read_sql("SELECT * FROM lab_staff ORDER BY rowid DESC", conn),
                use_container_width=True
            )

        # ----------------- LIVE DASHBOARD -----------------
        with tabs[2]:
            today = str(date.today())

            cur.execute("SELECT COUNT(*) FROM lab_attendance WHERE lab_date=?", (today,))
            st.metric("👨‍🎓 Students Today", cur.fetchone()[0])

            cur.execute("SELECT COUNT(DISTINCT session_id) FROM lab_attendance WHERE lab_date=?", (today,))
            st.metric("📅 Sessions Today", cur.fetchone()[0])
        # ----------------- REPORTS -----------------
        with tabs[3]:
            st.subheader("📊 Daily Lab Report")
            report_date = st.date_input("📅 Select Date", value=date.today())
            report_data = pd.read_sql("""
            SELECT 
                a.lab_date,
                s.lab_room,
                a.student_name,
                a.register_no,
                a.system_no,
                a.hours,
                a.staff_name
                FROM lab_attendance a
                JOIN lab_sessions s ON a.session_id = s.id
                WHERE a.lab_date = ?
                ORDER BY s.lab_room
            """, conn, params=(str(report_date),))

            if report_data.empty:
                st.info("📭 No attendance records for selected date")
            else:
                st.dataframe(report_data, use_container_width=True)

                total_students = len(report_data)
                total_hours = report_data["hours"].sum()

                st.metric("👨‍🎓 Total Students", total_students)
                st.metric("⏱ Total Lab Hours", total_hours)

    # ==========================================================
    # STUDENT
    # ==========================================================
    else:
        with tabs[0]:
            st.subheader("📝 Mark Lab Attendance")

            sessions = pd.read_sql("""
                SELECT * FROM lab_sessions
                WHERE class=? AND year=? AND session_date>=DATE('now')
                ORDER BY session_date
            """, conn, params=(user["degree"], f"{user['year']} YEAR"))

            if sessions.empty:
                st.info("📭 No lab sessions available")
                st.stop()

            labels = sessions.apply(
                lambda r: f"{r.session_date} | {r.lab_room} | {r.session_name}",
                axis=1
            )

            selected_label = st.selectbox("Select Session", labels)
            session_id = sessions.iloc[labels.tolist().index(selected_label)]["id"]

            selected_row = sessions[sessions["id"] == session_id].iloc[0]
            occupied = get_lab_occupancy(selected_row["lab_room"], session_id, conn)

            total_systems = TOTAL_SYSTEMS_PER_LAB[selected_row["lab_room"]]
            system_no = st.number_input("System Number", 1, total_systems)

            if st.button("✅ Mark Attendance"):
                try:
                    if system_no in occupied:
                        st.error("❌ System already occupied")
                    else:
                        cur.execute("""
                            INSERT INTO lab_attendance
                            (lab_date, session_id, register_no, student_name,
                             class, year, lab_room, system_no, hours, staff_name)
                            SELECT session_date, id, ?, ?, class, year,
                                   lab_room, ?, hours, staff_name
                            FROM lab_sessions WHERE id=?
                        """, (
                            user["phone"], user["name"],
                            system_no, session_id
                        ))
                        conn.commit()
                        st.success("🎉 Attendance marked successfully")
                except sqlite3.IntegrityError:
                    st.error("⚠️ Attendance already marked")

        with tabs[1]:
            st.subheader("📈 My Attendance History")

            history = pd.read_sql("""
                SELECT lab_date, lab_room, system_no, hours, staff_name
                FROM lab_attendance
                WHERE register_no=?
                ORDER BY lab_date DESC
            """, conn, params=(user["phone"],))

            st.dataframe(history, use_container_width=True)

        with tabs[2]:
            st.subheader("📊 My Performance")

            marks = pd.read_sql("""
                SELECT lab_subject, mark, max_mark, evaluated_date, remarks
                FROM lab_internal_marks
                WHERE register_no=?
            """, conn, params=(user["phone"],))

            if marks.empty:
                st.info("No internal marks available")
            else:
                st.dataframe(marks, use_container_width=True)

    conn.close()
    #------------------------------------
elif page =="daily_lab_report":
    # Access control
    if not st.session_state.user or st.session_state.user_role not in ["Faculty", "Admin"]:
        st.error("🔐 Faculty / Admin access required")
        st.stop()

    # Header (UNCHANGED UI)
    st.markdown("""
    <div class="lab-header">
        <h1>📊 Daily Lab Analytics Dashboard</h1>
        <h2>Comprehensive Lab Usage Reports & Insights</h2>
    </div>
    """, unsafe_allow_html=True)

    # Filters (UNCHANGED UI)
    col1, col2 = st.columns(2)
    with col1:
        report_date = st.date_input("📅 Select Date", value=date.today())
    with col2:
        selected_lab = st.selectbox(
            "🔍 Select Lab",
            ["All Labs", "Lab 01 ", "Lab 02", "IT Lab 3"]
        )

    # Generate report
    if st.button(
        "📈 Generate Comprehensive Report",
        type="primary",
        use_container_width=True
    ):
        generate_comprehensive_report(report_date, selected_lab, conn)

    conn.close()
# ================= EXCELLENCE GALLERY PAGE =================
elif page == "excellence_gallery":
    excellence_gallery_page(conn, cur)
#---------------------------------------------------------
elif page == "alumni_meet":
    # ---------- LOGIN CHECK ----------
    if not st.session_state.user:
        st.markdown("""
        <div style="text-align: center; padding: 4rem; margin: 2rem 0; background: white; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <div style="font-size: 80px; margin-bottom: 1rem; color: #3b82f6;">🎓</div>
            <h2 style="color: #1e40af; margin-bottom: 1rem;">Alumni Network Portal</h2>
            <p style="color: #64748b; margin: 1rem 0 2rem 0;">
                Please login to connect with alumni and view events
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Go to Login", key="alumni-login-redirect-btn", use_container_width=True):
            st.session_state.page = "🔓 Sign In"
            st.rerun()
        st.stop()

    # ---------- INITIALIZATION ----------
    user = st.session_state.user
    role = user["role"]
    user_name = user["name"].split()[0] if " " in user["name"] else user["name"]

    # ---------- HEADER WITH VISUALIZATION ----------
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0;">
        <h1 style="font-size: 3rem; font-weight: 900; margin-bottom: 0.5rem;
                   background: linear-gradient(90deg, #3b82f6, #8b5cf6, #10b981);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            🎓 Alumni Network
        </h1>
        <p style="color: #64748b; font-size: 1.2rem; margin-bottom: 2rem;">
            Connect, Network, and Grow with our Alumni Community
        </p>
    """, unsafe_allow_html=True)
    # ---------- WELCOME CARD ----------
    with st.container():
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("## 👋")
        with col2:
            st.markdown(f"### Welcome to the Alumni Network, {user_name}!")
            st.markdown(f"You're accessing as a **{role}**.")

    # ---------- STATISTICS CARD ----------
    st.markdown("### 📊 Alumni Network Statistics")
    
    # Get statistics (with error handling)
    try:
        stats = get_alumni_statistics()
    except:
        stats = {'total_alumni': 0, 'companies': 0, 'departments': 0, 'locations': 0}
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🎓 Alumni", stats['total_alumni'])
    with col2:
        st.metric("📅 Departments", stats['departments'])
    with col3:
        st.metric("🏢 Companies", stats['companies'])
    with col4:
        st.metric("🌍 Locations", stats['locations'])

    st.divider()

    # ---------- UPCOMING EVENTS ----------
    st.markdown("### ⏰ Upcoming Alumni Events")
    
    try:
        cur.execute("""
            SELECT title, date, venue 
            FROM alumni_events 
            WHERE status = 'Upcoming' AND date >= date('now')
            ORDER BY date 
            LIMIT 3
        """)
        upcoming_events = cur.fetchall()
        
        if upcoming_events:
            cols = st.columns(len(upcoming_events))
            for idx, (title, event_date, venue) in enumerate(upcoming_events):
                with cols[idx]:
                    event_date_obj = date.fromisoformat(event_date)
                    days_until = (event_date_obj - date.today()).days
                    
                    with st.container(border=True):
                        st.markdown(f"**{title}**")
                        st.markdown(f"# {days_until}")
                        st.markdown("days to go")
                        st.caption(f"📍 {venue}")
                        st.caption(f"📅 {event_date}")
        else:
            st.info("No upcoming events scheduled.")
    except:
        st.info("Events feature coming soon!")

    st.divider()

    # ==================================================
    # 👩‍🏫 FACULTY/ADMIN VIEW - CREATE EVENT
    # ==================================================
    if role in ["Faculty", "Admin"]:
        st.markdown("### 📅 Create Alumni Event")
        
        with st.form("alumni_event_form"):
            title = st.text_input("Event Title *")
            event_date = st.date_input("Event Date", min_value=date.today())
            venue = st.text_input("Venue *")
            description = st.text_area("Description *")
            
            col1, col2 = st.columns(2)
            with col1:
                capacity = st.number_input("Capacity", min_value=10, max_value=1000, value=100)
            with col2:
                registration_fee = st.number_input("Registration Fee (₹)", min_value=0.0, value=0.0, step=100.0)
            
            with st.expander("Additional Details (Optional)"):
                contact_person = st.text_input("Contact Person")
                contact_email = st.text_input("Contact Email")
                hashtag = st.text_input("Event Hashtag", placeholder="#AlumniMeet2025")
            
            if st.form_submit_button("Create Event", type="primary", use_container_width=True):
                if title and venue and description:
                    try:
                        cur.execute("""
                            INSERT INTO alumni_events 
                            (title, description, date, venue, capacity, registration_fee, 
                             contact_person, contact_email, hashtag, created_by, created_date, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            title, description, str(event_date), venue, capacity, registration_fee,
                            contact_person, contact_email, hashtag,
                            user["name"], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                            "Upcoming"
                        ))
                        conn.commit()
                        st.success("✅ Event created successfully!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.error("Please fill all required fields (*)")

        st.divider()

    # ==================================================
    # 📅 ALL ALUMNI EVENTS
    # ==================================================
    st.markdown("### 📋 All Alumni Events")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        filter_status = st.selectbox("Filter by Status", ["All", "Upcoming", "Past"])
    with col2:
        sort_by = st.selectbox("Sort by", ["Date (Newest)", "Date (Oldest)"])
    
    try:
        # Create events table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS alumni_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                date TEXT,
                venue TEXT,
                capacity INTEGER,
                registration_fee REAL,
                contact_person TEXT,
                contact_email TEXT,
                hashtag TEXT,
                created_by TEXT,
                created_date TEXT,
                status TEXT DEFAULT 'Upcoming'
            )
        """)
        conn.commit()
        
        # Build query
        query = "SELECT * FROM alumni_events"
        params = []
        
        if filter_status == "Upcoming":
            query += " WHERE status = 'Upcoming' AND date >= date('now')"
        elif filter_status == "Past":
            query += " WHERE status = 'Past' OR date < date('now')"
        
        if sort_by == "Date (Newest)":
            query += " ORDER BY date DESC"
        else:
            query += " ORDER BY date ASC"
        
        cur.execute(query, params)
        events = cur.fetchall()
        
        if not events:
            st.info("No events found. Be the first to create an event!")
        else:
            for event in events:
                if len(event) >= 5:
                    event_id = event[0]
                    title = event[1] if len(event) > 1 else "Untitled"
                    description = event[2] if len(event) > 2 else ""
                    event_date = event[3] if len(event) > 3 else ""
                    venue = event[4] if len(event) > 4 else ""
                    capacity = event[5] if len(event) > 5 else 0
                    
                    with st.expander(f"📅 {title} - {event_date}"):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**Description:** {description}")
                            st.markdown(f"**Venue:** {venue}")
                            if capacity:
                                st.markdown(f"**Capacity:** {capacity} attendees")
                            
                            if len(event) > 8 and event[8]:  # hashtag
                                st.markdown(f"**Hashtag:** #{event[8]}")
                        
                        with col2:
                            event_date_obj = date.fromisoformat(event_date) if event_date else date.today()
                            days_diff = (event_date_obj - date.today()).days
                            
                            if days_diff > 0:
                                st.markdown(f"⏰ **{days_diff} days left**")
                            elif days_diff == 0:
                                st.markdown("🎉 **TODAY**")
                            else:
                                st.markdown("✅ **Past Event**")
                            
                            if not (role in ["Faculty", "Admin"]):
                                if days_diff >= 0:
                                    if st.button("📝 Register", key=f"reg_{event_id}"):
                                        st.success(f"Registered for {title}!")
                        
                        # Delete button for faculty/admin
                        if role in ["Faculty", "Admin"]:
                            if st.button("🗑️ Delete Event", key=f"del_{event_id}"):
                                cur.execute("DELETE FROM alumni_events WHERE id=?", (event_id,))
                                conn.commit()
                                st.rerun()
    except Exception as e:
        st.info(f"Events feature coming soon!")

    st.divider()

    # ==================================================
    # 📱 ALUMNI PROFILE MANAGEMENT WITH PHONE, EMAIL, ADDRESS
    # ==================================================
    st.markdown("### 👤 Your Alumni Profile")
    
    try:
        # Create alumni_profiles table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS alumni_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_phone TEXT UNIQUE,
                student_name TEXT,
                department TEXT,
                batch_year TEXT,
                email TEXT,
                company TEXT,
                designation TEXT,
                location TEXT,
                phone TEXT,
                address TEXT,
                linkedin TEXT,
                skills TEXT,
                github TEXT,
                portfolio TEXT,
                interests TEXT,
                achievements TEXT,
                profile_completion INTEGER DEFAULT 0,
                is_visible INTEGER DEFAULT 1,
                created_date TEXT,
                updated_on TEXT
            )
        """)
        conn.commit()
        
        # Check if user has a profile
        cur.execute("SELECT * FROM alumni_profiles WHERE student_phone = ?", (user["phone"],))
        existing_profile = cur.fetchone()
        
        if existing_profile:
            st.success("✅ You have an alumni profile!")
            
            # Get column names
            cur.execute("PRAGMA table_info(alumni_profiles)")
            columns = [col[1] for col in cur.fetchall()]
            
            # Display profile in a nice card
            with st.container(border=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Name:** {existing_profile[2] if len(existing_profile) > 2 else 'N/A'}")
                    st.markdown(f"**Department:** {existing_profile[3] if len(existing_profile) > 3 else 'N/A'}")
                    st.markdown(f"**Batch Year:** {existing_profile[4] if len(existing_profile) > 4 else 'N/A'}")
                    
                    if 'phone' in columns and len(existing_profile) > columns.index('phone'):
                        phone_idx = columns.index('phone')
                        st.markdown(f"**Phone:** {existing_profile[phone_idx] if existing_profile[phone_idx] else 'N/A'}")
                    
                    if 'email' in columns and len(existing_profile) > columns.index('email'):
                        email_idx = columns.index('email')
                        st.markdown(f"**Email:** {existing_profile[email_idx] if existing_profile[email_idx] else 'N/A'}")
                    
                with col2:
                    st.markdown(f"**Company:** {existing_profile[6] if len(existing_profile) > 6 else 'N/A'}")
                    st.markdown(f"**Designation:** {existing_profile[7] if len(existing_profile) > 7 else 'N/A'}")
                    st.markdown(f"**Location:** {existing_profile[8] if len(existing_profile) > 8 else 'N/A'}")
                    
                    if 'address' in columns and len(existing_profile) > columns.index('address'):
                        address_idx = columns.index('address')
                        st.markdown(f"**Address:** {existing_profile[address_idx] if existing_profile[address_idx] else 'N/A'}")
            
            # Edit profile button
            if st.button("✏️ Edit Profile", use_container_width=True):
                st.session_state.edit_profile = True
            
            # Edit profile form
            if st.session_state.get('edit_profile', False):
                with st.form("edit_profile_form"):
                    st.markdown("#### ✏️ Edit Your Profile")
                    
                    # Get current values
                    curr_name = existing_profile[2] if len(existing_profile) > 2 else user["name"]
                    curr_dept = existing_profile[3] if len(existing_profile) > 3 else ""
                    curr_batch = existing_profile[4] if len(existing_profile) > 4 else ""
                    curr_email = existing_profile[5] if len(existing_profile) > 5 else ""
                    curr_company = existing_profile[6] if len(existing_profile) > 6 else ""
                    curr_designation = existing_profile[7] if len(existing_profile) > 7 else ""
                    curr_location = existing_profile[8] if len(existing_profile) > 8 else ""
                    
                    # Get phone and address
                    curr_phone = ""
                    curr_address = ""
                    
                    if 'phone' in columns and len(existing_profile) > columns.index('phone'):
                        curr_phone = existing_profile[columns.index('phone')] or ""
                    if 'address' in columns and len(existing_profile) > columns.index('address'):
                        curr_address = existing_profile[columns.index('address')] or ""
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        name = st.text_input("Full Name *", value=curr_name)
                        dept = st.text_input("Department *", value=curr_dept)
                        batch = st.text_input("Batch Year *", value=curr_batch)
                        phone = st.text_input("Phone Number", value=curr_phone, placeholder="+91 98765 43210")
                        email = st.text_input("Email ID", value=curr_email, placeholder="your.email@example.com")
                    
                    with col2:
                        company = st.text_input("Current Company", value=curr_company)
                        designation = st.text_input("Designation", value=curr_designation)
                        location = st.text_input("Location", value=curr_location)
                        address = st.text_area("Address", value=curr_address, placeholder="Your current address", height=80)
                    
                    col1, col2, col3 = st.columns(3)
                    with col2:
                        if st.form_submit_button("💾 Update Profile", type="primary", use_container_width=True):
                            if name and dept and batch:
                                try:
                                    # Ensure columns exist
                                    if 'phone' not in columns:
                                        cur.execute("ALTER TABLE alumni_profiles ADD COLUMN phone TEXT")
                                    if 'address' not in columns:
                                        cur.execute("ALTER TABLE alumni_profiles ADD COLUMN address TEXT")
                                    
                                    cur.execute("""
                                        UPDATE alumni_profiles 
                                        SET student_name = ?, department = ?, batch_year = ?, 
                                            email = ?, company = ?, designation = ?, location = ?,
                                            phone = ?, address = ?, updated_on = ?
                                        WHERE student_phone = ?
                                    """, (name, dept, batch, email, company, designation, location,
                                          phone, address, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                          user["phone"]))
                                    conn.commit()
                                    st.success("✅ Profile updated successfully!")
                                    st.session_state.edit_profile = False
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                    
                    with col1:
                        if st.form_submit_button("Cancel"):
                            st.session_state.edit_profile = False
                            st.rerun()
        else:
            # Create new profile
            with st.form("create_profile_form"):
                st.markdown("#### 🚀 Create Your Alumni Profile")
                st.markdown("Fill in your details to connect with the alumni network:")
                
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Full Name *", value=user["name"])
                    dept = st.text_input("Department *")
                    batch = st.text_input("Batch Year *")
                    phone = st.text_input("Phone Number", placeholder="+91 98765 43210")
                
                with col2:
                    email = st.text_input("Email ID", placeholder="your.email@example.com")
                    company = st.text_input("Current Company")
                    designation = st.text_input("Designation")
                    location = st.text_input("Location")
                
                address = st.text_area("Address", placeholder="Your current address", height=80)
                
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                with col2:
                    submit = st.form_submit_button("✅ Create Profile", type="primary", use_container_width=True)
                
                if submit:
                    if name and dept and batch:
                        try:
                            # Ensure all columns exist
                            cur.execute("PRAGMA table_info(alumni_profiles)")
                            existing_columns = [col[1] for col in cur.fetchall()]
                            
                            if 'phone' not in existing_columns:
                                cur.execute("ALTER TABLE alumni_profiles ADD COLUMN phone TEXT")
                            if 'address' not in existing_columns:
                                cur.execute("ALTER TABLE alumni_profiles ADD COLUMN address TEXT")
                            if 'designation' not in existing_columns:
                                cur.execute("ALTER TABLE alumni_profiles ADD COLUMN designation TEXT")
                            
                            cur.execute("""
                                INSERT INTO alumni_profiles 
                                (student_phone, student_name, department, batch_year, email, 
                                 company, designation, location, phone, address, 
                                 is_visible, created_date, updated_on)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                user["phone"], name, dept, batch, email, 
                                company, designation, location, phone, address,
                                1, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            ))
                            conn.commit()
                            st.success("✅ Profile created successfully!")
                            st.balloons()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                    else:
                        st.error("Please fill all required fields (*)")
    except Exception as e:
        st.info(f"Profile feature coming soon!")

    st.divider()

    # ==================================================
    # 👥 ALUMNI DIRECTORY
    # ==================================================
    st.markdown("### 👥 Alumni Directory")
    st.markdown("Connect with fellow alumni")
    
    # Search box
    search_term = st.text_input("🔍 Search alumni by name, department, or company", placeholder="Type to search...")
    
    try:
        # Get column names
        cur.execute("PRAGMA table_info(alumni_profiles)")
        columns = [col[1] for col in cur.fetchall()]
        
        # Build query
        query = """
            SELECT student_name, department, batch_year, company, designation, 
                   location, phone, email, address
            FROM alumni_profiles 
            WHERE is_visible = 1
        """
        params = []
        
        if search_term:
            query += """ AND (student_name LIKE ? OR department LIKE ? 
                           OR company LIKE ? OR designation LIKE ?)"""
            search_pattern = f"%{search_term}%"
            params = [search_pattern, search_pattern, search_pattern, search_pattern]
        
        query += " ORDER BY student_name LIMIT 20"
        
        cur.execute(query, params)
        alumni = cur.fetchall()
        
        if not alumni:
            st.info("No alumni profiles found. Be the first to create your profile!")
        else:
            st.markdown(f"**Found {len(alumni)} alumni**")
            
            for alum in alumni:
                name, dept, batch, company, designation, location, phone, email, address = alum
                
                with st.container(border=True):
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        # Avatar with first letter
                        st.markdown(f"""
                        <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #3b82f6, #8b5cf6); 
                                  border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                                  color: white; font-size: 24px; font-weight: bold;">
                            {name[0].upper() if name else 'A'}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"**{name}**")
                        
                        # Basic info
                        info_parts = []
                        if dept:
                            info_parts.append(f"📚 {dept}")
                        if batch:
                            info_parts.append(f"🎓 {batch}")
                        if company:
                            info_parts.append(f"🏢 {company}")
                        if designation:
                            info_parts.append(f"💼 {designation}")
                        if location:
                            info_parts.append(f"📍 {location}")
                        
                        if info_parts:
                            st.markdown(" | ".join(info_parts))
                        
                        # Contact info
                        contact_parts = []
                        if phone:
                            contact_parts.append(f"📞 {phone}")
                        if email:
                            contact_parts.append(f"📧 {email}")
                        if address:
                            contact_parts.append(f"🏠 {address[:30]}{'...' if len(address) > 30 else ''}")
                        
                        if contact_parts:
                            st.caption(" | ".join(contact_parts))
                        
                        # Connect button
                        if st.button("🤝 Connect", key=f"connect_{name}_{phone}"):
                            st.success(f"Connection request sent to {name}!")
    except Exception as e:
        st.info("Directory feature coming soon!")

    st.divider()

    # ==================================================
    # 💡 NETWORKING TIPS
    # ==================================================
    st.markdown("### 💡 Networking Tips")
    
    tips = [
        ("🤝", "Connect Early", "Reach out to alumni before you need help"),
        ("💼", "Be Professional", "Keep your profile updated and professional"),
        ("🎯", "Be Specific", "Clearly state what you're looking for"),
        ("🙏", "Show Gratitude", "Always thank people for their time"),
        ("🔄", "Follow Up", "Keep in touch even when you don't need anything"),
        ("🌟", "Give Back", "Help others when you can")
    ]
    
    cols = st.columns(3)
    for i, (emoji, title, desc) in enumerate(tips):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"# {emoji}")
                st.markdown(f"**{title}**")
                st.caption(desc)

    # ==================================================
    # 📱 MOBILE RESPONSIVE CSS
    # ==================================================
    st.markdown("""
    <style>
    @media (max-width: 768px) {
        .stMetric {
            padding: 0.5rem !important;
        }
        h1 { font-size: 2rem !important; }
        h3 { font-size: 1.2rem !important; }
        .stButton button {
            width: 100% !important;
        }
        div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
#----------------------------------------------------------------------------------------------------
elif page == "ted_talk":
    st.header("🎤 TED Talk")
    
    # Initialize filter value safely
    if "ted_category_filter_value" not in st.session_state:
        st.session_state.ted_category_filter_value = "All"

    # ---------- CHECK EXISTING COLUMNS ----------
    try:
        cur.execute("PRAGMA table_info(events)")
        columns = [col[1] for col in cur.fetchall()]
    except:
        columns = []
    
    # ---------- CSS STYLES ----------
    st.markdown("""
    <style>
    /* Stage Spotlight Effect */
    @keyframes spotlightPulse {
        0%, 100% { opacity: 0.6; transform: scale(1); }
        50% { opacity: 0.9; transform: scale(1.05); }
    }
    
    .spotlight-effect {
        position: relative;
        overflow: hidden;
    }
    
    .spotlight-effect::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(239, 68, 68, 0.2) 0%, transparent 70%);
        animation: spotlightPulse 4s infinite;
        z-index: 0;
    }
    
    /* Talk Card Animations */
    @keyframes talkCardAppear {
        0% { opacity: 0; transform: translateY(50px) rotateX(90deg); filter: blur(10px); }
        100% { opacity: 1; transform: translateY(0) rotateX(0); filter: blur(0); }
    }
    
    .talk-card-animation {
        animation: talkCardAppear 0.8s cubic-bezier(0.68, -0.55, 0.265, 1.55) forwards;
    }
    
    /* Idea Bulb Animation */
    @keyframes ideaGlow {
        0%, 100% { text-shadow: 0 0 10px rgba(245, 158, 11, 0.5), 0 0 20px rgba(245, 158, 11, 0.3); }
        50% { text-shadow: 0 0 20px rgba(245, 158, 11, 0.8), 0 0 30px rgba(245, 158, 11, 0.5), 0 0 40px rgba(245, 158, 11, 0.3); }
    }
    
    .idea-glow {
        animation: ideaGlow 3s infinite;
        display: inline-block;
    }
    
    /* Speech Bubble Effect */
    @keyframes bubbleFloat {
        0%, 100% { transform: translateY(0) scale(1); }
        33% { transform: translateY(-5px) scale(1.02); }
        66% { transform: translateY(5px) scale(0.98); }
    }
    
    .bubble-float {
        animation: bubbleFloat 6s ease-in-out infinite;
    }
    
    /* Red Carpet Effect */
    .red-carpet {
        position: relative;
        overflow: hidden;
    }
    
    .red-carpet::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(45deg, transparent 30%, rgba(239, 68, 68, 0.1) 50%, transparent 70%);
        animation: redCarpetShine 3s infinite linear;
        z-index: 0;
    }
    
    @keyframes redCarpetShine {
        0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
        100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
    }
    
    /* Inspirational Quote Cards */
    .quote-card {
        background: linear-gradient(145deg, #ffffff, #f8fafc);
        border-radius: 20px;
        padding: 2rem;
        border: 2px solid #e2e8f0;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        position: relative;
        overflow: hidden;
    }
    
    .quote-card::before {
        content: '"';
        position: absolute;
        top: 10px;
        left: 15px;
        font-size: 80px;
        color: rgba(239, 68, 68, 0.1);
        font-family: serif;
        line-height: 1;
    }
    
    .quote-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 5px;
        height: 100%;
        background: linear-gradient(to bottom, #ef4444, #f59e0b);
    }
    
    .quote-card:hover {
        transform: translateY(-10px) scale(1.02);
        box-shadow: 0 25px 50px rgba(239, 68, 68, 0.15);
        border-color: #ef4444;
    }
    
    /* Countdown Timer for Next Talk */
    @keyframes countdownPulse {
        0%, 100% { box-shadow: 0 0 20px rgba(239, 68, 68, 0.3); }
        50% { box-shadow: 0 0 30px rgba(239, 68, 68, 0.6), 0 0 40px rgba(239, 68, 68, 0.4); }
    }
    
    .countdown-pulse {
        animation: countdownPulse 2s infinite;
    }
    
    /* Speaker Profile Animation */
    @keyframes speakerReveal {
        0% { opacity: 0; transform: scale(0.8) rotate(-10deg); }
        100% { opacity: 1; transform: scale(1) rotate(0); }
    }
    
    .speaker-reveal {
        animation: speakerReveal 0.6s ease-out forwards;
    }
    
    /* Talk Theme Badge */
    .theme-badge {
        position: absolute;
        top: -10px;
        right: -10px;
        background: linear-gradient(45deg, #ef4444, #f59e0b);
        color: white;
        padding: 8px 20px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 800;
        transform: rotate(15deg);
        box-shadow: 0 5px 15px rgba(239, 68, 68, 0.4);
        z-index: 2;
    }
    
    /* Video Play Button */
    @keyframes playButtonPulse {
        0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
        70% { transform: scale(1.1); box-shadow: 0 0 0 15px rgba(239, 68, 68, 0); }
    }
    
    .play-button-pulse {
        animation: playButtonPulse 2s infinite;
    }
    
    /* Inspiration Sparkles */
    @keyframes sparkleFall {
        0% { transform: translateY(-100px) rotate(0deg); opacity: 0; }
        10% { opacity: 1; }
        90% { opacity: 1; }
        100% { transform: translateY(100vh) rotate(360deg); opacity: 0; }
    }
    
    .sparkle {
        position: fixed;
        font-size: 16px;
        opacity: 0;
        pointer-events: none;
        z-index: 10000;
    }
    
    /* Talk Duration Indicator */
    .duration-indicator {
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, #ef4444, #f59e0b, #3b82f6);
        border-radius: 2px;
        position: relative;
        overflow: hidden;
    }
    
    .duration-indicator::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.8), transparent);
        animation: durationShimmer 2s infinite linear;
    }
    
    @keyframes durationShimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    /* Audience Clap Effect */
    @keyframes clapEffect {
        0%, 100% { transform: scale(1) rotate(0deg); }
        25% { transform: scale(1.1) rotate(-5deg); }
        50% { transform: scale(1.2) rotate(5deg); }
        75% { transform: scale(1.1) rotate(-5deg); }
    }
    
    .clap-effect {
        animation: clapEffect 0.5s ease-in-out;
    }
    
    /* Category Filter Tags */
    .category-tag {
        display: inline-block;
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white;
        padding: 6px 15px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin: 5px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
    }
    
    .category-tag:hover {
        transform: translateY(-3px) scale(1.05);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.5);
    }
    
    /* Talk Transcript Preview */
    .transcript-preview {
        background: linear-gradient(180deg, #f8fafc, #e2e8f0);
        border-radius: 12px;
        padding: 1.5rem;
        border-left: 4px solid #ef4444;
        position: relative;
        overflow: hidden;
        max-height: 200px;
        overflow-y: auto;
    }
    
    .transcript-preview::-webkit-scrollbar {
        width: 6px;
    }
    
    .transcript-preview::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 3px;
    }
    
    .transcript-preview::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #ef4444, #dc2626);
        border-radius: 3px;
    }
    
    /* Inspiration Wave Effect */
    @keyframes inspirationWave {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .inspiration-wave {
        background: linear-gradient(90deg, rgba(239, 68, 68, 0.1), rgba(245, 158, 11, 0.1), rgba(59, 130, 246, 0.1));
        background-size: 400% 400%;
        animation: inspirationWave 8s ease infinite;
    }
    
    /* Stats Card Style */
    .stats-card {
        background: white;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        text-align: center;
        border-top: 4px solid;
        transition: transform 0.3s ease;
    }
    
    .stats-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    /* Custom Card Style */
    .custom-card {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
    }
    
    .card-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
    }
    
    .card-icon {
        font-size: 28px;
    }
    
    .card-title {
        color: #1e40af;
        font-size: 1.3rem;
        font-weight: 700;
        margin: 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ---------- LOGIN CHECK ----------
    if 'user' not in st.session_state or not st.session_state.user:
        st.markdown("""
        <div class="custom-card talk-card-animation" style="text-align: center; padding: 4rem; margin: 2rem 0;">
            <div class="idea-glow" style="font-size: 80px; margin-bottom: 1rem;">💡</div>
            <h2 style="color: #1e40af; margin-bottom: 1rem;">TEDx Department Talks</h2>
            <p style="color: #64748b; margin: 1rem 0 2rem 0;">
                Please login to access inspiring TED-style talks and ideas worth spreading
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Go to Login", key="ted-login-redirect-btn"):
            st.session_state.page = "login"
            st.rerun()
        st.stop()

    # ---------- INITIALIZATION ----------
    user = st.session_state.user
    role = user["role"]
    
    # Create uploads directory if it doesn't exist
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    
    # ---------- ENHANCED HEADER SECTION ----------
    st.markdown("""
    <div class="spotlight-effect" style="text-align: center; margin: 3rem 0 1rem 0; position: relative; z-index: 1;">
        <h1 style="font-size: 3.5rem; font-weight: 900; margin-bottom: 0.5rem;
                   background: linear-gradient(90deg, #ef4444, #f59e0b, #3b82f6);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                   letter-spacing: -1px; text-transform: uppercase;">
            🎤 TED-STYLE TALKS
        </h1>
        <p style="color: #64748b; font-size: 1.2rem; max-width: 700px; margin: 0 auto 2rem auto; position: relative; z-index: 1;">
            Ideas worth spreading • Inspiration for innovation • Voices that matter
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="width: 80%; height: 4px; background: linear-gradient(90deg, #ef4444, #dc2626, #b91c1c); 
                margin: 0 auto 2rem auto; border-radius: 2px; position: relative; overflow: visible;">
        <div style="position: absolute; top: -15px; left: 0; right: 0; text-align: center; color: #ef4444; 
                    font-size: 12px; font-weight: 600; letter-spacing: 3px; text-transform: uppercase;">
            STAGE
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---------- WELCOME AND STATISTICS ----------
    user_name = user["name"].split()[0] if " " in user["name"] else user["name"]

    # Get TED Talks statistics
    cur.execute("SELECT COUNT(*) FROM events WHERE event_type='TED'")
    total_talks = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(DISTINCT created_by) FROM events WHERE event_type='TED'")
    total_speakers = cur.fetchone()[0] or 0

    cur.execute("""
        SELECT COUNT(*) 
        FROM events 
        WHERE event_type='TED' AND date >= date('now')
    """)
    upcoming_talks = cur.fetchone()[0] or 0

    # Calculate years active from date column
    cur.execute("""
        SELECT MIN(date) FROM events WHERE event_type='TED'
    """)
    first_talk_date = cur.fetchone()[0]
    if first_talk_date:
        try:
            first_year = int(str(first_talk_date).split('-')[0])
            current_year = date.today().year
            years_active = current_year - first_year + 1
        except:
            years_active = 1
    else:
        years_active = 1

    # Statistics display
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🎤 Total Talks", total_talks)
        with col2:
            st.metric("👥 Speakers", total_speakers)
        with col3:
            st.metric("📅 Upcoming", upcoming_talks)
        with col4:
            st.metric("📊 Years Active", years_active)
    
    st.markdown(f"**Welcome to the Ideas Stage, {user_name}!** You're accessing as a **{role}**.")
    
    # ---------- UPCOMING TALK COUNTDOWN ----------
    st.markdown("---")
    st.subheader("⏰ Next TED Talk Countdown")
    
    # Get next upcoming talk
    cur.execute("""
        SELECT title, date, created_by, extra_data 
        FROM events 
        WHERE event_type='TED' 
        AND date >= date('now') 
        ORDER BY date 
        LIMIT 1
    """)
    next_talk_result = cur.fetchone()
    
    if next_talk_result:
        title, talk_date, speaker, extra_data_json = next_talk_result
        
        # Parse speaker from extra_data if available
        if extra_data_json:
            try:
                talk_data = json.loads(extra_data_json)
                speaker = talk_data.get("speaker", speaker)
            except:
                pass
                
        talk_date_obj = date.fromisoformat(talk_date)
        days_until = (talk_date_obj - date.today()).days
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Title:** {title[:50]}")
        with col2:
            st.info(f"**Speaker:** {speaker}")
        with col3:
            st.info(f"**Days Until:** {days_until}")
        
        if role == "Student":
            if st.button("📝 Register Interest", use_container_width=True):
                st.success(f"✅ Registered interest for '{title}'! We'll notify you.")
    else:
        message = "Organize the next talk!" if role in ["Faculty", "Admin"] else "Check back soon for upcoming inspiring talks!"
        st.info(message)

    # ==================================================
    # 👩‍🏫 FACULTY/ADMIN VIEW - ENHANCED TALK CREATION
    # ==================================================
    if role in ["Faculty", "Admin"]:
        st.markdown("---")
        st.subheader("🎤 Organize a TED-Style Talk")
        
        with st.form("ted_talk_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input(
                    "🎤 Talk Title",
                    placeholder="e.g., The Future of Artificial Intelligence in Education"
                )
                
                speaker = st.text_input(
                    "👤 Speaker Name",
                    placeholder="Name of the speaker or presenter"
                )
                
                talk_date = st.date_input(
                    "📅 Talk Date",
                    min_value=date.today()
                )
                
                duration = st.selectbox(
                    "⏱️ Duration",
                    ["5-10 mins", "10-15 mins", "15-20 mins", "20-30 mins", "30-45 mins", "45-60 mins"]
                )
            
            with col2:
                talk_type = st.selectbox(
                    "🎭 Talk Category",
                    ["Technology", "Science", "Education", "Business", "Personal Growth", 
                     "Social Issues", "Creativity", "Health", "Environment", "Leadership"]
                )
                
                audience = st.selectbox(
                    "👥 Target Audience",
                    ["All Students", "CS/IT Students", "Faculty Only", "Open to All", "Graduates"]
                )
                
                venue = st.selectbox(
                    "📍 Venue",
                    ["Main Auditorium", "Department Seminar Hall", "Virtual (Online)", 
                     "Open Air Theater", "Library Conference Room"]
                )
                
                language = st.selectbox(
                    "🗣️ Language",
                    ["English", "Tamil", "Bilingual", "Other"]
                )
            
            description = st.text_area(
                "📝 Description",
                placeholder="Provide a compelling description of your talk...",
                height=150
            )
            
            with st.expander("➕ Additional Options"):
                col1, col2 = st.columns(2)
                with col1:
                    max_attendees = st.number_input(
                        "👥 Maximum Attendees",
                        min_value=10,
                        max_value=500,
                        value=100
                    )
                    
                    recording_consent = st.checkbox(
                        "🎥 Allow Recording",
                        value=True
                    )
                
                with col2:
                    qna_session = st.checkbox(
                        "💬 Q&A Session",
                        value=True
                    )
                    
                    networking = st.checkbox(
                        "🤝 Networking Time",
                        value=True
                    )
                
                hashtag = st.text_input("#️⃣ Event Hashtag", placeholder="#TEDxDepartment2025")
                registration_link = st.text_input("🔗 Registration Link", placeholder="https://...")
                
                poster_img = st.file_uploader("🎨 Poster Image", type=["jpg", "png", "jpeg"])
                slides = st.file_uploader("📊 Presentation Slides", type=["pdf", "ppt", "pptx"])
            
            submit_btn = st.form_submit_button("🚀 Create TED Talk", type="primary", use_container_width=True)
            
            if submit_btn:
                if not all([title, speaker, description]):
                    st.error("❌ Please fill all required fields: Title, Speaker, and Description")
                else:
                    # Save images and files
                    poster_path = None
                    slides_path = None
                    
                    if poster_img:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        poster_path = f"uploads/ted_poster_{timestamp}_{poster_img.name}"
                        with open(poster_path, "wb") as f:
                            f.write(poster_img.getbuffer())
                    
                    if slides:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        slides_path = f"uploads/ted_slides_{timestamp}_{slides.name}"
                        with open(slides_path, "wb") as f:
                            f.write(slides.getbuffer())
                    
                    # Create JSON data for extra fields
                    talk_data = {
                        "speaker": speaker,
                        "duration": duration,
                        "talk_type": talk_type,
                        "audience": audience,
                        "language": language,
                        "max_attendees": max_attendees,
                        "recording_consent": recording_consent,
                        "qna_session": qna_session,
                        "networking": networking,
                        "hashtag": hashtag,
                        "registration_link": registration_link,
                        "poster_path": poster_path,
                        "slides_path": slides_path
                    }
                    
                    # Create full title with speaker
                    full_title = f"{title} - {speaker}"
                    
                    try:
                        # Insert into database
                        cur.execute("""
                            INSERT INTO events
                            (event_type, title, description, date, venue, image_path, created_by, extra_data, hashtag)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            "TED",
                            full_title,
                            description,
                            str(talk_date),
                            venue,
                            poster_path or "",
                            user["name"],
                            json.dumps(talk_data),
                            hashtag
                        ))
                        
                        conn.commit()
                        st.success("🎉 TED Talk Created Successfully!")
                        st.balloons()
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Talk creation failed: {str(e)}")

    # ==================================================
    # 🗣️ ALL TED TALKS - ENHANCED DISPLAY
    # ==================================================
    st.markdown("---")
    st.subheader("📚 TED Talks Library")
    
    # Filter and Search Options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_status = st.selectbox(
            "📅 Filter by Status",
            ["All", "Upcoming", "Past", "This Month"],
            key="ted_status_filter"
        )
    
    with col2:
        search_talks = st.text_input(
            "🔍 Search Talks",
            placeholder="Search by title, speaker, or topic..."
        )
    
    # Fetch TED Talks
    query = """
        SELECT 
            id, 
            event_type, 
            title, 
            description, 
            date, 
            venue, 
            image_path, 
            created_by,
            extra_data,
            hashtag
        FROM events 
        WHERE event_type='TED'
    """
    params = []

    if filter_status == "Upcoming":
        query += " AND date >= date('now')"
    elif filter_status == "Past":
        query += " AND date < date('now')"
    elif filter_status == "This Month":
        query += " AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')"

    if search_talks:
        query += " AND (title LIKE ? OR description LIKE ? OR created_by LIKE ?)"
        params.extend([f"%{search_talks}%", f"%{search_talks}%", f"%{search_talks}%"])

    query += " ORDER BY date DESC"

    try:
        cur.execute(query, params)
        talks = cur.fetchall()
    except Exception as e:
        st.error(f"Error fetching talks: {e}")
        talks = []
    
    if not talks:
        message = "Organize the first TED talk!" if role in ["Faculty", "Admin"] else "Check back soon for inspiring talks!"
        st.info(message)
    else:
        st.success(f"Found {len(talks)} inspiring talk(s)")
        
        # Display talks
        for idx, talk in enumerate(talks):
            # Unpack values
            talk_id = talk[0]
            title = talk[2]
            description = talk[3]
            talk_date = talk[4]
            venue = talk[5]
            image_path = talk[6]
            created_by = talk[7]
            extra_data_json = talk[8] if len(talk) > 8 else None
            hashtag = talk[9] if len(talk) > 9 else None
            
            # Parse extra data
            talk_data = {}
            if extra_data_json:
                try:
                    talk_data = json.loads(extra_data_json)
                except:
                    talk_data = {}
            
            # Extract TED Talk specific data
            speaker = talk_data.get("speaker", created_by)
            talk_category = talk_data.get("talk_type", "General")
            duration = talk_data.get("duration", "Not specified")
            audience = talk_data.get("audience", "All Students")
            language = talk_data.get("language", "English")
            recording_consent = talk_data.get("recording_consent", True)
            qna_session = talk_data.get("qna_session", True)
            networking = talk_data.get("networking", True)
            max_attendees = talk_data.get("max_attendees", 100)
            registration_link = talk_data.get("registration_link", "")
            poster_path = talk_data.get("poster_path", "")
            slides_path = talk_data.get("slides_path", "")
            
            # Calculate talk status
            try:
                talk_date_obj = date.fromisoformat(talk_date)
                days_diff = (talk_date_obj - date.today()).days
                is_past = days_diff < 0
                is_today = days_diff == 0
            except:
                is_past = False
                is_today = False
                days_diff = 0
            
            # Status badge
            if is_today:
                status = "🔴 LIVE TODAY"
            elif is_past:
                status = "📼 ARCHIVED"
            else:
                status = f"📅 IN {days_diff} DAYS"
            
            with st.expander(f"🎤 {title}"):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    if poster_path and os.path.exists(poster_path):
                        st.image(poster_path, use_container_width=True)
                    elif image_path and os.path.exists(image_path):
                        st.image(image_path, use_container_width=True)
                    else:
                        st.markdown(f"**{talk_category}**")
                    
                    st.markdown(f"**Status:** {status}")
                    st.markdown(f"**Speaker:** {speaker}")
                    st.markdown(f"**Date:** {talk_date}")
                    st.markdown(f"**Venue:** {venue}")
                    st.markdown(f"**Duration:** {duration}")
                
                with col2:
                    st.markdown("**Description:**")
                    st.write(description)
                    
                    st.markdown("**Details:**")
                    st.markdown(f"- **Language:** {language}")
                    st.markdown(f"- **Audience:** {audience}")
                    st.markdown(f"- **Max Attendees:** {max_attendees}")
                    
                    features = []
                    if recording_consent:
                        features.append("🎥 Recording")
                    if qna_session:
                        features.append("💬 Q&A")
                    if networking:
                        features.append("🤝 Networking")
                    
                    if features:
                        st.markdown(f"**Features:** {', '.join(features)}")
                    
                    if hashtag:
                        st.markdown(f"**Hashtag:** #{hashtag}")
                
                # Action buttons
                col1, col2, col3, col4 = st.columns(4)
                
                if slides_path and os.path.exists(slides_path):
                    with col1:
                        with open(slides_path, "rb") as f:
                            st.download_button(
                                label="📊 Slides",
                                data=f.read(),
                                file_name=os.path.basename(slides_path),
                                mime="application/octet-stream",
                                key=f"slides_{talk_id}"
                            )
                
                if not is_past:
                    with col2:
                        if registration_link:
                            st.link_button("📝 Register", url=registration_link)
                        else:
                            if st.button("✅ Attend", key=f"attend_{talk_id}"):
                                st.success(f"✅ Added to your schedule!")
                
                with col3:
                    if st.button("🔗 Share", key=f"share_{talk_id}"):
                        st.info("Share link copied to clipboard!")
                
                if role in ["Faculty", "Admin"] and created_by == user["name"]:
                    with col4:
                        if st.button("🗑️ Delete", key=f"del_{talk_id}"):
                            # Delete associated files
                            for file_path in [image_path, poster_path, slides_path]:
                                if file_path and os.path.exists(file_path):
                                    try:
                                        os.remove(file_path)
                                    except:
                                        pass
                            
                            cur.execute("DELETE FROM events WHERE id=?", (talk_id,))
                            conn.commit()
                            st.success("Talk deleted!")
                            st.rerun()
    
    # ==================================================
    # 💡 INSPIRATION SECTION
    # ==================================================
    st.markdown("---")
    st.subheader("💡 Talk Inspiration")
    
    # Inspiration quotes
    quotes = [
        ("🎯", "Start with WHY", "People don't buy what you do, they buy why you do it. - Simon Sinek"),
        ("🚀", "Make it Personal", "Share your authentic story. Vulnerability creates connection."),
        ("💡", "One Big Idea", "Focus on one core idea worth spreading."),
        ("📖", "Structure Matters", "Follow the classic narrative arc."),
        ("🎨", "Show, Don't Tell", "Use visuals, stories, and examples."),
        ("❤️", "Connect Emotionally", "Move people emotionally, not just intellectually.")
    ]
    
    cols = st.columns(3)
    for idx, (icon, title_text, quote) in enumerate(quotes):
        with cols[idx % 3]:
            with st.container():
                st.markdown(f"### {icon} {title_text}")
                st.caption(quote)
    
    # Talk Topic Ideas
    with st.expander("💭 Talk Topic Ideas", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🧠 Technology & Innovation**
            - The Future of AI in Education
            - Blockchain Beyond Cryptocurrency
            - Ethical Tech: Building Responsible AI
            - Quantum Computing Explained Simply
            
            **🌱 Personal Growth**
            - The Power of Mindfulness in Studies
            - Building Resilience in Challenging Times
            - Unlocking Your Creative Potential
            """)
        
        with col2:
            st.markdown("""
            **🌍 Social Impact**
            - Sustainable Technology Solutions
            - Digital Literacy for All
            - Mental Health in the Digital Age
            - Women in STEM: Breaking Barriers
            
            **🎓 Academic & Research**
            - Research Opportunities for Undergrads
            - Open Source Contribution Guide
            - Academic Publishing Demystified
            """)
        
        if role in ["Faculty", "Admin"]:
            st.info("💡 **Tip:** Encourage students to pick topics they're passionate about.")
# ==================IAV------------------------------------        
elif page == "industrial":
    st.header("🏭🎓 Industrial Academic Venture")
    st.caption("Industry–Institute Interaction & Professional Exposure")
    
    # Custom CSS for enhanced design
    st.markdown("""
    <style>
    /* Venture Cards */
    .venture-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
        border: none;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .venture-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 30px rgba(0,0,0,0.2);
    }
    
    .venture-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: white;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .venture-meta {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        color: #e0e0e0;
        font-size: 0.95rem;
    }
    
    .venture-meta b {
        color: #ffcc00;
    }
    
    .venture-desc {
        color: #f0f0f0;
        line-height: 1.6;
        padding: 1rem;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Type-specific colors */
    .type-ind-visit { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .type-guest-lecture { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
    .type-mou { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
    .type-internship { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }
    .type-sponsored { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
    
    /* Form styling */
    .stForm {
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
        border-radius: 15px;
        padding: 2rem;
        margin: 2rem 0;
    }
    
    /* Type badges */
    .type-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 0.5rem;
        color: white;
        background: rgba(255,255,255,0.2);
    }
    
    /* Empty state */
    .empty-state {
        text-align: center;
        padding: 3rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        color: white;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .venture-card {
            padding: 1rem;
        }
        .venture-title {
            font-size: 1.2rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    role = st.session_state.user_role
    
    # ==================================================
    # 👩‍🏫 FACULTY / ADMIN – ADD VENTURE
    # ==================================================
    if role in ["Faculty", "Admin"]:
        with st.expander("➕ Add New Venture", expanded=False):
            with st.form("venture_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    venture_type = st.selectbox(
                        "🎯 Venture Type *",
                        [
                            "Industrial Visit",
                            "Industry Guest Lecture", 
                            "MoU / Collaboration",
                            "Internship / Training Program",
                            "Industry Sponsored Project"
                        ]
                    )
                    title = st.text_input("📝 Program Title *", placeholder="Enter program title...")
                    industry = st.text_input("🏢 Industry / Company Name *", placeholder="Company name...")
                    
                with col2:
                    date_ev = st.date_input("📅 Date *")
                    venue = st.text_input("📍 Venue / Location", placeholder="Venue details...")
                    image = st.file_uploader(
                        "🖼️ Upload Image / Poster",
                        type=["jpg", "jpeg", "png"],
                        help="Recommended: 1200x630px"
                    )
                
                description = st.text_area(
                    "📋 Program Description", 
                    placeholder="Describe the program details, objectives, and outcomes...",
                    height=150
                )
                
                submitted = st.form_submit_button("💾 Save Venture", type="primary", use_container_width=True)
                
                if submitted:
                    if not title or not industry:
                        st.error("⚠️ Title and Industry Name are required!")
                    else:
                        img_path = None
                        if image:
                            if not os.path.exists("uploads"):
                                os.makedirs("uploads")
                            img_path = f"uploads/venture_{int(datetime.now().timestamp())}_{image.name}"
                            with open(img_path, "wb") as f:
                                f.write(image.getbuffer())
                        
                        cur.execute("""
                            INSERT INTO industrial_ventures
                            (venture_type, title, industry_name, description,
                             date, venue, image_path, created_by)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            venture_type,
                            title,
                            industry,
                            description,
                            str(date_ev),
                            venue,
                            img_path,
                            st.session_state.user["name"]
                        ))
                        conn.commit()
                        st.success("✅ Venture added successfully!")
                        st.balloons()
                        st.rerun()
    
    st.divider()
    
    # ==================================================
    # 📌 VIEW VENTURES
    # ==================================================
    st.subheader("📌 Industry–Academia Programs")
    
    # Filter options
    col1, col2 = st.columns([2, 2])
    with col1:
        filter_type = st.selectbox(
            "Filter by Type",
            ["All Types", "Industrial Visit", "Industry Guest Lecture", 
             "MoU / Collaboration", "Internship / Training Program", "Industry Sponsored Project"]
        )
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Date (Newest First)", "Date (Oldest First)", "Title (A-Z)"]
        )
    
    # Build query
    query = "SELECT * FROM industrial_ventures"
    params = []
    
    if filter_type != "All Types":
        query += " WHERE venture_type = ?"
        params.append(filter_type)
    
    if sort_by == "Date (Newest First)":
        query += " ORDER BY date DESC"
    elif sort_by == "Date (Oldest First)":
        query += " ORDER BY date ASC"
    elif sort_by == "Title (A-Z)":
        query += " ORDER BY title ASC"
    
    cur.execute(query, params)
    ventures = cur.fetchall()
    
    if not ventures:
        st.markdown("""
        <div class='empty-state'>
            <h3>🌟 No Ventures Yet</h3>
            <p>Be the first to add an industrial academic venture!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Display ventures in a grid
        for i in range(0, len(ventures), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(ventures):
                    venture = ventures[i + j]
                    
                    # Type mapping
                    type_colors = {
                        "Industrial Visit": "type-ind-visit",
                        "Industry Guest Lecture": "type-guest-lecture",
                        "MoU / Collaboration": "type-mou",
                        "Internship / Training Program": "type-internship",
                        "Industry Sponsored Project": "type-sponsored"
                    }
                    
                    type_icons = {
                        "Industrial Visit": "🚌",
                        "Industry Guest Lecture": "🎤",
                        "MoU / Collaboration": "🤝",
                        "Internship / Training Program": "👨‍💻",
                        "Industry Sponsored Project": "💰"
                    }
                    
                    venture_type = venture[1]
                    type_class = type_colors.get(venture_type, "type-ind-visit")
                    type_icon = type_icons.get(venture_type, "🏭")
                    
                    with cols[j]:
                        # Create a container for the venture card
                        with st.container():
                            # Card header with gradient background
                            st.markdown(f"""
                            <div class='venture-card {type_class}'>
                                <div style='padding: 0.5rem;'>
                                    <h3 style='color: white; margin: 0;'>{type_icon} {venture[2]}</h3>
                                    <span class='type-badge'>{venture_type}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Metadata in a separate container
                            meta_col1, meta_col2 = st.columns(2)
                            with meta_col1:
                                st.markdown(f"**🏢 Industry:** {venture[3]}")
                                st.markdown(f"**📅 Date:** {venture[5]}")
                            with meta_col2:
                                st.markdown(f"**📍 Venue:** {venture[6] if venture[6] else 'TBD'}")
                                st.markdown(f"**👤 Added by:** {venture[8]}")
                            
                            # Description expander
                            if venture[4]:
                                with st.expander("📋 View Description"):
                                    st.write(venture[4])
                            
                            # Image expander
                            if venture[7] and os.path.exists(venture[7]):
                                with st.expander("🖼️ View Image"):
                                    st.image(venture[7], use_container_width=True)
                            
                            # Action buttons
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                if st.button("📤 Share", key=f"share_{venture[0]}", use_container_width=True):
                                    st.toast(f"Share link copied for '{venture[2]}'!", icon="✅")
                            
                            if role in ["Faculty", "Admin"]:
                                with col_btn2:
                                    delete_key = f"del_{venture[0]}"
                                    if delete_key not in st.session_state:
                                        st.session_state[delete_key] = False
                                    
                                    if not st.session_state[delete_key]:
                                        if st.button("🗑 Delete", key=f"btn_{venture[0]}", use_container_width=True):
                                            st.session_state[delete_key] = True
                                            st.rerun()
                                    else:
                                        st.warning(f"Delete '{venture[2]}'?")
                                        confirm_col1, confirm_col2 = st.columns(2)
                                        with confirm_col1:
                                            if st.button("✅ Yes", key=f"yes_{venture[0]}", use_container_width=True):
                                                if venture[7] and os.path.exists(venture[7]):
                                                    os.remove(venture[7])
                                                cur.execute("DELETE FROM industrial_ventures WHERE id=?", (venture[0],))
                                                conn.commit()
                                                st.session_state[delete_key] = False
                                                st.success("Deleted!")
                                                st.rerun()
                                        with confirm_col2:
                                            if st.button("❌ No", key=f"no_{venture[0]}", use_container_width=True):
                                                st.session_state[delete_key] = False
                                                st.rerun()
                            
                            st.divider()
        
        # Statistics
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Ventures", len(ventures))
        with col2:
            visits = len([v for v in ventures if v[1] == "Industrial Visit"])
            st.metric("Industrial Visits", visits)
        with col3:
            lectures = len([v for v in ventures if v[1] == "Industry Guest Lecture"])
            st.metric("Guest Lectures", lectures)
        with col4:
            mous = len([v for v in ventures if v[1] == "MoU / Collaboration"])
            st.metric("MoUs", mous)
#===========club activities==================================
elif page == "clubs":

    st.header("🧩 Club Activities")
    st.markdown("""
    <style>
    /* Professional Club Activity Styles */
    
    /* Hero Section */
    .club-hero {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 2rem;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    /* Report Card Style */
    .report-card {
        background: white;
        border-radius: 10px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        border-left: 5px solid #4CAF50;
        position: relative;
    }
    
    .report-header {
        background: linear-gradient(135deg, #2c3e50 0%, #4CAF50 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px 8px 0 0;
        margin: -2rem -2rem 1rem -2rem;
    }
    
    .report-title {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: white;
    }
    
    .report-subtitle {
        font-size: 1.2rem;
        color: rgba(255,255,255,0.9);
        margin-bottom: 1rem;
    }
    
    .report-meta {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #3498db;
    }
    
    .report-section {
        margin: 1.5rem 0;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 8px;
    }
    
    .report-signature {
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 2px dashed #ddd;
    }
    
    /* Gallery Cards */
    .gallery-card {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
        margin: 1rem 0;
    }
    
    .gallery-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    
    .gallery-img {
        width: 100%;
        height: 200px;
        object-fit: cover;
    }
    
    .gallery-info {
        padding: 1rem;
        background: white;
    }
    
    /* Upload Zone */
    .upload-zone {
        border: 2px dashed #3498db;
        border-radius: 10px;
        padding: 3rem;
        text-align: center;
        background: rgba(52, 152, 219, 0.05);
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .upload-zone:hover {
        background: rgba(52, 152, 219, 0.1);
        border-color: #2980b9;
    }
    
    .upload-icon {
        font-size: 3rem;
        color: #3498db;
        margin-bottom: 1rem;
    }
    
    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0.2rem;
    }
    
    .status-approved {
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .status-pending {
        background: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
    
    .status-published {
        background: #d1ecf1;
        color: #0c5460;
        border: 1px solid #bee5eb;
    }
    
    /* College Header */
    .college-header {
        background: linear-gradient(135deg, #1a237e 0%, #283593 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    .college-name {
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .college-details {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Report Table */
    .report-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    
    .report-table th {
        background: #2c3e50;
        color: white;
        padding: 0.8rem;
        text-align: left;
        border: 1px solid #34495e;
    }
    
    .report-table td {
        padding: 0.8rem;
        border: 1px solid #ddd;
    }
    
    .report-table tr:nth-child(even) {
        background: #f8f9fa;
    }
    
    /* Download Button */
    .download-btn {
        background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
        color: white;
        border: none;
        padding: 0.5rem 1.5rem;
        border-radius: 25px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .download-btn:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(46, 204, 113, 0.4);
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .report-card {
            padding: 1rem;
        }
        .report-header {
            margin: -1rem -1rem 1rem -1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Hero Section
    st.markdown(f"""
    <div class='club-hero'>
        <h2>🏛️ Club Activities & Events</h2>
        <p style='font-size: 1.1rem; opacity: 0.9;'>Professional event reports, gallery uploads, and comprehensive club activity management</p>
        <div style='margin-top: 1rem;'>
            <span class='status-badge status-published'>Total Events: {len(cur.execute("SELECT * FROM events WHERE event_type='Club'").fetchall())}</span>
            <span class='status-badge status-approved'>Active Clubs: 8</span>
            <span class='status-badge status-pending'>Upcoming: 3</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    role = st.session_state.user_role
    
    # ==================================================
    # 📊 UPLOAD CLUB REPORTS & GALLERY
    # ==================================================
    st.subheader("📊 Upload Event Reports & Gallery")
    
    if role in ["Faculty", "Admin", "Student Coordinator"]:
        tab1, tab2, tab3 = st.tabs(["📄 Upload Report", "🖼️ Upload Gallery", "📋 View Reports"])
        
        with tab1:
            st.markdown("### 📄 Upload Professional Event Report")
            
            with st.form("report_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    event_date = st.date_input("📅 Event Date *")
                    event_title = st.text_input("🎯 Event Title *", placeholder="e.g., Green Computing and IT Sustainability")
                    club_name = st.selectbox(
                        "🏛️ Organizing Club *",
                        [
                            "Techno Connect Club",
                            "Computer Science Club",
                            "IT Club",
                            "AI & ML Club",
                            "Cultural Club",
                            "Sports Club",
                            "Literary Club",
                            "Entrepreneurship Cell"
                        ]
                    )
                    
                with col2:
                    event_time = st.time_input("⏰ Event Time", value=datetime.now().time())
                    venue = st.text_input("📍 Venue *", placeholder="e.g., II Semester Hall, IT Building")
                    event_type = st.selectbox(
                        "📋 Event Type",
                        [
                            "Tech Presentation",
                            "Workshop",
                            "Seminar",
                            "Competition",
                            "Guest Lecture",
                            "Training",
                            "Field Visit",
                            "Hackathon",
                            "Cultural Event",
                            "Sports Event"
                        ]
                    )
                
                # Organizers Section
                st.markdown("### 👥 Organizing Team")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    faculty_coordinator = st.text_input("Faculty Coordinator *", 
                                                       placeholder="e.g., Ms. S. Sindhu Priya B")
                with col2:
                    hod_name = st.text_input("HOD Name", 
                                            placeholder="e.g., Ms. P. Muthalikshmi")
                with col3:
                    principal_name = st.text_input("Principal", 
                                                  placeholder="e.g., Dr. S. Shalini")
                
                # Student Coordinators
                student_coordinators = st.text_area(
                    "👩‍🎓 Student Coordinators",
                    placeholder="Enter student coordinator names (one per line)\n\nExample:\nR.Kanishka, II B.Sc IT\nP.Sathiya priya, II B.Sc IT",
                    height=100
                )
                
                # Organized By Class/Semester
                organized_by = st.text_input("Organized By Class", 
                                           placeholder="e.g., III IT, II IT")
                
                # Event Description
                event_description = st.text_area(
                    "📝 Event Description *",
                    placeholder="Provide detailed description of the event...",
                    height=150
                )
                
                # Key Highlights
                highlights = st.text_area(
                    "🌟 Key Highlights / Outcomes",
                    placeholder="List the key outcomes, achievements, or highlights...",
                    height=100
                )
                
                # Upload Supporting Documents
                col1, col2 = st.columns(2)
                with col1:
                    report_file = st.file_uploader(
                        "📎 Upload Report Document",
                        type=["pdf", "docx", "txt"],
                        help="Upload the detailed report document"
                    )
                with col2:
                    poster_image = st.file_uploader(
                        "🖼️ Upload Event Poster",
                        type=["jpg", "jpeg", "png"],
                        help="Upload event poster/image"
                    )
                
                # College Header Details
                st.markdown("### 🏫 College Information")
                college_header = st.text_area(
                    "College Header Text",
                    value="MICHAEL JOB COLLEGE OF ARTS AND SCIENCE FOR WOMEN\nDepartment of Computer Science & INFORMATION TECHNOLOGY",
                    height=100,
                    help="College name and department details for report header"
                )
                
                submit_report = st.form_submit_button("📤 Upload Report", type="primary")
                
                if submit_report:
                    if not event_title or not venue:
                        st.error("⚠️ Please fill all required fields!")
                    else:
                        # Save report files
                        report_path = None
                        poster_path = None
                        
                        if report_file:
                            report_path = f"uploads/reports/report_{int(datetime.now().timestamp())}_{report_file.name}"
                            os.makedirs(os.path.dirname(report_path), exist_ok=True)
                            with open(report_path, "wb") as f:
                                f.write(report_file.getbuffer())
                        
                        if poster_image:
                            poster_path = f"uploads/posters/poster_{int(datetime.now().timestamp())}_{poster_image.name}"
                            os.makedirs(os.path.dirname(poster_path), exist_ok=True)
                            with open(poster_path, "wb") as f:
                                f.write(poster_image.getbuffer())
                        
                        # Create formatted report content
                        report_content = f"""
                        # COLLEGE EVENT REPORT
                        
                        ## College Information:
                        {college_header}
                        
                        ## Event Details:
                        **Title:** {event_title}
                        **Date:** {event_date} {event_time}
                        **Venue:** {venue}
                        **Type:** {event_type}
                        **Organized By:** {organized_by}
                        
                        ## Organizing Team:
                        **Principal:** {principal_name}
                        **HOD:** {hod_name}
                        **Faculty Coordinator:** {faculty_coordinator}
                        
                        ## Student Coordinators:
                        {student_coordinators}
                        
                        ## Event Description:
                        {event_description}
                        
                        ## Key Highlights:
                        {highlights}
                        
                        ---
                        *Report generated on {datetime.now().strftime('%d/%m/%Y %H:%M')}*
                        """
                        
                        # Save to database
                        cur.execute("""
                            INSERT INTO club_reports 
                            (event_title, event_date, club_name, venue, event_type,
                             faculty_coordinator, hod_name, principal_name,
                             student_coordinators, organized_by, description,
                             highlights, report_path, poster_path, college_header,
                             created_by, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            event_title, 
                            str(event_date), 
                            club_name, 
                            venue, 
                            event_type,
                            faculty_coordinator,
                            hod_name,
                            principal_name,
                            student_coordinators,
                            organized_by,
                            event_description,
                            highlights,
                            report_path,
                            poster_path,
                            college_header,
                            st.session_state.user["name"],
                            "Published"
                        ))
                        conn.commit()
                        
                        st.success("✅ Event Report Published Successfully!")
                        st.balloons()
                        st.rerun()
        
        with tab2:
            st.markdown("### 🖼️ Upload Event Gallery")
            
            # Existing events for gallery upload
            cur.execute("SELECT id, event_title, event_date FROM club_reports ORDER BY event_date DESC")
            existing_events = cur.fetchall()
            
            if existing_events:
                event_options = {f"{e[1]} ({e[2]})": e[0] for e in existing_events}
                selected_event = st.selectbox("Select Event for Gallery Upload", list(event_options.keys()))
                
                uploaded_images = st.file_uploader(
                    "Upload Event Photos",
                    type=["jpg", "jpeg", "png", "gif"],
                    accept_multiple_files=True,
                    help="Select multiple photos from the event"
                )
                
                if uploaded_images and st.button("📤 Upload to Gallery", type="primary"):
                    event_id = event_options[selected_event]
                    
                    for img in uploaded_images:
                        img_path = f"uploads/gallery/{event_id}_{int(datetime.now().timestamp())}_{img.name}"
                        os.makedirs(os.path.dirname(img_path), exist_ok=True)
                        with open(img_path, "wb") as f:
                            f.write(img.getbuffer())
                        
                        cur.execute("""
                            INSERT INTO club_gallery 
                            (event_id, image_path, uploaded_by, upload_date)
                            VALUES (?, ?, ?, ?)
                        """, (event_id, img_path, st.session_state.user["name"], str(datetime.now())))
                    
                    conn.commit()
                    st.success(f"✅ {len(uploaded_images)} photos uploaded to gallery!")
            else:
                st.info("No events found. Please upload a report first.")
        
        with tab3:
            st.markdown("### 📋 View All Reports")
            
            # Filter reports
            col1, col2 = st.columns(2)
            with col1:
                report_club_filter = st.selectbox(
                    "Filter by Club",
                    ["All Clubs"] + [
                        "Techno Connect Club",
                        "Computer Science Club",
                        "IT Club",
                        "AI & ML Club",
                        "Cultural Club",
                        "Sports Club",
                        "Literary Club",
                        "Entrepreneurship Cell"
                    ]
                )
            with col2:
                report_status = st.selectbox(
                    "Status",
                    ["All", "Published", "Draft", "Archived"]
                )
            
            # Build query
            query = "SELECT * FROM club_reports"
            params = []
            
            if report_club_filter != "All Clubs":
                query += " WHERE club_name = ?"
                params.append(report_club_filter)
                
                if report_status != "All":
                    query += " AND status = ?"
                    params.append(report_status)
            elif report_status != "All":
                query += " WHERE status = ?"
                params.append(report_status)
            
            query += " ORDER BY event_date DESC"
            
            cur.execute(query, params)
            reports = cur.fetchall()
            
            if not reports:
                st.info("No reports found.")
            else:
                for report in reports:
                    with st.container():
                        st.markdown(f"""
                        <div class='report-card'>
                            <div class='report-header'>
                                <div class='report-title'>{report[1]}</div>
                                <div class='report-subtitle'>{report[2]} • {report[3]} • {report[4]}</div>
                            </div>
                            
                            <div class='report-meta'>
                                <strong>📅 Date:</strong> {report[2]}<br>
                                <strong>📍 Venue:</strong> {report[4]}<br>
                                <strong>👥 Organized By:</strong> {report[10]}<br>
                                <strong>👩‍🏫 Faculty Coordinator:</strong> {report[6]}<br>
                                <strong>📊 Status:</strong> <span class='status-badge status-published'>{report[17]}</span>
                            </div>
                            
                            <div class='report-section'>
                                <strong>📝 Description:</strong><br>
                                {report[11][:200]}...{'<em> [Read more]</em>' if len(report[11]) > 200 else ''}
                            </div>
                            
                            <div style='margin-top: 1rem;'>
                                {f'<a href="{report[13]}" target="_blank" style="margin-right: 10px;">📎 View Report</a>' if report[13] else ''}
                                {f'<a href="{report[14]}" target="_blank" style="margin-right: 10px;">🖼️ View Poster</a>' if report[14] else ''}
                            </div>
                            
                            <div class='report-signature'>
                                <small>Report by: {report[16]} • Created on: {datetime.now().strftime('%d/%m/%Y')}</small>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Action buttons
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("📖 View Full Report", key=f"view_{report[0]}"):
                                st.session_state.selected_report = report[0]
                                st.rerun()
                        with col2:
                            if st.button("🖼️ View Gallery", key=f"gallery_{report[0]}"):
                                # Show gallery images
                                cur.execute("SELECT image_path FROM club_gallery WHERE event_id=?", (report[0],))
                                gallery_images = cur.fetchall()
                                if gallery_images:
                                    cols = st.columns(3)
                                    for idx, img in enumerate(gallery_images):
                                        if img[0] and os.path.exists(img[0]):
                                            with cols[idx % 3]:
                                                st.image(img[0], use_container_width=True)
                                else:
                                    st.info("No gallery images for this event.")
                        with col3:
                            if role in ["Faculty", "Admin"]:
                                if st.button("🗑 Delete", key=f"del_report_{report[0]}"):
                                    cur.execute("DELETE FROM club_reports WHERE id=?", (report[0],))
                                    conn.commit()
                                    st.success("Report deleted!")
                                    st.rerun()
    
    st.divider()
    
    # ==================================================
    # 🏆 CLUB SUMMARY REPORT (Like your screenshot)
    # ==================================================
    st.subheader("🏆 Club Summary Report (2025-2026)")
    
    # Create summary table
    st.markdown("""
    <div class='college-header'>
        <div class='college-name'>MICHAEL JOB COLLEGE OF ARTS AND SCIENCE FOR WOMEN</div>
        <div class='college-details'>
            Approved by UGC, Affiliated to Bharathiar University<br>
            Recognized by UGC under Section 2(f), ISO 9001:2015 certified<br>
            Near Sullur Boat Lake, Ravathur, Coimbatore - 641 402<br>
            www.mjcasa.ac.in | 9384861192 | mjcassollege@mjc.ac.in
        </div>
    </div>
    
    <h4 style='text-align: center; color: #2c3e50;'>ODD | 2025 - DEPARTMENT OF COMPUTER SCIENCE WITH ARTIFICIAL INTELLIGENCE & INFORMATION TECHNOLOGY</h4>
    <h4 style='text-align: center; color: #e74c3c; margin-bottom: 2rem;'>CLUB SUMMARY REPORT(2025-2026) ODD</h4>
    """, unsafe_allow_html=True)
    
    # Generate summary data
    cur.execute("""
        SELECT 
            ROW_NUMBER() OVER (ORDER BY event_date) as sno,
            event_date,
            event_type,
            event_title,
            organized_by
        FROM club_reports 
        WHERE status = 'Published'
        ORDER BY event_date
    """)
    summary_data = cur.fetchall()
    
    if summary_data:
        # Display as table
        st.markdown("""
        <table class='report-table'>
            <thead>
                <tr>
                    <th>S.NO</th>
                    <th>DATE</th>
                    <th>EVENT</th>
                    <th>TITLE</th>
                    <th>ORGANIZED BY</th>
                </tr>
            </thead>
            <tbody>
        """, unsafe_allow_html=True)
        
        for row in summary_data:
            st.markdown(f"""
                <tr>
                    <td>{row[0]}</td>
                    <td>{row[1]}</td>
                    <td>{row[2]}</td>
                    <td>{row[3]}</td>
                    <td>{row[4]}</td>
                </tr>
            """, unsafe_allow_html=True)
        
        st.markdown("""
            </tbody>
        </table>
        
        <div style='margin-top: 3rem; display: flex; justify-content: space-between;'>
            <div>
                <strong>HOD</strong><br>
                <em>Department of Computer Science & IT</em>
            </div>
            <div>
                <strong>CLUB CO-ORDINATOR</strong><br>
                <em>Student Activity Coordinator</em>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
         # Download button for summary
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📥 Download Summary Report", use_container_width=True):
                # Generate and offer download
                summary_text = f"""
                                MICHAEL JOB COLLEGE OF ARTS AND SCIENCE FOR WOMEN
                                Approved by UGC, Affiliated to Bharathiar University
                                Recognized by UGC under Section 2(f), ISO 9001:2015 certified
                                Near Sullur Boat Lake, Ravathur, Coimbatore - 641 402
                                www.mjcasa.ac.in 9384861192 mjcassollege@mjc.ac.in

                                ODD | 2025 -
                                DEPARTMENT OF COMPUTER SCIENCE WITH ARTIFICIAL INTELLIGENCE & INFORMATION TECHNOLOGY
                                CLUB SUMMARY REPORT(2025-2026) ODD

                                {'='*60}
                                S.NO | DATE       | EVENT                      | TITLE                            | ORGANIZED BY
                                {'='*60}
                                """
                for idx, row in enumerate(summary_data, 1):
                    summary_text += f"{idx:4d} | {row[1]:10} | {row[2]:25} | {row[3]:30} | {row[4]}\n"
                
                summary_text += f"""
                                    {'='*60}

                                    Generated on: {datetime.now().strftime('%d/%m/%Y %H:%M')}
                                    Total Events: {len(summary_data)}

                                    HOD                                      CLUB CO-ORDINATOR
                                    ________________                        ________________
                                """
                
                # Create download link
                st.download_button(
                    label="⬇️ Download as Text File",
                    data=summary_text,
                    file_name=f"club_summary_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
    else:
        st.info("No published events found for summary report.")
    
    # ==================================================
    # 📱 QUICK EVENT VIEW (Mobile Friendly)
    # ==================================================
    st.divider()
    st.subheader("📱 Recent Events")
    
    # Get recent events
    cur.execute("""
        SELECT event_title, event_date, venue, event_type, club_name, poster_path
        FROM club_reports 
        WHERE status = 'Published'
        ORDER BY event_date DESC 
        LIMIT 6
    """)
    recent_events = cur.fetchall()
    
    if recent_events:
        cols = st.columns(2)
        for idx, event in enumerate(recent_events):
            with cols[idx % 2]:
                with st.container():
                    st.markdown(f"""
                    <div class='gallery-card'>
                        {f'<img src="{event[5]}" class="gallery-img">' if event[5] and os.path.exists(event[5]) else '<div style="height: 150px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; color: white; font-size: 2rem;">🏆</div>'}
                        <div class='gallery-info'>
                            <strong>{event[0]}</strong><br>
                            <small>📅 {event[1]} | 🏛️ {event[4]}</small><br>
                            <span class='status-badge'>{event[3]}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("No recent events to display.")
#------------------------------------
elif page == "attendance_summary":
    # Main Header with gradient
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 20px;
        color: white;
        margin-bottom: 30px;
    ">
        <h1 style="color: white; margin: 0;">📊 Attendance Management</h1>
        <p style="opacity: 0.9; margin: 5px 0 0 0;">Faculty Entry | Student Dashboard View</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Statistics cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 15px; border: 1px solid #e2e8f0; text-align: center;">
            <h4 style="color: #3b82f6; margin: 0;">👥 Departments</h4>
            <h2 style="color: #1e3a8a; margin: 10px 0;">4</h2>
            <p style="color: #64748b;">CS, IT, BCA, AI</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: white; padding: 20px; border-radius: 15px; border: 1px solid #e2e8f0; text-align: center;">
            <h4 style="color: #3b82f6; margin: 0;">📊 Years</h4>
            <h2 style="color: #1e3a8a; margin: 10px 0;">3</h2>
            <p style="color: #64748b;">I, II, III Year</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: white; padding: 20px; border-radius: 15px; border: 1px solid #e2e8f0; text-align: center;">
            <h4 style="color: #3b82f6; margin: 0;">🎯 Current Date</h4>
            <h2 style="color: #1e3a8a; margin: 10px 0;">{date.today().strftime("%d/%m/%Y")}</h2>
            <p style="color: #64748b;">Today's date</p>
        </div>
        """, unsafe_allow_html=True)
    
    departments = ["CS", "IT", "BCA", "AI"]
    years = ["I Year", "II Year", "III Year"]
    
    # ==================================================
    # 📝 FACULTY / ADMIN – ATTENDANCE ENTRY
    # ==================================================
    if st.session_state.user_role in ["Faculty", "Admin"]:
        
        st.markdown("### 📝 Faculty Attendance Entry Panel")
        
        # Use tabs for better organization
        tab1, tab2, tab3 = st.tabs(["📅 Enter Attendance", "📊 View Trends", "📈 Analytics"])
        
        with tab1:
            with st.container():
                st.markdown("""
                <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                            padding: 20px;
                            border-radius: 15px;
                            border-left: 5px solid #3b82f6;
                            margin-bottom: 20px;">
                    <h4 style="color: #1e3a8a; margin: 0;">Quick Entry Guide</h4>
                    <p style="color: #475569; margin: 5px 0 0 0;">
                        1. Select the date<br>
                        2. Enter present count for each department-year<br>
                        3. Enter total strength<br>
                        4. Click Save Attendance
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                attendance_date = st.date_input(
                    "🗓️ Select Date",
                    value=date.today(),
                    help="Select the date for attendance entry",
                    key="attendance_entry_date"
                )
                
                with st.form("attendance_form"):
                    records = []
                    
                    # Department-wise cards
                    for dept in departments:
                        st.markdown(f"""
                        <div style="margin-top: 20px; margin-bottom: 10px;">
                            <h3 style="color: #1e40af; display: flex; align-items: center; gap: 10px;">
                                <span style="background: #3b82f6; color: white; padding: 5px 15px; border-radius: 20px;">{dept}</span>
                                Department
                            </h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        cols = st.columns(3)
                        
                        for i, year in enumerate(years):
                            with cols[i]:
                                st.markdown(f"""
                                <div style="background: #f8fafc; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                                    <h5 style="color: #475569; margin: 0 0 10px 0; text-align: center;">{year}</h5>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                present = st.number_input(
                                    f"✅ Present",
                                    min_value=0,
                                    value=0,
                                    step=1,
                                    key=f"{dept}_{year}_present_{attendance_date}",
                                    label_visibility="collapsed"
                                )
                                
                                total = st.number_input(
                                    f"👥 Total",
                                    min_value=0,
                                    value=60,
                                    step=1,
                                    key=f"{dept}_{year}_total_{attendance_date}",
                                    label_visibility="collapsed"
                                )
                                
                                # Calculate percentage
                                if total > 0 and present > 0:
                                    percentage = (present / total) * 100
                                    st.progress(percentage/100)
                                    st.caption(f"{percentage:.1f}%")
                                
                                records.append({
                                    "date": str(attendance_date),
                                    "department": dept,
                                    "year": year,
                                    "present": present,
                                    "total": total
                                })
                    
                    # Form submit button
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        save = st.form_submit_button(
                            "💾 Save Attendance",
                            use_container_width=True,
                            type="primary"
                        )
                        
                        if save:
                            with st.spinner('Saving attendance records...'):
                                # Delete existing records for this date
                                cur.execute("DELETE FROM attendance_summary WHERE date=?", (str(attendance_date),))
                                
                                # Insert new records
                                for r in records:
                                    if r["present"] > 0 or r["total"] > 0:  # Only save if there's data
                                        cur.execute("""
                                            INSERT INTO attendance_summary
                                            (date, department, year, present, total_strength)
                                            VALUES (?, ?, ?, ?, ?)
                                        """, (r["date"], r["department"], r["year"], r["present"], r["total"]))
                                
                                conn.commit()
                            
                            st.success(f"✅ Attendance saved successfully for {attendance_date}!")
                            st.balloons()
        
        with tab2:
            st.markdown("### 📊 Attendance Trends")
            
            # Fetch historical data for trends
            cur.execute("""
                SELECT date, SUM(present) as total_present, 
                       SUM(total_strength) as total_students
                FROM attendance_summary
                GROUP BY date
                ORDER BY date DESC
                LIMIT 30
            """)
            
            trend_data = cur.fetchall()
            
            if trend_data:
                # Create DataFrame for visualization
                df_trend = pd.DataFrame(trend_data, columns=['Date', 'Present', 'Total'])
                df_trend['Percentage'] = (df_trend['Present'] / df_trend['Total']) * 100
                df_trend['Date'] = pd.to_datetime(df_trend['Date'])
                
                # Create line chart
                fig = px.line(df_trend, x='Date', y='Percentage', 
                              title='📈 30-Day Attendance Trend',
                              markers=True)
                fig.update_layout(
                    plot_bgcolor='rgba(240, 244, 249, 0.5)',
                    paper_bgcolor='white'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Show stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📅 Days Recorded", len(trend_data))
                with col2:
                    avg_att = df_trend['Percentage'].mean()
                    st.metric("📊 Average %", f"{avg_att:.1f}%")
                with col3:
                    highest = df_trend['Percentage'].max()
                    st.metric("🏆 Highest %", f"{highest:.1f}%")
            else:
                st.info("No historical data available for trends")
        
        with tab3:
            st.markdown("### 📈 Department-wise Analytics")
            
            # Department comparison
            cur.execute("""
                SELECT department, 
                       AVG(present * 100.0 / total_strength) as avg_attendance,
                       SUM(present) as total_present,
                       SUM(total_strength) as total_students
                FROM attendance_summary
                GROUP BY department
            """)
            
            dept_data = cur.fetchall()
            
            if dept_data:
                df_dept = pd.DataFrame(dept_data, columns=['Department', 'Avg %', 'Present', 'Total'])
                
                # Bar chart
                fig = px.bar(df_dept, x='Department', y='Avg %', color='Department',
                             title='Average Attendance by Department')
                fig.update_layout(plot_bgcolor='white', showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
    
    # ==================================================
    # 📊 ATTENDANCE VIEW (ALL USERS)
    # ==================================================
    st.markdown("---")
    st.markdown("""
    <h2 style="color: #1e3a8a; text-align: center;">
        <span style="background: #3b82f6; color: white; padding: 5px 15px; border-radius: 10px;">📅</span>
        Attendance Overview
    </h2>
    """, unsafe_allow_html=True)
    
    # Initialize session state for date
    if "attendance_view_date" not in st.session_state:
        st.session_state.attendance_view_date = date.today()
    
    # Date selection
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        view_date = st.date_input(
            "Select Date",
            value=st.session_state.attendance_view_date,
            key="attendance_date_picker"
        )
        st.session_state.attendance_view_date = view_date
    
    with col2:
        if st.button("⬅️ Yesterday", use_container_width=True):
            st.session_state.attendance_view_date = view_date - timedelta(days=1)
            st.rerun()
    
    with col3:
        if st.button("Today", use_container_width=True):
            st.session_state.attendance_view_date = date.today()
            st.rerun()
    
    with col4:
        if st.button("Tomorrow ➡️", use_container_width=True):
            st.session_state.attendance_view_date = view_date + timedelta(days=1)
            st.rerun()
    
    # Fetch data for selected date
    cur.execute("""
        SELECT year, department, present, total_strength
        FROM attendance_summary
        WHERE date = ?
        ORDER BY year, department
    """, (str(view_date),))
    
    data = cur.fetchall()
    
    if not data:
        st.warning(f"⚠️ No attendance recorded for {view_date}")
    else:
        # Organize data by year
        year_data = {}
        for year, dept, present, total in data:
            if year not in year_data:
                year_data[year] = {"departments": {}, "totals": {"present": 0, "total": 0}}
            
            year_data[year]["departments"][dept] = present
            year_data[year]["totals"]["present"] += present
            year_data[year]["totals"]["total"] += total
        
        # Display each year
        for year, ydata in year_data.items():
            year_present = ydata["totals"]["present"]
            year_total = ydata["totals"]["total"]
            year_percentage = (year_present / year_total * 100) if year_total > 0 else 0
            
            # Color based on percentage
            if year_percentage >= 75:
                color = "#10b981"
            elif year_percentage >= 50:
                color = "#f59e0b"
            else:
                color = "#ef4444"
            
            # Year header
            st.markdown(f"""
            <div style="margin: 30px 0 15px 0;">
                <h3 style="color: #1e40af; display: inline-block; margin-right: 15px;">{year}</h3>
                <span style="background: {color}; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold;">
                    {year_percentage:.1f}% Attendance
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            # Department grid
            cols = st.columns(4)
            for i, dept in enumerate(departments):
                present = ydata["departments"].get(dept, 0)
                with cols[i]:
                    st.markdown(f"""
                    <div style="background: #f8fafc; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #e2e8f0;">
                        <div style="font-size: 14px; color: #64748b;">{dept}</div>
                        <div style="font-size: 24px; font-weight: bold; color: #1e40af;">{present}</div>
                        <div style="font-size: 12px; color: #94a3b8;">students</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Total card
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 20px;
                        border-radius: 15px;
                        text-align: center;
                        color: white;
                        margin: 20px 0;">
                <div style="font-size: 16px; opacity: 0.9;">Total Students Present</div>
                <div style="font-size: 48px; font-weight: bold; margin: 10px 0;">{year_present}</div>
                <div style="font-size: 14px; opacity: 0.8;">out of {year_total} students</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Admin/Export options
        if st.session_state.user_role in ["Faculty", "Admin"]:
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                # Export to CSV
                export_data = []
                for year, ydata in year_data.items():
                    row = {"Date": str(view_date), "Year": year}
                    for dept in departments:
                        row[dept] = ydata["departments"].get(dept, 0)
                    row["Total"] = ydata["totals"]["present"]
                    export_data.append(row)
                
                if export_data:
                    df_export = pd.DataFrame(export_data)
                    csv = df_export.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name=f"attendance_{view_date}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
#--------------------------------------------------
elif page == "fees":
    # Custom CSS for better UI
    st.markdown("""
        <style>
        .pdf-viewer {
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            background: #f8f9fa;
        }
        .header-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 25px;
            border-radius: 15px;
            color: white;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }
        .upload-box {
            border: 2px dashed #667eea;
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            background: #f0f2f6;
            margin: 20px 0;
        }
        .status-badge {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: bold;
        }
        .paid { background: #d4edda; color: #155724; }
        .pending { background: #fff3cd; color: #856404; }
        .overdue { background: #f8d7da; color: #721c24; }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
        <div class="header-card">
            <h1 style="margin:0; font-size: 2.5rem;">💰 Fee Structure Portal</h1>
            <p style="margin:10px 0 0 0; font-size: 1.1rem;">View and Manage Complete Payment Structure</p>
        </div>
    """, unsafe_allow_html=True)
    
    role = st.session_state.get("user_role")
    
    # Initialize database for PDF files
    cur.execute('''CREATE TABLE IF NOT EXISTS fee_structure_pdfs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        academic_year TEXT,
        description TEXT,
        uploaded_by TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        file_size REAL,
        is_active BOOLEAN DEFAULT 1
    )''')
    
    conn.commit()
    
    # ----------------- FACULTY/ADMIN SECTION -----------------
    if role in ["Faculty", "Admin"]:
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.subheader("📤 Upload Overall Fee Structure")
        with col2:
            st.metric("Total PDFs", len(cur.execute("SELECT * FROM fee_structure_pdfs").fetchall()))
        with col3:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        # Upload Section
        st.markdown('<div class="upload-box">', unsafe_allow_html=True)
        
        uploaded_pdf = st.file_uploader(
            "Choose a PDF file containing the complete fee structure",
            type=["pdf"],
            help="Upload the official fee structure document in PDF format"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if uploaded_pdf is not None:
            # Show file details
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"📄 **File:** {uploaded_pdf.name}")
            with col2:
                st.info(f"📏 **Size:** {uploaded_pdf.size/1024:.2f} KB")
            with col3:
                st.info(f"📅 **Type:** PDF")
            
            # Additional information
            with st.expander("📝 Add Document Details", expanded=True):
                academic_year = st.selectbox(
                    "Academic Year",
                    ["2024-25", "2025-26", "2026-27", "2027-28"],
                    index=0
                )
                
                description = st.text_area(
                    "Description",
                    placeholder="E.g., 'Complete fee structure including tuition, hostel, and other charges'",
                    height=100
                )
                
                tags = st.multiselect(
                    "Tags",
                    ["Tuition", "Hostel", "Examination", "Library", "Lab", "Transport", "Other"]
                )
            
            # Upload button
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("🚀 Upload PDF", type="primary", use_container_width=True):
                    try:
                        # Create fees directory if it doesn't exist
                        os.makedirs(FEES_DIR, exist_ok=True)
                        
                        # Generate unique filename
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        file_name = f"fee_structure_{academic_year}_{timestamp}.pdf"
                        file_path = os.path.join(FEES_DIR, file_name)
                        
                        # Save the file
                        with open(file_path, "wb") as f:
                            f.write(uploaded_pdf.getbuffer())
                        
                        # Save to database
                        cur.execute('''
                            INSERT INTO fee_structure_pdfs 
                            (file_name, file_path, academic_year, description, uploaded_by, file_size)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                            file_name, 
                            file_path, 
                            academic_year, 
                            description + f" | Tags: {', '.join(tags) if tags else 'None'}",
                            st.session_state.get("user_id", "Admin"),
                            uploaded_pdf.size
                        ))
                        conn.commit()
                        
                        st.success("✅ Fee structure PDF uploaded successfully!")
                        st.balloons()
                        
                        # Show preview
                        st.subheader("📄 Preview")
                        show_pdf_preview(file_path)
                        
                    except Exception as e:
                        st.error(f"❌ Error uploading file: {str(e)}")
            
            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    st.rerun()
        
        st.divider()
        
        # ----------------- MANAGE UPLOADED PDFs -----------------
        st.subheader("📋 Manage Uploaded Fee Structures")
        
        # Get all uploaded PDFs
        cur.execute("SELECT * FROM fee_structure_pdfs ORDER BY academic_year DESC, uploaded_at DESC")
        pdfs = cur.fetchall()
        
        if pdfs:
            # Filter options
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            with filter_col1:
                year_filter = st.selectbox(
                    "Filter by Academic Year",
                    ["All Years"] + list(set([pdf[3] for pdf in pdfs]))
                )
            
            # Apply filter
            filtered_pdfs = pdfs
            if year_filter != "All Years":
                filtered_pdfs = [pdf for pdf in pdfs if pdf[3] == year_filter]
            
            # Display PDFs in cards
            for pdf in filtered_pdfs:
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"""
                            ### 📄 {pdf[1]}
                            **Academic Year:** {pdf[3]}  
                            **Description:** {pdf[4]}  
                            **Uploaded:** {pdf[6]} | **Size:** {pdf[7]/1024:.2f} KB
                        """)
                    
                    with col2:
                        if st.button("👁️ View", key=f"view_{pdf[0]}", use_container_width=True):
                            show_pdf_preview(pdf[2])
                    
                    with col3:
                        if st.button("🗑️ Delete", key=f"delete_{pdf[0]}", type="secondary", use_container_width=True):
                            # Delete file from filesystem
                            if os.path.exists(pdf[2]):
                                os.remove(pdf[2])
                            
                            # Delete record from database
                            cur.execute("DELETE FROM fee_structure_pdfs WHERE id=?", (pdf[0],))
                            conn.commit()
                            
                            st.warning(f"Deleted: {pdf[1]}")
                            st.rerun()
                    
                    st.divider()
            
            # Summary statistics
            st.subheader("📊 Statistics")
            total_size = sum(pdf[7] for pdf in pdfs) / (1024 * 1024)  # Convert to MB
            years_count = len(set(pdf[3] for pdf in pdfs))
            
            stat1, stat2, stat3 = st.columns(3)
            with stat1:
                st.metric("Total Documents", len(pdfs))
            with stat2:
                st.metric("Total Size", f"{total_size:.2f} MB")
            with stat3:
                st.metric("Academic Years", years_count)
        
        else:
            st.info("📭 No fee structure PDFs uploaded yet.")
    
    # ----------------- STUDENT SECTION -----------------
    elif role == "Student":
        
        st.markdown("""
            <div style="background: #e8f4fd; padding: 20px; border-radius: 10px; margin-bottom: 30px;">
                <h3 style="color: #0c5460; margin:0;">📘 Fee Structure Documents</h3>
                <p style="color: #0c5460; margin:5px 0 0 0;">
                    View the complete fee structure for different academic years.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        # Search and filter
        search_col1, search_col2 = st.columns([2, 1])
        with search_col1:
            search_query = st.text_input("🔍 Search fee structures...", placeholder="Search by year or description")
        with search_col2:
            sort_by = st.selectbox("Sort by", ["Newest First", "Oldest First", "Academic Year"])
        
        # Get all PDFs
        cur.execute("SELECT * FROM fee_structure_pdfs WHERE is_active = 1 ORDER BY academic_year DESC")
        pdfs = cur.fetchall()
        
        if pdfs:
            # Apply search filter
            if search_query:
                pdfs = [pdf for pdf in pdfs 
                       if search_query.lower() in pdf[1].lower() 
                       or search_query.lower() in pdf[3].lower()
                       or search_query.lower() in str(pdf[4]).lower()]
            
            # Apply sorting
            if sort_by == "Oldest First":
                pdfs.sort(key=lambda x: x[6])
            elif sort_by == "Academic Year":
                pdfs.sort(key=lambda x: x[3], reverse=True)
            
            st.success(f"Found {len(pdfs)} fee structure document(s)")
            
            # Display PDFs
            for pdf in pdfs:
                with st.expander(f"📄 {pdf[1]} - {pdf[3]}", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Description:** {pdf[4]}")
                        st.write(f"**Uploaded on:** {pdf[6]}")
                        st.write(f"**File size:** {pdf[7]/1024:.2f} KB")
                    
                    with col2:
                        if st.button("📥 View PDF", key=f"student_view_{pdf[0]}", use_container_width=True):
                            show_pdf_preview(pdf[2])
                    
                    # Download button
                    if os.path.exists(pdf[2]):
                        with open(pdf[2], "rb") as file:
                            st.download_button(
                                label="⬇️ Download PDF",
                                data=file,
                                file_name=pdf[1],
                                mime="application/pdf",
                                key=f"download_{pdf[0]}",
                                use_container_width=True
                            )
            
            # Group by academic year
            st.subheader("📚 By Academic Year")
            years = sorted(set(pdf[3] for pdf in pdfs), reverse=True)
            
            for year in years:
                year_pdfs = [pdf for pdf in pdfs if pdf[3] == year]
                with st.expander(f"🎓 {year} ({len(year_pdfs)} document(s))"):
                    for pdf in year_pdfs:
                        if st.button(f"📄 {pdf[1]}", key=f"year_{pdf[0]}", use_container_width=True):
                            show_pdf_preview(pdf[2])
        
        else:
            st.warning("""
            ⚠️ No fee structure documents available.
            
            The fee structure PDFs will be uploaded by the administration.
            Please check back later or contact the accounts department.
            """)
            
            # Placeholder for upcoming documents
            st.info("📅 **Upcoming Fee Structures:**")
            st.write("- 2024-25 Academic Year (To be uploaded)")
            st.write("- 2025-26 Academic Year (To be uploaded)")
    
    # ----------------- PARENT/GUEST SECTION -----------------
    elif role == "Parent":
        st.subheader("👨‍👩‍👧‍👦 Fee Structure Information")
        st.info("""
        As a parent/guardian, you can view the complete fee structure
        to understand the payment requirements for your ward.
        """)
        
        # Simple PDF viewer for parents
        cur.execute("SELECT * FROM fee_structure_pdfs WHERE is_active = 1 ORDER BY academic_year DESC LIMIT 5")
        pdfs = cur.fetchall()
        
        if pdfs:
            st.write("**Latest Fee Structure Documents:**")
            for pdf in pdfs:
                if st.button(f"📋 View {pdf[3]} Fee Structure", key=f"parent_{pdf[0]}", use_container_width=True):
                    show_pdf_preview(pdf[2])
        else:
            st.info("Fee structure documents will be uploaded soon.")
# ---------------- ENHANCED TIMETABLE MODULE WITH CHATBOT ----------------
elif page == "schedule":

    if not st.session_state.user:
        st.warning("Login required")
        st.stop()

    st.header("📅 Academic Schedule Management")
    role = st.session_state.user_role
    if 'user_schedule_data' not in st.session_state:
        st.session_state.user_schedule_data = {
            'degree': st.session_state.user.get('degree', ''),
            'year': st.session_state.user.get('year', ''),
            'name': st.session_state.user.get('name', '')
        }
    # ================= MAIN CONTENT AREA =================
    col_main, col_side = st.columns([3,1])

    with col_main:

        # 👩‍🏫 FACULTY / ADMIN VIEW
        if role in ["Faculty", "Admin"]:
            st.subheader("📤 Manage Academic Schedules")
            
            # Add tabs for different schedule types
            tab1, tab2, tab3 = st.tabs(["📚 Class Timetable", "📝 Exam Timetable", "🗓️ Academic Calendar"])
            
            # ================= CLASS TIMETABLE TAB =================
            with tab1:
                timetable_type = st.selectbox(
                    "Select Timetable Type",
                    ["Class Timetable", "Internal Exam Timetable"],
                    key="class_tab_type"
                )
                
                degree = st.selectbox(
                    "Select Degree",
                    ["BSc CS", "BSc IT", "BCA", "BSc CS(AI)"],
                    key="class_degree"
                )
                
                year = st.selectbox("Select Year", [1, 2, 3], key="class_year")
                
                cur.execute("""
                    SELECT file_name, upload_date, description
                    FROM timetable_pdf
                    WHERE course=? AND year=? AND timetable_type=?
                """, (degree, year, timetable_type))
                existing = cur.fetchone()

                if existing:
                    path = os.path.join(TIMETABLE_DIR, existing[0])
                    file_ext = existing[0].split('.')[-1].lower()
                    
                    st.success(f"✅ Existing {timetable_type} (Updated on {existing[1]})")
                    if existing[2]:
                        st.caption(f"Description: {existing[2]}")
                    
                    # Display based on file type
                    if file_ext in ['jpg', 'jpeg', 'png']:
                        st.image(path, width=600)
                    elif file_ext == 'pdf':
                        st.info(f"📄 PDF file available for download")

                    # View/Download option
                    with open(path, "rb") as f:
                        st.download_button(
                            f"⬇️ Download {timetable_type}",
                            f,
                            file_name=existing[0],
                            mime=f"application/{'pdf' if file_ext == 'pdf' else 'octet-stream'}"
                        )

                st.markdown("---")
                st.subheader(f"Upload/Update {timetable_type}")
                
                description = st.text_input(
                    "Description (Optional)",
                    placeholder="e.g., Odd Semester 2024, Updated with lab sessions",
                    key="class_desc"
                )
                
                uploaded_file = st.file_uploader(
                    f"Upload {timetable_type}",
                    type=["jpg", "jpeg", "png", "pdf"],
                    key="class_upload"
                )
                
                if uploaded_file:
                    st.markdown("### 👀 Preview")
                    if uploaded_file.type.startswith('image'):
                        st.image(uploaded_file, width=400)
                    else:
                        st.info(f"📄 PDF file: {uploaded_file.name}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("💾 Save Timetable", key="save_class", type="primary"):
                        if not uploaded_file:
                            st.error("Please upload a file")
                        else:
                            # Ensure directory exists
                            os.makedirs(TIMETABLE_DIR, exist_ok=True)
                            
                            path = os.path.join(TIMETABLE_DIR, uploaded_file.name)
                            with open(path, "wb") as f:
                                f.write(uploaded_file.getvalue())

                            # Delete existing entry
                            cur.execute("""
                                DELETE FROM timetable_pdf
                                WHERE course=? AND year=? AND timetable_type=?
                            """, (degree, year, timetable_type))

                            # Insert new entry
                            cur.execute("""
                                INSERT INTO timetable_pdf
                                (course, year, timetable_type, file_name, description, upload_date)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                degree,
                                year,
                                timetable_type,
                                uploaded_file.name,
                                description,
                                datetime.now().strftime("%d-%m-%Y %H:%M")
                            ))

                            conn.commit()
                            st.success(f"✅ {timetable_type} saved successfully!")
                            st.rerun()

                with col2:
                    if existing and st.button("🗑️ Delete", key="delete_class"):
                        cur.execute("""
                            DELETE FROM timetable_pdf
                            WHERE course=? AND year=? AND timetable_type=?
                        """, (degree, year, timetable_type))
                        conn.commit()
                        # Also delete the file
                        try:
                            os.remove(path)
                        except:
                            pass
                        st.success(f"🗑️ {timetable_type} deleted!")
                        st.rerun()

            # ================= EXAM TIMETABLE TAB =================
            with tab2:
                st.subheader("📝 Semester Exam Timetable")
                
                cur.execute("""
                    SELECT file_name, upload_date, description
                    FROM timetable_pdf
                    WHERE timetable_type='Semester Exam'
                """)
                existing = cur.fetchall()
                
                if existing:
                    st.success(f"✅ Found {len(existing)} exam timetable(s)")
                    for file_info in existing:
                        file_name, upload_date, description = file_info
                        exam_path = os.path.join(TIMETABLE_DIR, file_name)
                        
                        with st.expander(f"📄 {file_name} (Updated: {upload_date})"):
                            if description:
                                st.caption(f"Description: {description}")
                            
                            with open(exam_path, "rb") as f:
                                st.download_button(
                                    "⬇️ Download",
                                    f,
                                    file_name=file_name,
                                    mime="application/pdf",
                                    key=f"dl_{file_name}"
                                )
                            
                            if st.button(f"🗑️ Delete", key=f"del_{file_name}"):
                                cur.execute("""
                                    DELETE FROM timetable_pdf
                                    WHERE file_name=?
                                """, (file_name,))
                                conn.commit()
                                try:
                                    os.remove(exam_path)
                                except:
                                    pass
                                st.success("Deleted!")
                                st.rerun()
                
                st.markdown("---")
                st.subheader("Upload New Exam Timetable")
                
                exam_description = st.text_input(
                    "Exam Description",
                    placeholder="e.g., BSc CS Semester 2 Exams - April 2024",
                    key="exam_desc"
                )
                
                exam_files = st.file_uploader(
                    "Upload Semester Exam Timetable(s)",
                    type=["pdf"],
                    accept_multiple_files=True,
                    key="exam_upload"
                )
                
                if exam_files:
                    st.info(f"Selected {len(exam_files)} file(s) for upload")
                    
                    if st.button("📤 Upload Exam Timetables", key="upload_exam", type="primary"):
                        for exam_file in exam_files:
                            path = os.path.join(TIMETABLE_DIR, exam_file.name)
                            with open(path, "wb") as f:
                                f.write(exam_file.getvalue())
                            
                            cur.execute("""
                                INSERT INTO timetable_pdf
                                (course, year, timetable_type, file_name, description, upload_date)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (
                                "All",
                                "All",
                                "Semester Exam",
                                exam_file.name,
                                exam_description,
                                datetime.now().strftime("%d-%m-%Y %H:%M")
                            ))
                        
                        conn.commit()
                        st.success(f"✅ {len(exam_files)} exam timetable(s) uploaded!")
                        st.rerun()

            # ================= ACADEMIC CALENDAR TAB =================
            with tab3:
                st.subheader("🗓️ Academic Calendar Management")
                
                # Display existing academic calendars
                cur.execute("""
                    SELECT file_name, upload_date, description, year
                    FROM timetable_pdf
                    WHERE timetable_type='Academic Calendar'
                    ORDER BY upload_date DESC
                """)
                existing_calendars = cur.fetchall()
                
                if existing_calendars:
                    st.success(f"✅ Found {len(existing_calendars)} academic calendar(s)")
                    
                    for file_info in existing_calendars:
                        file_name, upload_date, description, cal_year = file_info
                        cal_path = os.path.join(TIMETABLE_DIR, file_name)
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{file_name}**")
                            st.caption(f"Academic Year: {cal_year} | Uploaded: {upload_date}")
                            if description:
                                st.caption(f"Description: {description}")
                        
                        with col2:
                            with open(cal_path, "rb") as f:
                                st.download_button(
                                    "⬇️ Download",
                                    f,
                                    file_name=file_name,
                                    mime="application/pdf",
                                    key=f"cal_dl_{file_name}"
                                )
                            
                            if st.button("🗑️", key=f"cal_del_{file_name}"):
                                cur.execute("""
                                    DELETE FROM timetable_pdf
                                    WHERE file_name=?
                                """, (file_name,))
                                conn.commit()
                                try:
                                    os.remove(cal_path)
                                except:
                                    pass
                                st.success("Deleted!")
                                st.rerun()
                
                st.markdown("---")
                st.subheader("Upload New Academic Calendar")
                
                cal_year = st.selectbox(
                    "Academic Year",
                    ["2023-2024", "2024-2025", "2025-2026", "2026-2027", "General"],
                    key="cal_year"
                )
                
                cal_description = st.text_input(
                    "Calendar Description",
                    placeholder="e.g., Complete academic schedule with holidays and important dates",
                    key="cal_desc"
                )
                
                calendar_file = st.file_uploader(
                    "Upload Academic Calendar (PDF)",
                    type=["pdf"],
                    key="cal_upload"
                )
                
                if calendar_file:
                    st.info(f"File: {calendar_file.name}")
                    
                    if st.button("📅 Upload Academic Calendar", key="upload_cal", type="primary"):
                        path = os.path.join(TIMETABLE_DIR, calendar_file.name)
                        with open(path, "wb") as f:
                            f.write(calendar_file.getvalue())
                        
                        cur.execute("""
                            INSERT INTO timetable_pdf
                            (course, year, timetable_type, file_name, description, upload_date)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            "All",
                            cal_year,
                            "Academic Calendar",
                            calendar_file.name,
                            cal_description,
                            datetime.now().strftime("%d-%m-%Y %H:%M")
                        ))
                        
                        conn.commit()
                        st.success("✅ Academic calendar uploaded!")
                        st.rerun()

        # 🎓 STUDENT VIEW
        else:
            st.subheader("📋 View Academic Schedules")
            
            # Get student info
            raw_degree = st.session_state.user.get("degree", "")
            year = st.session_state.user.get("year", "")
            student_name = st.session_state.user.get("name", "")
            
            if not raw_degree or not year:
                st.error("Profile data incomplete. Please contact admin.")
                st.stop()
            
            # Normalize degree
            d = raw_degree.strip().upper()
            if "AI" in d:
                course = "BSc CS(AI)"
            elif "IT" in d:
                course = "BSc IT"
            elif "BCA" in d:
                course = "BCA"
            elif "CS" in d:
                course = "BSc CS"
            else:
                st.error("Unable to detect your degree. Contact admin.")
                st.stop()
            
            # Quick info card
            with st.container():
                col_info1, col_info2, col_info3 = st.columns(3)
                with col_info1:
                    st.metric("Degree", course)
                with col_info2:
                    st.metric("Year", f"Year {year}")
                with col_info3:
                    st.metric("Status", "Active")
            
            # Create tabs for student view
            stud_tab1, stud_tab2, stud_tab3 = st.tabs([
                "📚 Class Timetable", 
                "📝 Exam Schedules", 
                "🗓️ Academic Calendar"
            ])
            
            # ================= STUDENT CLASS TIMETABLE =================
            with stud_tab1:
                # Class Timetable
                st.subheader("Class Timetable")
                cur.execute("""
                    SELECT file_name, upload_date, description
                    FROM timetable_pdf
                    WHERE course=? AND year=? AND timetable_type='Class Timetable'
                """, (course, year))
                
                class_timetable = cur.fetchone()
                
                if not class_timetable:
                    st.warning("Class timetable not uploaded yet")
                    st.info("Ask the chatbot when it will be available!")
                else:
                    file_name, upload_date, description = class_timetable
                    path = os.path.join(TIMETABLE_DIR, file_name)
                    file_ext = file_name.split('.')[-1].lower()
                    
                    st.success(f"🕒 Last Updated: {upload_date}")
                    if description:
                        st.caption(f"Description: {description}")
                    
                    if file_ext in ['jpg', 'jpeg', 'png']:
                        st.image(path, width=700)
                    elif file_ext == 'pdf':
                        with open(path, "rb") as f:
                            st.download_button(
                                "⬇️ Download Class Timetable",
                                f,
                                file_name=file_name,
                                mime="application/pdf"
                            )
                    
                    # Always show download button
                    with open(path, "rb") as f:
                        st.download_button(
                            "⬇️ Download Timetable",
                            f,
                            file_name=file_name,
                            mime=f"application/{'pdf' if file_ext == 'pdf' else 'octet-stream'}"
                        )
                
                # Internal Exam Timetable
                st.subheader("Internal Exam Timetable")
                cur.execute("""
                    SELECT file_name, upload_date, description
                    FROM timetable_pdf
                    WHERE course=? AND year=? AND timetable_type='Internal Exam Timetable'
                """, (course, year))
                
                internal_exam = cur.fetchone()
                
                if not internal_exam:
                    st.info("Internal exam timetable not available")
                else:
                    file_name, upload_date, description = internal_exam
                    path = os.path.join(TIMETABLE_DIR, file_name)
                    
                    st.success(f"📝 Last Updated: {upload_date}")
                    if description:
                        st.caption(f"Description: {description}")
                    
                    with open(path, "rb") as f:
                        st.download_button(
                            "⬇️ Download Internal Exam Timetable",
                            f,
                            file_name=file_name,
                            mime="application/pdf"
                        )

            # ================= STUDENT EXAM TIMETABLES =================
            with stud_tab2:
                st.subheader("📝 Semester Exam Timetables")
                
                cur.execute("""
                    SELECT file_name, upload_date, description
                    FROM timetable_pdf
                    WHERE timetable_type='Semester Exam'
                    ORDER BY upload_date DESC
                """)
                
                exam_timetables = cur.fetchall()
                
                if not exam_timetables:
                    st.warning("No exam timetables available yet")
                else:
                    for idx, (file_name, upload_date, description) in enumerate(exam_timetables):
                        path = os.path.join(TIMETABLE_DIR, file_name)
                        
                        with st.expander(f"📄 {file_name} (Updated: {upload_date})"):
                            if description:
                                st.caption(f"Description: {description}")
                            
                            with open(path, "rb") as f:
                                st.download_button(
                                    "⬇️ Download Exam Timetable",
                                    f,
                                    file_name=file_name,
                                    mime="application/pdf",
                                    key=f"exam_dl_{idx}"
                                )

            # ================= STUDENT ACADEMIC CALENDAR =================
            with stud_tab3:
                st.subheader("🗓️ Academic Calendar")
                
                cur.execute("""
                    SELECT file_name, upload_date, description, year
                    FROM timetable_pdf
                    WHERE timetable_type='Academic Calendar'
                    ORDER BY upload_date DESC
                """)
                
                academic_calendars = cur.fetchall()
                
                if not academic_calendars:
                    st.warning("Academic calendar not available yet")
                else:
                    st.info("Download the academic calendar for important dates, holidays, and schedule")
                    
                    for idx, (file_name, upload_date, description, cal_year) in enumerate(academic_calendars):
                        path = os.path.join(TIMETABLE_DIR, file_name)
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{file_name}**")
                            st.caption(f"Academic Year: {cal_year} | Uploaded: {upload_date}")
                            if description:
                                st.caption(f"Description: {description}")
                        
                        with col2:
                            with open(path, "rb") as f:
                                st.download_button(
                                    "⬇️ Download",
                                    f,
                                    file_name=file_name,
                                    mime="application/pdf",
                                    key=f"acad_dl_{idx}"
                                )
# ---------------- FEEDBACK MODULE ----------------
elif page == "support":

    if not st.session_state.user:
        st.warning("Please login to access feedback")
    else:

        st.header("📝 Support Desk")

        role = st.session_state.user["role"].strip().lower()

        # ================= NOTIFICATION =================
        notification_count = 0
        if role != "student":
            cur.execute("SELECT COUNT(*) FROM feedback WHERE status='Open'")
            notification_count = cur.fetchone()[0]

        if notification_count > 0:
            st.markdown(f"""
            <div style='background-color: #ff4b4b; color: white; padding: 0.5rem; border-radius: 5px; margin-bottom: 1rem;'>
                🔔 <strong>{notification_count} new query{'' if notification_count == 1 else 's'} pending</strong>
            </div>
            """, unsafe_allow_html=True)

        # ================= STUDENT VIEW =================
        if role == "student":

            st.subheader("📥 Submit Your Query")

            query_type = st.selectbox(
                "Category",
                ["General Inquiry", "Technical Issue", "Course Related", "Account Issue", "Other"]
            )

            msg = st.text_area(
                "Enter your query",
                height=100,
                placeholder="Describe your issue in detail..."
            )

            if st.button("📤 Submit Query", use_container_width=True):
                if not msg.strip():
                    st.error("Query cannot be empty")
                else:
                    cur.execute("""
                        INSERT INTO feedback
                        (student_phone, category, student_message, faculty_reply, status, created_at)
                        VALUES (?, ?, ?, ?, ?, datetime('now'))
                    """, (
                        st.session_state.user["phone"],
                        query_type,
                        msg,
                        "",
                        "Open"
                    ))
                    conn.commit()
                    st.success("✅ Your query has been submitted successfully!")
                    st.rerun()

            st.divider()

            # ===== STUDENT HISTORY =====
            st.subheader("📨 Your Query History")

            cur.execute("""
                SELECT id, student_message, category, faculty_reply, status, created_at
                FROM feedback
                WHERE student_phone=?
                ORDER BY created_at DESC
            """, (st.session_state.user["phone"],))

            rows = cur.fetchall()

            if not rows:
                st.info("📭 No queries submitted yet")
            else:
                for r in rows:
                    status_icon = {
                        "Open": "🔴",
                        "Replied": "🟢",
                        "In Progress": "🟡",
                        "Closed": "⚫"
                    }.get(r[4], "⚪")

                    with st.expander(f"{status_icon} {r[2]} - {r[4]}"):
                        st.markdown(f"**📝 Your Query:**")
                        st.write(r[1])
                        st.markdown(f"**📅 Submitted:** {r[5]}")

                        if r[3]:
                            st.markdown("**👩‍🏫 Faculty Reply:**")
                            st.success(r[3])
                        else:
                            st.info("⏳ Waiting for faculty reply")

        # ================= FACULTY / ADMIN =================
        else:

            tab1, tab2, tab3 = st.tabs(["📋 Open Queries", "✅ Replied Queries", "📊 Dashboard"])

            # ===== OPEN QUERIES =====
            with tab1:

                cur.execute("""
                    SELECT id, student_phone, student_message, category, status, created_at
                    FROM feedback
                    WHERE status='Open' OR status='In Progress'
                    ORDER BY created_at DESC
                """)
                open_rows = cur.fetchall()

                if not open_rows:
                    st.success("🎉 All caught up! No pending queries.")
                else:
                    for r in open_rows:
                        with st.expander(f"📌 {r[3]} - {r[4]}"):
                            st.write("📞 Phone:", r[1])
                            st.write("📝 Query:", r[2])
                            st.write("📅 Submitted:", r[5])

                            reply = st.text_area(
                                "✍️ Type your reply",
                                key=f"reply_{r[0]}"
                            )

                            col1, col2, col3 = st.columns(3)

                            with col1:
                                if st.button("📤 Send Reply", key=f"send_{r[0]}"):
                                    if reply.strip():
                                        cur.execute("""
                                            UPDATE feedback
                                            SET faculty_reply=?, status='Replied'
                                            WHERE id=?
                                        """, (reply, r[0]))
                                        conn.commit()
                                        st.success("Reply sent!")
                                        st.rerun()

                            with col2:
                                if st.button("⏸️ In Progress", key=f"progress_{r[0]}"):
                                    cur.execute("""
                                        UPDATE feedback
                                        SET status='In Progress'
                                        WHERE id=?
                                    """, (r[0],))
                                    conn.commit()
                                    st.rerun()

                            with col3:
                                if st.button("❌ Close", key=f"close_{r[0]}"):
                                    cur.execute("""
                                        UPDATE feedback
                                        SET status='Closed'
                                        WHERE id=?
                                    """, (r[0],))
                                    conn.commit()
                                    st.rerun()

            # ===== REPLIED =====
            with tab2:

                cur.execute("""
                    SELECT student_phone, student_message, category, faculty_reply, created_at
                    FROM feedback
                    WHERE status='Replied'
                    ORDER BY created_at DESC
                """)
                replied_rows = cur.fetchall()

                if not replied_rows:
                    st.info("No replied queries yet")
                else:
                    for r in replied_rows:
                        with st.expander(f"📌 {r[2]}"):
                            st.write("📞 Phone:", r[0])
                            st.write("📝 Query:", r[1])
                            st.success("👩‍🏫 Reply:")
                            st.write(r[3])
                            st.write("📅 Submitted:", r[4])

            # ===== DASHBOARD =====
            with tab3:

                col1, col2, col3 = st.columns(3)

                cur.execute("SELECT COUNT(*) FROM feedback WHERE status='Open'")
                open_count = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM feedback WHERE status='Replied'")
                replied_count = cur.fetchone()[0]

                cur.execute("SELECT COUNT(*) FROM feedback WHERE status='In Progress'")
                progress_count = cur.fetchone()[0]

                col1.metric("📥 Open", open_count)
                col2.metric("✅ Replied", replied_count)
                col3.metric("⏳ In Progress", progress_count)

                st.subheader("📈 Query Type Distribution")

                cur.execute("""
                    SELECT category, COUNT(*)
                    FROM feedback
                    GROUP BY category
                """)
                type_data = cur.fetchall()

                if type_data:
                    import pandas as pd
                    df = pd.DataFrame(type_data, columns=["Category", "Count"])
                    st.bar_chart(df.set_index("Category"))
                else:
                    st.info("No query data available yet.")

    st.markdown("""
    <style>
    /* Main container styling */
    .logout-container {
        min-height: 85vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 2rem;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 20px;
        margin: 1rem;
        animation: fadeIn 0.8s ease-out;
    }
    
    /* Title styling */
    .logout-title {
        font-size: 3.5rem;
        font-weight: 800;
        color: #2c3e50;
        margin-bottom: 1rem;
        text-align: center;
        background: linear-gradient(45deg, #3498db, #2c3e50);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Subtitle styling */
    .logout-subtitle {
        font-size: 1.2rem;
        color: #7f8c8d;
        text-align: center;
        margin-bottom: 3rem;
        max-width: 500px;
        line-height: 1.6;
    }
    
    /* Icon animation */
    .logout-icon {
        font-size: 5rem;
        margin: 2rem 0;
        animation: pulse 2s infinite;
        color: #e74c3c;
    }
    
    /* Logout button container */
    .button-container {
        display: flex;
        gap: 20px;
        margin-top: 2rem;
        flex-wrap: wrap;
        justify-content: center;
    }
    
    /* Primary logout button */
    .logout-btn {
        background: linear-gradient(45deg, #e74c3c, #c0392b) !important;
        color: white !important;
        border: none !important;
        padding: 16px 40px !important;
        border-radius: 50px !important;
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3) !important;
        min-width: 200px !important;
    }
    
    .logout-btn:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(231, 76, 60, 0.4) !important;
        background: linear-gradient(45deg, #c0392b, #e74c3c) !important;
    }
    
    .logout-btn:active {
        transform: translateY(-1px) !important;
    }
    
    /* Cancel button */
    .cancel-btn {
        background: linear-gradient(45deg, #95a5a6, #7f8c8d) !important;
        color: white !important;
        border: none !important;
        padding: 16px 40px !important;
        border-radius: 50px !important;
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(149, 165, 166, 0.3) !important;
        min-width: 200px !important;
    }
    
    .cancel-btn:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(149, 165, 166, 0.4) !important;
        background: linear-gradient(45deg, #7f8c8d, #95a5a6) !important;
    }
    
    /* Success message styling */
    .success-message {
        background: linear-gradient(45deg, #2ecc71, #27ae60);
        color: white;
        padding: 20px 30px;
        border-radius: 15px;
        margin: 2rem auto;
        text-align: center;
        max-width: 500px;
        animation: slideIn 0.5s ease-out;
        box-shadow: 0 5px 20px rgba(46, 204, 113, 0.3);
    }
    
    /* Warning message styling */
    .warning-message {
        background: linear-gradient(45deg, #f39c12, #e67e22);
        color: white;
        padding: 20px 30px;
        border-radius: 15px;
        margin: 2rem auto;
        text-align: center;
        max-width: 500px;
        animation: slideIn 0.5s ease-out;
        box-shadow: 0 5px 20px rgba(243, 156, 18, 0.3);
    }
    
    /* User info card */
    .user-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin: 2rem 0;
        text-align: center;
        max-width: 400px;
        animation: float 3s ease-in-out infinite;
    }
    
    .user-avatar {
        width: 80px;
        height: 80px;
        background: linear-gradient(45deg, #3498db, #2c3e50);
        border-radius: 50%;
        margin: 0 auto 15px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 2rem;
        font-weight: bold;
    }
    
    .user-name {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 5px;
    }
    
    .user-role {
        font-size: 1rem;
        color: #7f8c8d;
        padding: 5px 15px;
        background: #ecf0f1;
        border-radius: 20px;
        display: inline-block;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: scale(0.9); }
        to { opacity: 1; transform: scale(1); }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    
    /* Session stats */
    .stats-container {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin: 2rem 0;
        flex-wrap: wrap;
    }
    
    .stat-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        min-width: 150px;
        text-align: center;
    }
    
    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: #3498db;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #7f8c8d;
        margin-top: 5px;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .logout-title {
            font-size: 2.5rem;
        }
        
        .logout-icon {
            font-size: 4rem;
        }
        
        .button-container {
            flex-direction: column;
            align-items: center;
        }
        
        .logout-btn, .cancel-btn {
            width: 100%;
            max-width: 300px;
        }
    }
    </style>
    """, unsafe_allow_html=True)
elif page == "logout":
    sign_out_page()
   # -------------------- CUSTOM CSS FOR ENHANCED DESIGN --------------------
    st.markdown("""
    <style>
        /* Main page styling */
        .main {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }
    
        /* WhatsApp button */
        .whatsapp-float {
            position: fixed;
            bottom: 100px;
            right: 30px;
            background-color: #25D366;
            color: white;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            text-decoration: none;
            box-shadow: 0 6px 15px rgba(37, 211, 102, 0.3);
            z-index: 9999;
            transition: all 0.3s ease;
        }
    
        .whatsapp-float:hover {
            background-color: #128C7E;
            transform: scale(1.1);
            box-shadow: 0 8px 20px rgba(37, 211, 102, 0.4);
        }
    
        /* Scroll to top button */
        .scroll-top-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 9998;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 50%;
            width: 55px;
            height: 55px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            box-shadow: 0 6px 15px rgba(102, 126, 234, 0.3);
            text-decoration: none;
            transition: all 0.3s ease;
        }
            .scroll-top-btn:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
    }
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Input area */
    .stTextInput > div > div > input {
        border-radius: 15px !important;
        border: 2px solid #e0e0e0 !important;
        padding: 12px 20px !important;
        font-size: 16px !important;
    }
    
    .stButton button {
        border-radius: 15px !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        padding: 10px 30px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)
# -------------------- WHATSAPP FLOAT BUTTON --------------------
st.markdown("""
<a href="https://wa.me/917010539553" 
   target="_blank" 
   class="whatsapp-float">
   💬
</a>
""", unsafe_allow_html=True)

# -------------------- SCROLL TO TOP BUTTON --------------------
st.markdown("""
<a href="#top" class="scroll-top-btn">⬆️</a>
""", unsafe_allow_html=True)

# -------------------- ENHANCED WELCOME HEADER --------------------
if st.session_state.get("user"):
    user = st.session_state.user
    name = user.get("name", "User")
    role = user.get("role", "").upper()
    email = user.get("email", "")
    
    st.markdown(f"""
    <div class="welcome-header">
        <div style="display: flex; align-items: center; gap: 20px;">
            <div style="font-size: 50px;">👋</div>
            <div>
                <h1 style="margin: 0; font-size: 28px; font-weight: 700;">
                    Welcome back, {name}!
                </h1>
                <p style="margin: 8px 0 0 0; font-size: 16px; opacity: 0.9;">
                    <strong>Role:</strong> {role} • <strong>Email:</strong> {email}
                </p>
                <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.8;">
                    Last login: Today • Status: <span style="color: #4ade80;">● Active</span>
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
# -------------------- SAMPLE CONTENT TO DEMO SCROLL --------------------
st.markdown("<div id='top'></div>", unsafe_allow_html=True)
st.markdown("""
<br><br><br><br><br><br><br><br><br><br>
<p style="text-align: center; color: #666; padding: 50px;">
    Scroll up to see the scroll-to-top button in action! ⬆️
</p>
""", unsafe_allow_html=True)