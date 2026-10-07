import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import io
from fpdf import FPDF

# Sayfa yapılandırması ve çeviri koruması
st.set_page_config(page_title="Kişisel Bütçe ve Harcama Takip Paneli", layout="wide")
st.markdown(
    """
    <html translate="no" class="notranslate">
    <head>
    <meta name="google" content="notranslate">
    <meta http-equiv="Content-Language" content="tr">
    </head>
    </html>
    """,
    unsafe_allow_html=True
)

st.title("💰 Kişisel Bütçe ve Harcama Takip Paneli")

# Türkçe ay isimleri sözlüğü
aylar = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
    7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
}

def format_turkce_tarih(tarih_str):
    try:
        dt = pd.to_datetime(tarih_str)
        return f"{dt.day} {aylar[dt.month]} {dt.year}"
    except:
        return tarih_str

# 1. OTURUM DURUMU (SESSION STATE) İLE VERİ YÖNETİMİ
if 'transactions' not in st.session_state:
    st.session_state['transactions'] = pd.DataFrame(columns=[
        'Tarih', 'İşlem Türü', 'Kategori', 'Tutar (TL)', 'Açıklama'
    ])
    ornek_veri = pd.DataFrame([
        {'Tarih': '2026-10-01', 'İşlem Türü': 'Gelir', 'Kategori': 'Maaş', 'Tutar (TL)': 45000.0, 'Açıklama': 'Ekim Maaşı'},
        {'Tarih': '2026-10-02', 'İşlem Türü': 'Gider', 'Kategori': 'Kira', 'Tutar (TL)': 12000.0, 'Açıklama': 'Ev Kirası'},
        {'Tarih': '2026-10-03', 'İşlem Türü': 'Gider', 'Kategori': 'Market', 'Tutar (TL)': 3500.0, 'Açıklama': 'Aylık market alışverişi'},
        {'Tarih': '2026-10-04', 'İşlem Türü': 'Gider', 'Kategori': 'Faturalar', 'Tutar (TL)': 1500.0, 'Açıklama': 'Elektrik, Su, İnternet'},
        {'Tarih': '2026-10-05', 'İşlem Türü': 'Gider', 'Kategori': 'Eğlence', 'Tutar (TL)': 2000.0, 'Açıklama': 'Sinema ve dışarıda yemek'}
    ])
    st.session_state['transactions'] = pd.concat([st.session_state['transactions'], ornek_veri], ignore_index=True)

df = st.session_state['transactions']

# 2. YAN MENÜ: YENİ İŞLEM EKLEME
st.sidebar.header("➕ Yeni İşlem Ekle")
islem_turu = st.sidebar.selectbox("İşlem Türü", ["Gider", "Gelir"])

if islem_turu == "Gider":
    kategori = st.sidebar.selectbox("Kategori", ["Market", "Kira", "Faturalar", "Eğlence", "Ulaşım", "Giyim", "Diğer"])
else:
    kategori = st.sidebar.selectbox("Kategori", ["Maaş", "Ek Gelir", "Yatırım", "Hediye", "Diğer"])

tutar = st.sidebar.number_input("Tutar (TL)", min_value=0.0, value=500.0, step=50.0)
tarih = st.sidebar.date_input("İşlem Tarihi", datetime.today())
aciklama = st.sidebar.text_input("Açıklama", "")

if st.sidebar.button("İşlemi Kaydet"):
    yeni_satir = pd.DataFrame([{
        'Tarih': str(tarih),
        'İşlem Türü': islem_turu,
        'Kategori': kategori,
        'Tutar (TL)': tutar,
        'Açıklama': aciklama
    }])
    st.session_state['transactions'] = pd.concat([st.session_state['transactions'], yeni_satir], ignore_index=True)
    st.sidebar.success("İşlem başarıyla eklendi!")
    st.rerun()

# 3. ÖZET METRİK KARTLARI (KPI)
toplam_gelir = df[df['İşlem Türü'] == 'Gelir']['Tutar (TL)'].sum()
toplam_gider = df[df['İşlem Türü'] == 'Gider']['Tutar (TL)'].sum()
net_bakiye = toplam_gelir - toplam_gider
tasarruf_orani = (net_bakiye / toplam_gelir * 100) if toplam_gelir > 0 else 0

st.markdown("### 📊 Finansal Durum Özeti")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Toplam Gelir", f"{toplam_gelir:,.2f} TL")
col2.metric("Toplam Gider", f"{toplam_gider:,.2f} TL")
col3.metric("Net Bakiye", f"{net_bakiye:,.2f} TL", delta=f"{net_bakiye:,.2f} TL")
col4.metric("Tasarruf Oranı", f"%{tasarruf_orani:.1f}")

st.markdown("---")

# 4. GRAFİKLER VE GÖRSELLEŞTİRME
gider_df = df[df['İşlem Türü'] == 'Gider'].copy()
if not gider_df.empty:
    gider_df['Türkçe Tarih'] = gider_df['Tarih'].apply(format_turkce_tarih)

c1, c2 = st.columns(2)

with c1:
    st.subheader("🛍️ Kategorilere Göre Gider Dağılımı")
    if not gider_df.empty:
        kategori_gider = gider_df.groupby('Kategori')['Tutar (TL)'].sum().reset_index()
        fig_pie = px.pie(kategori_gider, names='Kategori', values='Tutar (TL)', hole=0.4, title="Gider Dağılımı")
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Henüz gider kaydı bulunmuyor.")

with c2:
    st.subheader("📅 Tarih Bazlı Harcama Trendi")
    if not gider_df.empty:
        tarih_gider = gider_df.groupby(['Tarih', 'Türkçe Tarih'])['Tutar (TL)'].sum().reset_index().sort_values('Tarih')
        fig_line = px.line(tarih_gider, x='Türkçe Tarih', y='Tutar (TL)', markers=True, title="Günlük Gider Hareketleri")
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Trend için yeterli gider verisi yok.")

st.markdown("---")

# 5. İŞLEM GEÇMİŞİ VE TABLO
st.subheader("📋 Tüm İşlem Geçmişi")
gosterim_df = df.copy()
gosterim_df['Tarih'] = gosterim_df['Tarih'].apply(format_turkce_tarih)
st.dataframe(gosterim_df, use_container_width=True)

# 6. VERİ DIŞA AKTARMA (CSV, EXCEL VE PDF)
st.markdown("---")
st.subheader("📥 Rapor Dışa Aktarımı")

d_col1, d_col2, d_col3, d_col4 = st.columns(4)

with d_col1:
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📄 CSV Olarak İndir",
        data=csv_data,
        file_name='kisisel_butce_raporu.csv',
        mime='text/csv',
    )

with d_col2:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Butce_Raporu')
    excel_data = output.getvalue()
    st.download_button(
        label="📊 Excel Olarak İndir",
        data=excel_data,
        file_name='kisisel_butce_raporu.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )

def temizle_turkce(metin):
    tr_harfler = str.maketrans("ğüşıöçĞÜŞİÖÇ", "gusiocGUSIOC")
    return str(metin).translate(tr_harfler)

def create_pdf(veri):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 10, txt="Kisisel Butce ve Harcama Raporu", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(35, 10, "Tarih", 1)
    pdf.cell(25, 10, "Islem", 1)
    pdf.cell(35, 10, "Kategori", 1)
    pdf.cell(30, 10, "Tutar (TL)", 1)
    pdf.cell(65, 10, "Aciklama", 1)
    pdf.ln()
    
    pdf.set_font("Arial", size=8)
    for idx, row in veri.iterrows():
        pdf.cell(35, 8, temizle_turkce(row['Tarih']), 1)
        pdf.cell(25, 8, temizle_turkce(row['İşlem Türü']), 1)
        pdf.cell(35, 8, temizle_turkce(row['Kategori']), 1)
        pdf.cell(30, 8, f"{row['Tutar (TL)']:,.2f}", 1)
        pdf.cell(65, 8, temizle_turkce(row['Açıklama'][:30]), 1)
        pdf.ln()
        
    # Bytearray nesnesini kesin olarak bytes tipine dönüştürelim
    return bytes(pdf.output())

with d_col3:
    try:
        pdf_bytes = create_pdf(df)
        st.download_button(
            label="📑 PDF Olarak İndir",
            data=pdf_bytes,
            file_name='kisisel_butce_raporu.pdf',
            mime='application/pdf',
        )
    except Exception as e:
        st.error(f"PDF oluşturulamadı: {e}")

with d_col4:
    if st.button("🗑️ Tüm Verileri Temizle"):
        st.session_state['transactions'] = pd.DataFrame(columns=['Tarih', 'İşlem Türü', 'Kategori', 'Tutar (TL)', 'Açıklama'])
        st.rerun()