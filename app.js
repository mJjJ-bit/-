(function () {
  "use strict";

  const STORAGE_KEY = "synthCards.v1";
  const FOLDERS_KEY = "synthFolders.v1";
  const ALL_FOLDERS_FILTER = "__all__";

  /** @typedef {{id:string,name:string,answerImage:string,createdAt:number,known:boolean,seenCount:number,folder:string}} Card */

  /** @type {Card[]} */
  let cards = loadCards();

  /** @type {string[]} */
  let folders = loadFolders();

  function loadCards() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) return [];
      parsed.forEach((c) => {
        if (typeof c.folder !== "string") c.folder = "";
      });
      return parsed;
    } catch (e) {
      console.error("Failed to load cards", e);
      return [];
    }
  }

  function saveCards() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(cards));
    } catch (e) {
      // An unguarded QuotaExceededError here (common on iOS Safari, which
      // has a much tighter localStorage limit than desktop/Android Chrome)
      // would otherwise abort whatever click handler called saveCards()
      // partway through, silently breaking the rest of that action.
      console.error("Failed to save cards", e);
      showToast("저장 공간이 부족해서 저장하지 못했습니다. 사진이 큰 카드를 정리해 보세요.");
    }
  }

  function loadFolders() {
    try {
      const raw = localStorage.getItem(FOLDERS_KEY);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) return [];
      return parsed.filter((f) => typeof f === "string");
    } catch (e) {
      console.error("Failed to load folders", e);
      return [];
    }
  }

  function saveFolders() {
    try {
      localStorage.setItem(FOLDERS_KEY, JSON.stringify(folders));
    } catch (e) {
      console.error("Failed to save folders", e);
      showToast("저장 공간이 부족해서 저장하지 못했습니다.");
    }
  }

  function uid() {
    return "c_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 8);
  }

  // window.alert/confirm/prompt are unreliable inside a sandboxed embed
  // (e.g. Claude Artifacts), so all user prompts are done with in-page UI
  // instead of the native dialogs.
  let toastTimer = null;
  function showToast(message) {
    const el = document.getElementById("toast");
    el.textContent = message;
    el.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      el.hidden = true;
    }, 2600);
  }

  // Turns a button into a two-step "click again to confirm" control so
  // destructive actions don't need window.confirm().
  function armConfirmButton(button, confirmLabel, action) {
    const originalLabel = button.textContent;
    let armed = false;
    let revertTimer = null;
    button.addEventListener("click", (e) => {
      e.stopPropagation();
      if (!armed) {
        armed = true;
        button.textContent = confirmLabel;
        button.classList.add("confirming");
        revertTimer = setTimeout(() => {
          armed = false;
          button.textContent = originalLabel;
          button.classList.remove("confirming");
        }, 3000);
      } else {
        clearTimeout(revertTimer);
        armed = false;
        button.textContent = originalLabel;
        button.classList.remove("confirming");
        action();
      }
    });
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

      // Mouse and touch are handled separately (rather than via Pointer
      // Events) because Safari on iPad has a history of unreliable
      // setPointerCapture/touch-action interaction, silently dropping
      // pointermove during a drag. Native touch events with preventDefault
      // are the reliable cross-browser way to draw on a canvas.
      canvas.addEventListener("mousedown", (e) => this.startStroke(e.clientX, e.clientY));
      canvas.addEventListener("mousemove", (e) => this.continueStroke(e.clientX, e.clientY));
      window.addEventListener("mouseup", () => this.endStroke());

      canvas.addEventListener(
        "touchstart",
        (e) => {
          e.preventDefault();
          const t = e.changedTouches[0];
          this.startStroke(t.clientX, t.clientY);
        },
        { passive: false }
      );
      canvas.addEventListener(
        "touchmove",
        (e) => {
          e.preventDefault();
          const t = e.changedTouches[0];
          this.continueStroke(t.clientX, t.clientY);
        },
        { passive: false }
      );
      canvas.addEventListener(
        "touchend",
        (e) => {
          e.preventDefault();
          this.endStroke();
        },
        { passive: false }
      );
      canvas.addEventListener(
        "touchcancel",
        (e) => {
          e.preventDefault();
          this.endStroke();
        },
        { passive: false }
      );

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

    getPos(clientX, clientY) {
      const rect = this.canvas.getBoundingClientRect();
      const scaleX = this.canvas.width / rect.width;
      const scaleY = this.canvas.height / rect.height;
      return {
        x: (clientX - rect.left) * scaleX,
        y: (clientY - rect.top) * scaleY,
      };
    }

    pushUndoSnapshot() {
      this.undoStack.push(this.canvas.toDataURL());
      if (this.undoStack.length > 30) this.undoStack.shift();
    }

    startStroke(clientX, clientY) {
      this.drawing = true;
      this.pushUndoSnapshot();
      this.last = this.getPos(clientX, clientY);
    }

    continueStroke(clientX, clientY) {
      if (!this.drawing) return;
      const pos = this.getPos(clientX, clientY);
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

    endStroke() {
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
  const emptyFolderMsg = document.getElementById("empty-folder-msg");
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
  const studyFolderFilterEl = document.getElementById("study-folder-filter");

  let studyOrder = [];
  let studyIndex = 0;

  function folderScopedCards() {
    const sel = studyFolderFilterEl.value;
    if (sel === ALL_FOLDERS_FILTER) return cards;
    return cards.filter((c) => (c.folder || "") === sel);
  }

  function currentDeck() {
    const scoped = folderScopedCards();
    if (filterUnknownEl.checked) {
      return scoped.filter((c) => !c.known);
    }
    return scoped;
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
    const scoped = folderScopedCards();
    const deck = currentDeck();
    studyOrder = deck.map((c) => cards.indexOf(c));
    if (studyIndex >= studyOrder.length) studyIndex = 0;

    if (cards.length === 0) {
      emptyDeckMsg.hidden = false;
      emptyFolderMsg.hidden = true;
      studyCardEl.hidden = true;
      deckProgressEl.textContent = "0 / 0";
      cardPositionEl.textContent = "";
      return;
    }
    emptyDeckMsg.hidden = true;

    if (scoped.length === 0) {
      emptyFolderMsg.hidden = false;
      studyCardEl.hidden = true;
      deckProgressEl.textContent = "0 / 0";
      cardPositionEl.textContent = "";
      return;
    }
    emptyFolderMsg.hidden = true;

    if (studyOrder.length === 0) {
      studyCardEl.hidden = true;
      deckProgressEl.textContent = `0 / ${scoped.length} (모르는 카드 없음)`;
      cardPositionEl.textContent = "";
      return;
    }

    studyCardEl.hidden = false;
    const knownCount = scoped.filter((c) => c.known).length;
    deckProgressEl.textContent = `${knownCount} / ${scoped.length} 암기 완료`;
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

  armConfirmButton(document.getElementById("btn-reset-progress"), "정말요? (다시 클릭)", () => {
    cards.forEach((c) => (c.known = false));
    saveCards();
    refreshStudyView();
    showToast("기록을 초기화했습니다.");
  });

  filterUnknownEl.addEventListener("change", () => rebuildStudyOrder(false));
  studyFolderFilterEl.addEventListener("change", () => rebuildStudyOrder(false));

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
    answerImage.src = card.answerImage;
    answerBlock.hidden = false;
    btnReveal.hidden = true;
    btnMarkKnow.hidden = false;
    btnMarkUnknown.hidden = false;
    card.seenCount = (card.seenCount || 0) + 1;
    saveCards();
  });

  function markAndAdvance(known) {
    if (studyOrder.length === 0) return;
    const card = cards[studyOrder[studyIndex]];
    card.known = known;
    const wasFiltered = filterUnknownEl.checked;
    if (wasFiltered) {
      rebuildStudyOrder(false);
    } else {
      showCardAt(studyIndex + 1);
      const scoped = folderScopedCards();
      deckProgressEl.textContent = `${scoped.filter((c) => c.known).length} / ${scoped.length} 암기 완료`;
    }
    saveCards();
  }

  btnMarkKnow.addEventListener("click", () => markAndAdvance(true));
  btnMarkUnknown.addEventListener("click", () => markAndAdvance(false));

  // ---------- Manage tab ----------
  const cardNameInput = document.getElementById("card-name-input");
  const editorTitle = document.getElementById("editor-title");
  const btnSaveCard = document.getElementById("btn-save-card");
  const btnCancelEdit = document.getElementById("btn-cancel-edit");
  const cardListEl = document.getElementById("card-list");
  const cardCountEl = document.getElementById("card-count");
  const cardFolderSelectEl = document.getElementById("card-folder-select");
  const btnAddFolder = document.getElementById("btn-add-folder");
  const newFolderInput = document.getElementById("new-folder-input");
  const folderListEl = document.getElementById("folder-list");

  let activeFolderFilter = ALL_FOLDERS_FILTER;
  let renamingFolder = null;

  function populateFolderSelects() {
    const sortedFolders = folders.slice().sort((a, b) => a.localeCompare(b, "ko"));

    const prevCardFolder = cardFolderSelectEl.value;
    cardFolderSelectEl.innerHTML = '<option value="">미분류</option>';
    sortedFolders.forEach((f) => {
      const opt = document.createElement("option");
      opt.value = f;
      opt.textContent = f;
      cardFolderSelectEl.appendChild(opt);
    });
    if ([...cardFolderSelectEl.options].some((o) => o.value === prevCardFolder)) {
      cardFolderSelectEl.value = prevCardFolder;
    }

    const prevStudyFilter = studyFolderFilterEl.value;
    studyFolderFilterEl.innerHTML = '<option value="__all__">전체</option><option value="">미분류</option>';
    sortedFolders.forEach((f) => {
      const opt = document.createElement("option");
      opt.value = f;
      opt.textContent = f;
      studyFolderFilterEl.appendChild(opt);
    });
    if ([...studyFolderFilterEl.options].some((o) => o.value === prevStudyFilter)) {
      studyFolderFilterEl.value = prevStudyFilter;
    }
  }

  function addFolder() {
    const trimmed = newFolderInput.value.trim();
    if (!trimmed) {
      showToast("폴더 이름을 입력해 주세요.");
      newFolderInput.focus();
      return;
    }
    if (folders.includes(trimmed)) {
      showToast("이미 있는 폴더 이름입니다.");
      return;
    }
    folders.push(trimmed);
    saveFolders();
    populateFolderSelects();
    cardFolderSelectEl.value = trimmed;
    newFolderInput.value = "";
    renderFolderList();
    showToast(`"${trimmed}" 폴더를 만들었습니다.`);
  }

  btnAddFolder.addEventListener("click", addFolder);
  newFolderInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") addFolder();
  });

  function commitRenameFolder(oldName, newName) {
    const trimmed = newName.trim();
    if (!trimmed || trimmed === oldName) {
      renamingFolder = null;
      renderFolderList();
      return;
    }
    if (folders.includes(trimmed)) {
      showToast("이미 있는 폴더 이름입니다.");
      return;
    }
    folders = folders.map((f) => (f === oldName ? trimmed : f));
    cards.forEach((c) => {
      if (c.folder === oldName) c.folder = trimmed;
    });
    if (activeFolderFilter === oldName) activeFolderFilter = trimmed;
    renamingFolder = null;
    saveFolders();
    saveCards();
    populateFolderSelects();
    renderFolderList();
    renderCardList();
    refreshStudyView();
  }

  function deleteFolder(name) {
    const count = cards.filter((c) => c.folder === name).length;
    folders = folders.filter((f) => f !== name);
    cards.forEach((c) => {
      if (c.folder === name) c.folder = "";
    });
    if (activeFolderFilter === name) activeFolderFilter = ALL_FOLDERS_FILTER;
    saveFolders();
    saveCards();
    populateFolderSelects();
    renderFolderList();
    renderCardList();
    refreshStudyView();
    showToast(count > 0 ? `"${name}" 폴더를 삭제하고 카드 ${count}개를 미분류로 옮겼습니다.` : `"${name}" 폴더를 삭제했습니다.`);
  }

  function renderFolderList() {
    folderListEl.innerHTML = "";

    const specialEntries = [
      { value: ALL_FOLDERS_FILTER, label: "전체", count: cards.length },
      { value: "", label: "미분류", count: cards.filter((c) => !c.folder).length },
    ];
    const folderEntries = folders
      .slice()
      .sort((a, b) => a.localeCompare(b, "ko"))
      .map((f) => ({ value: f, label: f, count: cards.filter((c) => c.folder === f).length }));

    [...specialEntries, ...folderEntries].forEach((entry) => {
      const li = document.createElement("li");
      li.className = "folder-item" + (activeFolderFilter === entry.value ? " active" : "");

      const isCustomFolder = entry.value !== ALL_FOLDERS_FILTER && entry.value !== "";

      if (isCustomFolder && renamingFolder === entry.value) {
        const input = document.createElement("input");
        input.type = "text";
        input.className = "folder-rename-input";
        input.value = entry.value;
        const commit = () => commitRenameFolder(entry.value, input.value);
        input.addEventListener("click", (e) => e.stopPropagation());
        input.addEventListener("keydown", (e) => {
          if (e.key === "Enter") commit();
          if (e.key === "Escape") {
            renamingFolder = null;
            renderFolderList();
          }
        });
        const saveBtn = document.createElement("button");
        saveBtn.textContent = "✓";
        saveBtn.title = "저장";
        saveBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          commit();
        });
        const cancelBtn = document.createElement("button");
        cancelBtn.textContent = "✕";
        cancelBtn.title = "취소";
        cancelBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          renamingFolder = null;
          renderFolderList();
        });
        li.appendChild(input);
        li.appendChild(saveBtn);
        li.appendChild(cancelBtn);
        folderListEl.appendChild(li);
        input.focus();
        input.select();
        return;
      }

      const nameEl = document.createElement("span");
      nameEl.className = "folder-name";
      nameEl.textContent = entry.label;

      const countEl = document.createElement("span");
      countEl.className = "folder-count";
      countEl.textContent = String(entry.count);

      li.appendChild(nameEl);
      li.appendChild(countEl);

      if (isCustomFolder) {
        const actions = document.createElement("div");
        actions.className = "item-actions";
        const renameBtn = document.createElement("button");
        renameBtn.textContent = "✎";
        renameBtn.title = "이름 변경";
        renameBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          renamingFolder = entry.value;
          renderFolderList();
        });
        const delBtn = document.createElement("button");
        delBtn.textContent = "×";
        delBtn.title = "삭제";
        armConfirmButton(delBtn, "정말?", () => deleteFolder(entry.value));
        actions.appendChild(renameBtn);
        actions.appendChild(delBtn);
        li.appendChild(actions);
      }

      li.addEventListener("click", () => {
        activeFolderFilter = entry.value;
        renderFolderList();
        renderCardList();
      });

      folderListEl.appendChild(li);
    });
  }

  const photoDropZone = document.getElementById("photo-drop-zone");
  const photoPlaceholder = document.getElementById("photo-placeholder");
  const answerPhotoPreview = document.getElementById("answer-photo-preview");
  const answerPhotoInput = document.getElementById("answer-photo-input");
  const btnChoosePhoto = document.getElementById("btn-choose-photo");
  const btnRemovePhoto = document.getElementById("btn-remove-photo");

  let editingId = null;
  let currentAnswerImage = null;

  // Downscale + re-encode an uploaded photo so a multi-MB phone photo
  // doesn't blow through localStorage's per-origin quota.
  function loadPhotoAsDataURL(file, maxDim = 1000, quality = 0.85) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onerror = () => reject(reader.error);
      reader.onload = () => {
        const img = new Image();
        img.onerror = () => reject(new Error("invalid image"));
        img.onload = () => {
          const scale = Math.min(1, maxDim / Math.max(img.width, img.height));
          const w = Math.round(img.width * scale);
          const h = Math.round(img.height * scale);
          const canvas = document.createElement("canvas");
          canvas.width = w;
          canvas.height = h;
          const ctx = canvas.getContext("2d");
          ctx.fillStyle = "#fff";
          ctx.fillRect(0, 0, w, h);
          ctx.drawImage(img, 0, 0, w, h);
          resolve(canvas.toDataURL("image/jpeg", quality));
        };
        img.src = reader.result;
      };
      reader.readAsDataURL(file);
    });
  }

  function setAnswerPhoto(dataURL) {
    currentAnswerImage = dataURL;
    if (dataURL) {
      answerPhotoPreview.src = dataURL;
      answerPhotoPreview.hidden = false;
      photoPlaceholder.hidden = true;
      btnRemovePhoto.hidden = false;
    } else {
      answerPhotoPreview.src = "";
      answerPhotoPreview.hidden = true;
      photoPlaceholder.hidden = false;
      btnRemovePhoto.hidden = true;
    }
  }

  async function handlePhotoFile(file) {
    if (!file || !file.type.startsWith("image/")) {
      showToast("이미지 파일을 선택해 주세요.");
      return;
    }
    try {
      const dataURL = await loadPhotoAsDataURL(file);
      setAnswerPhoto(dataURL);
    } catch (e) {
      showToast("사진을 불러오지 못했습니다.");
    }
  }

  photoDropZone.addEventListener("click", () => answerPhotoInput.click());
  btnChoosePhoto.addEventListener("click", () => answerPhotoInput.click());
  answerPhotoInput.addEventListener("change", () => {
    if (answerPhotoInput.files[0]) handlePhotoFile(answerPhotoInput.files[0]);
    answerPhotoInput.value = "";
  });

  btnRemovePhoto.addEventListener("click", (e) => {
    e.stopPropagation();
    setAnswerPhoto(null);
  });

  ["dragenter", "dragover"].forEach((evt) =>
    photoDropZone.addEventListener(evt, (e) => {
      e.preventDefault();
      photoDropZone.classList.add("drag-over");
    })
  );
  ["dragleave", "drop"].forEach((evt) =>
    photoDropZone.addEventListener(evt, (e) => {
      e.preventDefault();
      photoDropZone.classList.remove("drag-over");
    })
  );
  photoDropZone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files && e.dataTransfer.files[0];
    if (file) handlePhotoFile(file);
  });

  function resetEditor() {
    editingId = null;
    cardNameInput.value = "";
    setAnswerPhoto(null);
    editorTitle.textContent = "새 카드 만들기";
    btnCancelEdit.hidden = true;
    cardFolderSelectEl.value =
      activeFolderFilter !== ALL_FOLDERS_FILTER && activeFolderFilter !== "" ? activeFolderFilter : "";
  }

  btnSaveCard.addEventListener("click", () => {
    const name = cardNameInput.value.trim();
    if (!name) {
      showToast("구조 이름을 입력해 주세요.");
      cardNameInput.focus();
      return;
    }
    if (!currentAnswerImage) {
      showToast("정답 구조 사진을 업로드해 주세요.");
      return;
    }
    const folder = cardFolderSelectEl.value;

    if (editingId) {
      const card = cards.find((c) => c.id === editingId);
      if (card) {
        card.name = name;
        card.answerImage = currentAnswerImage;
        card.folder = folder;
      }
    } else {
      cards.push({
        id: uid(),
        name,
        answerImage: currentAnswerImage,
        createdAt: Date.now(),
        known: false,
        seenCount: 0,
        folder,
      });
    }
    saveCards();
    resetEditor();
    renderFolderList();
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
    setAnswerPhoto(card.answerImage);
    cardFolderSelectEl.value = card.folder || "";
    cardNameInput.focus();
  }

  function deleteCard(id) {
    cards = cards.filter((c) => c.id !== id);
    saveCards();
    if (editingId === id) resetEditor();
    renderFolderList();
    renderCardList();
    refreshStudyView();
  }

  function renderCardList() {
    const visibleCards =
      activeFolderFilter === ALL_FOLDERS_FILTER
        ? cards
        : cards.filter((c) => (c.folder || "") === activeFolderFilter);

    cardCountEl.textContent = String(visibleCards.length);
    cardListEl.innerHTML = "";
    visibleCards.forEach((card) => {
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
      const folderLabel = card.folder ? `${card.folder} · ` : "";
      statEl.textContent =
        folderLabel + (card.known ? "✅ 암기 완료" : "미암기") + ` · 확인 ${card.seenCount || 0}회`;
      info.appendChild(nameEl);
      info.appendChild(statEl);

      const actions = document.createElement("div");
      actions.className = "item-actions";
      const editBtn = document.createElement("button");
      editBtn.textContent = "수정";
      editBtn.addEventListener("click", () => editCard(card.id));
      const delBtn = document.createElement("button");
      delBtn.textContent = "삭제";
      armConfirmButton(delBtn, "정말?", () => deleteCard(card.id));
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
    const payload = { version: 1, cards, folders };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
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
  const importChoiceOverlay = document.getElementById("import-choice-overlay");
  const importChoiceText = document.getElementById("import-choice-text");
  const btnImportMerge = document.getElementById("btn-import-merge");
  const btnImportReplace = document.getElementById("btn-import-replace");
  const btnImportCancel = document.getElementById("btn-import-cancel");

  let pendingImport = null;

  function finishImport(merge) {
    if (!pendingImport) return;
    const { validCards, importedFolders } = pendingImport;
    pendingImport = null;
    importChoiceOverlay.hidden = true;

    cards = merge ? cards.concat(validCards) : validCards;

    const folderSet = new Set(merge ? folders : []);
    importedFolders.forEach((f) => folderSet.add(f));
    cards.forEach((c) => {
      if (c.folder) folderSet.add(c.folder);
    });
    folders = Array.from(folderSet);

    saveCards();
    saveFolders();
    populateFolderSelects();
    renderFolderList();
    renderCardList();
    refreshStudyView();
    showToast(`카드 ${validCards.length}개를 불러왔습니다.`);
  }

  btnImportMerge.addEventListener("click", () => finishImport(true));
  btnImportReplace.addEventListener("click", () => finishImport(false));
  btnImportCancel.addEventListener("click", () => {
    pendingImport = null;
    importChoiceOverlay.hidden = true;
  });

  document.getElementById("btn-import").addEventListener("click", () => importFileInput.click());
  importFileInput.addEventListener("change", () => {
    const file = importFileInput.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const parsed = JSON.parse(String(reader.result));
        let importedCards;
        let importedFolders;
        if (Array.isArray(parsed)) {
          importedCards = parsed;
          importedFolders = [];
        } else if (parsed && Array.isArray(parsed.cards)) {
          importedCards = parsed.cards;
          importedFolders = Array.isArray(parsed.folders) ? parsed.folders.filter((f) => typeof f === "string") : [];
        } else {
          throw new Error("invalid format");
        }
        const validCards = importedCards.filter((c) => c && typeof c.name === "string" && typeof c.answerImage === "string");
        validCards.forEach((c) => {
          if (!c.id) c.id = uid();
          if (typeof c.known !== "boolean") c.known = false;
          if (typeof c.seenCount !== "number") c.seenCount = 0;
          if (typeof c.createdAt !== "number") c.createdAt = Date.now();
          if (typeof c.folder !== "string") c.folder = "";
        });

        pendingImport = { validCards, importedFolders };
        importChoiceText.textContent = `카드 ${validCards.length}개를 불러왔습니다. 기존 카드에 추가할까요, 모두 교체할까요?`;
        importChoiceOverlay.hidden = false;
      } catch (e) {
        showToast("파일을 읽을 수 없습니다. 올바른 JSON 파일인지 확인해 주세요.");
      } finally {
        importFileInput.value = "";
      }
    };
    reader.readAsText(file);
  });

  // ---------- Init ----------
  populateFolderSelects();
  renderFolderList();
  renderCardList();
  refreshStudyView();
})();
