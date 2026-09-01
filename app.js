(function () {
  "use strict";

  const STORAGE_KEY = "synthCards.v1";

  /** @typedef {{id:string,name:string,answerImage:string,createdAt:number,known:boolean,seenCount:number}} Card */

  /** @type {Card[]} */
  let cards = loadCards();

  function loadCards() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) return [];
      return parsed;
    } catch (e) {
      console.error("Failed to load cards", e);
      return [];
    }
  }

  function saveCards() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(cards));
  }

  function uid() {
    return "c_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 8);
  }

  // ---------- Reusable drawing pad ----------
  class DrawPad {
    constructor(canvas, penWidthInput, eraserBtn, undoBtn, clearBtn) {
      this.canvas = canvas;
      this.ctx = canvas.getContext("2d");
      this.penWidthInput = penWidthInput;
      this.eraserBtn = eraserBtn;
      this.erasing = false;
      this.drawing = false;
      this.undoStack = [];
      this.last = { x: 0, y: 0 };

      this.resizeToDisplaySize();
      this.clear(false);

      canvas.addEventListener("pointerdown", (e) => this.onPointerDown(e));
      canvas.addEventListener("pointermove", (e) => this.onPointerMove(e));
      window.addEventListener("pointerup", () => this.onPointerUp());
      window.addEventListener("pointercancel", () => this.onPointerUp());

      if (eraserBtn) {
        eraserBtn.addEventListener("click", () => {
          this.erasing = !this.erasing;
          eraserBtn.classList.toggle("active", this.erasing);
        });
      }
      if (undoBtn) undoBtn.addEventListener("click", () => this.undo());
      if (clearBtn) clearBtn.addEventListener("click", () => this.clear());
    }

    resizeToDisplaySize() {
      // Keep the internal bitmap at a fixed logical resolution (set via
      // width/height attributes in HTML); CSS controls the display size.
    }

    getPos(e) {
      const rect = this.canvas.getBoundingClientRect();
      const scaleX = this.canvas.width / rect.width;
      const scaleY = this.canvas.height / rect.height;
      return {
        x: (e.clientX - rect.left) * scaleX,
        y: (e.clientY - rect.top) * scaleY,
      };
    }

    pushUndoSnapshot() {
      this.undoStack.push(this.canvas.toDataURL());
      if (this.undoStack.length > 30) this.undoStack.shift();
    }

    onPointerDown(e) {
      this.drawing = true;
      this.pushUndoSnapshot();
      this.last = this.getPos(e);
      this.canvas.setPointerCapture(e.pointerId);
    }

    onPointerMove(e) {
      if (!this.drawing) return;
      const pos = this.getPos(e);
      const ctx = this.ctx;
      ctx.lineJoin = "round";
      ctx.lineCap = "round";
      ctx.lineWidth = Number(this.penWidthInput ? this.penWidthInput.value : 3) * (this.erasing ? 3 : 1);
      if (this.erasing) {
        ctx.globalCompositeOperation = "destination-out";
        ctx.strokeStyle = "rgba(0,0,0,1)";
      } else {
        ctx.globalCompositeOperation = "source-over";
        ctx.strokeStyle = "#2b2a27";
      }
      ctx.beginPath();
      ctx.moveTo(this.last.x, this.last.y);
      ctx.lineTo(pos.x, pos.y);
      ctx.stroke();
      this.last = pos;
    }

    onPointerUp() {
      this.drawing = false;
    }

    undo() {
      const snap = this.undoStack.pop();
      if (!snap) {
        this.clear(false);
        return;
      }
      const img = new Image();
      img.onload = () => {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.drawImage(img, 0, 0);
      };
      img.src = snap;
    }

    clear(pushUndo = true) {
      if (pushUndo) this.pushUndoSnapshot();
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }

    isBlank() {
      const data = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height).data;
      for (let i = 3; i < data.length; i += 4) {
        if (data[i] !== 0) return false;
      }
      return true;
    }

    toDataURL() {
      return this.canvas.toDataURL("image/png");
    }
  }

  // ---------- Tabs ----------
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabPanels = document.querySelectorAll(".tab-panel");
  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabButtons.forEach((b) => b.classList.remove("active"));
      tabPanels.forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
      if (btn.dataset.tab === "manage") renderCardList();
      if (btn.dataset.tab === "study") refreshStudyView();
    });
  });

  // ---------- Study tab ----------
  const drawCanvas = document.getElementById("draw-canvas");
  const studyPad = new DrawPad(
    drawCanvas,
    document.getElementById("pen-width"),
    document.getElementById("btn-eraser"),
    document.getElementById("btn-undo"),
    document.getElementById("btn-clear")
  );

  const emptyDeckMsg = document.getElementById("empty-deck-msg");
  const studyCardEl = document.getElementById("study-card");
  const cardNameEl = document.getElementById("card-name");
  const answerBlock = document.getElementById("answer-block");
  const answerImage = document.getElementById("answer-image");
  const btnReveal = document.getElementById("btn-reveal");
  const btnMarkKnow = document.getElementById("btn-mark-know");
  const btnMarkUnknown = document.getElementById("btn-mark-unknown");
  const deckProgressEl = document.getElementById("deck-progress");
  const cardPositionEl = document.getElementById("card-position");
  const filterUnknownEl = document.getElementById("filter-unknown");

  let studyOrder = [];
  let studyIndex = 0;

  function currentDeck() {
    if (filterUnknownEl.checked) {
      return cards.filter((c) => !c.known);
    }
    return cards;
  }

  function rebuildStudyOrder(keepPosition) {
    const deck = currentDeck();
    const prevId = studyOrder[studyIndex] ? cards[studyOrder[studyIndex]] && cards[studyOrder[studyIndex]].id : null;
    studyOrder = deck.map((c) => cards.indexOf(c));
    if (keepPosition && prevId) {
      const idx = studyOrder.findIndex((i) => cards[i].id === prevId);
      studyIndex = idx >= 0 ? idx : 0;
    } else {
      studyIndex = 0;
    }
    refreshStudyView();
  }

  function refreshStudyView() {
    const deck = currentDeck();
    studyOrder = deck.map((c) => cards.indexOf(c));
    if (studyIndex >= studyOrder.length) studyIndex = 0;

    if (cards.length === 0) {
      emptyDeckMsg.hidden = false;
      studyCardEl.hidden = true;
      deckProgressEl.textContent = "0 / 0";
      cardPositionEl.textContent = "";
      return;
    }
    emptyDeckMsg.hidden = true;

    if (studyOrder.length === 0) {
      studyCardEl.hidden = true;
      deckProgressEl.textContent = "0 / 0 (모르는 카드 없음)";
      cardPositionEl.textContent = "";
      return;
    }

    studyCardEl.hidden = false;
    const knownCount = cards.filter((c) => c.known).length;
    deckProgressEl.textContent = `${knownCount} / ${cards.length} 암기 완료`;
    cardPositionEl.textContent = `${studyIndex + 1} / ${studyOrder.length}`;

    const card = cards[studyOrder[studyIndex]];
    cardNameEl.textContent = card.name;
    studyPad.clear(false);
    studyPad.undoStack = [];
    answerBlock.hidden = true;
    btnReveal.hidden = false;
    btnMarkKnow.hidden = true;
    btnMarkUnknown.hidden = true;
  }

  document.getElementById("btn-shuffle").addEventListener("click", () => {
    for (let i = studyOrder.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [studyOrder[i], studyOrder[j]] = [studyOrder[j], studyOrder[i]];
    }
    studyIndex = 0;
    showCardAt(studyIndex);
  });

  document.getElementById("btn-reset-progress").addEventListener("click", () => {
    if (!confirm("모든 카드의 암기 기록을 초기화할까요?")) return;
    cards.forEach((c) => (c.known = false));
    saveCards();
    refreshStudyView();
  });

  filterUnknownEl.addEventListener("change", () => rebuildStudyOrder(false));

  function showCardAt(idx) {
    if (studyOrder.length === 0) {
      refreshStudyView();
      return;
    }
    studyIndex = ((idx % studyOrder.length) + studyOrder.length) % studyOrder.length;
    const card = cards[studyOrder[studyIndex]];
    cardNameEl.textContent = card.name;
    cardPositionEl.textContent = `${studyIndex + 1} / ${studyOrder.length}`;
    studyPad.clear(false);
    studyPad.undoStack = [];
    answerBlock.hidden = true;
    btnReveal.hidden = false;
    btnMarkKnow.hidden = true;
    btnMarkUnknown.hidden = true;
  }

  document.getElementById("btn-prev").addEventListener("click", () => showCardAt(studyIndex - 1));
  document.getElementById("btn-next").addEventListener("click", () => showCardAt(studyIndex + 1));

  btnReveal.addEventListener("click", () => {
    if (studyOrder.length === 0) return;
    const card = cards[studyOrder[studyIndex]];
    card.seenCount = (card.seenCount || 0) + 1;
    saveCards();
    answerImage.src = card.answerImage;
    answerBlock.hidden = false;
    btnReveal.hidden = true;
    btnMarkKnow.hidden = false;
    btnMarkUnknown.hidden = false;
  });

  function markAndAdvance(known) {
    if (studyOrder.length === 0) return;
    const card = cards[studyOrder[studyIndex]];
    card.known = known;
    saveCards();
    const wasFiltered = filterUnknownEl.checked;
    if (wasFiltered) {
      rebuildStudyOrder(false);
    } else {
      showCardAt(studyIndex + 1);
      deckProgressEl.textContent = `${cards.filter((c) => c.known).length} / ${cards.length} 암기 완료`;
    }
  }

  btnMarkKnow.addEventListener("click", () => markAndAdvance(true));
  btnMarkUnknown.addEventListener("click", () => markAndAdvance(false));

  // ---------- Manage tab ----------
  const answerCanvas = document.getElementById("answer-canvas");
  const answerPad = new DrawPad(
    answerCanvas,
    document.getElementById("answer-pen-width"),
    document.getElementById("btn-answer-eraser"),
    document.getElementById("btn-answer-undo"),
    document.getElementById("btn-answer-clear")
  );

  const cardNameInput = document.getElementById("card-name-input");
  const editorTitle = document.getElementById("editor-title");
  const btnSaveCard = document.getElementById("btn-save-card");
  const btnCancelEdit = document.getElementById("btn-cancel-edit");
  const cardListEl = document.getElementById("card-list");
  const cardCountEl = document.getElementById("card-count");

  let editingId = null;

  function resetEditor() {
    editingId = null;
    cardNameInput.value = "";
    answerPad.clear(false);
    answerPad.undoStack = [];
    editorTitle.textContent = "새 카드 만들기";
    btnCancelEdit.hidden = true;
  }

  btnSaveCard.addEventListener("click", () => {
    const name = cardNameInput.value.trim();
    if (!name) {
      alert("구조 이름을 입력해 주세요.");
      cardNameInput.focus();
      return;
    }
    if (answerPad.isBlank()) {
      alert("정답 구조를 그려 주세요.");
      return;
    }
    const imageData = answerPad.toDataURL();

    if (editingId) {
      const card = cards.find((c) => c.id === editingId);
      if (card) {
        card.name = name;
        card.answerImage = imageData;
      }
    } else {
      cards.push({
        id: uid(),
        name,
        answerImage: imageData,
        createdAt: Date.now(),
        known: false,
        seenCount: 0,
      });
    }
    saveCards();
    resetEditor();
    renderCardList();
    refreshStudyView();
  });

  btnCancelEdit.addEventListener("click", resetEditor);

  function editCard(id) {
    const card = cards.find((c) => c.id === id);
    if (!card) return;
    editingId = id;
    cardNameInput.value = card.name;
    editorTitle.textContent = "카드 수정";
    btnCancelEdit.hidden = false;
    const img = new Image();
    img.onload = () => {
      answerPad.clear(false);
      answerPad.ctx.drawImage(img, 0, 0, answerCanvas.width, answerCanvas.height);
    };
    img.src = card.answerImage;
    cardNameInput.focus();
  }

  function deleteCard(id) {
    const card = cards.find((c) => c.id === id);
    if (!card) return;
    if (!confirm(`"${card.name}" 카드를 삭제할까요?`)) return;
    cards = cards.filter((c) => c.id !== id);
    saveCards();
    if (editingId === id) resetEditor();
    renderCardList();
    refreshStudyView();
  }

  function renderCardList() {
    cardCountEl.textContent = String(cards.length);
    cardListEl.innerHTML = "";
    cards.forEach((card) => {
      const li = document.createElement("li");
      li.className = "card-list-item";

      const img = document.createElement("img");
      img.src = card.answerImage;
      img.alt = card.name;

      const info = document.createElement("div");
      info.className = "info";
      const nameEl = document.createElement("div");
      nameEl.className = "name";
      nameEl.textContent = card.name;
      const statEl = document.createElement("div");
      statEl.className = "stat";
      statEl.textContent = (card.known ? "✅ 암기 완료" : "미암기") + ` · 확인 ${card.seenCount || 0}회`;
      info.appendChild(nameEl);
      info.appendChild(statEl);

      const actions = document.createElement("div");
      actions.className = "item-actions";
      const editBtn = document.createElement("button");
      editBtn.textContent = "수정";
      editBtn.addEventListener("click", () => editCard(card.id));
      const delBtn = document.createElement("button");
      delBtn.textContent = "삭제";
      delBtn.addEventListener("click", () => deleteCard(card.id));
      actions.appendChild(editBtn);
      actions.appendChild(delBtn);

      li.appendChild(img);
      li.appendChild(info);
      li.appendChild(actions);
      cardListEl.appendChild(li);
    });
  }

  // ---------- Import / Export ----------
  document.getElementById("btn-export").addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(cards, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "synthesis-flashcards.json";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  });

  const importFileInput = document.getElementById("import-file");
  document.getElementById("btn-import").addEventListener("click", () => importFileInput.click());
  importFileInput.addEventListener("change", () => {
    const file = importFileInput.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const parsed = JSON.parse(String(reader.result));
        if (!Array.isArray(parsed)) throw new Error("invalid format");
        const validCards = parsed.filter((c) => c && typeof c.name === "string" && typeof c.answerImage === "string");
        const merge = confirm(
          `${validCards.length}개의 카드를 불러왔습니다.\n확인: 기존 카드에 추가\n취소: 기존 카드를 모두 교체`
        );
        validCards.forEach((c) => {
          if (!c.id) c.id = uid();
          if (typeof c.known !== "boolean") c.known = false;
          if (typeof c.seenCount !== "number") c.seenCount = 0;
          if (typeof c.createdAt !== "number") c.createdAt = Date.now();
        });
        cards = merge ? cards.concat(validCards) : validCards;
        saveCards();
        renderCardList();
        refreshStudyView();
      } catch (e) {
        alert("파일을 읽을 수 없습니다. 올바른 JSON 파일인지 확인해 주세요.");
      } finally {
        importFileInput.value = "";
      }
    };
    reader.readAsText(file);
  });

  // ---------- Init ----------
  renderCardList();
  refreshStudyView();
})();
