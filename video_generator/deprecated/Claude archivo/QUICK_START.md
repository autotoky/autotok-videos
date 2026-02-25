# 🚀 QUICK START - SISTEMA v3.5

**Guía rápida para empezar en 10 minutos.**

---

## ✅ **PRE-REQUISITOS**

- [x] Python 3.7+ instalado
- [x] FFmpeg instalado y en PATH
- [x] Google Drive Desktop sincronizado
- [x] Credenciales Google Sheets (`credentials.json`)

---

## 📦 **1. PREPARAR MATERIAL (5 min)**

### **En Google Drive:**

```
G:\Mi unidad\recursos_videos\
└── proyector_magcubic\
    ├── hooks\          ← 10+ clips .mp4 (3-6 segundos)
    ├── brolls\         ← 20+ clips .mp4 (nombrados A_*.mp4, B_*.mp4, etc.)
    └── audios\         ← 3+ audios .mp3 (nombrados bof1_*.mp3)
```

**Nombrar archivos:**
- Hooks: `hook_boom.mp4` o `hook_patas_START2.mp4`
- Brolls: `A_producto.mp4`, `B_mano.mp4`, `C_fondo.mp4`
- Audios: `bof1_andaluz.mp3`, `bof1_chavalita.mp3`, `bof1_motivada.mp3`

**Esperar sincronización Drive** ⏳

---

## 📝 **2. CREAR BOF (3 min)**

### **Duplicar plantilla:**
```bash
cp PLANTILLA_BOF.json bof_proyector_magcubic.json
```

### **Editar `bof_proyector_magcubic.json`:**
```json
{
  "deal_math": "2x1 + Envío gratis",
  "guion_audio": "¿Buscas proyector 4K? Este proyector tiene resolución 4K, Android integrado y altavoces potentes. Ahora 2x1 con envío gratis. Link en bio.",
  "hashtags": "#proyector #4k #ofertas #gadget #tech #viral",
  "url_producto": "https://amzn.to/tu-link",
  "variantes": [
    {"overlay_line1": "PROYECTOR 4K", "overlay_line2": "2X1 HOY", "seo_text": "Proyector 4K oferta 2x1 🔥"},
    {"overlay_line1": "ENVÍO GRATIS", "overlay_line2": "HOY", "seo_text": "Proyector envío gratis ⚡"},
    {"overlay_line1": "ANDROID TV", "overlay_line2": "INTEGRADO", "seo_text": "Proyector Android incluido 📺"},
    {"overlay_line1": "ALTAVOCES", "overlay_line2": "POTENTES", "seo_text": "Proyector audio premium 🔊"},
    {"overlay_line1": "OFERTA", "overlay_line2": "BRUTAL", "seo_text": "Proyector oferta increíble 💥"}
  ]
}
```

---

## 🎯 **3. GENERAR VIDEOS (2 min)**

```bash
# Importar BOF
python scripts/import_bof.py proyector_magcubic bof_proyector_magcubic.json

# Escanear material
python scripts/scan_material.py proyector_magcubic

# Generar 20 videos
python main.py --producto proyector_magcubic --batch 20 --cuenta lotopdevicky
```

**Output:** 20 videos en `videos_generados_py/lotopdevicky/`

---

## 📅 **4. PROGRAMAR (1 min)**

```bash
python programador.py --cuenta lotopdevicky --dias 7 --test
```

**Resultado:**
- Videos en `calendario/DD-MM-YYYY/`
- Añadidos a Google Sheet TEST
- Listos para subir a TikTok

---

## ✅ **¡LISTO!**

**Has generado 20 videos únicos en menos de 10 minutos.**

---

## 🔄 **PRÓXIMOS PASOS**

### **Subir a TikTok Studio:**
1. Abrir Sheet TEST
2. Copiar info de videos programados
3. Subir videos a TikTok Studio
4. Cambiar estado en Sheet: `En Calendario` → `Borrador`

### **Sincronizar:**
```bash
python mover_videos.py --cuenta lotopdevicky --sync --test
```

### **Programar en TikTok:**
1. Programar videos en TikTok
2. Cambiar estado en Sheet: `Borrador` → `Programado`
3. Sincronizar de nuevo

---

## 📚 **MÁS INFO**

- **README.md** - Documentación completa
- **CHULETA_COMANDOS.md** - Referencia rápida
- **PLANTILLA_BOF.json** - Template para nuevos BOFs

---

**¡A producir contenido!** 🎬✨
