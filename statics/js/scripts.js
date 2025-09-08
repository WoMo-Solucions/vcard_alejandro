document.addEventListener("DOMContentLoaded", function () {
  // --- 1) Verificar que el CSS esté cargado (fallback si abres el HTML directo) ---
  const stylesheets = Array.from(document.styleSheets || []);
  const cssLoaded = stylesheets.some(sheet => sheet.href && sheet.href.includes('styles.css'));
  if (!cssLoaded) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = './statics/css/styles.css';
    document.head.appendChild(link);
  }

  // --- 2) Cargar datos desde el VCF ---
  const vcfUrl = "./statics/julianramirez.vcf";
  fetch(vcfUrl)
    .then(res => res.text())
    .then(data => {
      // Helper: obtiene el valor de una línea clave del VCF (caso-insensible, multilínea)
      const escapeRE = s => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      const getValue = (key) => {
        const re = new RegExp(`^${escapeRE(key)}:(.*)$`, "mi");
        const m = data.match(re);
        return m ? m[1].trim() : "";
      };

      // Campos base
      const nombre      = getValue("FN");
      const empresa     = getValue("ORG");
      const cargo       = getValue("TITLE");
      const telefono    = getValue("TEL");
      const email       = getValue("EMAIL");
      const direccion   = (() => {
        // Si la dirección viene como "ADR;TYPE=home:;;Cali - Colombia;;;;"
        const adr = getValue("ADR;TYPE=home");
        if (!adr) return "";
        // Partes separadas por ";", filtramos vacíos y unimos legible
        return adr.split(";").filter(Boolean).join(" ").trim();
      })();
      const nota        = getValue("NOTE");
      const universidad = getValue("X-SCHOOL");

      // URLs (todas)
      const urls = data.match(/^URL:(.*)$/gmi)?.map(u => u.replace(/^URL:/i, "").trim()) || [];

      // --- 3) Rellenar HTML ---
      const $ = (sel) => document.querySelector(sel);
      const setText = (sel, txt) => { const el = $(sel); if (el) el.textContent = txt || ""; };

      setText("h1", nombre);
      setText("h2", empresa);
      const cargoEl = $(".cargo");
      if (cargoEl) cargoEl.innerHTML = `<i class="fas fa-briefcase"></i> ${cargo || ""}`;
      const uniEl = $(".ubicacion.uni");
      if (uniEl) uniEl.innerHTML = `<i class="fas fa-university"></i> ${universidad || ""}`;
      const dirEl = $(".ubicacion.direccion");
      if (dirEl) dirEl.innerHTML = `<i class="fas fa-map-marker-alt"></i> ${direccion || ""}`;
      const msgEl = $(".mensaje p");
      if (msgEl) msgEl.innerHTML = (nota || "").replace(/\\n/g, "<br>");

      // Enlaces
      const setHref = (sel, href) => { const el = $(sel); if (el) el.href = (href && href.trim()) ? href : "#"; };
      // WhatsApp directo con el teléfono del VCF
      setHref(".whatsapp", telefono ? `https://wa.me/${telefono.replace(/\D/g, "")}` : "");
      setHref(".email", email ? `mailto:${email}` : "");

      // LinkedIn / GitHub / Instagram desde la lista de URLs (por contenido)
      setHref(".linkedin",  urls.find(u => /linkedin/i.test(u)));
      setHref(".github",    urls.find(u => /github/i.test(u)));
      setHref(".instagram", urls.find(u => /instagram/i.test(u)));

      // --- 4) Certificado profesional (sin texto quemado) ---
      // Busca en ROLE, luego X-CREDENCIAL y X-LICENCIA
      const certificado = (getValue("ROLE") || getValue("X-CREDENCIAL") || getValue("X-LICENCIA")).trim();
      const credEl = document.getElementById("credencial");
      if (credEl) {
        if (certificado) {
          // Muestra exactamente lo que viene del VCF
          const span = credEl.querySelector("span");
          if (span) span.textContent = certificado;
          credEl.hidden = false;
        } else {
          credEl.hidden = true;
        }
      }

      // --- 5) Botón Guardar Contacto ---
      const guardarBtn = document.getElementById("guardarContacto");
      if (guardarBtn) {
        guardarBtn.addEventListener("click", function (e) {
          e.preventDefault();
          const link = document.createElement("a");
          link.href = vcfUrl;
          link.download = `${(nombre || "contacto").replace(/ /g, "_")}.vcf`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        });
      }
    })
    .catch(err => console.error("Error cargando datos del VCF:", err));
});