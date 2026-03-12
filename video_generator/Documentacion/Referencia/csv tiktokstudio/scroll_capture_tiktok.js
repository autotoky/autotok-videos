// ═══════════════════════════════════════════════════════════
// AutoTok — TikTok Studio Video Extractor v2.0
// ═══════════════════════════════════════════════════════════
// Pega esto en la consola del inspector (F12 → Console)
// en la página de TikTok Studio > Publicaciones
// Hará scroll automático y capturará TODOS los videos
// ═══════════════════════════════════════════════════════════

(async () => {
  const SCROLL_DELAY = 500;   // ms entre scrolls (más lento = más fiable)
  const SCROLL_AMOUNT = 200;  // px por scroll (menos = más granular)
  const IDLE_LIMIT = 25;      // scrolls sin nuevos videos → parar
  const LOAD_WAIT = 3000;     // ms extra cuando llega al fondo (lazy load)

  const collected = new Map();

  function captureVisible() {
    const links = document.querySelectorAll('a[href*="/video/"]');
    let newCount = 0;

    links.forEach(link => {
      const href = link.getAttribute('href') || '';
      const match = href.match(/@([^/]+)\/video\/(\d+)/);
      if (!match) return;

      const cuenta = match[1];
      const postId = match[2];
      if (collected.has(postId)) return;

      const title = link.textContent.trim();

      let container = link;
      for (let i = 0; i < 20; i++) {
        container = container.parentElement;
        if (!container) break;
        if (container.querySelectorAll('[data-tt*="ItemRow"]').length > 0 ||
            container.querySelectorAll('[data-tt*="PublishStageLabel"]').length > 0) {
          break;
        }
      }

      let dateStr = '';
      if (container) {
        const dateEl = container.querySelector('[data-tt*="PublishStageLabel"]');
        if (dateEl) dateStr = dateEl.textContent.trim();
      }

      let metrics = [];
      if (container) {
        const metricEls = container.querySelectorAll('[data-tt*="ItemRow"]');
        metricEls.forEach(el => {
          const text = el.textContent.trim();
          if (text && text !== '') metrics.push(text);
        });
      }

      collected.set(postId, {
        cuenta, postId,
        title: title.substring(0, 100),
        date: dateStr,
        views: metrics[0] || '0',
        likes: metrics[1] || '0',
        comments: metrics[2] || '0',
      });
      newCount++;
    });
    return newCount;
  }

  function findScrollContainer() {
    // Buscar el contenedor scrollable MÁS GRANDE que contenga videos
    const allDivs = document.querySelectorAll('div');
    let best = null;
    let bestHeight = 0;

    for (const div of allDivs) {
      // Debe ser scrollable (scrollHeight > clientHeight) y tener altura real (>200px)
      if (div.scrollHeight > div.clientHeight + 50 &&
          div.clientHeight > 200 &&
          div.querySelector('a[href*="/video/"]')) {
        if (div.scrollHeight > bestHeight) {
          best = div;
          bestHeight = div.scrollHeight;
        }
      }
    }
    return best || document.scrollingElement || document.documentElement;
  }

  console.log('🔍 AutoTok Extractor v2.0 — Iniciando...');

  const scrollEl = findScrollContainer();
  console.log('   Contenedor:', scrollEl.tagName, scrollEl.className?.substring(0, 60));
  console.log('   scrollHeight:', scrollEl.scrollHeight, 'clientHeight:', scrollEl.clientHeight);

  captureVisible();
  console.log(`   Videos iniciales: ${collected.size}`);

  // Scroll hasta arriba
  scrollEl.scrollTop = 0;
  await new Promise(r => setTimeout(r, 1000));

  let idleCount = 0;
  let lastSize = collected.size;
  let scrollCount = 0;
  let lastScrollHeight = scrollEl.scrollHeight;
  let bottomHits = 0;
  const MAX_BOTTOM_RETRIES = 8;

  while (idleCount < IDLE_LIMIT) {
    scrollEl.scrollTop += SCROLL_AMOUNT;
    await new Promise(r => setTimeout(r, SCROLL_DELAY));

    captureVisible();
    scrollCount++;

    if (collected.size > lastSize) {
      if (scrollCount % 20 === 0 || collected.size - lastSize > 5) {
        console.log(`   📦 ${collected.size} videos (scroll #${scrollCount})`);
      }
      lastSize = collected.size;
      idleCount = 0;
      bottomHits = 0;
    } else {
      idleCount++;
    }

    // Detectar fondo
    const atBottom = scrollEl.scrollTop + scrollEl.clientHeight >= scrollEl.scrollHeight - 20;

    if (atBottom && bottomHits < MAX_BOTTOM_RETRIES) {
      bottomHits++;
      console.log(`   ⏳ Fondo #${bottomHits} (${collected.size} videos). Esperando lazy load...`);

      // Esperar lazy load
      await new Promise(r => setTimeout(r, LOAD_WAIT));
      captureVisible();

      if (scrollEl.scrollHeight > lastScrollHeight) {
        console.log(`   ✅ Más contenido! scrollHeight: ${lastScrollHeight} → ${scrollEl.scrollHeight}`);
        lastScrollHeight = scrollEl.scrollHeight;
        idleCount = 0;
        bottomHits = 0;
      } else {
        // Truco: scroll arriba un poco y volver abajo para forzar carga
        scrollEl.scrollTop -= 1000;
        await new Promise(r => setTimeout(r, 800));
        scrollEl.scrollTop = scrollEl.scrollHeight;
        await new Promise(r => setTimeout(r, LOAD_WAIT));
        captureVisible();

        if (scrollEl.scrollHeight > lastScrollHeight || collected.size > lastSize) {
          console.log(`   🔄 Retry exitoso: ${collected.size} videos`);
          lastScrollHeight = scrollEl.scrollHeight;
          lastSize = collected.size;
          idleCount = 0;
        }
      }

      if (bottomHits >= MAX_BOTTOM_RETRIES) {
        console.log(`   🛑 ${MAX_BOTTOM_RETRIES} intentos en el fondo sin más datos. Parando.`);
        break;
      }
    }
  }

  // ═══ RESULTADO ═══
  const cuenta = collected.values().next().value?.cuenta || 'unknown';

  console.log(`\n✅ ¡LISTO! ${collected.size} videos de @${cuenta}`);
  console.log(`   Scrolls: ${scrollCount}`);
  console.log('\n📊 Lista completa:');

  let i = 1;
  for (const [postId, v] of collected) {
    console.log(`   ${i++}. ${postId} | ${v.date.padEnd(15)} | ${String(v.views).padStart(8)} views | ${v.title.substring(0, 40)}`);
  }

  console.log(`\n📋 Click derecho en la consola → "Copy All" → pega en un .txt`);
  console.log(`   Luego: python import_studio_html.py archivo.txt --cuenta ${cuenta}`);

  return { count: collected.size, cuenta };
})();
