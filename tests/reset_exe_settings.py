import json, io, os

settings = os.path.join("dist", "data", "settings.json")
os.makedirs(os.path.dirname(settings), exist_ok=True)
data = {
    "assets": "C:\\Users\\mehmet\\AppData\\Games\\No, I'm not a Human\\NoImNotAHuman_Data\\sharedassets0.assets",
    "language": "en"
}
with io.open(settings, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print("EXE settings reset to en")
