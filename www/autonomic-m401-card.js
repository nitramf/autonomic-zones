class AutonomicM401Card extends HTMLElement {
  setConfig(config) {
    if (!config.entities || !Array.isArray(config.entities) || config.entities.length !== 4) {
      throw new Error("Autonomic M401 card needs exactly 4 zone objects.");
    }
    this.config = {
      show_volume: true,
      ...config
    };
    if (!this.shadowRoot) this.attachShadow({mode: "open"});
    this.shadowRoot.innerHTML = `
      <ha-card>
        <div class="wrap">
          <div class="header"></div>
          <div class="grid"></div>
        </div>
      </ha-card>
      <style>
        ha-card { overflow:hidden; }
        .wrap { padding:16px; }
        .header { font-size:1.15em; font-weight:500; margin-bottom:12px; }
        .grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }
        .zone { border:0; border-radius:14px; padding:12px; text-align:left;
          background:var(--secondary-background-color); color:var(--primary-text-color);
          cursor:pointer; }
        .zone.on { background:var(--state-active-color,var(--primary-color)); color:white; }
        .top { display:flex; justify-content:space-between; align-items:center; }
        .name { font-size:16px; font-weight:600; }
        .power { font-size:12px; opacity:.8; }
        .row { margin-top:10px; display:grid; grid-template-columns:1fr auto; gap:8px; align-items:center; }
        input[type=range] { width:100%; }
        select { width:100%; border-radius:8px; padding:5px; }
        .mute { border:0; border-radius:8px; padding:5px 8px; cursor:pointer; }
        .muted { background:var(--error-color); color:white; }
        .vol { font-size:12px; min-width:36px; text-align:right; }
      </style>`;
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    if (this.config) this.render();
  }

  state(id) { return this._hass?.states?.[id]; }

  render() {
    if (!this._hass) return;
    this.shadowRoot.querySelector(".header").textContent =
      this.config.title || "Autonomic M401";
    const grid = this.shadowRoot.querySelector(".grid");
    grid.replaceChildren();

    const showVolume = this.config.show_volume !== false;

    for (const z of this.config.entities) {
      const power = this.state(z.power);
      const volume = this.state(z.volume);
      const mute = this.state(z.mute);
      const source = this.state(z.source);
      const box = document.createElement("div");
      box.className = "zone" + (power?.state === "on" ? " on" : "");

      const top = document.createElement("div");
      top.className = "top";
      const name = document.createElement("div");
      name.className = "name";
      name.textContent = z.name;
      const p = document.createElement("div");
      p.className = "power";
      p.textContent = power?.state === "on" ? "AN" : "AUS";
      top.append(name, p);

      box.append(top);

      let slider;
      if (showVolume) {
        const volRow = document.createElement("div");
        volRow.className = "row";
        slider = document.createElement("input");
        slider.type = "range"; slider.min = "0"; slider.max = "100";
        slider.value = volume?.state ?? "0";
        slider.disabled = power?.state !== "on";
        const vol = document.createElement("div");
        vol.className = "vol"; vol.textContent = `${volume?.state ?? 0}%`;
        slider.addEventListener("change", () => this._hass.callService("number", "set_value", {
          entity_id: z.volume, value: Number(slider.value)
        }));
        slider.addEventListener("input", () => vol.textContent = `${slider.value}%`);
        volRow.append(slider, vol);
        box.append(volRow);
      }

      const controls = document.createElement("div");
      controls.className = "row";
      const select = document.createElement("select");
      ["S1","S2","S3","S4","S5","S6","S7","S8"].forEach(s => {
        const o = document.createElement("option"); o.value=s; o.textContent=s;
        if (source?.state === s) o.selected=true;
        select.append(o);
      });
      select.disabled = power?.state !== "on";
      select.addEventListener("change", () => this._hass.callService("select", "select_option", {
        entity_id: z.source, option: select.value
      }));

      const muteBtn = document.createElement("button");
      muteBtn.className = "mute" + (mute?.state === "on" ? " muted" : "");
      muteBtn.textContent = mute?.state === "on" ? "Stumm" : "Mute";
      muteBtn.disabled = power?.state !== "on";
      muteBtn.addEventListener("click", () => this._hass.callService("switch",
        mute?.state === "on" ? "turn_off" : "turn_on",
        {entity_id: z.mute}));

      controls.append(select, muteBtn);

      box.append(controls);

      box.addEventListener("click", (ev) => {
        if (ev.target === slider || ev.target === select || ev.target === muteBtn) return;
        this._hass.callService("switch",
          power?.state === "on" ? "turn_off" : "turn_on",
          {entity_id: z.power});
      });
      grid.append(box);
    }
  }

  getCardSize() { return 5; }
}
customElements.define("autonomic-m401-card", AutonomicM401Card);
window.customCards = window.customCards || [];
window.customCards.push({
  type: "autonomic-m401-card",
  name: "Autonomic M401 Zones",
  description: "Four-zone power, volume, mute and source control."
});
