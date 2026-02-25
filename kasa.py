import customtkinter as ctk
import sqlite3
from datetime import datetime

try:
    import winsound
except ImportError:
    winsound = None 

RENK_ANA = "#2b2b2b"     
RENK_PANEL = "#3a3a3a"    
RENK_YESIL = "#2ecc71"     
RENK_KIRMIZI = "#e74c3c"   
RENK_MAVI = "#3498db"      
RENK_SARI = "#f1c40f"      
FONT_ANA = "Segoe UI"

class BufeSistemi(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Köşem Büfe - Modern Satış & Kasa Sistemi")
        self.geometry("1100x750") 
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        self.veritabani_olustur()
        self.sepet = []           
        self.toplam_fiyat = 0.0   
        self.toplam_maliyet = 0.0 
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.arayuz_olustur()
        self.ozet_guncelle()

    def veritabani_olustur(self):
        self.conn = sqlite3.connect("bufe_veritabani.db")
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS Urunler 
                         (barkod TEXT PRIMARY KEY, isim TEXT, alis REAL, satis REAL, satilan_adet INTEGER DEFAULT 0)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS Gunluk (id INTEGER PRIMARY KEY, ciro REAL, kar REAL)''')
        self.c.execute("INSERT OR IGNORE INTO Gunluk (id, ciro, kar) VALUES (1, 0.0, 0.0)")
        self.conn.commit()

    def ses_cikar(self, tur="ok"):
        if winsound:
            freq = 1500 if tur == "ok" else 500
            winsound.Beep(freq, 150) 

    def arayuz_olustur(self):

        self.sekme_alani = ctk.CTkTabview(self, corner_radius=15, fg_color=RENK_ANA)
        self.sekme_alani.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.sekme_satis = self.sekme_alani.add(" 🛒 Satış Ekranı ")
        self.sekme_ekle = self.sekme_alani.add(" 📦 Ürün Yönetimi ")
        self.sekme_ozet = self.sekme_alani.add(" 📊 Rapor & Kasa ")
        
        self.satis_ekrani_kur()
        self.urun_ekle_ekrani_kur()
        self.ozet_ekrani_kur()

    def satis_ekrani_kur(self):

        self.sekme_satis.grid_columnconfigure(0, weight=3)
        self.sekme_satis.grid_columnconfigure(1, weight=2)
        self.sekme_satis.grid_rowconfigure(0, weight=1)

        sol_panel = ctk.CTkFrame(self.sekme_satis, fg_color=RENK_PANEL, corner_radius=15)
        sol_panel.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        
        ctk.CTkLabel(sol_panel, text="🧾 Sepet / Fiş Listesi", font=(FONT_ANA, 18, "bold"), text_color="#bbb").pack(pady=10)
        
        self.liste_alani = ctk.CTkTextbox(sol_panel, font=("Consolas", 16), fg_color="#222", text_color="white", corner_radius=10)
        self.liste_alani.pack(pady=5, padx=10, fill="both", expand=True)
        self.liste_alani.configure(state="disabled")

        sag_panel = ctk.CTkFrame(self.sekme_satis, fg_color="transparent")
        sag_panel.grid(row=0, column=1, sticky="nsew")

        fiyat_karti = ctk.CTkFrame(sag_panel, fg_color="#222", border_color=RENK_YESIL, border_width=2, corner_radius=20)
        fiyat_karti.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(fiyat_karti, text="TOPLAM TUTAR", font=(FONT_ANA, 14, "bold"), text_color="#888").pack(pady=(15, 0))
        self.toplam_etiketi = ctk.CTkLabel(fiyat_karti, text="0.00 ₺", font=(FONT_ANA, 48, "bold"), text_color=RENK_YESIL)
        self.toplam_etiketi.pack(pady=(0, 15))

        input_frame = ctk.CTkFrame(sag_panel, fg_color=RENK_PANEL, corner_radius=15)
        input_frame.pack(fill="x", pady=10, ipady=10)

        ctk.CTkLabel(input_frame, text="Adet", font=(FONT_ANA, 12)).pack(anchor="w", padx=20)
        self.satis_adet = ctk.CTkEntry(input_frame, width=200, height=40, font=(FONT_ANA, 18, "bold"), justify="center", corner_radius=10)
        self.satis_adet.insert(0, "1")
        self.satis_adet.pack(padx=20, pady=(0, 10), fill="x")

        ctk.CTkLabel(input_frame, text="Barkod Okut", font=(FONT_ANA, 12)).pack(anchor="w", padx=20)
        self.satis_barkod = ctk.CTkEntry(input_frame, width=200, height=45, placeholder_text="||||||||||||||", font=(FONT_ANA, 18), corner_radius=10)
        self.satis_barkod.pack(padx=20, pady=(0, 15), fill="x")
        self.satis_barkod.bind("<Return>", self.urunu_sepete_ekle)
        self.satis_barkod.focus()

        self.bitir_buton = ctk.CTkButton(sag_panel, text="✅ SATIŞI ONAYLA", font=(FONT_ANA, 20, "bold"), height=60, 
                                         fg_color=RENK_YESIL, hover_color="#27ae60", corner_radius=15, command=self.islemi_bitir)
        self.bitir_buton.pack(fill="x", pady=10)

        self.temizle_buton = ctk.CTkButton(sag_panel, text="🗑️ İPTAL ET / TEMİZLE", font=(FONT_ANA, 14, "bold"), height=40,
                                           fg_color=RENK_KIRMIZI, hover_color="#c0392b", corner_radius=15, command=self.sepeti_temizle)
        self.temizle_buton.pack(fill="x", pady=5)

    def urunu_sepete_ekle(self, event):
        barkod = self.satis_barkod.get()
        self.satis_barkod.delete(0, 'end') 
        
        try:
            adet = int(self.satis_adet.get())
            if adet < 1: adet = 1
        except ValueError:
            adet = 1
            
        self.c.execute("SELECT isim, alis, satis FROM Urunler WHERE barkod=?", (barkod,))
        urun = self.c.fetchone()
        
        if urun:
            isim, alis, satis = urun
            self.ses_cikar("ok")
            
            toplam_satis = satis * adet
            toplam_alis = alis * adet
            
            self.sepet.append((barkod, isim, toplam_alis, toplam_satis, adet))
            self.toplam_fiyat += toplam_satis
            self.toplam_maliyet += toplam_alis
            
            zaman = datetime.now().strftime("%H:%M")
            satir = f"[{zaman}] {isim[:15]:<15} x{adet:<2} {toplam_satis:>6.2f} ₺\n"
            
            self.liste_alani.configure(state="normal")
            self.liste_alani.insert("end", satir)
            self.liste_alani.configure(state="disabled")
            self.liste_alani.see("end")
            
            self.toplam_etiketi.configure(text=f"{self.toplam_fiyat:.2f} ₺")
            
            self.satis_adet.delete(0, 'end')
            self.satis_adet.insert(0, "1")
        else:
            self.ses_cikar("hata")
            self.toplam_etiketi.configure(text="BULUNAMADI!", text_color=RENK_KIRMIZI)
            self.after(1500, lambda: self.toplam_etiketi.configure(text=f"{self.toplam_fiyat:.2f} ₺", text_color=RENK_YESIL))

    def islemi_bitir(self):
        if not self.sepet: return 
        
        kar = self.toplam_fiyat - self.toplam_maliyet
        self.c.execute("UPDATE Gunluk SET ciro = ciro + ?, kar = kar + ? WHERE id=1", (self.toplam_fiyat, kar))
        
        for barkod, isim, alis_top, satis_top, adet in self.sepet:
            self.c.execute("UPDATE Urunler SET satilan_adet = satilan_adet + ? WHERE barkod=?", (adet, barkod))
        
        self.conn.commit()
        self.sepeti_temizle(tamamen=True)
        self.ozet_guncelle() 
        self.ses_cikar("ok")

    def sepeti_temizle(self, tamamen=False):
        self.sepet.clear()
        self.toplam_fiyat = 0.0
        self.toplam_maliyet = 0.0
        
        self.liste_alani.configure(state="normal")
        self.liste_alani.delete("1.0", "end")
        if not tamamen:
            self.liste_alani.insert("end", "--- İŞLEM İPTAL EDİLDİ ---\n")
        self.liste_alani.configure(state="disabled")
        
        self.toplam_etiketi.configure(text="0.00 ₺")

    def urun_ekle_ekrani_kur(self):
        self.sekme_ekle.grid_columnconfigure(0, weight=1)
        self.sekme_ekle.grid_columnconfigure(1, weight=1)
        self.sekme_ekle.grid_rowconfigure(0, weight=1)

        sol_frame = ctk.CTkFrame(self.sekme_ekle, fg_color=RENK_PANEL, corner_radius=15)
        sol_frame.grid(row=0, column=0, padx=10, sticky="nsew")
        
        ctk.CTkLabel(sol_frame, text="📦 Kayıtlı Ürünler", font=(FONT_ANA, 18, "bold")).pack(pady=10)
        self.urun_listesi_frame = ctk.CTkScrollableFrame(sol_frame, fg_color="transparent")
        self.urun_listesi_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.urunleri_listele()

        sag_frame = ctk.CTkFrame(self.sekme_ekle, fg_color=RENK_PANEL, corner_radius=15)
        sag_frame.grid(row=0, column=1, padx=10, sticky="nsew")
        
        ctk.CTkLabel(sag_frame, text="✏️ Ürün Düzenle / Ekle", font=(FONT_ANA, 18, "bold")).pack(pady=20)
        
        self.ekle_barkod = ctk.CTkEntry(sag_frame, placeholder_text="Barkod", height=40, font=(FONT_ANA, 14))
        self.ekle_barkod.pack(pady=10, padx=20, fill="x")
        self.ekle_barkod.bind("<Return>", self.urun_bilgisi_getir)
        
        self.ekle_isim = ctk.CTkEntry(sag_frame, placeholder_text="Ürün Adı", height=40, font=(FONT_ANA, 14))
        self.ekle_isim.pack(pady=10, padx=20, fill="x")
        
        fiyat_frame = ctk.CTkFrame(sag_frame, fg_color="transparent")
        fiyat_frame.pack(pady=10, fill="x", padx=20)
        
        self.ekle_alis = ctk.CTkEntry(fiyat_frame, placeholder_text="Alış Fiyatı", width=120)
        self.ekle_alis.pack(side="left", padx=5)
        self.ekle_satis = ctk.CTkEntry(fiyat_frame, placeholder_text="Satış Fiyatı", width=120)
        self.ekle_satis.pack(side="right", padx=5)
        
        self.kaydet_buton = ctk.CTkButton(sag_frame, text="💾 KAYDET", font=(FONT_ANA, 16, "bold"), height=45,
                                          fg_color=RENK_MAVI, command=self.urun_kaydet)
        self.kaydet_buton.pack(pady=20, padx=20, fill="x")
        
        self.durum_etiketi = ctk.CTkLabel(sag_frame, text="", font=(FONT_ANA, 12))
        self.durum_etiketi.pack()

    def urunleri_listele(self):
        for widget in self.urun_listesi_frame.winfo_children():
            widget.destroy()
        
        self.c.execute("SELECT barkod, isim, satis FROM Urunler ORDER BY isim ASC")
        urunler = self.c.fetchall()
        
        for barkod, isim, satis in urunler:
            satir = ctk.CTkFrame(self.urun_listesi_frame, fg_color="#222", corner_radius=8)
            satir.pack(fill="x", pady=3, padx=2)
            
            ctk.CTkLabel(satir, text=f"{isim}", font=(FONT_ANA, 14, "bold")).pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(satir, text=f"{satis} ₺", text_color=RENK_YESIL).pack(side="left", padx=10)
            
            ctk.CTkButton(satir, text="Sil", width=40, height=25, fg_color=RENK_KIRMIZI, 
                          command=lambda b=barkod: self.urun_sil(b)).pack(side="right", padx=10)

    def urun_sil(self, barkod):
        self.c.execute("DELETE FROM Urunler WHERE barkod=?", (barkod,))
        self.conn.commit()
        self.urunleri_listele()
        self.ozet_guncelle()

    def urun_bilgisi_getir(self, event):
        barkod = self.ekle_barkod.get()
        self.ekle_isim.delete(0, 'end')
        self.ekle_alis.delete(0, 'end')
        self.ekle_satis.delete(0, 'end')
        
        self.c.execute("SELECT isim, alis, satis FROM Urunler WHERE barkod=?", (barkod,))
        urun = self.c.fetchone()
        
        if urun:
            isim, alis, satis = urun
            self.ses_cikar("ok")
            self.ekle_isim.insert(0, isim)
            self.ekle_alis.insert(0, str(alis))
            self.ekle_satis.insert(0, str(satis))
            self.durum_etiketi.configure(text="Ürün Bulundu!", text_color=RENK_SARI)
            self.ekle_satis.focus()
        else:
            self.ses_cikar("ok")
            self.durum_etiketi.configure(text="Yeni Ürün!", text_color=RENK_MAVI)
            self.ekle_isim.focus()

    def urun_kaydet(self):
        barkod = self.ekle_barkod.get()
        isim = self.ekle_isim.get()
        try:
            alis = float(self.ekle_alis.get().replace(",", "."))
            satis = float(self.ekle_satis.get().replace(",", "."))
            self.c.execute("INSERT OR REPLACE INTO Urunler (barkod, isim, alis, satis, satilan_adet) VALUES (?, ?, ?, ?, COALESCE((SELECT satilan_adet FROM Urunler WHERE barkod=?), 0))", (barkod, isim, alis, satis, barkod))
            self.conn.commit()
            self.durum_etiketi.configure(text="Kaydedildi!", text_color=RENK_YESIL)
            self.urunleri_listele()
            self.ozet_guncelle()
            
            self.ekle_barkod.delete(0, 'end')
            self.ekle_isim.delete(0, 'end')
            self.ekle_alis.delete(0, 'end')
            self.ekle_satis.delete(0, 'end')
            self.ekle_barkod.focus()
        except ValueError:
            self.durum_etiketi.configure(text="Fiyat Hatalı!", text_color=RENK_KIRMIZI)

    def ozet_ekrani_kur(self):
        self.sekme_ozet.grid_columnconfigure(0, weight=1)
        
        panel = ctk.CTkFrame(self.sekme_ozet, fg_color=RENK_PANEL, corner_radius=20)
        panel.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(panel, text="📊 GÜNLÜK RAPOR", font=(FONT_ANA, 24, "bold"), text_color="#bbb").pack(pady=20)
        
        
        info_frame = ctk.CTkFrame(panel, fg_color="transparent")
        info_frame.pack(fill="x", padx=20)

        ciro_kart = ctk.CTkFrame(info_frame, fg_color="#222", border_color=RENK_MAVI, border_width=2)
        ciro_kart.pack(side="left", fill="x", expand=True, padx=10)
        ctk.CTkLabel(ciro_kart, text="Toplam Ciro", font=(FONT_ANA, 14)).pack(pady=(10,0))
        self.ciro_etiket = ctk.CTkLabel(ciro_kart, text="0.00 ₺", font=(FONT_ANA, 28, "bold"), text_color=RENK_MAVI)
        self.ciro_etiket.pack(pady=(0,10))

        kar_kart = ctk.CTkFrame(info_frame, fg_color="#222", border_color=RENK_SARI, border_width=2)
        kar_kart.pack(side="left", fill="x", expand=True, padx=10)
        ctk.CTkLabel(kar_kart, text="Net Kâr", font=(FONT_ANA, 14)).pack(pady=(10,0))
        self.kar_etiket = ctk.CTkLabel(kar_kart, text="0.00 ₺", font=(FONT_ANA, 28, "bold"), text_color=RENK_SARI)
        self.kar_etiket.pack(pady=(0,10))
        
        ctk.CTkLabel(panel, text="🏆 Bugünün Yıldızları", font=(FONT_ANA, 18, "bold")).pack(pady=(30, 10))
        self.encok_satanlar_liste = ctk.CTkTextbox(panel, height=150, fg_color="#222", font=("Consolas", 14))
        self.encok_satanlar_liste.pack(fill="x", padx=30)
        self.encok_satanlar_liste.configure(state="disabled")

        ctk.CTkButton(panel, text="🌙 GÜNÜ KAPAT (Z RAPORU)", fg_color=RENK_KIRMIZI, hover_color="#c0392b", height=50, font=(FONT_ANA, 16, "bold"),
                      command=self.gunu_kapat).pack(pady=20, padx=30, fill="x")
        self.kapanis_etiketi = ctk.CTkLabel(panel, text="")
        self.kapanis_etiketi.pack()

    def ozet_guncelle(self):
        self.c.execute("SELECT ciro, kar FROM Gunluk WHERE id=1")
        veri = self.c.fetchone()
        if veri:
            self.ciro_etiket.configure(text=f"{veri[0]:.2f} ₺")
            self.kar_etiket.configure(text=f"{veri[1]:.2f} ₺")
        
        self.c.execute("SELECT isim, satilan_adet FROM Urunler WHERE satilan_adet > 0 ORDER BY satilan_adet DESC LIMIT 5")
        satanlar = self.c.fetchall()
        
        self.encok_satanlar_liste.configure(state="normal")
        self.encok_satanlar_liste.delete("1.0", "end")
        for i, (isim, adet) in enumerate(satanlar, 1):
            self.encok_satanlar_liste.insert("end", f"{i}. {isim:<20} -> {adet} Adet\n")
        self.encok_satanlar_liste.configure(state="disabled")

    def gunu_kapat(self):
        self.c.execute("UPDATE Gunluk SET ciro = 0.0, kar = 0.0 WHERE id=1")
        self.c.execute("UPDATE Urunler SET satilan_adet = 0")
        self.conn.commit()
        self.ozet_guncelle()
        self.kapanis_etiketi.configure(text="✅ GÜN KAPATILDI!", text_color=RENK_YESIL)
        self.after(3000, lambda: self.kapanis_etiketi.configure(text=""))

if __name__ == "__main__":
    uygulama = BufeSistemi()
    uygulama.mainloop()