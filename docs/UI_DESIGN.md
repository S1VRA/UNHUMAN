# NH Mod Tool — UI Tasarım Dokümanı

Sürüm hedefi: v0.5.0
Yaklaşım: Modern masaüstü, koyu ağırlıklı, düşük gürültü, içerik odaklı; her ekranda tek bir birincil eylem ve çift tema (Dark varsayılan, Light seçilebilir).

Bu doküman v0.5.0 kod tabanından çıkarılmış envantere dayanır. Verilen tüm token, ölçü ve kural değerleri uygulama kararıdır; kod fazı bunları birebir uygular.

---

## 1. Tasarım İlkeleri

1. **Boş alan kıymetlidir** — her ekranda birincil eylem tam olarak bir tanedir; geri kalan butonlar ikincil veya üçüncül hiyerarşidedir.
2. **Token-tabanlı renk** — hiçbir renk widget gövdesinde yazılmaz; tüm renkler theme token'larından gelir, böylece Dark/Light geçişi tek noktadan olur.
3. **Kademeli hiyerarşi** — yüzeyler (base/surface/elevated/overlay) ile metin (primary/secondary/muted) arasında her zaman belgelenmiş WCAG oranı korunur.
4. **Durum her zaman birden fazla kanalda** — başarı/hata yalnızca renkle değil, ikon + metin + renk üçlüsüyle iletilir.
5. **Klavye her yerde** — her ekran fare kullanılmadan tam erişilir; odak göstergesi her odaklanabilir bileşende görünür.
6. **Uzun işlem asla sessiz değildir** — 300 ms üzeri her işlem progress + iptal sunar; iptal butonu işlem çubuğunun sağındadır.
7. **Yıkıcı eylem önce onay, sonra geri bildirim** — sil/geri yükleme işlemleri yalnızca ikincil onayla çalışır ve sonucu toast ile bildirir.

---

## 2. Mevcut UI Envanteri (koddan çıkarıldı)

Kod: `NHModTool.py` (v0.5.0) + `theme.py`. Pencere: `root.geometry("1260x820")`, `root.minsize(1000, 680)`, `tk scaling 1.15`, başlık `"No, I'm not a Human - Mod Tool • v0.5.0"`.

| Ekran | Fonksiyon | Bileşenler | Sorunlar |
|---|---|---|---|
| Ana çerçeve | `build_shell` (satır 1266) | Sol kenar çubuğu 200px sabit (tk.Frame + Label tabanlı nav), alt bilgi çubuğu (footer), `menu_status` etiketi | Nav `pack_propagate(False)` ile sabit piksel; nav "butonları" gerçek buton değil (Label); `_game_badge` `place()` ile sabit piksel koordinat (menü genişliğine bağımlı); "S1VRA · NH Mod Tool v0.5.0" brand metni footer'da |
| Home | `create_home` (1354) | `_page_shell` başlık+gövde kartı; durum şeridi (4 adet sol-sağ düğme: Open game folder, Restore backup, Clear cache, Data folder…); 2x2 emoji kart grid'i; alttan ipucu etiketi | Kartlarda emoji ikon (🖼 📦 🛠 📈); `Title.TLabel` stili theme.py'ye bağlı; `place()` yok ama grid + `pack` iç içe; kart hover durumu yok (cursor hand2 var) |
| Photos | `create_photos`/`build_photos` (1460/1467) | Arama kutusu (🔍 emoji), "show masks" checkbox (hardcoded EN), zoom satırı (- / % / + / 1:1, 🔋 emoji), sol: Canvas galeri + dikey scrollbar + indeterminate progressbar; sağ panel 340px sabit (IN GAME (CURRENT) + NEW IMAGE + "Photo…" + APPLY TO GAME) | Başlık "Photo Mods" hardcoded EN; "show masks" hardcoded EN; sağ panel `pack_propagate(False)` 340px sabit; zoom ikonu 🔋 (piller) yanlış anlam; galeri boş durumu canvas üstü metin; yüklenme hâlinde progress metinsiz |
| Photo Pack (ZIP) | `create_zip_page` (2096) | "Choose ZIP…" + readonly Entry; tk.Listbox (EXTENDED) + scrollbar; indeterminate progressbar; bilgi paneli (hardcoded **Türkçe**); "No ZIP loaded." durumu; APPLY ZIP TO GAME | Bilgi paneli 2124–2135 satırlarında locale'den bağımsız Türkçe yazılıyor (parite ihlali); başlık hardcoded EN; Listbox yerine modern liste/table öneriliyor |
| Manager | `create_manager` (2257) | "BACK UP GAME FILE NOW" (Vurgu) + açıklama; listbox (SINGLE) + scrollbar; Restore (Tehlike) / Copy / Delete / Open folder; önbellek satırı | `_add_listbox_hover` ile manuel hover; restore butonu da "Backup" uygular; durum etiketleri "✓ Restored:" hardcoded EN |
| Status | `create_status` (2444) | Salt-okunur tk.Text + scrollbar; Verify game file / Open game folder / Refresh | Başlık ve tüm satırlar hardcoded EN; text widget yerine düzenli liste/satır görünümü öneriliyor |
| Settings | `create_settings` (2524) | Oyun dosyası satırı (Browse…, Scan again), dil Combobox (en/tr), ayar bilgi Text'i, "Restore original game file from backup" (Tehlike), indeterminate status_bar | Alt başlık ve butonlar hardcoded EN; tema seçici yok (yalnızca koyu tema); aynı anda iki ayrı progressbar kullanımı |

Kod genelinde gözlemler:

- **İki paralel tema sistemi**: `theme.py#apply_obsidian_theme` (İngilizce stil adları: `Card.TFrame`, `Muted.TLabel`, `Accent.TButton`…) main() satır 2749'dan çağrılıyor; `NHModTool.py#apply_theme` (Türkçe stil adları: `Kart.TFrame`, `Baslik.TLabel`, `Vurgu.TButton`…) `App.__init__` satır 1111'den çağrılıyor. İkisi de `theme_use("clam")` yapıyor ve renk paletleri **drifte sahip** (ör. card `#16181F` vs `#161820`, accent `#4F8CFF` vs `#3B82F6`). `Title.TLabel` sadece theme.py'de tanımlı; `Muted.TLabel` theme.py'de. Bu iki sistemi tek token kaynağında birleştirmek zorunlu.
- **`print()` ihlali**: `theme.py` satır 14 `print(f"Theme warning: ...")` — repo kuralına aykırı (kod fazında `_cli_out` desenine taşınacak).
- **Klavye kısayolları**: yalnızca zoom için var (`<Control-plus>`, `<Control-KP_Add>`, `<Control-minus>`, `<Control-KP_Subtract>`, `<Control-0>`, `<MouseWheel>` galeri üzerinde).
- **Treeview hiç kullanılmıyor**; listeler `tk.Listbox`, `tk.Text`, `tk.Canvas` üzerinde.
- **İkonlar emoji** (🔍 🔋 ℹ 🖼 📦 🛠 📈) ve tamamen işletim sistemine bağlı; tutarlı görünmez.
- **Hover**: `_add_hover_effect` (satır 324) ve `_add_listbox_hover` (330) manuel `bind` ile; ttk state map kullanılmıyor.
- **Dialog kullanımı**: çok sayıda hardcoded EN `messagebox.*` çağrısı (ör. satır 1426, 1454, 1947, 2027, 2083, 2230, 2319, 2687) — başlıklar ve metinler locale'den gelmiyor.
- **Birincil eylemler**: Photos "APPLY TO GAME", ZIP "APPLY ZIP TO GAME", Manager "BACK UP GAME FILE NOW" — metinler hardcoded, stilleme Vurgu.TButton üzerinden.

---

## 3. Renk Paleti (Design Tokens)

İki palet: **Dark** (varsayılan) ve **Light**. Tüm değerler HEX'tir. Oranlar WCAG 2.1 relative luminance ile hesaplanmış ve yanında işaretlenmiştir; hesaplanmayan yer yoktur.

### 3.1 Dark (varsayılan)

| Token | HEX | Açıklama |
|---|---|---|
| `bg.base` | `#0D0E12` | Pencere kökü, kenar çubuğu |
| `bg.surface` | `#16181F` | Kartlar, paneller |
| `bg.elevated` | `#1C1F28` | Açılırlar, popover, hover yüzeyi |
| `bg.overlay` | `#22252E` | Modal arka planı / devre dışı dolgular |
| `text.primary` | `#F3F4F6` | Ana metin (base üstü 17.53:1, surface üstü 16.11:1 — AAA) |
| `text.secondary` | `#C5C9D4` | Alt başlıklar, gövde metni (base 11.65:1, surface 10.70:1 — AAA) |
| `text.muted` | `#8A90A2` | Etiketler, ipuçları, tablo başlıkları (base 6.05:1, surface 5.56:1 — AA) |
| `text.inverse` | `#FFFFFF` | Solid buton ve seçili nav metni |
| `border.subtle` | `#2A2D3A` | Kart iç ayırıcılar |
| `border.default` | `#2E3140` | Kart/input çerçevesi |
| `border.focus` | `#60A5FA` | Odak halkası (surface üstü 6.97:1 — AA) |
| `accent.primary` | `#3B82F6` | Bağlantı metni, ikonlar, odak (base üstü 5.24:1 — AA) |
| `accent.hover` | `#60A5FA` | Bağlantı/ikon hover (base üstü 7.59:1 — AAA) |
| `accent.pressed` | `#1D4ED8` | Basılı durum |
| `accent.subtle` | `#1E2A44` | Seçili nav hover zemin, vurgu çipleri |
| `accent.solid` | `#2563EB` | Birincil buton dolgusu (beyaz metin 5.17:1 — AA) |
| `state.success.text` | `#3DDC84` | Başarı (kendi bg üstü 7.54:1 — AAA) |
| `state.success.bg` | `#123524` | Başarı çipi/badge zemini |
| `state.warning.text` | `#FFB020` | Uyarı (kendi bg üstü 7.57:1 — AAA) |
| `state.warning.bg` | `#3A2A0E` | Uyarı çipi zemini |
| `state.danger.text` | `#FF5C5C` | Hata metni (kendi bg üstü 5.37:1 — AA) |
| `state.danger.bg` | `#3A1416` | Hata çipi zemini |
| `state.danger.solid` | `#B91C1C` | Tehlike buton dolgusu (beyaz metin 6.47:1 — AA) |
| `state.info.text` | `#60A5FA` | Bilgi (kendi bg üstü 6.14:1 — AA) |
| `state.info.bg` | `#12243D` | Bilgi çipi zemini |
| `disabled.bg` | `#22252E` | Devre dışı bileşen zemini |
| `disabled.text` | `#59607A` | Devre dışı metin (bilinçli AA altı, etkileşimsiz) |

### 3.2 Light

| Token | HEX | Açıklama |
|---|---|---|
| `bg.base` | `#F6F7F9` | Pencere kökü, kenar çubuğu |
| `bg.surface` | `#FFFFFF` | Kartlar, paneller |
| `bg.elevated` | `#F0F1F4` | Açılırlar, hover yüzeyi |
| `bg.overlay` | `#EAECF0` | Modal zemin / devre dışı dolgu |
| `text.primary` | `#111318` | Ana metin (base 17.33:1, surface 18.58:1 — AAA) |
| `text.secondary` | `#444A57` | Alt başlıklar (base 8.29:1, surface 8.89:1 — AAA) |
| `text.muted` | `#6B7280` | Etiketler (base 4.51:1, surface 4.83:1 — AA) |
| `text.inverse` | `#FFFFFF` | Solid buton ve seçili nav metni |
| `border.subtle` | `#E3E5EA` | Kart iç ayırıcılar |
| `border.default` | `#C9CED8` | Kart/input çerçevesi (surface üstü 1.58:1 — yalnızca ayırıcı; gerekli alanlarda bg.base kullanılır) |
| `border.focus` | `#2563EB` | Odak halkası (surface üstü 5.17:1 — AA) |
| `accent.primary` | `#2563EB` | Bağlantı, ikonlar (surface üstü 5.17:1 — AA) |
| `accent.hover` | `#1D4ED8` | Bağlantı/ikon hover (surface üstü 6.70:1 — AA) |
| `accent.pressed` | `#1E40AF` | Basılı durum |
| `accent.subtle` | `#E7EEFC` | Seçili nav hover zemin, çipler |
| `accent.solid` | `#2563EB` | Birincil buton dolgusu (beyaz metin 5.17:1 — AA) |
| `state.success.text` | `#166534` | Başarı metni (kendi bg üstü 6.38:1 — AA) |
| `state.success.bg` | `#E7F6EC` | Başarı çipi zemini |
| `state.warning.text` | `#92400E` | Uyarı metni (kendi bg üstü 6.46:1 — AA) |
| `state.warning.bg` | `#FFF3E0` | Uyarı çipi zemini |
| `state.danger.text` | `#991B1B` | Hata metni (kendi bg üstü 7.18:1 — AA) |
| `state.danger.bg` | `#FDEAEA` | Hata çipi zemini |
| `state.danger.solid` | `#B91C1C` | Tehlike buton dolgusu (beyaz metin 6.47:1 — AA) |
| `state.info.text` | `#1E40AF` | Bilgi metni (kendi bg üstü 7.49:1 — AA) |
| `state.info.bg` | `#E7EEFC` | Bilgi çipi zemini |
| `disabled.bg` | `#F0F1F4` | Devre dışı zemin |
| `disabled.text` | `#9AA0AC` | Devre dışı metin (bilinçli AA altı) |

**Kontrast kuralı**: `text.muted` yalnızca bilgi amaçlı etiketlerde kullanılır; buton, link ve form etiketlerinde `text.secondary` veya üzeri zorunludur. `text.inverse` yalnızca `accent.solid`, `state.danger.solid` ve seçili nav zemini üzerinde kullanılır.

---

## 4. Tipografi

Tek aile: **Segoe UI** (Windows sistem fontu, 8 ağırlık). Monospace özel durumda **Consolas**. Tk'de nokta (pt) ölçektir; tüm değerler pt'dir ve `tk scaling 1.15` ile çalışır.

| Tokens | Boyut | Ağırlık | Satır aralığı | Kullanım |
|---|---|---|---|---|
| `type.display` | 24 | Bold | 1.4 (≈34 px) | Sadece Home merchandising başlığı |
| `type.h1` | 17 | Bold | 1.35 | Sayfa başlığı (`Baslik` karşılığı) |
| `type.h2` | 13 | Semibold | 1.35 | Panel içi blok başlıkları (IN GAME, NEW IMAGE) |
| `type.h3` | 11 | Semibold | 1.3 | Liste grubu başlıkları |
| `type.body` | 10 | Regular | 1.35 | Gövde metni, butonlar |
| `type.small` | 9 | Regular | 1.3 | Yardımcı metinler, ipuçları |
| `type.caption` | 8 | Regular | 1.3 | Footer, state çipi metni |
| `type.mono` | 10 | Regular | 1.3 | Yol, MD5, zaman damgası, log metni |

Kurallar:

- Sayfa başlığı her ekranda tek `h1`; altında tek satır `type.small` / muted açıklama.
- Tablo ve liste hücreleri `type.body`; sütun başlıkları `type.small` + semibold + muted.
- Input/buton metni asla `small` altına inmez.
- Yol ve hash değerleri daima `type.mono`; gerektiğinde `wraplength` ile kesilir.

---

## 5. Boşluk ve Yerleşim Sistemi

- **Temel birim**: 4px. Tüm boşluklar 4'ün katıdır.
- **Tokenlar**: `xs=4`, `sm=8`, `md=12`, `lg=16`, `xl=24`, `2xl=32`, `3xl=40`.
- **Pencere**: varsayılan 1260x820, `minsize` 1000x680, `tk scaling 1.15` (temel olarak kalır; DPI farkı `root.tk.call("tk", "scaling")` ile okunur).
- **Çerçeve**: sol kenar çubuğu **208px** sabit (200px + 8px iç boşluk), içerik alanı geri kalan genişlik. İçerik kenar boşlukları `lg=16` (dikey) / `xl=24` (yatay).
- **Grid**: Home nesneleri 4 kolon (2x2 kartlar korunur, `rowconfigure`/`columnconfigure` weight=1). Photos galerisi Canvas'ta akışkan hücreler; sağ panel **360px** sabit (340 yerine — ikon halkası ve badge'ler için). ZIP listesi ve Status/Settings metinleri tam genişlik.
- **Kenar boşlukları (padding) standardı**: kart içi `lg=16`; panel üst boşluk `sm=8`; buton grupları arası `md=12`; birincil buton ile içerik arası `xl=24`.
- **Yükseklik**: buton `28px` (içerik yüksekliği 20px + 4px padding), liste satırı `30px`, nav öğesi `36px`, galeri hücresi `CELL_W x CELL_H` mevcut sabitler korunur.

---

## 6. İkon Dili

- **Kaynak**: Emoji değil. **Segoe MDL2 Assets** (Windows 10) / **Segoe Fluent Icons** (Windows 11) font glifleri, `tk.Label`/`tk.Button` içinde `font=("Segoe Fluent Icons" veya "Segoe MDL2 Assets", size)` ile çizilir. Uygulama Windows-only olduğu için ek bağımlılık yok, PyInstaller ile sorunsuz.
- **Boyut**: 16 (buton içi), 20 (kart/panel başlığı), 24 (boş durum ikonları, büyük eylemler).
- **Renk**: varsayılan `text.secondary`; vurgularda `accent.primary`; state ikonlarında `state.*.text`; hover'da `accent.hover`. Asla `text.inverse` üzerinde ikon kullanılmaz.
- **Hangi ekranda hangi ikonlar** (glif adları — Segoe Fluent/MDL2 kod noktaları):
  - Kenar çubuğu: Home `E80F`, Photos `EB9F`, Photo Pack `E8B5` (ZIP), Manager `E7B8`, Status `E9D9`, Settings `E713`.
  - Home kartları: Photo Mods `EB9F`, Photo Pack `E8B5`, Mod Manager `E7B8`, Game Status `E9D9`; kart sağ ok `E76B`.
  - Photos: arama `E721`, zoom `E7EF`/`E738` (sıfırlama `E93A`), "in game" `E73E`, "new image" `E91B`, uygula `E768` (kontrol işareti).
  - ZIP: ZIP `E8B5`, bilgi `E946`, uygula `E768`.
  - Manager: yedekle `E104`, geri yükle `E777`, sil `E74D`, klasör `E838`, önbellek `E8B7`.
  - Status: doğrula `E9D9`, yenile `E72C`.
  - Settings: dil `E765`, gözat `E838`, geri yükle `E777`.
  - Durum çipleri: başarı `E73E`, uyarı `E7BA`, hata `EA39`, bilgi `E946`.
- **İkon butonu**: sadece ikon; 32x32px, `text.secondary`; tooltip için `<ToolTip>` eşdeğeri (tk `tooltip` widget'ı) ile etiket metni.

---

## 7. Bileşen Kütüphanesi

Style isimleri ttk `StyleName.StateName` desenindedir ve **tek kaynak** olan token yapısına bağlanır.

### 7.1 Primary Button (`Primary.TButton`)
- Amaç: ekranın tek birincil eylemi (APPLY TO GAME, APPLY ZIP TO GAME, BACK UP NOW).
- Görünüm: dolgu `accent.solid`, metin `text.inverse` semibold `type.body`, köşe yarıçapı 4px, `padding=(20, 10)`.
- Durumlar: normal `accent.solid` (beyaz 5.17:1); hover `#1D4ED8` (6.70:1); pressed `#1E40AF` (8.72:1); focus `border.focus` halka; disabled `disabled.bg` + `disabled.text`.

### 7.2 Secondary Button (`Secondary.TButton`)
- Dolgu `bg.surface`, metin `text.primary`, `border.default` 1px çerçeve.
- Durumlar: hover `bg.elevated`; pressed `bg.overlay`; focus halka; disabled standardı.
- Tüm sayfa yardımcı aksiyonları (Open folder, Refresh, Clear cache) bu stildedir.

### 7.3 Danger Button (`Danger.TButton`)
- Dolgu `state.danger.solid`, metin `text.inverse` (6.47:1).
- Yalnızca yıkıcı eylemler: Restore backup, Delete, Restore original. Kolayca dokunulmayacak konumda (işlem satırının sol ucu).
- Durumlar: hover `#A11C1C` (doğrulama gerekli olmayacak şekilde `accent` kuralıyla koyu zincir), pressed `#7F1515`, disabled standardı, focus halka.

### 7.4 Icon Button (`Icon.TButton`)
- 32x32px, `text.secondary` ikon, arka plan `transparent`/`bg.base`.
- Durumlar: hover `bg.surface`, pressed `bg.overlay`, focus halka, disabled `disabled.text`. Tooltip zorunlu.

### 7.5 Text Input (`Input.TEntry`)
- `fieldbackground bg.surface`, metin `text.primary`, `border.default` 1px, `padding=8`, imleç `insertcolor text.primary`.
- Durumlar: focus `border.focus` 2px `focuscolor`; disabled `bg.overlay` + `disabled.text`. Ghost placeholder yok — zorunlu alanlarda üst etiket `type.small` muted.

### 7.6 Search Input (`Search.TEntry`)
- Photos arama; solda 16px arama ikonu, sağda metin boşken kaldır butonu (X `E711`).
- Debounce 200ms (mevcut) korunur; boş durumda "No matching characters" galeri boş durumu gösterilir.

### 7.7 Card (`Card.TFrame`)
- `bg.surface` + `border.subtle` 1px, köşe 4px, iç boşluk `lg=16`.
- Home kartları etkileşimlidir: hover `bg.elevated` + `border.default`; odaklanabilir (Enter ile `show_page`); sağ kenarda `→` ikonu `accent.primary`.

### 7.8 List / Table Row
- `Listbox` yerine **`ttk.Treeview`** (headless satır modu) veya satır `tk.Frame`: satır yüksekliği 30px, hover `bg.elevated`, seçili `accent.subtle` + `text.primary` (12.98:1 — AAA), ayrıcı `border.subtle`.
- ZIP listesi EXTENDED seçim destekler; Manager listesi SINGLE.

### 7.9 Tab / Nav Item (`Nav.TButton`)
- Kenar çubuğu öğesi 208px genişliğinde, 36px yüksekliğinde, solda 16px ikon + `lg=16` boşluk + metin.
- Normal: metin `text.muted`; hover `bg.surface` + `text.primary`; **seçili**: `accent.solid` zemin + `text.inverse` (5.17:1) + sol kenarda 4px `border.focus` çizgi.

### 7.10 Dialog (`Dialog.Toplevel`)
- Modal `Toplevel`; zemin `bg.surface`, `border.focus` 1px çerçeve, gölge yerine `bg.overlay` perde. Başlık `h2`, gövde `type.body`, buton sırası sağa hizalı.
- Birincil onay sağda, ikincil sola. Esc = kapatma. `grab_set` korunur.
- Traceback'ler asla böyle gösterilmez; yalnızca özet + log yolu + GitHub Issues (mevcut `_show_error_dialog` davranışı).

### 7.11 Toast / Status Bar Message
- Alt bilgi çubuğu (`Toast.TLabel`): sol `loader_lbl` pozisyonunda; metin `type.small`. Başarı `state.success.text` + ikon; hata `state.danger.text` + ikon; bilgi `text.muted`.
- Toast süresi 2500ms; uzun durumlar bar metni olarak kalır (bir sonraki durum gelene kadar).

### 7.12 Progress Bar (`Primary.Horizontal.TProgressbar`)
- Indeterminate: 4px yükseklik, `accent.solid`, zemin `bg.overlay`.
- Determinate (karar): ZIP doğrulama/uygulama için paylaşımlı `status_bar`; metin eşlik eder. İptal butonu çubuğun sağında `Secondary`.

### 7.13 Empty State block (`Empty.TFrame`)
- 24px `state.info` ikonu + `type.body` metin + isteğe bağlı tek `Secondary` buton.
- Yerleri: Photos galerisi (arama eşleşmesi yok), ZIP listesi (dosya seçilmedi), Manager (yedek yok), Home (oyun bulunamadı).

### 7.14 Badge / Chip (`Chip.TLabel`)
- `state.*.bg` zemin + `state.*.text` `type.caption`, `lg=16` yatay boşluk, 2px dikey.
- Kullanım: "Game found" rozeti (Home/kenar çubuğu), ZIP eşleşme özeti, Status özetleri.

---

## 8. Ekran Ekran Tasarım

### 8.1 Home

- **Amaç**: oyun durumunu göstermek ve dört alt sayfayı tek tıklamayla açmak.
- **Birincil eylem**: yok — Home bir girdi sayfasıdır; birincil eylem, oyun bulunamadıysa "Scan again" (`Secondary` kararı), bulunduysa kartlardan hedef seçimi.
- **Tel-çizim**:
```
┌────────────────────────────────────────────────────────────┐
│ ▮ NH Mod Tool                    oyun durumu çipi [bulundu] │
│ Nav: Home   Photos   ZIP   Manager   Status   Settings     │
├────────────────────────────────────────────────────────────┤
│  Welcome                                    [Game: ✓ yolu] │
│  Açıklama cümlesi                                4 ikincil │
│  ┌──────────────┐  ┌──────────────┐                     │
│  │ [ikon] Photo │  │ [ikon] Photo │                     │
│  │ Mods         │  │ Pack         │                     │
│  │ açıklama  →  │  │ açıklama  →  │  2x2 kart grid      │
│  └──────────────┘  └──────────────┘                     │
│  ┌──────────────┐  ┌──────────────┐                     │
│  │ [ikon] Mod   │  │ [ikon] Game  │                     │
│  │ Manager      │  │ Status       │                     │
│  └──────────────┘  └──────────────┘                     │
│  İpucu satırı (caption)                                  │
├────────────────────────────────────────────────────────────┤
│ durum metni                      NH Mod Tool · v0.5.0    │
└────────────────────────────────────────────────────────────┘
```
- **Bileşenler**: `Nav` (kenar çubuğu), `Card.TFrame` x4, `Secondary` butonları (durum şeridi), `Chip` (game found), `Caption` ipucu.
- **Boş durum**: oyun bulunamadı → şeritte `Scanning for the game…` + `Scan again` ikincil butonu; kartlar yine de görünür.
- **Yükleniyor**: tarama sırasında footer'da indeterminate çubuk (mevcut `loader_lbl` deseni).
- **Hata durumu**: oyun dosyası bozuksa şeritte `state.danger` çipi + `Verify` önerisi.
- **Klavye**: `F5` yenile; kart odak + `Enter` ile açılır.

### 8.2 Photos

- **Amaç**: karakter galerisinde arama/zoom yapıp tek fotoğrafı tek tıklamayla oyuna uygulamak.
- **Birincil eylem**: `APPLY TO GAME` (sağ panel altı) — seçim yokken disabled.
- **Tel-çizim**:
```
┌────────────────────────────────────────────────────────────┐
│  Photo Mods                                      [uygula]  │
│  Alt açıklama (small)                                     │
│ ├ [🔍 arama] [ ] show masks │ − 100% + 1:1 ▓             │
│ ├───────────── galeri ───────┼── sağ panel 360px ────────┤
│ │ (Canvas akışkan hücrelar)  │ IN GAME (CURRENT)         │
│ │   + dikey scrollbar        │  [önceki foto]            │
│ │   boş pilot: "search none" │ File/format/size meta      │
│ │                            │ ─────────────             │
│ │                            │ NEW IMAGE                 │
│ │                            │  [yeni foto]              │
│ │                            │ [yol]  [Photo…]           │
│ │ zoom ipucu caption         │ [   APPLY TO GAME   ]     │
└────────────────────────────────────────────────────────────┘
```
- **Bileşenler**: `Search.TEntry`, `Checkbutton` (show masks), `Icon.TButton` (zoom −/+ /1:1), Canvas+`Treeview`-boş durum, sağ paneller `Card.TFrame`, `Primary` button.
- **Boş durum**: arama eşleşmesi yok → canvas ortasında `Empty` block "No matching characters".
- **Yükleniyor**: galeri üstünde 4px indeterminate çubuk + `Scanning…` metni.
- **Hata durumu**: seçili fotoğraf açılamazsa sağ panelde `state.danger` çipi + ikon; `messagebox` yerine inline hata.
- **Klavye**: mevcutlar korunur — `Ctrl+Plus`/`Ctrl+Minus`/`Ctrl+0` zoom, `Ctrl+wheel` zoom; yeni: `Alt+1` arama odağı, `Enter` seçili karakteri seçer, `Ctrl+Return` uygular.

### 8.3 Photo Pack (ZIP)

- **Amaç**: hazır ZIP'i seçip tüm eşleşen görselleri doğrulanmış şekilde toplu uygulamak.
- **Birincil eylem**: `APPLY ZIP TO GAME` — ZIP yüklenmeden disabled.
- **Tel-çizim**:
```
┌────────────────────────────────────────────────────────────┐
│  Photo Pack (ZIP)                                [uygula]  │
│  [zıp yolu]  [Choose ZIP…]  [ZIP ikonu]                   │
│ ┌──────────────── içerik listesi ─────────────┐            │
│ │  satır  [matching çip]        [önizleme]    │            │
│ │  satır  [matching çip]        [önizleme]    │            │
│ │  ...  (Treeview/hücre ızgarası)             │            │
│ └─────────────────────────────────────────────┘            │
│  ℹ info paneli (locale'den, 4 adım)                       │
│  durum metni   [   APPLY ZIP TO GAME   ]  ▓ progress      │
└────────────────────────────────────────────────────────────┘
```
- **Bileşenler**: `Input.TEntry` (readonly) + `Secondary` (Choose ZIP), `Chip` (eşleşme sayısı), liste `Treeview`, `Info` çipi paneli, `Primary` buton, `Progress`.
- **Boş durum**: ZIP yok → "No ZIP loaded." + Choose ZIP butonu.
- **Yükleniyor**: `Scanning ZIP…` + indeterminate çubuk.
- **Hata durumu**: ZIP reddi (Zip Slip/Bomb) → inline `state.danger` çipi, dosya açılmaz.
- **Klavye**: `Ctrl+O` ZIP seç; liste ok tuşlarıyla gezilir; `Ctrl+Return` uygular.

### 8.4 Manager

- **Amaç**: yedekleri listelemek, geri yüklemek, kopyalamak, silmek ve önbelleği yönetmek.
- **Birincil eylem**: `BACK UP GAME FILE NOW`.
- **Tel-çizim**:
```
┌────────────────────────────────────────────────────────────┐
│  Mod Manager                                               │
│  [BACK UP GAME FILE NOW] açıklama (small)                  │
│ ┌────────── yedek listesi ──────────┐        [Refresh]     │
│ │  [satır] tsp-bak                  │                      │
│ │  [satır seçili] tsp2-bak          │                      │
│ │  ...                              │                      │
│ └───────────────────────────────────┘                      │
│  durum etiketi (✓ Restored / empty)                        │
│ [Restore] [Copy to backups] [Delete]            [Open]     │
│  Cache: <hücre sayısı>  [Clear cache]  [Data folder]      │
└────────────────────────────────────────────────────────────┘
```
- **Bileşenler**: `Primary` (backup now), `Treeview` liste, `Danger` (Restore/Delete), `Secondary` (Copy/Open/Clear), `Chip` (cache count), `Empty` (yedek yok).
- **Boş durum**: "No backups found yet. The first photo / ZIP apply creates one automatically." (locale'den) + açıklama.
- **Yükleniyor**: `status_bar` indeterminate; seçim tabanlı işlemler hızlı olduğu için progress yok.
- **Hata durumu**: geri yükleme reddi → `state.danger` çipi üstte; `messagebox` yerine inline.
- **Klavye**: `Insert` yedek al; `Delete` seçili yedeği siler (onayla); `Ctrl+R` yenile; ok tuşları liste.

### 8.5 Status

- **Amaç**: yapılan değişikliklerin zaman çizelgesi ve oyun dosyasının doğrulanma durumu.
- **Birincil eylem**: `Verify game file` (doğrulama butonu, ekranda tek).
- **Tel-çizim**:
```
┌────────────────────────────────────────────────────────────┐
│  Game Status                                  [Refresh]    │
│  [Verify game file]  [Open game folder]                   │
│ ┌──────────── rapor ──────────────┐                        │
│  Game file                        │                         │
│  • C:\…\sharedassets0.assets      │                         │
│  • Size … | modified …            │                         │
│  Mod history (n actions)          │                         │
│  • [chip] 2026-09-21 12:04  apply 3 item(s) …              │
│  Backups: n found …               │                         │
│ └─────────────────────────────────┘                        │
└────────────────────────────────────────────────────────────┘
```
- **Bileşenler**: `Primary` (Verify), `Secondary` (Refresh/Open folder), `Chip` listesi, satır tabanlı `Treeview` (tk.Text yerine).
- **Boş durum**: oyun dosyası yok ve geçmiş boş → "Your game file is untouched." mesajı.
- **Yükleniyor**: Verify sırasında `status_bar` indeterminate + "Verifying…".
- **Hata durumu**: doğrulama farkı → satır `state.danger` renkli + `Chip` "modified".
- **Klavye**: `F5` yenile; `Enter` seçili satırda doğrula.

### 8.6 Settings

- **Amaç**: dil, tema, oyun dosyası yolu ve geri yükleme ayarları.
- **Birincil eylem**: yok — ayar grubu sayfası; tüm değişiklikler anında kaydedilir; tek vurgulu buton "Restore original game file from backup" (`Danger`).
- **Tel-çizim**:
```
┌────────────────────────────────────────────────────────────┐
│  Settings                                                  │
│  Game detection & file locations                           │
│  [yol …]  [Browse…] [Scan again]                           │
│  Language: [en ▾]  (restart hint small)                    │
│  Theme:    [ Dark ▾ | Light ]   ← yeni                      │
│  ┌──────── ayar bilgisi ────────┐                          │
│  │ Selected: …                  │                          │
│  │ Other candidates …           │                          │
│  └──────────────────────────────┘                          │
│  [Restore original game file from backup]                  │
│  ▓ status_bar  durum_metni                                │
└────────────────────────────────────────────────────────────┘
```
- **Bileşenler**: `Secondary` (Browse/Scan again), `Combobox` (dil, tema), `Input` (yol), `Danger` (restore), `Text` bilgi paneli, `Progress`.
- **Boş durum**: yol yok → placeholder metni "Game data file (sharedassets0.assets)" + uyarı.
- **Yükleniyor**: tarama sırasında `status_bar` indeterminate + "Scanning…".
- **Hata durumu**: bozuk dock değil — ayar doğrulama uyarıları `settings.corrected` çipinde özetlenir.
- **Klavye**: dil/tema `Combobox` ok tuşları; `Ctrl+B` Browse; `Ctrl+S` yok (otomatik kayıt).

---

## 9. Etkileşim ve Animasyon

- **Pencere açılış/kapanış**: animasyon yok; açılışta `root.update_idletasks()` ile ilk kare toplanır. Kapanışta onay yalnızca o anda işlem çalışıyorsa (`Exit confirm`).
- **Sekme geçişi**: animasyon yok — `pack_forget`/`pack` anında geçiş; `show_page` sonrası `after(50, on_page_shown)` korunur.
- **Buton hover gecikmesi**: 0ms — ttk state map anında uygulanır (`_add_hover_effect` bind deseni kaldırılır).
- **Toast süresi**: 2500ms; ardından footer durum metni tekrar `text.muted`'a döner.
- **Uzun işlemlerde iptal**: ZIP uygulama ve oyun taraması `status_bar` + iptal `Secondary` butonu (çubuk sağında); iptal iş parçacığı bayrağı `self.busy` ile zaten var olan kilit desenine bağlanır.
- **Yıkıcı işlem onay deseni**: Delete backup, Restore (her iki yer), Restore original → `Dialog` (askyesno deseni): ayrıntı metni + `Danger` onay + `Cancel`. ZIP/photo uygulama değiştirilebilir sayım gösterir ve yine onaylar (mevcut 2027/2230 korunur, metinleri locale'den).

---

## 10. Erişilebilirlik

- **Klavye navigasyonu**:
  - `Tab` / `Shift+Tab`: odak sırası (sol→sağ, üst→alt).
  - `Enter`: seçili eylemi çalıştır (kart, buton, nav öğesi).
  - `Esc`: dialog kapat; arama temizle.
  - `F5` / `Ctrl+R`: geçerli sayfayı yenile.
  - `Ctrl+O`: geçerli sayfaya uygun dosya seç (ZIP / Photo / Assets).
  - `Ctrl++` / `Ctrl+-` / `Ctrl+0`: galeri zoom (mevcut, korunur).
  - `Alt+1`..`Alt+6`: sayfa geçişi (kenar çubuğu sırası).
  - `Ctrl+Return`: birincil eylem (APPLY…).
- **Focus göstergesi**: her odaklanabilir bileşende `border.focus` 2px dış halka; gizli odak yok. Canvas galerisi `takefocus=1` ile mevcut ve halkalı kalır.
- **Kontrast**: tüm normal metin `AA` (≥4.5:1), ana metin çiftleri `AAA` (≥7:1); yalnızca bilinçli devre dışı metin AA altıdır.
- **Ekran okuyucu notu**: tkinter `accessible` özelliği sınırlı; kritik butonlara `widget.configure(class_=...)` veya yardımcı `ToolTip` ile etiket verilir; galeri hücrelerine `_name` ile karakter adı; nav öğelerine "Page: X" öneki. Window API'si üzerinden setitle değil, `ttk` bileşen metinleriyle.
- **Renk körlüğü**: state'lerde yalnızca renk kullanılmaz — her `state.*` çipi ikon + metin içerir; seçili nav öğesinde sol kenar çizgisi + metin değişimi; hover'da renk + `cursor="hand2"` birlikte.

---

## 11. Refactor İçin Uygulama Notları

Bu bölüm FAZ 3 (mimari) ve FAZ 4b+ (kod) yol haritasıdır.

- **theme.py'de tutulacak token'lar** (tek kaynak): bölüm 3'teki tüm HEX değerleri `DARK_TOKENS`/`LIGHT_TOKENS` sözlükleri; `FONT`, `type.*` boyutları; `spacing.*` birimleri; `CELL_W`/`CELL_H` taşınır.
- **Yeni modüller** (mevcut tek dosya mimarisi korunarak, aşamalı):
  - `nhmodtool/gui/tokens.py` — token sözlükleri + `color(key)` yardımcısı.
  - `nhmodtool/gui/theme.py` — `apply_theme(root, palette)`; ttk stil adlarını token'dan üretir (mevcut theme.py'nin yerini alır).
  - `nhmodtool/gui/widgets/button.py` — Primary/Second/Danger/Icon ttk fabrikaları.
  - `nhmodtool/gui/widgets/inputs.py` — Input/Search/Combobox fabrikaları.
  - `nhmodtool/gui/widgets/feedback.py` — Toast, Chip, Empty, Progress yardımcıları.
  - `nhmodtool/gui/dialogs.py` — `ask_confirm`, `error_dialog` (mevcut `_show_error_dialog` deseni).
- **ttk.Style stil isimleri** (tek standart): `Primary.TButton`, `Secondary.TButton`, `Danger.TButton`, `Icon.TButton`, `Input.TEntry`, `Search.TEntry`, `Card.TFrame`, `Nav.TButton`, `Chip.TLabel`, `Empty.TFrame`, `Dialog.Toplevel`, `Toast.TLabel`, `Primary.Horizontal.TProgressbar`, `List.Treeview`. Eski `Kart/Baslik/Soluk/Bilgi/Tehlike/Vurgu/Altbaslik` isimleri bu isimlere **eşlenir ve kaldırılır**.
- **Değiştirilecek eski kod**:
  - `theme.py#apply_obsidian_theme` ve `NHModTool.py#apply_theme` → tek `gui/theme.py#apply_theme(root, palette)`.
  - `NHModTool.py#_add_hover_effect` (324) ve `_add_listbox_hover` (330) → ttk `style.map` state'lerine.
  - `NHModTool.py#build_shell` (1266) nav → `Nav.TButton`; footer "S1VRA · …" brand dizesi tek karar noktasında (bkz. handoff notu).
  - `create_zip_page` (2096) bilgi paneli 2124–2135 → `t("photo_pack.howto_*")` locale anahtarları.
  - `create_status` (2444) tk.Text → satır tabanlı liste bileşeni.
  - Listbox kullanımları (2108, 2274) → `Treeview` satır stili.
  - `_show_error_dialog` (134) dialog text'i → bölüm 7.10 standartları (içerik değişmez).
- **Geriye dönük uyumluluk**: `settings.json` anahtarları (`assets`, `photo_dir`, `language`, `zoom`, `theme`, `backup_interval_minutes`) korunur; yalnızca yeni `"theme": "dark" | "light"` anahtarı `validate_settings` şemasına eklenir (varsayılan `"dark"`). Eski stil adlarını kullanan dış theme bağımlılığı yok.

---

## 12. Kabul Kriterleri (kod aşamasında test edilecek)

- [ ] Her ekranda tam olarak bir birincil eylem
- [ ] Hiçbir renk hardcoded değil, hepsi `gui/tokens.py`'den
- [ ] ttk.Style tabanlı stil sistemi kullanılıyor; `style.map` ile durumlar tanımlı
- [ ] Her buton normal/hover/pressed/focus/disabled durumuna sahip
- [ ] Klavye ile tüm ekranlar kullanılabiliyor (bölüm 10 kısayolları)
- [ ] Kontrast hedef: normal metin AA, ana metinler AAA
- [ ] `settings.json` `"theme": "light"` ile Light palet uygulanır ve kalıcıdır
- [ ] Boş durum block'ları: Photos, ZIP, Manager, Home tanımlı içerikle
- [ ] Uzun işlemler progress + iptal gösteriyor (tarama, ZIP uygulama)
- [ ] Traceback kullanıcıya gösterilmiyor; yalnızca özet + log yolu + GitHub Issues
- [ ] ZIP bilgi paneli ve tüm `messagebox.*` metinleri locale'den okunuyor (EN/TR parite)

---

=== HANDOFF ===
TAMAMLANAN: docs/UI_DESIGN.md oluşturuldu (v0.5.0 hedefi; 12 bölüm + token tabloları + WCAG kontrast oranları hesaplandı ve yazıldı). Envanter koddan birebir çıkarıldı (build_shell, create_home/photos/zip/manager/status/settings, theme.py, apply_theme, messagebox, kısayollar). Kod değişmedi.
DEĞİŞEN DOSYALAR: (kod değişmedi; yalnızca yeni doküman)
YENİ DOSYALAR: docs/UI_DESIGN.md
SİLİNEN DOSYALAR: (yok)
YARIM KALAN: (yok)
KEŞFEDİLEN SORUNLAR: (1) İki paralel tema sistemi (theme.py İngilizce stil adları + NHModTool.py Türkçe stil adları, farklı paletler, çift `theme_use("clam")`) — birleştirme kararı bölüm 11'de. (2) theme.py satır 14 `print()` — repo `print()` yasağına aykırı, kod fazında `_cli_out`'a taşınmalı. (3) ZIP bilgi paneli (NHModTool.py 2124–2135) locale'den bağımsız **Türkçe** sabit yazıyor; `photo_pack.howto_*` anahtarları locales'te var ama kod kullanmıyor — EN modda da Türkçe görünür. (4) Footer "S1VRA · NH Mod Tool v0.5.0" — github.com/S1VRA/UNHUMAN sahibinin kullanıcı adı; iletişim bilgisi değildir (e-posta/link yok), doküman "NH Mod Tool · v0.5.0" olarak nötrleştirdi — repo politikası onayı "doğrulama gerekiyor". (5) `state.danger.hover`/`state.danger.pressed` alt tonları (`#A11C1C`, `#7F1515`) dokümanda somut verildi; tuş oranları beyaz metin üzerinde hesaplanmadı — "doğrulama gerekiyor". (6) Tema seçici önerildi; light palette mevcut kodda yok, `settings.json` şemasına `theme` anahtarı eklenmesi gerekecek.
YENİ i18n ANAHTARLARI GEREKLİ: photos.title, photos.subtitle, photos.search_placeholder, photos.show_masks, photos.zoom_tip, photos.in_game, photos.new_image, photos.pick_photo, photos.select_hint, photos.empty_gallery, photos.apply; zip.choose_zip, zip.empty, zip.scanning, zip.apply, zip.matches_summary; status.subtitle, status.verify, status.refresh, status.game_file, status.not_set, status.mod_history, status.no_history, status.backups, status.unchanged; settings.subtitle, settings.browse, settings.scan_again, settings.selected, settings.candidates, settings.file_exists, settings.restore_original, settings.restart_hint (mevcut), settings.theme, theme.dark, theme.light; common.busy, common.confirm_apply, common.confirm_delete, common.confirm_restore, common.confirm_exit, common.restored, common.copied, common.deleted, common.verify_ok, common.verify_modified, common.scanning; home.scanning, home.found, home.not_found; nav.tooltips; error.verify_failed (mevcut metinlerin t()'ye taşınması; dokümana göre ZIP bilgi paneli mevcut `photo_pack.howto_*`'a bağlanacak).
KIRILMIŞ OLABİLECEKLER: Bu oturumda kod değişmedi; hiçbir dosya etkilenmedi. Kod fazında stil adları yeniden adlandırılırken eski `Kart/Baslik/…` adlarını kullanan widget'lar güncellenmezse görünüm bozulabilir — bölüm 11 eşleme listesi uygulanmalı.
SONRAKİ ADIM ÖNERİSİ: Bölüm 11'deki token kaynağını kodda oluşturup iki tema sistemini tek `apply_theme` altında birleştirmek ve `settings.json` şemasına `theme` anahtarını eklemek.
=== HANDOFF SONU ===