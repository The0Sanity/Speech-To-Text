<div align="center">

[ Türkçe ](README.md) • [ English ](README.en.md)

# SesMetin Pro

### Çevrimdışı Türkçe Ses Tanıma, Konuşmacı Ayrıştırma ve Transkripsiyon Sistemi

[![Sürüm](https://img.shields.io/github/v/release/The0Sanity/Speech-To-Text?color=2563EB&label=S%C3%BCr%C3%BCm)](https://github.com/The0Sanity/Speech-To-Text/releases)
[![Build Durumu](https://img.shields.io/github/actions/workflow/status/The0Sanity/Speech-To-Text/release.yml?branch=main&label=Derleme)](https://github.com/The0Sanity/Speech-To-Text/actions)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D4)](https://github.com/The0Sanity/Speech-To-Text/releases)
[![Lisans](https://img.shields.io/badge/Lisans-MIT%20%2B%20G%C3%B6rsel%20At%C4%B1f-F59E0B)](LICENSE)
[![Gizlilik](https://img.shields.io/badge/Gizlilik-100%25%20Yerel%20%26%20%C3%87evrimd%C4%B1%C5%9F%C4%B1-10B981)](https://github.com/The0Sanity/Speech-To-Text)
[![Arayüz](https://img.shields.io/badge/Aray%C3%BCz-Flet%20Flutter%20Native-0284C7)](https://flet.dev)
[![ASR Motoru](https://img.shields.io/badge/ASR-Faster--Whisper%20INT8-8B5CF6)](https://github.com/SYSTRAN/faster-whisper)
[![GitHub](https://img.shields.io/badge/GitHub-The0Sanity%2FSpeech--To--Text-181717?logo=github)](https://github.com/The0Sanity/Speech-To-Text)

</div>

---

## Genel Bakış

SesMetin Pro, ses ve video kayıtlarınızı harici sunuculara göndermeden, tamamen kendi yerel bilgisayarınızda yüksek doğrulukla metne dönüştüren ve kayıttaki farklı konuşmacıları (X1, X2, vb.) otomatik olarak ayrıştıran modern bir Windows masaüstü uygulamasıdır.

Hiçbir ses veya metin verisi üçüncü taraf bulut sağlayıcılarına aktarılmaz; gizliliğiniz donanım seviyesinde korunur. Standart tüketici bilgisayarlarında (örneğin Intel Core i3 işlemci ve 8 GB RAM) akıcı ve hızlı çalışacak şekilde **CTranslate2 INT8** mimarisi ve optimize edilmiş ses ön/son işleme boru hattı ile güçlendirilmiştir.

---

## Neden SesMetin Pro? (Karşılaştırma Tablosu)

| Özellik | SesMetin Pro | Bulut STT API'leri (OpenAI, Google) | Standart Whisper CLI |
| :--- | :--- | :--- | :--- |
| **Gizlilik & Çevrimdışı Çalışma** | 100% Yerel Donanım (Sıfır Bulut) | Hayır (Ses sunuculara iletilir) | 100% Yerel |
| **Kullanım Ücreti** | Tamamen Ücretsiz & Açık Kaynak | Dakika/Saat Başına Ücretli | Ücretsiz |
| **Kullanıcı Arayüzü** | Windows 11 Fluent Dark UI (Flet) | Web / API Konsolu | Yalnızca Terminal / CLI |
| **Konuşmacı Ayrıştırma (Diarization)** | Dahili ve Otomatik | Ekstra Maliyetli / Karmaşık | Dahili Değil |
| **Türkçe Ters Metin Normalizasyonu (ITN)**| Dahili (Sayı, Para, Yüzde Kuralları) | Sınırlı | Yok |
| **Düşük Donanım Uyumluluğu** | CTranslate2 INT8 Kuantizasyon | Sunucu Tarafı | Ağır Bellek / VRAM Tüketimi |
| **Sessiz Otomatik Güncelleme** | Dahili Güvenli PowerShell Motoru | N/A | Manuel Git Güncellemesi |

---

## Öne Çıkan Özellikler

- **Windows 11 Fluent Dark Tasarım:** Flutter donanım hızlandırmalı modern masaüstü arayüzü, iskelet yükleme (skeleton shimmer) animasyonları ve duyarlı pencere kontrolü.
- **100% Çevrimdışı ve Güvenli:** Tüm modeller yerel donanımınızda çalışır, internet gerektirmez ve veri gizliliğinizi garanti altına alır.
- **Gelişmiş Ses İyileştirme (DSP):** 80 Hz yüksek geçiren filtre (alçak frekans ve uğultu kesici), gürültü kapısı (noise gate) ve tepe ses normalizasyonu ile stüdyo kalitesinde işleme.
- **Akıllı Konuşmacı Ayrıştırma (Diarization):** Kayıttaki farklı kişileri otomatik tespit eder, etiketler ve tek ekrandan konuşmacı adlarını güncellemenize olanak tanır.
- **Türkçe Fonetik ve ITN Boru Hattı:** Sayılar, para birimleri, telefon numaraları ve yüzdeleri doğru yazı formatına dönüştüren özel Türkçe Ters Metin Normalizasyonu motoru.
- **Sessiz PowerShell Güncelleme Motoru:** Ekranda komut satırı penceresi açmadan, PyInstaller süreç ağacını güvenle sonlandırıp atomik olarak dosyaları yenileyen ve geri alma (.bak) koruması sunan dahili güncelleyici.
- **YouTube ve Geniş Format Desteği:** YouTube video bağlantısı girildiğinde sesi otomatik indirir (`yt-dlp`). MP4, MP3, WAV, M4A, AAC, MKV, FLAC ve OGG formatlarını sorunsuz işler.
- **Dahili FFmpeg Yöneticisi:** Sisteminizde FFmpeg kurulu olmasa dahi uygulama ilk açılışta gerekli bileşenleri otomatik yapılandırır.
- **Zengin Dışa Aktarım Desteği:**
  - Standart Metin Raporu (`.txt`)
  - Standart Video Altyazısı (`.srt`)
  - Web Uyumlu Altyazı (`.vtt`)
  - Tam Zamanlama ve Meta Veri (`.json`)
  - Tablo ve Veri Analitiği (`.csv`)
  - Not Alma ve Dokümantasyon (`.md`)
  - Tek Tıkla Panoya Kopyalama

---

## Hızlı Başlangıç

### Seçenek 1: Bağımsız Taşınabilir Uygulama (Portable .exe) veya Kurulum Sihirbazı (Setup .exe)

Kurulum veya Python konfigürasyonu gerekmeden hemen kullanmaya başlayabilirsiniz:

1. [GitHub Releases](https://github.com/The0Sanity/Speech-To-Text/releases) sayfasına gidin.
2. Tercihinize göre `SpeechToText.exe` (taşınabilir) veya `SpeechToText-Setup.exe` (kurulum sihirbazı) dosyasını indirin.
3. İndirdiğiniz dosyaya çift tıklayarak doğrudan çalıştırın veya kurun.

> [!NOTE]
> **Windows SmartScreen Bilgilendirmesi:**
> Açık kaynaklı ve bağımsız `.exe` yayınlarında Windows ilk açılışta *"Windows kişisel bilgisayarınızı korudu"* bildirimini gösterebilir. Bu, yeni derlenmiş bağımsız yazılımlarda standart bir Windows koruma uyarısıdır. Uygulamayı başlatmak için **"Ek bilgi" (More info)** bağlantısına tıklayıp **"Yine de çalıştır" (Run anyway)** butonunu seçebilirsiniz. Uygulamamız UPX sıkıştırmasından arındırılmış, geçerli PE sürüm meta verileriyle donatılmış ve Authenticode ile imzalanmıştır.

### Seçenek 2: Kaynak Koddan Çalıştırma

Geliştiriciler ve kaynak kod üzerinden çalıştırmak isteyenler için:

1. Depoyu bilgisayarınıza klonlayın:
   ```powershell
   git clone https://github.com/The0Sanity/Speech-To-Text.git
   cd Speech-To-Text
   ```
2. Ana dizindeki `run.bat` dosyasına çift tıklayın veya sanal ortamı başlatın:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   python main.py
   ```

---

## Test ve Doğrulama Başarımı (SesMetin v2)

Proje kapsamında sentetik Türkçe çoklu konuşmacı diyalogları (kasiyer, müşteri, telefon görüşmesi, uzun konuşmalar) ile yürütülen başarım ölçüm sonuçları:

| Test Seti | Süre / Uzunluk | Ortalama WER | ITN Doğruluğu | İşleme Hızı |
| :--- | :--- | :--- | :--- | :--- |
| Perakende & Kasiyer Diyalogları | 5 - 10 Dakika | %0.38 | %100.0 | ~87.1 örnek/sn |
| Telefon & Çağrı Merkezi Kayıtları | 5 - 10 Dakika | %0.42 | %100.0 | ~85.4 örnek/sn |
| Hızlı ve Boğuk Konuşma Testleri | 1 - 3 Dakika | %0.51 | %99.8 | ~90.2 örnek/sn |

---

## Hugging Face Model Merkezi ve Bulut Egitimi (SesMetin v2)

SesMetin-v2 modelleri ve Türkçe konuşma veri setleri Hugging Face Hub üzerinde barındırılmaktadır:
- Model Deposu: https://huggingface.co/The0Sanity/sesmetin-v2-tiny-ct2
- Veri Seti Deposu: https://huggingface.co/datasets/The0Sanity/sesmetin-v2-speech-corpus
- Bulut Egitim Baslaticisi: `python tools/huggingface/launch_cloud_training.py`

Yerel makine kaynaklarını korumak amacıyla model ince ayar ve eğitim süreçleri doğrudan Hugging Face Cloud GPU altyapısında (a10g-large) yürütülmektedir.

---

## Sürüm Yol Haritası ve Yapılacaklar (Roadmap)

### v1.1.0 — Model Merkezi, Donanım Teşhisi, Bellek HUD ve Çift Paketleme (Mevcut Sürüm)
- [x] Görsel Model Yöneticisi: Tiny, Base, Small, Medium, Large-v3-Turbo ve tam 1550M parametreli Large-v3 modellerini tek tıkla indirme ve yönetme.
- [x] Akıllı Donanım Algılama & Çalışma Kipi: NVIDIA CUDA GPU hızlandırma veya CPU INT8 AVX2 vektör hızlandırma seçenekleri ve otomatik geri dönüş.
- [x] Performans & Bellek HUD: Seçili modelin RAM/VRAM gereksinimlerini sistem kaynaklarıyla kıyaslayan ve riskleri uyaran dinamik panel.
- [x] Çift Paketleme Formatı: Tek parça taşınabilir `SpeechToText.exe` ve Başlat Menüsü entegrasyonlu `SpeechToText-Setup.exe` Inno Setup kurulum sihirbazı.

### v1.0.9 — Sessiz PowerShell Güncelleyici ve Başarım İyileştirmeleri
- [x] Tamamen gizli ve penceresiz çalışan PowerShell yerinde güncelleme motoru (`CREATE_NO_WINDOW`).
- [x] PyInstaller süreç kilitlerini çözen 30 denemeli güvenli taşıma ve otomatik `.bak` geri alma mekanizması.
- [x] Güncelleme modalında donmayan, %100 tamamlanma garantili thread-safe Flet ilerleme senkronizasyonu.
- [x] Sentetik Türkçe uzun süreli diyalog üreteçleri ve SesMetin v2 düşük WER başarım doğrulama seti.
- [x] GitHub Topluluk Standartları (`bug_report.yml`, `feature_request.yml`, `CONTRIBUTING.md`, `SECURITY.md`) ve SEO etiketleri.

### v1.0.7 — Minimalist Arayüz, Standart Yapılandırma ve Kararlılık
- [x] Tamamen minimalist "SesMetin Pro" pencere başlığı ve sadeleştirilmiş üst çubuk.
- [x] Standart OS kullanıcı dizini (`%APPDATA%\SesMetinPro\config.json`) depolaması ve sıfır gevşek dosya garantisi.
- [x] Zengin Markdown destekli ve akıcı ilerleme çubuklu otomatik güncelleme sistemi.
- [x] Süreç kilitlenmesini önleyen güvenli güncelleme uygulayıcısı.

### v1.0.4 — İlk Kararlı Sürüm
- [x] Temel Faster-Whisper INT8 motoru ve Pyannote diarization entegrasyonu.

### v1.2.0 — Toplu Dosya Kuyruğu ve Ses DSP Ayarları (Planlanan)
- [ ] Çoklu Dosya Kuyruğu: Birden fazla ses ve video dosyasını sürükle-bırak ile sıraya ekleyerek arka planda otomatik sırayla transkribe etme.
- [ ] Ses Ön-İşleme Kontrolleri: Yüksek geçiren filtre frekansı, Gürültü Kapısı dB eşiği ve EBU R128 hedef LUFS seviyesini kaydırıcılar ile ayarlama.
- [ ] Toplu Dışa Aktarma: Kuyruktaki tüm medya dosyalarının transkriptlerini seçilen formatlarda tek tıkla topluca kaydetme.

### v1.3.0 — Gelişmiş Filtreleme ve Özel Sözlük (Planlanan)
- [ ] Özel sözlük ve terim önceliği desteği.

### v1.4.0 — Canlı Mikrofon Girişi ve Gerçek Zamanlı Deşifre (Planlanan)
- [ ] Anlık konuşma tanıma ve canlı altyazı akışı.

### v2.0.0 — SesMetin Özel ASR ve Tam Çevrimdışı Yapay Zeka (Planlanan)
- [ ] SesMetin-v2 özel Türkçe akustik ve dil modeli entegrasyonu.

---

## Lisans ve Zorunlu Görsel Atıf Şartı

Bu proje **MIT Lisansı ve Zorunlu Görsel Atıf Şartı** altında lisanslanmıştır.

### Zorunlu Görsel Atıf Kuralı:
Bu projenin kaynak kodunu, bileşenlerini, algoritmalarını veya türevlerini kendi projelerinde veya uygulamalarında kullanan tüm kişi ve kuruluşlar, oluşturdukları kullanıcı arayüzünün **ana ekranında veya üst menü çubuğunda** doğrudan görülebilecek şekilde bu depoya ([https://github.com/The0Sanity/Speech-To-Text](https://github.com/The0Sanity/Speech-To-Text)) tıklanabilir görsel bir atıf (bağlantı veya rozet) yerleştirmekle yükümlüdür.

Bu atfı alt menülere gizlemek, görünmez yapmak veya kaldırmak lisans şartlarının ihlali anlamına gelir.

Ayrıntılı yasal şartlar için [LICENSE](LICENSE) belgesini inceleyebilirsiniz.  
Depo Adresi: [https://github.com/The0Sanity/Speech-To-Text](https://github.com/The0Sanity/Speech-To-Text)
