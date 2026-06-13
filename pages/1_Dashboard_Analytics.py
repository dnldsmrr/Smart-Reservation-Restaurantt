import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils import load_mysql_data, load_local_data, COMMON_CSS, STATUS_COLORS, GOLD, DARK, MONTH_MAP, check_admin_login

# Initialize session state BEFORE set_page_config
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False
if "admin_sidebar_open" not in st.session_state:
    st.session_state.admin_sidebar_open = True

CHART_HEIGHT = 380

_sidebar_state = "expanded" if st.session_state.admin_sidebar_open else "collapsed"
st.set_page_config(page_title="Dashboard Analytics · Mandala Rasa",
                   page_icon=":material/bar_chart:", layout="wide",
                   initial_sidebar_state=_sidebar_state)
st.markdown(COMMON_CSS, unsafe_allow_html=True)

# ✅ Authentication Check
check_admin_login()

# Floating "Show Menu" FAB — only rendered when sidebar is collapsed
if not st.session_state.admin_sidebar_open:
    st.markdown("""<style>
div.element-container:has(#sara-show-menu-marker)+div.element-container .stButton>button{
    position:fixed!important;top:14px!important;left:14px!important;
    z-index:9999990!important;width:46px!important;height:46px!important;
    min-height:46px!important;border-radius:12px!important;padding:0!important;
    background:linear-gradient(135deg,#FF6B35,#FF8E66)!important;
    box-shadow:0 4px 14px rgba(255,107,53,0.4)!important;border:none!important;
    transition:transform 0.18s ease,box-shadow 0.18s ease!important;
}
div.element-container:has(#sara-show-menu-marker)+div.element-container .stButton>button:hover{
    transform:scale(1.08)!important;box-shadow:0 6px 18px rgba(255,107,53,0.5)!important;
}
div.element-container:has(#sara-show-menu-marker)+div.element-container .stButton>button svg,
div.element-container:has(#sara-show-menu-marker)+div.element-container .stButton>button svg path,
div.element-container:has(#sara-show-menu-marker)+div.element-container .stButton>button span{
    fill:white!important;color:white!important;
}
div.element-container:has(#sara-show-menu-marker),
div.element-container:has(#sara-show-menu-marker)+div.element-container:has(.stButton){
    height:0!important;overflow:visible!important;margin:0!important;padding:0!important;
}
</style><span id="sara-show-menu-marker" style="display:none;"></span>""", unsafe_allow_html=True)
    if st.button("", icon=":material/menu:", key="show_sidebar_btn"):
        st.session_state.admin_sidebar_open = True
        st.rerun()

# Sidebar
with st.sidebar:
    st.markdown("<h3 style='margin-top:0; padding-top:0; color:#FF6B35;'>SARA Admin</h3>", unsafe_allow_html=True)
    st.write("Sistem manajemen reservasi Mandala Rasa.")
    st.markdown("---")
    
    st.page_link("Beranda.py", label="Halaman Chat Utama", icon=":material/chat:")
    st.page_link("pages/1_Dashboard_Analytics.py", label="Dashboard Analytics", icon=":material/bar_chart:")
    st.page_link("pages/2_Reservation_Management.py", label="Kelola Reservasi", icon=":material/table_chart:")

    st.markdown("---")
    if st.button("Keluar Admin", icon=":material/logout:", use_container_width=True, key="dashboard_logout"):
        st.session_state.admin_logged_in = False
        st.toast("Admin keluar.")
        st.rerun()
        
    st.markdown("---")
    st.markdown("**Filter Dashboard**")
    df_all = load_mysql_data()
    if df_all is None or df_all.empty:
        st.warning("MySQL tidak tersedia atau kosong, menggunakan data lokal sebagai fallback.")
        df_all = load_local_data()

    selected_months = st.multiselect(
        "Bulan", options=list(range(1,13)),
        format_func=lambda m: MONTH_MAP[m],
        default=list(range(1,13))
    )
    selected_status = st.multiselect(
        "Status Reservasi",
        options=df_all["Status Reservasi"].unique().tolist(),
        default=df_all["Status Reservasi"].unique().tolist()
    )
    selected_area = st.multiselect(
        "Area Meja",
        options=df_all["Area Meja"].unique().tolist(),
        default=df_all["Area Meja"].unique().tolist()
    )


# ---- Apply filters ----
df = df_all.copy()
if selected_months:
    df = df[df["Bulan"].isin(selected_months)]
if selected_status:
    df = df[df["Status Reservasi"].isin(selected_status)]
if selected_area:
    df = df[df["Area Meja"].isin(selected_area)]

# ---- Header ----
st.markdown("""
<div style="background:linear-gradient(135deg,#FF6B35,#FF8E66);border-radius:16px;
     padding:30px 36px;color:#FFFFFF;margin-bottom:1.5rem;display:flex;
     justify-content:space-between;align-items:center;">
  <div>
    <div style="font-size:0.8rem;letter-spacing:2px;text-transform:uppercase;
         color:#FFFBF8;margin-bottom:6px;font-weight:600;">Admin · Restaurant</div>
    <h1 style="font-family:'Outfit',sans-serif;font-size:2rem;margin:0;color:#FFFFFF;">
      Dashboard Analytics</h1>
    <p style="margin:4px 0 0;color:rgba(255,255,255,0.8);font-size:0.9rem;">
      Insight & performa operasional restoran</p>
  </div>
  <div style="font-size:3rem; color:#FFFFFF;"><span class="material-symbols-outlined" style="font-size:3rem;font-variation-settings:'FILL' 1,'wght' 400,'GRAD' 0,'opsz' 48;vertical-align:middle;">bar_chart</span></div>
</div>
""", unsafe_allow_html=True)

# ==================== KPI ====================
st.markdown('<div class="section-title"><span class="material-symbols-outlined" style="vertical-align:middle;font-size:1.2rem;margin-right:6px;">push_pin</span>Overview KPI</div>', unsafe_allow_html=True)

total_rev  = df["Total Estimasi (IDR)"].sum()
avg_rating = df["Rating"].mean()
total_cust = df["Customer ID"].nunique()
status_cnt = df["Status Reservasi"].value_counts()

k1,k2,k3,k4 = st.columns(4)
with k1:
    st.markdown(f"""<div class="kpi-card" style="--accent:#FF6B35">
        <div class="kpi-label">Total Reservasi</div>
        <div class="kpi-value">{len(df):,}</div>
        <div class="kpi-sub">dari 500 data total</div>
    </div>""", unsafe_allow_html=True)
with k2:
    st.markdown(f"""<div class="kpi-card" style="--accent:#28A745">
        <div class="kpi-label">Total Revenue</div>
        <div class="kpi-value">Rp{total_rev/1_000_000:.1f}Jt</div>
        <div class="kpi-sub">estimasi total pendapatan</div>
    </div>""", unsafe_allow_html=True)
with k3:
    st.markdown(f"""<div class="kpi-card" style="--accent:#007BFF">
        <div class="kpi-label">Average Rating</div>
        <div class="kpi-value"><span class="material-symbols-outlined" style="font-size:1.1rem;vertical-align:middle;font-variation-settings:'FILL' 1,'wght' 400,'GRAD' 0,'opsz' 24;color:#FFA500;">star</span> {avg_rating:.2f}</div>
        <div class="kpi-sub">skala 1–5 ({df["Rating"].count()} ulasan)</div>
    </div>""", unsafe_allow_html=True)
with k4:
    st.markdown(f"""<div class="kpi-card" style="--accent:#6C757D">
        <div class="kpi-label">Total Pelanggan</div>
        <div class="kpi-value">{total_cust:,}</div>
        <div class="kpi-sub">unique customer ID</div>
    </div>""", unsafe_allow_html=True)

k5,k6,k7,k8 = st.columns(4)
confirmed  = status_cnt.get("Confirmed",  0)
pending    = status_cnt.get("Pending",    0)
cancelled  = status_cnt.get("Cancelled",  0)
noshow     = status_cnt.get("No-show",    0)
with k5:
    st.markdown(f"""<div class="kpi-card" style="--accent:#28A745">
        <div class="kpi-label">Confirmed</div>
        <div class="kpi-value">{confirmed}</div>
        <div class="kpi-sub">{confirmed/max(len(df),1)*100:.1f}% dari total</div>
    </div>""", unsafe_allow_html=True)
with k6:
    st.markdown(f"""<div class="kpi-card" style="--accent:#FFA500">
        <div class="kpi-label">Pending</div>
        <div class="kpi-value">{pending}</div>
        <div class="kpi-sub">{pending/max(len(df),1)*100:.1f}% dari total</div>
    </div>""", unsafe_allow_html=True)
with k7:
    st.markdown(f"""<div class="kpi-card" style="--accent:#DC3545">
        <div class="kpi-label">Cancelled</div>
        <div class="kpi-value">{cancelled}</div>
        <div class="kpi-sub">{cancelled/max(len(df),1)*100:.1f}% dari total</div>
    </div>""", unsafe_allow_html=True)
with k8:
    st.markdown(f"""<div class="kpi-card" style="--accent:#6C757D">
        <div class="kpi-label">No-show</div>
        <div class="kpi-value">{noshow}</div>
        <div class="kpi-sub">{noshow/max(len(df),1)*100:.1f}% dari total</div>
    </div>""", unsafe_allow_html=True)

# ==================== RESERVATION ANALYTICS ====================
st.markdown('<div class="section-title"><span class="material-symbols-outlined" style="vertical-align:middle;font-size:1.2rem;margin-right:6px;">calendar_month</span>Reservation Analytics</div>', unsafe_allow_html=True)

# Tren Bulanan
monthly = df.groupby("Bulan").agg(
    Jumlah=("Reservation ID","count"),
    Revenue=("Total Estimasi (IDR)","sum")
).reset_index()
monthly["Nama Bulan"] = monthly["Bulan"].map(MONTH_MAP)

col_a, col_b = st.columns(2)
with col_a:
    fig_monthly = go.Figure()
    fig_monthly.add_trace(go.Bar(
        x=monthly["Nama Bulan"], y=monthly["Jumlah"],
        marker_color=GOLD, name="Jumlah Reservasi",
        text=monthly["Jumlah"], textposition="outside"
    ))
    fig_monthly.update_layout(
        title="Tren Reservasi Bulanan",
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter"), xaxis_title="", yaxis_title="Jumlah",
        margin=dict(t=50,b=30,l=30,r=10), height=CHART_HEIGHT,
        title_font=dict(family="Outfit", size=16)
    )
    st.plotly_chart(fig_monthly, use_container_width=True)

with col_b:
    status_df = df["Status Reservasi"].value_counts().reset_index()
    status_df.columns = ["Status","Jumlah"]
    colors = [STATUS_COLORS.get(s, "#ccc") for s in status_df["Status"]]
    fig_status = go.Figure(go.Pie(
        labels=status_df["Status"], values=status_df["Jumlah"],
        marker_colors=colors, hole=0.5,
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>%{value} reservasi<br>%{percent}<extra></extra>"
    ))
    fig_status.update_layout(
        title="Distribusi Status Reservasi",
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter"), height=CHART_HEIGHT,
        margin=dict(t=50,b=20,l=10,r=10),
        title_font=dict(family="Outfit", size=16),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2)
    )
    st.plotly_chart(fig_status, use_container_width=True)

col_c, col_d = st.columns(2)
with col_c:
    ch = df["Channel Booking"].value_counts().reset_index()
    ch.columns = ["Channel","Jumlah"]
    fig_ch = px.bar(ch, x="Jumlah", y="Channel", orientation="h",
                    color="Jumlah", color_continuous_scale=["#FFEAE0","#FF6B35"],
                    text="Jumlah")
    fig_ch.update_traces(textposition="outside")
    fig_ch.update_layout(
        title="Distribusi Channel Booking",
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter"), height=CHART_HEIGHT,
        margin=dict(t=50,b=20,l=10,r=30),
        title_font=dict(family="Outfit", size=16),
        coloraxis_showscale=False, yaxis=dict(categoryorder="total ascending")
    )
    st.plotly_chart(fig_ch, use_container_width=True)

with col_d:
    area = df["Area Meja"].value_counts().reset_index()
    area.columns = ["Area","Jumlah"]
    fig_area = px.pie(area, names="Area", values="Jumlah",
                      color_discrete_sequence=["#FF6B35", "#FF8E66", "#FFB399", "#2D2522", "#403531", "#5C4A45"])
    fig_area.update_traces(textinfo="label+value", hole=0.4)
    fig_area.update_layout(
        title="Distribusi Area Meja",
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter"), height=CHART_HEIGHT,
        margin=dict(t=50,b=20,l=10,r=10),
        title_font=dict(family="Outfit", size=16),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2)
    )
    st.plotly_chart(fig_area, use_container_width=True)

# Occasion
occ = df["Occasion"].value_counts().reset_index()
occ.columns = ["Occasion","Jumlah"]
occ = occ[occ["Occasion"] != "None"]
fig_occ = px.bar(occ, x="Occasion", y="Jumlah",
                 color="Jumlah", color_continuous_scale=["#FFEAE0","#FF6B35"],
                 text="Jumlah")
fig_occ.update_traces(textposition="outside")
fig_occ.update_layout(
    title="Distribusi Occasion",
    plot_bgcolor="white", paper_bgcolor="white",
    font=dict(family="Inter"), height=CHART_HEIGHT,
    margin=dict(t=50,b=30,l=10,r=10),
    title_font=dict(family="Outfit", size=16),
    coloraxis_showscale=False, xaxis_title="", yaxis_title="Jumlah"
)
st.plotly_chart(fig_occ, use_container_width=True)

# ==================== REVENUE ANALYTICS ====================
st.markdown('<div class="section-title"><span class="material-symbols-outlined" style="vertical-align:middle;font-size:1.2rem;margin-right:6px;">payments</span>Revenue Analytics</div>', unsafe_allow_html=True)

col_r1, col_r2 = st.columns(2)

with col_r1:
    rev_ch = df.groupby("Channel Booking")["Total Estimasi (IDR)"].sum().reset_index()
    rev_ch.columns = ["Channel","Revenue"]
    rev_ch = rev_ch.sort_values("Revenue", ascending=True)
    fig_rch = px.bar(rev_ch, x="Revenue", y="Channel", orientation="h",
                     color="Revenue", color_continuous_scale=["#FFEAE0","#FF6B35"],
                     text=rev_ch["Revenue"].apply(lambda x: f"Rp{x/1e6:.1f}Jt"))
    fig_rch.update_traces(textposition="outside")
    fig_rch.update_layout(
        title="Revenue per Channel",
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter"), height=CHART_HEIGHT,
        margin=dict(t=50,b=20,l=10,r=60),
        title_font=dict(family="Outfit", size=15),
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_rch, use_container_width=True)

with col_r2:
    rev_area = df.groupby("Area Meja")["Total Estimasi (IDR)"].sum().reset_index()
    rev_area.columns = ["Area","Revenue"]
    rev_area = rev_area.sort_values("Revenue", ascending=False)
    fig_ra = px.bar(rev_area, x="Area", y="Revenue",
                    color="Revenue", color_continuous_scale=["#FFEAE0","#FF6B35"],
                    text=rev_area["Revenue"].apply(lambda x: f"Rp{x/1e6:.1f}Jt"))
    fig_ra.update_traces(textposition="outside")
    fig_ra.update_layout(
        title="Revenue per Area Meja",
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter"), height=CHART_HEIGHT,
        margin=dict(t=50,b=30,l=10,r=10),
        title_font=dict(family="Outfit", size=15),
        coloraxis_showscale=False, xaxis_title="", yaxis_title="IDR"
    )
    st.plotly_chart(fig_ra, use_container_width=True)

rev_occ = df[df["Occasion"]!="None"].groupby("Occasion")["Total Estimasi (IDR)"].sum().reset_index()
rev_occ.columns = ["Occasion","Revenue"]
fig_ro = px.pie(rev_occ, names="Occasion", values="Revenue",
                color_discrete_sequence=["#FF6B35", "#FF8E66", "#FFB399", "#2D2522", "#403531", "#5C4A45"])
fig_ro.update_traces(textinfo="label+percent", hole=0.35, automargin=True)
fig_ro.update_layout(
    title="Revenue per Occasion",
    plot_bgcolor="white", paper_bgcolor="white",
    font=dict(family="Inter"), height=520,
    margin=dict(t=70,b=70,l=20,r=20),
    title_font=dict(family="Outfit", size=16),
    legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=1.02)
)
st.plotly_chart(fig_ro, use_container_width=True)

fig_mrev = go.Figure()
fig_mrev.add_trace(go.Scatter(
    x=monthly["Nama Bulan"], y=monthly["Revenue"],
    mode="lines+markers+text",
    line=dict(color=GOLD, width=3),
    marker=dict(size=10, color=GOLD, line=dict(color="white",width=2)),
    text=[f"Rp{v/1e6:.0f}Jt" for v in monthly["Revenue"]],
    textposition="top center", name="Revenue"
))
fig_mrev.update_layout(
    title="Tren Revenue Bulanan",
    plot_bgcolor="white", paper_bgcolor="white",
    font=dict(family="Inter"), height=430,
    margin=dict(t=70,b=50,l=20,r=20),
    title_font=dict(family="Outfit", size=16),
    xaxis_title="", yaxis_title="IDR"
)
st.plotly_chart(fig_mrev, use_container_width=True)

# ==================== CUSTOMER ANALYTICS ====================
st.markdown('<div class="section-title"><span class="material-symbols-outlined" style="vertical-align:middle;font-size:1.2rem;margin-right:6px;">group</span>Customer Analytics</div>', unsafe_allow_html=True)

col_cu1, col_cu2 = st.columns(2)

with col_cu1:
    avg_ps = df["Jumlah Orang"].mean()
    ps_dist = df["Jumlah Orang"].value_counts().sort_index().reset_index()
    ps_dist.columns = ["Jumlah Orang","Frekuensi"]
    fig_ps = px.bar(ps_dist, x="Jumlah Orang", y="Frekuensi",
                    color="Frekuensi", color_continuous_scale=["#FFEAE0","#FF6B35"])
    fig_ps.add_vline(x=avg_ps, line_dash="dash", line_color="#DC3545",
                     annotation_text=f"Avg: {avg_ps:.1f}", annotation_position="top right")
    fig_ps.update_layout(
        title=f"Distribusi Party Size (Avg: {avg_ps:.1f})",
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter"), height=CHART_HEIGHT,
        margin=dict(t=50,b=30,l=10,r=10),
        title_font=dict(family="Outfit", size=15),
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_ps, use_container_width=True)

with col_cu2:
    rated = df[df["Rating"].notna()].copy()
    rated["Rating Bucket"] = pd.cut(rated["Rating"],
                                    bins=[0,2,3,4,4.5,5],
                                    labels=["<2","2–3","3–4","4–4.5","4.5–5"])
    rb = rated["Rating Bucket"].value_counts().sort_index().reset_index()
    rb.columns = ["Rating","Jumlah"]
    fig_rb = px.bar(rb, x="Rating", y="Jumlah",
                    color="Jumlah", color_continuous_scale=["#DC3545","#FFA500","#28A745"],
                    text="Jumlah")
    fig_rb.update_traces(textposition="outside")
    fig_rb.update_layout(
        title=f"Distribusi Rating (Avg: {rated['Rating'].mean():.2f})",
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Inter"), height=CHART_HEIGHT,
        margin=dict(t=50,b=30,l=10,r=10),
        title_font=dict(family="Outfit", size=15),
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_rb, use_container_width=True)

pay = df["Metode Pembayaran"].value_counts().reset_index()
pay.columns = ["Metode","Jumlah"]
fig_pay = px.pie(pay,
                 names="Metode", values="Jumlah",
                 color_discrete_sequence=["#FF6B35","#2D2522","#28A745","#007BFF","#DC3545","#6C757D","#FFA500","#1abc9c"])
fig_pay.update_traces(textinfo="label+percent", hole=0.4)
fig_pay.update_layout(
    title="Distribusi Metode Pembayaran",
    plot_bgcolor="white", paper_bgcolor="white",
    font=dict(family="Inter"), height=CHART_HEIGHT,
    margin=dict(t=50,b=20,l=10,r=10),
    title_font=dict(family="Outfit", size=15),
    legend=dict(orientation="h", yanchor="bottom", y=-0.35)
)
st.plotly_chart(fig_pay, use_container_width=True)

st.markdown("---")
st.caption(f"Data ditampilkan: **{len(df):,}** reservasi · Filter aktif: bulan {', '.join(MONTH_MAP[m] for m in sorted(selected_months)) if selected_months else 'semua'}")
