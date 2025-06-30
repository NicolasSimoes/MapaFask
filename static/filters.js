document.addEventListener("DOMContentLoaded", function () {
  let map;
  for (let k in window) {
    if (k.startsWith("map_") && window[k]?.eachLayer) {
      map = window[k];
      break;
    }
  }
  if (!map) return;

  const markers = [];
  map.eachLayer(layer => {
    if (layer instanceof L.Marker && layer.getPopup()) {
      markers.push(layer);
    }
  });

  function getCheckedValues(groupId) {
    return Array.from(document.querySelectorAll(`#${groupId} .scrollbox input:checked`))
      .map(cb => cb.value.toLowerCase());
  }

  function filterMarkers() {
    const areas  = getCheckedValues('area-group');
    const ids    = getCheckedValues('id-group');
    const names  = getCheckedValues('name-group');

    markers.forEach(marker => {
      let raw = marker.getPopup()?.getContent?.() || "";
      if (typeof raw !== "string") raw = raw.innerHTML || raw.textContent || "";
      const plain = String(raw).toLowerCase().replace(/\s+/g, '');

      const okA = areas.length === 0 || areas.some(a => plain.includes('rota:</b>' + a.replace(/\s+/g, '')));
      const okI = ids.length   === 0 || ids.some(i => plain.includes('id:</b>' + i));
      const okN = names.length === 0 || names.some(n => plain.includes('cliente:</b>' + n.replace(/\s+/g, '')));

      if (okA && okI && okN) {
        marker.addTo(map);
      } else {
        map.removeLayer(marker);
      }
    });

    // Atualiza contador
    const visibleCount = markers.filter(m => map.hasLayer(m)).length;
    document.getElementById('marker-count').textContent = visibleCount;
  }

  document.getElementById('btn-search').onclick = filterMarkers;

  document.getElementById('btn-clear').onclick = () => {
    document.querySelectorAll('.scrollbox input:checked').forEach(cb => cb.checked = false);

    // Limpa caixas de busca
    document.querySelectorAll('.filter-search').forEach(input => {
      input.value = '';
      input.dispatchEvent(new Event('input'));
    });

    filterMarkers();
  };

  document.getElementById('btn-deselect').onclick = () => {
    markers.forEach(marker => map.removeLayer(marker));
    document.getElementById('marker-count').textContent = "0";
  };

  document.getElementById('btn-toggle').onclick = () => {
    const ctrl = document.querySelector('.leaflet-control-layers');
    ctrl.style.display = ctrl.style.display === 'none' ? '' : 'none';
  };

  // Filtro por texto + rolagem
  document.querySelectorAll('.filter-group').forEach(group => {
    const input = group.querySelector('.filter-search');
    const items = group.querySelectorAll('.scrollbox label');

    input.addEventListener('input', () => {
      const val = input.value.toLowerCase();
      let firstVisible = null;

      items.forEach(label => {
        const text = label.textContent.toLowerCase();
        const visible = text.includes(val);
        label.style.display = visible ? '' : 'none';
        if (visible && !firstVisible) firstVisible = label;
      });

      if (firstVisible) {
        const scrollbox = group.querySelector('.scrollbox');
        scrollbox.scrollTop = firstVisible.offsetTop - scrollbox.offsetTop;
      }
    });
  });

  // Selecionar todos
  document.querySelectorAll('.filter-group').forEach(group => {
    const toggle = group.querySelector('.check-all');
    const checks = group.querySelectorAll('.scrollbox input[type="checkbox"]');

    toggle.addEventListener('change', () => {
      checks.forEach(cb => {
        if (cb.closest('label').style.display !== "none") {
          cb.checked = toggle.checked;
        }
      });
    });
  });

  // Inicializa contador na carga
  document.getElementById('marker-count').textContent = markers.length;
});
