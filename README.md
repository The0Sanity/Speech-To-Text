<div align="center">

[ Türkçe ](README.md) • [ English ](README.en.md)

# SesMetin Pro

### Windows için çevrimdışı Türkçe ses tanıma ve konuşmacı etiketleme

[![Sürüm](https://img.shields.io/github/v/release/The0Sanity/Speech-To-Text?color=2563EB&label=S%C3%BCr%C3%BCm)](https://github.com/The0Sanity/Speech-To-Text/releases)
[![Derleme](https://img.shields.io/github/actions/workflow/status/The0Sanity/Speech-To-Text/release.yml?branch=main&label=Derleme)](https://github.com/The0Sanity/Speech-To-Text/actions)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-0078D4)](https://github.com/The0Sanity/Speech-To-Text/releases)
[![Lisans](https://img.shields.io/badge/Lisans-MIT%20%2B%20G%C3%B6rsel%20At%C4%B1f-F59E0B)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-The0Sanity%2FSpeech--To--Text-181717?logo=github)](https://github.com/The0Sanity/Speech-To-Text)

</div>

---

## Ne yapar

SesMetin Pro, ses ve video dosyalarını ya da bir YouTube bağlantısını zaman
damgalı ve konuşmacı etiketli (X1, X2, ...) Türkçe metne dönüştürür. Metni
düzeltebilir ve dışa aktarabilirsiniz. Tanıma, OpenAI Whisper modelleriyle
(faster-whisper üzerinden) kendi bilgisayarınızda çalışır; ses ve metin
verileriniz hiçbir yere yüklenmez.

İnternet yalnızca üç iş için kullanılır: seçtiğiniz modelin ilk indirilmesi,
YouTube bağlantısı verdiğinizde sesin alınması ve GitHub'da yeni sürüm
denetimi.

## Özellikler

- **Metne dönüştürme:** Whisper Tiny, Base, Small, Medium, Large-v3 ve
  Large-v3-Turbo; işlemcide (INT8) veya NVIDIA ekran kartında. Modeller
  uygulama içinden indirilir ve silinir.
- **Konuşmacı etiketleri:** bölümler sese göre gruplanır ve X1, X2, ...
  olarak etiketlenir; konuşmacı adlarını değiştirebilirsiniz. Bu basit bir
  akustik kümelemedir ve doğruluğu ölçülmemiştir.
- **Türkçe sayı biçimlendirme:** söylenen sayılar, yüzdeler, para birimleri
  ve sıra sayıları rakamla yazılır ("yüzde yirmi beş", "%25" olur).
- **Girdi:** MP4, MP3, WAV, M4A, AAC, MKV, FLAC, OGG veya YouTube bağlantısı
  (`yt-dlp` ile). FFmpeg yoksa ilk açılışta indirilir.
- **Düzenleme:** arama, bul ve değiştir, konuşmacı adı değiştirme.
- **Dışa aktarma:** `.txt`, `.srt`, `.vtt`, `.json`, `.csv`, `.md` veya
  panoya kopyalama.
- **Güncelleme:** uygulama GitHub Releases'i denetler ve tek tıkla kendini
  günceller.

## Ölçülen doğruluk

FLEURS Türkçe test kümesinden 150 kayıtta, uygulamanın kendi işlem hattıyla
ölçülen kelime hata oranı (WER). Düşük olan daha iyidir.

| Model | v1.1.5 | v1.1.7 |
| :--- | :--- | :--- |
| Whisper Tiny | %67,38 | %41,07 |
| Whisper Small | %32,62 | %15,18 |

Diğer modeller ölçülmedi. FLEURS, tek konuşmacının okuduğu kısa cümlelerden
oluşur; röportaj, telefon sesi ve müzikte sonuçlar farklı olur. Yöntem, tüm
ölçümler ve sınırlar [docs/BENCHMARKS.md](docs/BENCHMARKS.md) belgesindedir.

## Kurulum

1. [GitHub Releases](https://github.com/The0Sanity/Speech-To-Text/releases)
   sayfasını açın.
2. `SpeechToText-Setup.exe` (kurulum) veya `SpeechToText.exe` (taşınabilir,
   kurulum gerektirmez) dosyasını indirin.
3. Çalıştırın.

> [!NOTE]
> **Windows SmartScreen:** yayın dosyaları Windows'un güvendiği bir
> sertifikayla imzalı değildir; bu yüzden ilk açılışta *"Windows kişisel
> bilgisayarınızı korudu"* uyarısı çıkar. **"Ek bilgi"** ve ardından
> **"Yine de çalıştır"** seçeneğine tıklayın. İndirdiğiniz dosyayı
> doğrulayabilmeniz için her yayında iki dosyanın SHA-256 değeri yer alır.

> [!IMPORTANT]
> **Önceki herhangi bir sürümden güncelleme:** bu sürümlerdeki dahili
> güncelleyici güvenilir çalışmıyor. v1.1.7 veya daha yeni bir sürümü bir
> kez elle indirin; sonrasında uygulama içi güncelleme çalışır. v1.1.6 olarak
> yayınlanan sürüm de buna dahildir: v1.1.5 kaynağından derlenmiştir ve
> kendini 1.1.5 olarak gösterir.

### Kaynak koddan çalıştırma

```powershell
git clone https://github.com/The0Sanity/Speech-To-Text.git
cd Speech-To-Text
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Testler: `python -m pytest tests`.

## "SesMetin" modelleri hakkında

v1.1.5'e kadar olan sürümler altı "SesMetin" modeli sunuyordu. Üç v2 model
dosyası, standart Whisper modelleriyle bayt bayt aynıdır (aynı SHA-256) ve üç
v1 deposu mevcut değildir; yani bu sürümler standart Whisper'ı başka bir adla
çalıştırıyordu. v1.1.7 bunları model listesinden kaldırır. Ayarlarınızda bu
adlardan biri varsa karşılık gelen Whisper modeli kullanılır ve daha önce
indirdiğiniz dosyalar yeniden kullanılır.

Bu proje için hazırlanan Türkçe veri kümeleri Hugging Face'te durmaktadır:

- [sesmetin-v2-prtk-speech-corpus](https://huggingface.co/datasets/The0Sanity/sesmetin-v2-prtk-speech-corpus)
- [sesmetin-v2-tdk-10m-corpus](https://huggingface.co/datasets/The0Sanity/sesmetin-v2-tdk-10m-corpus)
- [sesmetin-v2-speech-corpus](https://huggingface.co/datasets/The0Sanity/sesmetin-v2-speech-corpus)

Eğitim ve yayınlama betikleri `tools/` klasöründedir.

## Yol haritası

### Yayınlananlar
- [x] v1.0.4: ilk kararlı sürüm.
- [x] v1.0.7: ayarlar `%APPDATA%\SesMetinPro` altında saklanır.
- [x] v1.1.0: model yöneticisi, donanım algılama, kurulum sihirbazı.
- [x] v1.1.7: doğruluk düzeltmeleri, çalışan güncelleyici, dürüst model
  listesi, ölçülmüş başarım. Python uygulamasının son özellik sürümü.

### Sırada
- [ ] v2.0.0: uygulamanın Rust ve Tauri arayüzüyle yeniden yazılması. Aynı
  özellikler, yeni bir konuşmacı ayrıştırma modeli, imzalı tek tıkla
  güncelleme. Plan ve kabul ölçütleri [docs/PARITY.md](docs/PARITY.md) ve
  [docs/adr/0001-rewrite-app-in-rust.md](docs/adr/0001-rewrite-app-in-rust.md)
  belgelerindedir.

### Fikirler, takvime bağlı değil
- [ ] Birden çok dosya için toplu kuyruk.
- [ ] Canlı mikrofon ile metne dönüştürme.
- [ ] Özel sözlük.

Tüm geçmiş: [CHANGELOG.md](CHANGELOG.md).

## Lisans ve zorunlu görsel atıf şartı

Bu proje **MIT Lisansı ve Zorunlu Görsel Atıf Şartı** altında lisanslanmıştır.

Bu projenin kaynak kodunu, bileşenlerini veya algoritmalarını kendi
uygulamasında kullanan, gömen ya da değiştiren herkes, arayüzünün **ana
ekranında veya üst menü çubuğunda** bu depoya
([https://github.com/The0Sanity/Speech-To-Text](https://github.com/The0Sanity/Speech-To-Text))
**açıkça görünen, tıklanabilir bir atıf bağlantısı** bulundurmak zorundadır.

Bu görsel atfı gizlemek, görünmez yapmak veya kaldırmak lisans ihlalidir.

Tüm şartlar: [LICENSE](LICENSE).
Depo adresi: [https://github.com/The0Sanity/Speech-To-Text](https://github.com/The0Sanity/Speech-To-Text)
