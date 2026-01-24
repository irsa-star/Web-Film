import streamlit as st
import sqlite3
from pathlib import Path

# =============================
# DATABASE
# =============================
DB_PATH = "film.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def create_table():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS film (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            judul TEXT,
            genre TEXT,
            sinopsis TEXT,
            tahun INTEGER,
            rating REAL,
            durasi TEXT,
            umur TEXT,
            poster TEXT
        )
    """)
    conn.commit()
    conn.close()

create_table()

# =============================
# DATABASE STATS (LIKE per user)
# =============================
def create_stats_table():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS film_stats (
            film_id INTEGER,
            username TEXT,
            PRIMARY KEY(film_id, username),
            FOREIGN KEY(film_id) REFERENCES film(id)
        )
    """)
    conn.commit()
    conn.close()

create_stats_table()

# =============================
# DATABASE USER WATCHLIST
# =============================
def create_watchlist_table():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            film_id INTEGER,
            FOREIGN KEY(film_id) REFERENCES film(id)
        )
    """)
    conn.commit()
    conn.close()

create_watchlist_table()

# =============================
# DATABASE USER LOGIN
# =============================
def create_user_table():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    """)
    # default admin dan user
    c.execute("INSERT OR IGNORE INTO user (username,password,role) VALUES ('admin','admin123','admin')")
    c.execute("INSERT OR IGNORE INTO user (username,password,role) VALUES ('user','user123','user')")
    conn.commit()
    conn.close()

create_user_table()

# =============================
# CONFIG
# =============================
st.set_page_config(
    page_title="Web Rekomendasi Film",
    layout="wide"
)

# =============================
# SESSION LOGIN
# =============================
if "login" not in st.session_state:
    st.session_state.login = False
    st.session_state.role = ""
    st.session_state.username = ""

# =============================
# CSS GLOBAL
# =============================
st.markdown("""
<style>
.stApp { background-color: #40513B; }
section[data-testid="stSidebar"] { background-color: #6F8F72; }
h1, h2, h3, h4, h5, h6, label, p { color: white !important; }
input, textarea, select { background-color: #E8F0E8 !important; color: black !important; border-radius: 8px !important; }
button { background-color: #4F6F52 !important; color: white !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# =============================
# SELECTBOX & FILE UPLOADER
# =============================
st.markdown("""
<style>
div[data-baseweb="select"] > div { background-color: #A5C89E !important; border: 2px solid #4F6F52 !important; border-radius: 8px !important; }
div[data-baseweb="select"] span { color: #1b1b1b !important; }
section[data-testid="stFileUploader"], div[data-testid="stFileUploaderDropzone"] { background-color: #A5C89E !important; border: 2px dashed #4F6F52 !important; border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)

# =============================
# LOGIN PAGE
# =============================
if not st.session_state.login:
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT role FROM user WHERE username=? AND password=?", (username, password))
        data = c.fetchone()
        conn.close()
        if data:
            st.session_state.login = True
            st.session_state.role = data[0]
            st.session_state.username = username
            st.success("Login berhasil")
            st.rerun()
        else:
            st.error("Username atau password salah")
    st.stop()

# =============================
# SIDEBAR
# =============================
st.sidebar.success(f"Login sebagai: {st.session_state.role}")
menu_list = ["🏠 Semua Film", "🔍 Cari Film", "⭐ Watchlist"]
if st.session_state.role == "admin":
    menu_list.insert(1, "➕ Tambah Film")
menu = st.sidebar.radio("Menu", menu_list)
if st.sidebar.button("Logout"):
    st.session_state.login = False
    st.session_state.role = ""
    st.session_state.username = ""
    st.rerun()

# =============================
# HALAMAN: SEMUA FILM
# =============================
if menu == "🏠 Semua Film":
    st.title("🎬 Web Rekomendasi Film")
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT f.id, f.judul, f.genre, f.tahun, f.rating, f.durasi, f.umur, f.poster,
        (SELECT COUNT(*) FROM film_stats WHERE film_id=f.id) as likes_count
        FROM film f
    """)
    data = c.fetchall()
    conn.close()
    if data:
        for film in data:
            col1,col2 = st.columns([1,3])
            with col1:
                if film[7] and Path(film[7]).exists():
                    st.image(film[7], width=160)
                else:
                    st.write("🎞️ No Poster")
            with col2:
                st.markdown(f"""
**🎥 {film[1]}**  
Genre: {film[2]}  
Tahun: {film[3]}  
Rating: ⭐ {film[4]}  
Durasi: {film[5]}  
Umur: {film[6]}  
❤️ {film[8]} Likes
""")
                # Hapus admin
                if st.session_state.role=="admin":
                    if st.button(f"🗑️ Hapus {film[1]}", key=f"hapus_{film[0]}"):
                        conn = get_conn()
                        c = conn.cursor()
                        c.execute("DELETE FROM film WHERE id=?",(film[0],))
                        c.execute("DELETE FROM film_stats WHERE film_id=?",(film[0],))
                        c.execute("DELETE FROM user_watchlist WHERE film_id=?",(film[0],))
                        conn.commit()
                        conn.close()
                        st.success("Film berhasil dihapus")
                        st.rerun()
                # LIKE per user
                like_key = f"like_{film[0]}"
                if st.button("❤️ Like", key=like_key):
                    conn = get_conn()
                    c = conn.cursor()
                    # cek user sudah like?
                    c.execute("SELECT 1 FROM film_stats WHERE film_id=? AND username=?",
                              (film[0], st.session_state.username))
                    exists = c.fetchone()
                    if not exists:
                        c.execute("INSERT INTO film_stats(film_id,username) VALUES (?,?)",
                                  (film[0], st.session_state.username))
                    conn.commit()
                    conn.close()
                    st.rerun()
                # Watchlist per user
                watchlist_key = f"watchlist_{film[0]}"
                if st.button("➕ Tambah ke Watchlist", key=watchlist_key):
                    conn = get_conn()
                    c = conn.cursor()
                    c.execute("SELECT 1 FROM user_watchlist WHERE username=? AND film_id=?",
                              (st.session_state.username, film[0]))
                    exists = c.fetchone()
                    if not exists:
                        c.execute("INSERT INTO user_watchlist(username, film_id) VALUES (?,?)",
                                  (st.session_state.username, film[0]))
                    conn.commit()
                    conn.close()
                    st.success(f"{film[1]} ditambahkan ke Watchlist")
            st.markdown("---")
    else:
        st.info("Belum ada film.")

# =============================
# HALAMAN: TAMBAH FILM
# =============================
elif menu=="➕ Tambah Film":
    st.title("➕ Tambah Film")
    judul = st.text_input("Judul Film")
    genre = st.selectbox("Genre", ["Action","Drama","Comedy","Horor","Romance"])
    tahun = st.number_input("Tahun Rilis",1900,2100)
    rating = st.number_input("Rating (0–10)",0.0,10.0,step=0.1,format="%.1f")
    st.subheader("Durasi Film")
    col1,col2=st.columns(2)
    with col1: jam=st.number_input("Jam",0,10,step=1)
    with col2: menit=st.number_input("Menit",0,59,step=1)
    durasi=f"{jam} jam {menit} menit"
    umur=st.selectbox("Batasan Umur",["10+","15+","18+","25+"])
    sinopsis=st.text_area("Sinopsis")
    poster=st.file_uploader("Poster Film", type=["jpg","png"])
    poster_path=None
    if poster:
        Path("poster").mkdir(exist_ok=True)
        poster_path=f"poster/{poster.name}"
        with open(poster_path,"wb") as f: f.write(poster.getbuffer())
    if st.button("💾 Simpan Film"):
        conn=get_conn()
        c=conn.cursor()
        c.execute("""INSERT INTO film (judul,genre,sinopsis,tahun,rating,durasi,umur,poster)
        VALUES (?,?,?,?,?,?,?,?)""",(judul,genre,sinopsis,tahun,rating,durasi,umur,poster_path))
        conn.commit()
        conn.close()
        st.success("Film berhasil ditambahkan!")

# =============================
# HALAMAN: CARI FILM
# =============================
elif menu=="🔍 Cari Film":
    st.title("🔍 Cari Film")
    keyword=st.text_input("Cari judul film")
    conn=get_conn()
    c=conn.cursor()
    c.execute("SELECT judul,genre,tahun FROM film WHERE judul LIKE ?",(f"%{keyword}%",))
    hasil=c.fetchall()
    conn.close()
    if hasil:
        for h in hasil: st.write(f"🎬 **{h[0]}** ({h[1]}) - {h[2]}")
    else: st.warning("Film tidak ditemukan.")

# =============================
# HALAMAN: WATCHLIST
# =============================
elif menu=="⭐ Watchlist":
    st.title("⭐ Watchlist Saya")
    st.info("Klik ➕ Tambah ke Watchlist pada halaman Semua Film untuk menambahkan ke Watchlist.")
    conn=get_conn()
    c=conn.cursor()
    c.execute("""
        SELECT f.judul,f.genre,f.tahun,f.rating,f.durasi,f.umur,f.poster,
        (SELECT COUNT(*) FROM film_stats WHERE film_id=f.id) as likes_count
        FROM film f
        JOIN user_watchlist u ON f.id=u.film_id
        WHERE u.username=?
    """,(st.session_state.username,))
    watchlist_data=c.fetchall()
    conn.close()
    if watchlist_data:
        for film in watchlist_data:
            col1,col2=st.columns([1,3])
            with col1:
                if film[6] and Path(film[6]).exists(): st.image(film[6],width=160)
                else: st.write("🎞️ No Poster")
            with col2:
                st.markdown(f"""
**🎥 {film[0]}**  
Genre: {film[1]}  
Tahun: {film[2]}  
Rating: ⭐ {film[3]}  
Durasi: {film[4]}  
Umur: {film[5]}  
❤️ {film[7]} Likes
""")
            st.markdown("---")
    else:
        st.info("Belum ada film di Watchlist.")
