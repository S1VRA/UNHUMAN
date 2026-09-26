<p align="center">
  <a href="https://github.com/S1VRA/UNHUMAN/releases"><img src="https://img.shields.io/badge/version-0.5.0-blue" alt="Version"></a>
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/python-3.14+-blue" alt="Python">
</p>

<h1 align="center">NH Mod Tool</h1>

<p align="center">
  A modern mod management tool for <b>"No, I'm not a Human"</b>, built with tkinter/ttk and ttkbootstrap (darkly theme).
</p>

---

## English

### What it does
- Replace in-game character images with your photos, one at a time
- Apply many ready-made character images from a ZIP at once
- Automatic backup before every change, restore anytime via Mod Manager
- English + Turkish interface

## Installation

### Windows Installer (Recommended)
1. Go to the [Releases page](https://github.com/S1VRA/UNHUMAN/releases)
2. Download `NHModTool_v0.5.0_Setup.exe`
3. Double-click and follow the setup wizard
4. A Start Menu shortcut will be created

### From Source (For Developers)
```bash
git clone https://github.com/S1VRA/UNHUMAN.git
cd UNHUMAN
pip install -r requirements.txt
python NHModTool.py
```

## Usage
1. Open **Settings** → select your game file (auto-detected via Scan)
2. **Photo Mods** → pick a character + a photo → Apply
3. Or **Photo Pack (ZIP)** → choose a ZIP → Apply ZIP to Game

## Antivirus Notice
NH Mod Tool is an unsigned open-source application. Some antivirus engines (especially Microsoft Defender) may flag Python-packaged EXEs as suspicious. This is a **false positive** affecting all PyInstaller/Nuitka apps. The source code is fully available for review.

## FAQ

### Windows SmartScreen warning
This is normal for unsigned apps. Windows shows "Windows protected your PC". Click "More info" → "Run anyway".

### Does the game file get modified?
Yes, but every change creates an automatic `.bak` backup next to the game file. Mod Manager can restore it anytime.

### Which game version is supported?
"No, I'm not a Human" — any Unity-based version with a `sharedassets0.assets` file.

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md)

## License
MIT — see [LICENSE](LICENSE)

## Contact
Use [GitHub Issues](https://github.com/S1VRA/UNHUMAN/issues) for questions and bug reports.

---

## Türkçe

### Ne işe yarar
- Oyun içi karakter görsellerini fotoğraflarınızla tek tek değiştirin
- Birçok hazır karakter görselini ZIP'ten tek seferde uygulayın
- Her değişiklikten önce otomatik yedek, Mod Yöneticisi'nden her zaman geri yükleyin
- İngilizce + Türkçe arayüz

## Kurulum

### Windows Kurulum Dosyası (Önerilen)
1. [Releases sayfasına](https://github.com/S1VRA/UNHUMAN/releases) gidin
2. `NHModTool_v0.5.0_Setup.exe` indirin
3. Çift tıklayın, kurulum sihirbazını takip edin
4. Başlat menüsüne kısayol eklenir

### Kaynaktan Çalıştırma (Geliştiriciler için)
```bash
git clone https://github.com/S1VRA/UNHUMAN.git
cd UNHUMAN
pip install -r requirements.txt
python NHModTool.py
```

## Kullanım
1. **Ayarlar** → oyun dosyanızı seçin (Tarama ile otomatik bulunur)
2. **Fotoğraf Modları** → karakter + fotoğraf seçin → Uygula
3. ya da **Fotoğraf Paketi (ZIP)** → ZIP seçin → ZIP'i Oyuna Uygula

## Antivirüs Uyarısı
NH Mod Tool imzasız bir açık kaynak uygulamadır. Bazı antivirüs motorları (özellikle Microsoft Defender) Python ile paketlenmiş EXE'leri yanlışlıkla şüpheli olarak işaretleyebilir. Bu bir **false positive**'dir. Kaynak kod tamamen açıktır.

## SSS

### Windows SmartScreen uyarısı görüyorum
Bu normaldir. "Windows bilgisayarınızı korudu" uyarısı çıkar. "Ek bilgi" → "Yine de çalıştır" diyerek devam edebilirsiniz.

### Oyun dosyası değişiyor mu?
Evet, ama her değişiklikten önce otomatik `.bak` yedeği alınır. Mod Yöneticisi sekmesinden her zaman geri yükleyebilirsiniz.

### Hangi oyun sürümü destekleniyor?
"No, I'm not a Human" — Unity tabanlı, `sharedassets0.assets` dosyası olan tüm sürümler.

## Katkıda Bulunma
Bkz. [CONTRIBUTING.md](CONTRIBUTING.md)

## Lisans
MIT — bkz. [LICENSE](LICENSE)

## İletişim
Sorular ve hata bildirimleri için [GitHub Issues](https://github.com/S1VRA/UNHUMAN/issues) kullanın.