// Fills the Wall of Fame from supporters.json. Names go in as text, never as HTML.
(function () {
  var TIERS = [
    ["legend", "Legend", "r4"],
    ["arcade-hero", "Arcade Hero", "r3"],
    ["high-scorer", "High Scorer", "r2"],
    ["insert-coin", "Insert Coin", "r1"],
  ];

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function empty(root) {
    var box = el("div", "empty", "PLAYER 1 READY");
    box.appendChild(el("small", "", "The board is empty. Be the first name on it."));
    root.replaceChildren(box);
  }

  function render(root, list, limit) {
    var supporters = Array.isArray(list && list.supporters) ? list.supporters : [];
    if (!supporters.length) return empty(root);
    var board = el("div", "board");
    var shown = 0;
    TIERS.forEach(function (tier) {
      var names = supporters.filter(function (s) { return s && s.tier === tier[0] && typeof s.name === "string"; });
      if (!names.length || (limit && shown >= limit)) return;
      var rank = el("div", "rank " + tier[2]);
      rank.appendChild(el("h3", "", tier[1]));
      var ul = el("ul", "names");
      names.forEach(function (s) {
        if (limit && shown >= limit) return;
        ul.appendChild(el("li", "", s.name.slice(0, 40)));
        shown++;
      });
      rank.appendChild(ul);
      board.appendChild(rank);
    });
    root.replaceChildren(board);
  }

  document.querySelectorAll("[data-wall]").forEach(function (root) {
    var limit = parseInt(root.getAttribute("data-limit") || "0", 10);
    fetch("supporters.json", { cache: "no-cache" })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (data) { render(root, data, limit); })
      .catch(function () { empty(root); });
  });

  // Download count: a file the repo updates every few hours from GitHub's own numbers, so visitors never contact GitHub's API.
  var MIN_SHOWN = 25; // not shown until it reaches this, so a brand-new count doesn't look sad
  var dl = document.querySelector("[data-downloads]");
  if (dl) {
    fetch("downloads.json", { cache: "no-cache" })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) {
        var n = d && typeof d.downloads === "number" ? d.downloads : 0;
        if (n >= MIN_SHOWN) {
          dl.querySelector("[data-downloads-n]").textContent = n.toLocaleString("en-US");
          dl.hidden = false;
        }
      })
      .catch(function () {});
  }

  document.querySelectorAll("[data-year]").forEach(function (n) { n.textContent = new Date().getFullYear(); });
})();
