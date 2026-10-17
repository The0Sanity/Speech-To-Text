<div align="center">

[ Türkçe ](README.md) • [ English ](README.en.md)

# SesMetin Pro

### Çevrimdışı Türkçe Ses Tanıma, Konuşmacı Ayrıştırma ve Transkripsiyon Sistemi

[![Sürüm](https://img.shields.io/github/v/release/The0Sanity/Speech-To-Text?color=2563EB&label=S%C3%BCr%C3%BCm)](https://github.com/The0Sanity/Speech-To-Text/releases)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D4)](https://github.com/The0Sanity/Speech-To-Text/releases)
[![Lisans](https://img.shields.io/badge/Lisans-MIT%20%2B%20G%C3%B6rsel%20At%C4%B1f-F59E0B)](LICENSE)
[![Gizlilik](https://img.shields.io/badge/Gizlilik-100%25%20Yerel%20%26%20%C3%87evrimd%C4%B1%C5%9F%C4%B1-10B981)](https://github.com/The0Sanity/Speech-To-Text)
[![Arayüz](https://img.shields.io/badge/Aray%C3%BCz-Flet%20Flutter%20Native-0284C7)](https://flet.dev)
[![ASR Motoru](https://img.shields.io/badge/ASR-Faster--Whisper%20INT8-8B5CF6)](https://github.com/SYSTRAN/faster-whisper)
[![GitHub](https://img.shields.io/badge/GitHub-The0Sanity%2FSpeech--To--Text-181717?logo=github)](https://github.com/The0Sanity/Speech-To-Text)

</div>

---

## Genel Bakış

SesMetin Pro, ses ve video kayıtlarınızı internet bağlantısına ihtiyaç duymadan, tamamen kendi bilgisayarınızda metne dönüştüren ve kayıttaki farklı konuşmacıları (X1, X2, vb.) otomatik olarak ayrıştıran modern bir masaüstü uygulamasıdır.

Hiçbir ses veya metin verisi harici sunuculara veya bulut sağlayıcılarına gönderilmez; gizliliğiniz tamamen korunur. Standart tüketici donanımlarında (örneğin Intel Core i3 ve 8 GB RAM) yüksek performans, akıcı kullanım ve düşük bellek tüketimi için **CTranslate2 INT8** mimarisiyle optimize edilmiştir.

---

## Öne Çıkan Özellikler

- **Windows 11 Fluent Dark Tasarım:** Flutter donanım hızlandırmalı modern masaüstü arayüzü, iskelet yükleme (skeleton shimmer) animasyonları ve duyarlı pencere kontrolü.
- **100% Çevrimdışı ve Güvenli:** Tüm modeller yerel donanımınızda çalışır, internet gerektirmez ve veri gizliliğinizi garanti altına alır.
- **Gelişmiş Ses İyileştirme:** 80 Hz yüksek geçiren filtre (alçak frekans ve uğultu kesici), gürültü kapısı (noise gate) ve tepe ses normalizasyonu ile stüdyo kalitesinde işleme.
- **Akıllı Konuşmacı Ayrıştırma (Diarization):** Kayıttaki farklı kişileri otomatik tespit eder, etiketler ve tek ekrandan konuşmacı adlarını güncellemenize olanak tanır.
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
- **Kesintisiz Güncelleme Kontrolü:** Uygulama açılışında ve ayarlar sekmesinde GitHub Releases üzerinden yeni sürümleri otomatik kontrol eder.

---

## Hızlı Başlangıç

### Seçenek 1: Bağımsız Uygulama (.exe) — Tavsiye Edilen

Kurulum veya teknik konfigürasyon gerekmez:

1. [GitHub Releases](https://github.com/The0Sanity/Speech-To-Text/releases) sayfasına gidin.
2. En güncel sürümün altındaki `SpeechToText.exe` dosyasını indirin.
3. İndirdiğiniz dosyaya çift tıklayarak doğrudan çalıştırın.

> [!NOTE]
> **Windows SmartScreen Bilgilendirmesi:**
> Açık kaynaklı ve bağımsız `.exe` yayınlarında Windows ilk açılışta *"Windows kişisel bilgisayarınızı korudu"* bildirimini gösterebilir. Bu, yeni derlenmiş bağımsız yazılımlarda standart bir Windows koruma uyarısıdır. Uygulamayı başlatmak için **"Ek bilgi" (More info)** bağlantısına tıklayıp **"Yine de çalıştır" (Run anyway)** butonunu seçebilirsiniz. Uygulamamız UPX sıkıştırmasından arındırılmış, geçerli PE sürüm meta verileriyle donatılmış ve Authenticode ile imzalanmıştır.

### Seçenek 2: Kaynak Koddan Çalıştırma

Geliştiriciler ve kaynak kod üzerinden çalıştırmak isteyenler için:

1. Depoyu bilgisayarınıza klonlayın veya zip olarak indirin.
2. Ana dizindeki `run.bat` dosyasına çift tıklayın.
   - Sanal ortam (`venv`) ve gerekli kütüphaneler arka planda otomatik hazırlanır ve uygulama açılır.
3. Dilerseniz terminal üzerinden de başlatabilirsiniz:
   ```powershell
   python main.py
   ```

---

## Sürüm Yol Haritası ve Yapılacaklar (Roadmap)

Geliştirme süreci planlı sürümler halinde yürütülmektedir. v2.0.0 sürümüne kadar eklenecek tüm özellikler aşağıda listelenmiştir:

### v1.0.3 — Kararlı Temel ve Hızlı Başlatma (Mevcut Sürüm)
- [x] Tek parça bağımsız `SpeechToText.exe` dağıtımı (Python kurulumu gerektirmez).
- [x] Anında başlatma optimizasyonu ve pencere önceliklendirmesi (arka planda bekleme sorunu giderildi).
- [x] Flutter iskelet yükleme (skeleton shimmer) geçiş animasyonları.
- [x] Antivirüs yanlış alarm (false-positive) koruması (UPX kaldırıldı, Authenticode dijital imza ve tam PE meta verisi eklendi).
- [x] Dahili FFmpeg bootstrapper (sistemde FFmpeg bulunmadığında otomatik indirme ve yapılandırma).
- [x] GitHub Releases tabanlı otomatik güncelleme motoru.

### v1.1.0 — Model Merkezi ve Donanım Teşhisi (Planlanan)
- [ ] Görsel Model Yöneticisi (Tiny, Base, Small, Medium modellerini tek tıkla indirme, silme ve disk alanı yönetimi).
- [ ] Akıllı Donanım Teşhisi (NVIDIA CUDA / cuDNN ve CPU AVX2 donanımını otomatik algılama ve arayüzden çalışma modu seçimi).
- [ ] Çift Paketleme Formatı (Taşınabilir tek parça Portable `.exe` ve standart Windows Kurulum Sihirbazı Setup `.exe`).
- [ ] Toplu Dosya İşleme Kuyruğu (Birden fazla ses ve video dosyasını listeye ekleyerek sırayla otomatik transkribe etme).

### v1.2.0 — Gerçek Zamanlı Canlı Konuşma ve Masaüstü Altyazı (Planlanan)
- [ ] Canlı Mikrofon Girişi (Toplantı, ders ve canlı yayınları konuşulurken gerçek zamanlı metne dökme).
- [ ] Masaüstü Yüzen Altyazı Çubuğu (Diğer uygulamaların üzerinde konumlanan şeffaf ve her zaman üstte altyazı şeridi).
- [ ] Silero VAD Akıllı Parçalama (Cümle ortası kesilmeleri önleyen 400ms sessizlik tabanlı dinamik konuşma ayrımı).
- [ ] Özel Fonetik Terim ve Kısaltma Sözlüğü (Sektörel ve teknik terimlerin tanıma doğruluğunu artıran kullanıcı sözlüğü).

### v2.0.0 — Kurumsal Konuşma Zekası ve Yerel Özet (Hedef Sürüm)
- [ ] Çapraz Dil Çevirisi (Türkçe konuşmaları gerçek zamanlı olarak İngilizce, Almanca, Fransızca ve İspanyolca altyazıya dönüştürme).
- [ ] Kalıcı Konuşmacı Tanıma (Kullanıcı ses profillerini kaydederek gelecekteki kayıtlarda konuşmacıları otomatik eşleme).
- [ ] Dahili Video Altyazı Gömücü (Oluşturulan altyazıları doğrudan videoya gömülü hardsub olarak render etme).
- [ ] Sıfır Bulut Yerel LLM Toplantı Özeti (İnternet bağlantısı olmadan çalışan yerel yapay zeka ile toplantı notları, kararlar ve eylem planı çıkarma).

---

## Lisans ve Zorunlu Görsel Atıf Şartı

Bu proje **MIT Lisansı ve Zorunlu Görsel Atıf Şartı** altında lisanslanmıştır.

### Zorunlu Görsel Atıf Kuralı:
Bu projenin kaynak kodunu, bileşenlerini, algoritmalarını veya türevlerini kendi projelerinde veya uygulamalarında kullanan tüm kişi ve kuruluşlar, oluşturdukları kullanıcı arayüzünün **ana ekranında veya üst menü çubuğunda** doğrudan görülebilecek şekilde bu depoya ([https://github.com/The0Sanity/Speech-To-Text](https://github.com/The0Sanity/Speech-To-Text)) tıklanabilir görsel bir atıf (bağlantı veya rozet) yerleştirmekle yükümlüdür.

Bu atfı alt menülere gizlemek, görünmez yapmak veya kaldırmak lisans şartlarının ihlali anlamına gelir.

Ayrıntılı yasal şartlar için [LICENSE](LICENSE) belgesini inceleyebilirsiniz.  
Depo Adresi: [https://github.com/The0Sanity/Speech-To-Text](https://github.com/The0Sanity/Speech-To-Text)
