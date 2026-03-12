// ═══════════════════════════════════════════════════════════
// AutoTok — TikTok Studio Network Interceptor v1.0
// ═══════════════════════════════════════════════════════════
// PASO 1: Pega esto en la consola (F12 → Console) en TikTok Studio > Posts
// PASO 2: Haz scroll manual hacia abajo, despacio, hasta el final
// PASO 3: Cuando llegues al fondo, escribe: AUTOTOK_DUMP()
// ═══════════════════════════════════════════════════════════

(() => {
  // Almacén global de videos capturados
  window.__AUTOTOK = window.__AUTOTOK || { videos: new Map(), rawResponses: [] };
  const store = window.__AUTOTOK;

  // ── Detectar si un objeto JSON parece un video/post de TikTok ──
  function extractVideos(data, source) {
    let found = 0;

    // Estrategia: buscar recursivamente arrays de objetos con campos típicos de posts
    function walk(obj, depth) {
      if (depth > 8 || !obj) return;

      if (Array.isArray(obj)) {
        // ¿Es un array de posts? Comprobar el primer elemento
        for (const item of obj) {
          if (item && typeof item === 'object') {
            // Campos típicos de un post de TikTok
            const postId = item.item_id || item.id || item.video_id || item.postId || item.post_id;
            const createTime = item.create_time || item.createTime || item.publish_time || item.publishTime;
            const title = item.title || item.desc || item.description || item.caption || '';

            // Si tiene un ID numérico largo (>15 dígitos) + algún otro campo, es un post
            if (postId && String(postId).length > 15 && (createTime || title)) {
              if (!store.videos.has(String(postId))) {
                // Extraer stats si las hay
                const stats = item.statistics || item.stats || {};
                const video_info = item.video || {};

                store.videos.set(String(postId), {
                  postId: String(postId),
                  title: String(title).substring(0, 120),
                  createTime: createTime || '',
                  // Intentar múltiples nombres para views/likes/etc
                  views: stats.play_count || stats.playCount || stats.views || stats.view_count || item.play_count || 0,
                  likes: stats.digg_count || stats.diggCount || stats.likes || stats.like_count || item.digg_count || 0,
                  comments: stats.comment_count || stats.commentCount || stats.comments || item.comment_count || 0,
                  shares: stats.share_count || stats.shareCount || stats.shares || item.share_count || 0,
                  duration: video_info.duration || item.duration || 0,
                  // Guardar objeto RAW completo para inspección
                  _raw: item,
                  _source: source,
                });
                found++;
              }
            }
          }
        }
      }

      // Seguir buscando en sub-objetos
      if (typeof obj === 'object' && !Array.isArray(obj)) {
        for (const key of Object.keys(obj)) {
          walk(obj[key], depth + 1);
        }
      }
    }

    walk(data, 0);
    return found;
  }

  // ── Patch fetch ──
  const originalFetch = window.fetch;
  window.fetch = async function(...args) {
    const response = await originalFetch.apply(this, args);

    try {
      const url = typeof args[0] === 'string' ? args[0] : args[0]?.url || '';

      // Solo interceptar respuestas JSON de TikTok
      if (url.includes('tiktok.com') || url.startsWith('/')) {
        const clone = response.clone();
        clone.json().then(data => {
          const prevCount = store.videos.size;
          const found = extractVideos(data, `fetch:${url.substring(0, 100)}`);
          if (found > 0) {
            console.log(`🎯 +${found} videos (total: ${store.videos.size}) ← ${url.substring(0, 80)}`);
          }
          // Guardar respuestas que contenían datos útiles
          if (found > 0) {
            store.rawResponses.push({
              url: url.substring(0, 200),
              videoCount: found,
              timestamp: new Date().toISOString(),
              dataKeys: Object.keys(data).join(','),
            });
          }
        }).catch(() => {}); // No es JSON, ignorar
      }
    } catch (e) {}

    return response;
  };

  // ── Patch XMLHttpRequest ──
  const originalXHROpen = XMLHttpRequest.prototype.open;
  const originalXHRSend = XMLHttpRequest.prototype.send;

  XMLHttpRequest.prototype.open = function(method, url, ...rest) {
    this.__autotok_url = url;
    return originalXHROpen.call(this, method, url, ...rest);
  };

  XMLHttpRequest.prototype.send = function(...args) {
    this.addEventListener('load', function() {
      try {
        const url = this.__autotok_url || '';
        if (url.includes('tiktok.com') || url.startsWith('/')) {
          const data = JSON.parse(this.responseText);
          const found = extractVideos(data, `xhr:${url.substring(0, 100)}`);
          if (found > 0) {
            console.log(`🎯 +${found} videos (total: ${store.videos.size}) ← XHR ${url.substring(0, 80)}`);
            store.rawResponses.push({
              url: url.substring(0, 200),
              videoCount: found,
              timestamp: new Date().toISOString(),
            });
          }
        }
      } catch (e) {}
    });
    return originalXHRSend.apply(this, args);
  };

  // ── Comando para ver estado ──
  window.AUTOTOK_STATUS = () => {
    console.log(`\n📊 AutoTok Interceptor — ${store.videos.size} videos capturados`);
    console.log(`   Respuestas interceptadas: ${store.rawResponses.length}`);
    if (store.rawResponses.length > 0) {
      console.log('   Últimas fuentes:');
      store.rawResponses.slice(-5).forEach(r => {
        console.log(`     ${r.timestamp} | +${r.videoCount} | ${r.url.substring(0, 70)}`);
      });
    }
    return store.videos.size;
  };

  // ── Comando para volcar resultados ──
  window.AUTOTOK_DUMP = () => {
    const videos = Array.from(store.videos.values());

    if (videos.length === 0) {
      console.log('❌ No hay videos capturados. ¿Has hecho scroll en la página de Posts?');
      console.log('   Si no se captura nada, prueba AUTOTOK_DEBUG() para ver qué pasa.');
      return;
    }

    // Ordenar por createTime descendente
    videos.sort((a, b) => {
      const ta = typeof a.createTime === 'number' ? a.createTime : 0;
      const tb = typeof b.createTime === 'number' ? b.createTime : 0;
      return tb - ta;
    });

    console.log(`\n✅ ¡LISTO! ${videos.length} videos capturados via API`);
    console.log('📊 Lista completa:\n');

    videos.forEach((v, i) => {
      // Formatear fecha
      let dateStr = '';
      if (typeof v.createTime === 'number' && v.createTime > 1000000000) {
        const d = new Date(v.createTime * 1000);
        dateStr = d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: undefined })
                  + ', ' + d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
      } else {
        dateStr = String(v.createTime);
      }

      console.log(`   ${String(i+1).padStart(4)}. ${v.postId} | ${dateStr.padEnd(18)} | ${String(v.views).padStart(8)} views | ${v.title.substring(0, 50)}`);
    });

    console.log(`\n📋 Click derecho en la consola → "Copy All" → pega en un .txt`);
    console.log(`   O usa: AUTOTOK_JSON() para copiar como JSON`);

    return videos.length;
  };

  // ── Comando para exportar JSON limpio ──
  window.AUTOTOK_JSON = () => {
    const videos = Array.from(store.videos.values()).map(v => ({
      postId: v.postId,
      title: v.title,
      createTime: v.createTime,
      views: v.views,
      likes: v.likes,
      comments: v.comments,
      shares: v.shares,
      duration: v.duration,
    }));

    videos.sort((a, b) => (b.createTime || 0) - (a.createTime || 0));

    const json = JSON.stringify(videos, null, 2);
    console.log(json);
    console.log(`\n📋 ${videos.length} videos. Click derecho → "Copy All" para copiar.`);
    return videos;
  };

  // ── Comando para ver campos RAW del primer video ──
  window.AUTOTOK_RAW = (n = 0) => {
    const videos = Array.from(store.videos.values());
    if (videos.length === 0) {
      console.log('❌ No hay videos capturados.');
      return;
    }
    const v = videos[n];
    console.log(`\n🔍 Video #${n} RAW — postId: ${v.postId}`);
    console.log('Campos disponibles:', Object.keys(v._raw).join(', '));
    console.log(JSON.stringify(v._raw, null, 2));
    return v._raw;
  };

  // ── Comando para exportar JSON completo con RAW ──
  window.AUTOTOK_FULL = () => {
    const videos = Array.from(store.videos.values()).map(v => v._raw);
    const blob = new Blob([JSON.stringify(videos, null, 2)], {type:'application/json'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'lotop_full.json';
    a.click();
    console.log(`📥 Descargando lotop_full.json con ${videos.length} videos (datos RAW completos)`);
  };

  // ── Debug: ver qué URLs se interceptan ──
  window.AUTOTOK_DEBUG = () => {
    console.log('🔧 Modo debug activado — se mostrarán TODAS las respuestas JSON interceptadas');
    store._debug = true;

    // Re-patch fetch con debug
    const debugFetch = window.fetch;
    window.fetch = async function(...args) {
      const response = await debugFetch.apply(this, args);
      try {
        const url = typeof args[0] === 'string' ? args[0] : args[0]?.url || '';
        const clone = response.clone();
        clone.json().then(data => {
          const keys = Object.keys(data);
          console.log(`   🔍 [fetch] ${url.substring(0, 80)} → keys: ${keys.join(',').substring(0, 100)}`);
        }).catch(() => {});
      } catch(e) {}
      return response;
    };
  };

  console.log('');
  console.log('═══════════════════════════════════════════════════════');
  console.log('  🎯 AutoTok Network Interceptor v1.0 — ACTIVO');
  console.log('═══════════════════════════════════════════════════════');
  console.log('');
  console.log('  Ahora haz scroll hacia abajo en la lista de Posts.');
  console.log('  Verás mensajes 🎯 cada vez que se capturen videos.');
  console.log('');
  console.log('  Comandos disponibles:');
  console.log('    AUTOTOK_STATUS()  → Ver cuántos videos llevas');
  console.log('    AUTOTOK_DUMP()    → Volcar la lista completa');
  console.log('    AUTOTOK_JSON()    → Exportar como JSON');
  console.log('    AUTOTOK_RAW(0)    → Ver campos RAW del video N');
  console.log('    AUTOTOK_FULL()    → Descargar JSON con TODOS los campos');
  console.log('    AUTOTOK_DEBUG()   → Ver TODAS las llamadas de red');
  console.log('');
})();
