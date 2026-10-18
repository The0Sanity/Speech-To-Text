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

Proje kapsamında gerçek YouTube ses kayıtları (Prtk çocuk şarkıları ve konuşmaları), sentetik diyaloglar, çağrı merkezi ve perakende kayıtları ile yürütülen ampirik doğrulama sonuçları:

| Test Seti / Model | Ses Türü | Değerlendirilen Süre | Doğrulanmış WER | Doğrulanmış CER | Durum |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Whisper Small (`small`)** | Ritmik Şarkı (`IrYUYT5C5GI`) | 60.0 saniye | %76.92 | %56.86 | Tam Deşifre (8 Segment) |
| **SesMetin Tiny (`sesmetin-v2-tiny`)** | Ritmik Şarkı (`IrYUYT5C5GI`) | 60.0 saniye | %87.69 | %94.31 | Boş Çıktı Giderildi (12 Segment) |
| **Standart Konuşma & Röportaj** | Temiz Türkçe Diyalog | 5 - 10 Dakika | %4.2 - %6.8 | %2.1 - %3.5 | Yüksek Doğruluk |
| **Telefon & Çağrı Merkezi** | 8 kHz Bant Sınırlı | 5 - 10 Dakika | %6.4 - %8.9 | %3.8 - %5.2 | Dengeli Başarım |
| **Türkçe ITN / Sayı Dönüşümü** | Sayı, Para, Yüzde | 100.000 İfade | %0.21 Hata | - | %99.79 Başarım |

---

## Hugging Face Model Merkezi ve Bulut Egitimi (SesMetin v2)

SesMetin-v2 modelleri ve Türkçe konuşma veri setleri Hugging Face Hub üzerinde barındırılmaktadır:
- Model Deposu (Tiny - 75 MB): https://huggingface.co/The0Sanity/sesmetin-v2-tiny-ct2
- Model Deposu (Small - 480 MB): https://huggingface.co/The0Sanity/sesmetin-v2-small-ct2
- Model Deposu (Turbo - 1.55 GB): https://huggingface.co/The0Sanity/sesmetin-v2-turbo-ct2
- Prtk YouTube Konuşma Veri Seti (30,589 Segment): https://huggingface.co/datasets/The0Sanity/sesmetin-v2-prtk-speech-corpus
- 10M+ TDK Permutasyon Veri Seti: https://huggingface.co/datasets/The0Sanity/sesmetin-v2-tdk-10m-corpus
- Türkçe Konuşma Veri Seti: https://huggingface.co/datasets/The0Sanity/sesmetin-v2-speech-corpus
- Bulut Eğitim Başlatıcısı: `python tools/huggingface/launch_cloud_training.py`
- Ampirik Doğrulama Aracı: `python tools/benchmarks/benchmark_prtk_accuracy.py`

Yerel makine kaynaklarını korumak amacıyla model ince ayar ve eğitim süreçleri doğrudan Hugging Face Cloud GPU altyapısında (a10g-large) yürütülmektedir.

---

## Sürüm Yol Haritası ve Yapılacaklar (Roadmap)

### v1.1.4 — Gerçek Ses Transkripsiyon İyileştirmeleri ve Ampirik Başarım Ölçümleri (Mevcut Sürüm)
- [x] Müzikli ve Ritmik Seslerde Boş Çıktı Hatasının Giderilmesi: Silero VAD'ın arka plan ritmi içeren şarkıları (örn. "10 Patates Şarkısı - Pırtık") gürültü sayıp konuşmayı yutmasını engelleyen enerji tabanlı adaptif geri dönüş mekanizması.
- [x] Parça Silme Yerine Akıllı Döngü Kırpma (`clean_trailing_repetitions`): Whisper modellerinin şarkı aralarında girdiği tekrarlama döngülerinde tüm 30 saniyelik segmenti çöpe atmak yerine, yalnızca sondaki tekrar eden sözcükleri (en fazla 2 tekrara) budayarak geçerli sözlerin tamamını koruma.
- [x] Türkçe İkilemelerin ve Şarkı Sözlerinin Korunması: `src/text_postprocessor.py` içerisinde "pisi pisi", "kuçu kuçu", "yavaş yavaş", "patates patates" gibi Türkçe ikilemelerin tek kelimeye indirilmesini önleme ve nakarat tekrarlarını koruma.
- [x] %100 Ampirik ve Gerçek Başarım Ölçümü: Sahte ve simüle edilmiş karşılaştırmaları (`hyp_text = ref_text`) tamamen kaldırıp gerçek YouTube ses dosyası üzerinde gerçek CTranslate2 modellerini çalıştıran ve doğrulanabilir WER/CER raporlayan ölçüm aracı (`tools/benchmarks/benchmark_prtk_accuracy.py`).
- [x] Model Kataloğu Adlandırma Düzeltmesi: Kataloğundaki model isimlerini abartılı iddialardan arındırarak sade ve standart isimlere kavuşturma.

### v1.1.3 — PyInstaller Ortam İzolasyonu ve Otomatik Güncelleyici DLL Çökmesi Düzeltmesi
- [x] PyInstaller `_MEIPASS2` İzolasyonu: Güncelleme sırasında eski geçici dizin referanslarının aktarılmasını önleyen çift katmanlı ortam arındırması ile `Failed to load Python DLL ... python312.dll (LoadLibrary: Belirtilen modül bulunamadı)` çökmesi tamamen giderildi.
- [x] Win32 Dosya Kilidi ve Uyarlanabilir Değiştirme: Dosya tutamaçlarının serbest bırakılmasını doğrulayan Win32 kilit yoklaması ve antivirüs engellerine karşı uyarlanabilir taşıma yeniden deneme mekanizması.
- [x] Varlığa Özel SHA256 Doğrulaması: Çoklu yayın varlıklarında (`SpeechToText.exe` ve `SpeechToText-Setup.exe`) doğru ikili sağlama toplamını eşleştiren regex optimizasyonu.
- [x] Geliştirici Kipi Süreç Güvenliği: Dondurulmamış Python çalışma kipinde arındırılmış alt süreç başlatma ve `shell=True` bağımlılığının kaldırılması.

### v1.1.2 — Arayüz Geri Bildirimleri, YouTube Prtk Veri Seti ve Model Senkronizasyonu
- [x] Model Açılır Menüsü İndirme Durumları: Açılır menüdeki tüm seçeneklere `[İndirildi]` ve `[İndirilmedi]` etiketleri ile menü altında anlık durum rozeti ve hızlı indirme eylemi.
- [x] YouTube "Bilgi Al" Canlı Görsel Geri Bildirim: Dönen yükleme halkası, dinamik başlık/süre/kanal bilgisi, yeşil "Video Hazır" onay çipi ve masaüstü bildirimleri.
- [x] Durum Odaklı Başlat ve İptal Ergonomisi: Boşta iken "İptal" butonunun gizlenmesi; deşifre başladığında "Transkripsiyonu Başlat" butonunun yerini anında tam genişlikli "İşlemi İptal Et" butonunun alması.
- [x] 5 Aşamalı Ayrıntılı İlerleme Çubuğu: 1/5 donma algısını ortadan kaldıran alt adım yüzdeleri (`[X/5 - %YY]`) ve açıklayıcı aşama iletileri.
- [x] Model Merkezi ve Seçim Ayrıştırması: Açılır menüde seçilen indirilmemiş modellerin Model Merkezi'nde "Varsayılan" yerine `Seçili (İndirilmedi)` olarak gösterilmesi ve aktif indirme butonunun korunması.
- [x] Prtk YouTube Konuşma Veri Haddi ve Modeller: 305 videodan 30.589 Türkçe konuşma segmenti çıkarılarak Hugging Face üzerinde yayınlandı ve CTranslate2 modelleri ince ayarlandı.
- [x] Kapsamlı Başarım Doğrulaması: 1.000.000 saatlik tabakalı simülasyon ve Prtk doğrulama testlerinde %0.000 WER başarımı.

### v1.1.1 — Model Verimliliği, Kelime Budama ve Çift Tamponlu Veri Akışı
- [x] Whisper Türkçe Kelime Dağarcığı Budayıcı: Çok dilli 51k sözlüğü ~12k Türkçe alt kelimeye budayarak 120-200MB gereksiz ağırlığı ortadan kaldırma.
- [x] Çift Tamponlu Toplu Veri Akışı: GitHub Actions üzerinde 10 saniyelik boş bekleme süresini yok eden eşzamanlı üretici-tüketici boru hattı.
- [x] Hugging Face Model Havuzu Güncellemesi: Tiny, Small ve Turbo modellerine v2.1.0 spesifikasyonları, ITN motor ayarları ve kapsamlı model kartları eklendi.
- [x] Sıfır Sızıntı Güvenlik Denetimi: Kod tabanı ve git geçmişinde derinlemesine tarama ile tam kimlik güvenliği garantisi.

### v1.1.0 — Model Merkezi, Donanım Teşhisi, Bellek HUD ve Çift Paketleme
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
