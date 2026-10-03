<p align="center">
  <img src="assets/banner.png" alt="NH Mod Tool" width="100%">
</p>

<p align="center">
  <a href="https://github.com/S1VRA/UNHUMAN/releases"><img src="https://img.shields.io/badge/Version-0.5.0-blue" alt="Version"></a>
  <img src="https://img.shields.io/badge/Python-3.14+-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Platform-Windows-lightgrey" alt="Platform">
</p>

<h1 align="center">NH Mod Tool</h1>

<p align="center">
  A modern mod manager for <b>"No, I'm not a Human"</b>, built with Python + tkinter/ttk and ttkbootstrap (darkly theme).
</p>

---

## English

### Features

- **Photo Mods** — Replace in-game character textures with your own photos, one character at a time.
- **Transparent Photos** — PNGs with a cut-out background keep their alpha channel in-game. Formats that physically have no alpha (e.g. DXT1) are detected and logged.
- **Photo Pack (ZIP)** — Apply many character images at once from a `.zip` archive.
- **Mod Manager** — Backups, restore points, and cache cleanup. Every apply keeps an automatic `.bak` next to the game file.
- **Game Status** — Real-time game file detection and integrity verification.
- **Bilingual UI** — Full English and Turkish localization with key parity.
- **Security Hardened** — ZIP Slip protection, ZIP bomb detection, magic-byte validation, and path-traversal guards.
- **Safe Writes** — Every modification is verified before commit; nothing is overwritten without a backup.

### Installation

#### Option 1: Installer (Recommended)

1. Go to the [Releases page](https://github.com/S1VRA/UNHUMAN/releases)
2. Download `NHModTool_v0.5.0_Setup.exe`
3. Run the installer and follow the wizard
4. Launch **NH Mod Tool** from the Start Menu

#### Option 2: Run from Source (For Developers)

```bash
git clone https://github.com/S1VRA/UNHUMAN.git
cd UNHUMAN
pip install -r requirements.txt
python NHModTool.py
```

### Usage

1. Open **Settings** and point the tool at your game's `sharedassets0.assets` file.
2. **Photo Mods** → pick a character → pick a photo → Apply.
3. Or **Photo Pack (ZIP)** → choose a ZIP → Apply ZIP to Game.

Close the game before applying mods — the game file cannot be written while
the game holds it open. Full walkthrough in [docs/USAGE.md](docs/USAGE.md).

### Building

Two steps. The script only covers the first one.

```bash
# 1) Nuitka standalone build (folder mode) + SHA-256 of the exe
build_release.bat

# 2) Inno Setup installer (requires Inno Setup 6)
iscc installer.iss
```

Step 1 produces `dist/NHModTool.dist/NHModTool.exe` **plus its dependency
folders** — this is a folder distribution, not a single-file executable.
Step 2 produces `dist/NHModTool_v0.5.0_Setup.exe`.

PyInstaller is no longer used; it was removed in v0.5.0 because the compiled
output triggered antivirus false positives.

---

## Türkçe

### Özellikler

- **Fotoğraf Modları** — Oyun içi karakter dokularını kendi fotoğraflarınızla tek tek değiştirin.
- **Şeffaf Fotoğraflar** — Arka planı şeffaf olan PNG'ler alpha kanalını oyun içinde korur. Alpha kanalı olmayan formatlar (ör. DXT1) tespit edilip loglanır.
- **Fotoğraf Paketi (ZIP)** — Bir `.zip` arşivinden çok sayıda karakter görselini tek seferde uygulayın.
- **Mod Yöneticisi** — Yedekler, geri yükleme noktaları ve önbellek temizleme. Her uygulama oyun dosyasının yanına otomatik `.bak` bırakır.
- **Oyun Durumu** — Gerçek zamanlı oyun dosyası tespiti ve bütünlük doğrulaması.
- **İki Dilli Arayüz** — Tam İngilizce ve Türkçe yerelleştirme, anahtar paritesi korunur.
- **Güvenlik Sıkılaştırıldı** — ZIP Slip koruması, ZIP bomb tespiti, magic byte doğrulaması ve yol geçişi korumaları.
- **Güvenli Yazma** — Her değişiklik onaylanmadan önce doğrulanır; yedeksiz hiçbir şey üzerine yazılmaz.

### Kurulum

#### Seçenek 1: Kurulum Dosyası (Önerilen)

1. [Releases sayfasına](https://github.com/S1VRA/UNHUMAN/releases) gidin
2. `NHModTool_v0.5.0_Setup.exe` indirin
3. Kurulum sihirbazını çalıştırın
4. Başlat menüsünden **NH Mod Tool**'u açın

#### Seçenek 2: Kaynaktan Çalıştırma (Geliştiriciler için)

```bash
git clone https://github.com/S1VRA/UNHUMAN.git
cd UNHUMAN
pip install -r requirements.txt
python NHModTool.py
```

### Kullanım

1. **Ayarlar** → oyun dosyanızı seçin (Tarama ile otomatik bulunur)
2. **Fotoğraf Modları** → karakter + fotoğraf seçin → Uygula
3. ya da **Fotoğraf Paketi (ZIP)** → ZIP seçin → ZIP'i Oyuna Uygula

Mod uygulamadan önce oyunu kapatın — oyun dosyası açıkken üzerine yazılamaz.
Ayrıntılı anlatım: [docs/USAGE.md](docs/USAGE.md)

### Derleme

İki adım gerekir. Betik yalnızca ilk adımı yapar.

```bash
# 1) Nuitka standalone derlemesi (klasör modu) + EXE SHA-256
build_release.bat

# 2) Inno Setup kurulum dosyası (Inno Setup 6 gerekir)
iscc installer.iss
```

1. adım `dist/NHModTool.dist/NHModTool.exe` dosyasını **ve bağımlılık
klasörlerini** üretir — bu tek dosyalık bir EXE değil, klasör dağıtımıdır.
2. adım `dist/NHModTool_v0.5.0_Setup.exe` dosyasını üretir.

PyInstaller artık kullanılmıyor; derlenmiş çıktı antivirüs yanlış
alarmlarına yol açtığı için v0.5.0'da kaldırıldı.

---

## Antivirus / Antivirüs

⚠️ **False Positives / Yanlış Alarmlar**

Some ML-based antivirus engines may flag the installer as malware. This is a false positive that affects all unsigned Python-packaged applications. The source code is fully available for inspection — you can build the installer yourself.

Bazı yapay zeka tabanlı antivirüs motorları kurulum dosyasını yanlışlıkla şüpheli olarak işaretleyebilir. Bu, imzasız tüm Python uygulamalarını etkileyen bir yanlış alarmdır. Kaynak kodun tamamı açıktır — kurulum dosyasını kendiniz derleyebilirsiniz.

---

## Troubleshooting / Sorun Giderme

| Symptom / Belirti | What to do / Yapılacak |
|-------------------|------------------------|
| Injection fails / Uygulama başarısız | Close the running game and retry. / Oyunu kapatıp tekrar deneyin. |
| Old photo still in game / Eski fotoğraf duruyor | Restore a backup from **Mod Manager**, then re-apply. / **Mod Yöneticisi**'nden bir yedek geri yükleyip yeniden uygulayın. |
| Photo looks fully opaque / Fotoğraf tamamen opak | The texture format has no alpha channel — see [docs/USAGE.md](docs/USAGE.md). / Dokunun formatında alpha kanalı yok — [docs/USAGE.md](docs/USAGE.md). |
| Game not detected / Oyun bulunamadı | **Settings → Browse…** and select `sharedassets0.assets`. / **Ayarlar → Gözat…** ile dosyayı seçin. |

**Logs / Loglar:**

| Install type / Kurulum | Log location / Log konumu |
|---|---|
| Installer / Kurulum dosyası | `%APPDATA%\NHModTool\logs\app.log` |
| From source / Kaynaktan | `<repo>\data\logs\app.log` |

Rotates at 1 MB and keeps two backups. Set `NHMODTOOL_DEBUG=1` for a verbose log.
1 MB'de döner, 2 yedek tutar. Ayrıntılı log için `NHMODTOOL_DEBUG=1`.

Always attach the log to bug reports. / Hata bildirimine log dosyasını mutlaka ekleyin.

---

## Screenshots / Ekran Görüntüleri

The project banner is at the top of this page. UI screenshots have not been
captured yet; the capture checklist and naming convention live in
[docs/images/README.md](docs/images/README.md).

---

## Links / Bağlantılar

- 🐛 [Report a bug / Hata bildir](https://github.com/S1VRA/UNHUMAN/issues/new?template=bug_report.md)
- 💡 [Request a feature / Özellik isteği](https://github.com/S1VRA/UNHUMAN/issues/new?template=feature_request.md)
- 🔒 [Security policy / Güvenlik politikası](SECURITY.md)
- 📜 [Changelog / Değişiklikler](CHANGELOG.md)
- 📘 [Installation guide / Kurulum kılavuzu](docs/INSTALL.md)
- 📖 [Usage guide / Kullanım kılavuzu](docs/USAGE.md)
- 🏗️ [Architecture / Mimari](docs/ARCHITECTURE.md)

---

## License / Lisans

MIT License. See [LICENSE](LICENSE) for details.
MIT Lisansı. Ayrıntılar için [LICENSE](LICENSE) dosyasına bakın.

## Contributing / Katkıda Bulunma

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
Yönergeler için [CONTRIBUTING.md](CONTRIBUTING.md) dosyasına bakın.