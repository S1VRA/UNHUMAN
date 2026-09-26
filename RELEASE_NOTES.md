# 🎉 NH Mod Tool v0.5.0

**"No, I'm not a Human"** için mod yöneticisi — artık modern, güvenli ve profesyonel.

v0.4.0'ın üstüne oturduk, arayüzü baştan yaptık, güvenliği sertleştirdik, paketlemeyi değiştirdik. İşte karşınızda: **v0.5.0**.

---

## ✨ Öne Çıkanlar

### 🎨 Modern Arayüz
Karanlık tema baştan tasarlandı — ttkbootstrap (darkly) üzerine kurulu, sade ve okunaklı. Butonlar artık anlamlı: birincil eylem mavi, tehlike kırmızı, ikincil gri. Fareyle üzerine geldiğinde tepki veriyor, klavyeyle gezilebiliyor. Yüksek DPI ekranlarda artık bulanık değil.

### 🌍 Tam Türkçe Desteği
Arayüzün her cümlesi çevrildi. İngilizce ve Türkçe arasında geçiş yapabilirsiniz — anahtarlar birebir eşleşiyor, yarım çeviri yok.

### 🛡️ Güvenlik Sıkılaştırması
- **Zip Slip koruması** — kötü niyetli ZIP'ler oyun klasörünüzün dışına dosya yazamaz
- **Zip bomb tespiti** — şişirilmiş arşivler otomatik reddedilir
- **Magic byte doğrulaması** — `.png` uzantılı bir `.exe` geçemez
- **Silme güvenlik kapısı** — yönetilen klasörlerin dışına `rmtree` çalışmaz
- **Ayar şeması doğrulaması** — bozuk `settings.json` uygulamayı çökertmez

### 📦 Profesyonel Kurulum
Artık ZIP çıkarmaya gerek yok. Setup.exe'yi indirin, çift tıklayın, bitti. Başlat menüsüne kısayol, Denetim Masası'nda "Program Ekle/Kaldır" kaydı, otomatik uninstaller — hepsi çalışıyor.

---

## 🔧 Neler Değişti

**Eklendi**
- Global exception handler (`sys`, `threading`, `Tk` callback'leri)
- `%APPDATA%\NHModTool\logs` altında döner log dosyası (5 MB × 3)
- Pencere boyutu ve konumu hatırlanıyor
- Boş durum ekranları — ne yapacağınızı söyleyen yönlendirmeler
- `theme.py` — tüm renk, tipografi ve boşluk token'ları tek yerde

**Değişti**
- PyInstaller → **Nuitka** (antivirüs false positive'lerini azaltır)
- Elle yazılmış ttk stilleri → **ttkbootstrap (darkly)**
- Tüm kullanıcı metinleri `locales/{en,tr}.json`'a taşındı

**Düzeltildi**
- Uzun süren işlemlerde arayüz donması
- Türkçe modundayken İngilizce metin sızması
- Bozuk ayar dosyası uygulamayı çökertiyordu → şimdi `.bak` yedeği alıp varsayılana dönüyor

**Silindi**
- Ölü kod (`preview_in_label` gölge tanımı, kullanılmayan `_make_checkerboard`, `DATA_DIR_LOW`)
- Eski `apply_obsidian_theme` fonksiyonu
- PyInstaller spec dosyası

---

## 📥 Kurulum

1. Aşağıdan **`NHModTool_v0.5.0_Setup.exe`** dosyasını indirin (28.6 MB)
2. Çift tıklayın, kurulum sihirbazını takip edin
3. Başlat menüsünden **NH Mod Tool**'u açın

Windows SmartScreen ilk seferde uyarabilir. **"Ek bilgi" → "Yine de çalıştır"** ile geçebilirsiniz — uygulama kod imzalı değil, bu normaldir.

---

## ⚠️ Bilinen Sorunlar

- **Microsoft Defender** bazen kurulum dosyasını şüpheli olarak işaretleyebilir. Bu, imzasız tüm Python uygulamalarında görülen bir **yanlış alarmdır.** Kaynak kodu açık, kendiniz derleyebilirsiniz.
- İlk açılışta ayarlarınız yeniden düzenlenebilir — `%APPDATA%\NHModTool`'a taşındı.

---

## 📋 Doğrulama

**SHA-256:**   **3931FCAC6F75208D9AF4E7951A9C90ED9229D67340C7D2CE38A4BCCACB99B64F**

İndirdiğiniz dosyanın bütünlüğünü doğrulamak için:

```powershell
Get-FileHash NHModTool_v0.5.0_Setup.exe -Algorithm SHA256
``` 

---

## 🙏 Teşekkürler

Bu sürüm, v0.4.0'dan bu yana geçen sürede gelen geri bildirimlerle şekillendi. Hata bildirimi, öneri ve testleriniz için teşekkürler.

Sorun mu buldunuz? GitHub Issues üzerinden bildirin.   
Tam değişiklik geçmişi: CHANGELOG.md
Kaynak kodu: github.com/S1VRA/UNHUMAN 
