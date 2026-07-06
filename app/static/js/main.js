document.addEventListener("submit", (event) => {
    const form = event.target;
    const message = form.dataset.confirm;
    if (message && !window.confirm(message)) {
        event.preventDefault();
    }
});

function setTheme(theme) {
    document.documentElement.dataset.theme = theme;
    document.body.dataset.theme = theme;
    localStorage.setItem("cyber-dashboard-theme", theme);
    document.querySelectorAll("[data-theme-toggle]").forEach((toggle) => {
        const nextTheme = theme === "dark" ? "light" : "dark";
        toggle.setAttribute("aria-label", `Switch to ${nextTheme} theme`);
        toggle.setAttribute("title", `Switch to ${nextTheme} theme`);
    });
}

setTheme(document.documentElement.dataset.theme || "light");

document.querySelectorAll("[data-theme-toggle]").forEach((toggle) => {
    toggle.addEventListener("click", () => {
        const currentTheme = document.documentElement.dataset.theme === "dark" ? "dark" : "light";
        setTheme(currentTheme === "dark" ? "light" : "dark");
    });
});

document.addEventListener("click", (event) => {
    const toggle = event.target.closest("[data-profile-picture-toggle]");
    if (!toggle) {
        return;
    }

    const wrapper = toggle.closest("[data-profile-picture]");
    const menu = wrapper.querySelector("[data-profile-picture-menu]");
    menu.hidden = !menu.hidden;
});

const navToggle = document.querySelector(".nav-toggle");
const navigation = document.querySelector(".nav-links");

if (navToggle && navigation) {
    navToggle.addEventListener("click", () => {
        const isOpen = navToggle.getAttribute("aria-expanded") === "true";
        navToggle.setAttribute("aria-expanded", String(!isOpen));
        navigation.classList.toggle("is-open", !isOpen);
    });
}

function escapeHtml(value) {
    return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function renderInlineMarkdown(value) {
    return escapeHtml(value)
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
        .replace(/\*([^*]+)\*/g, "<em>$1</em>");
}

function renderNoteMarkdown(value) {
    const lines = value.split(/\r?\n/);
    const output = [];
    let listOpen = false;

    const closeList = () => {
        if (listOpen) {
            output.push("</ul>");
            listOpen = false;
        }
    };

    lines.forEach((line) => {
        const trimmed = line.trim();
        if (!trimmed) {
            closeList();
            return;
        }

        if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
            if (!listOpen) {
                output.push("<ul>");
                listOpen = true;
            }
            output.push(`<li>${renderInlineMarkdown(trimmed.slice(2))}</li>`);
            return;
        }

        closeList();
        if (trimmed.startsWith("### ")) {
            output.push(`<h3>${renderInlineMarkdown(trimmed.slice(4))}</h3>`);
        } else if (trimmed.startsWith("## ")) {
            output.push(`<h2>${renderInlineMarkdown(trimmed.slice(3))}</h2>`);
        } else if (trimmed.startsWith("# ")) {
            output.push(`<h1>${renderInlineMarkdown(trimmed.slice(2))}</h1>`);
        } else {
            output.push(`<p>${renderInlineMarkdown(trimmed)}</p>`);
        }
    });

    closeList();
    return output.join("");
}

function updateNotePreview(editor) {
    const body = editor.querySelector("[data-note-body]");
    const preview = editor.querySelector("[data-note-preview]");
    const stats = editor.querySelector("[data-note-stats]");
    if (!body) {
        return;
    }

    const text = body.value || "";
    const words = text.trim() ? text.trim().split(/\s+/).length : 0;
    if (stats) {
        stats.textContent = `${words} words · ${text.length} characters`;
    }
    if (preview) {
        preview.innerHTML = text.trim()
            ? renderNoteMarkdown(text)
            : '<p class="meta">Start writing to preview your note.</p>';
    }
}

function wrapSelection(textarea, before, after = before) {
    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const selected = textarea.value.slice(start, end) || "text";
    textarea.setRangeText(`${before}${selected}${after}`, start, end, "select");
    textarea.focus();
}

function applyNoteAction(textarea, action) {
    if (action === "bold") {
        wrapSelection(textarea, "**", "**");
    } else if (action === "italic") {
        wrapSelection(textarea, "*", "*");
    } else if (action === "code") {
        wrapSelection(textarea, "`", "`");
    } else if (action === "heading") {
        textarea.setRangeText(`## ${textarea.value.slice(textarea.selectionStart, textarea.selectionEnd) || "Heading"}`, textarea.selectionStart, textarea.selectionEnd, "select");
        textarea.focus();
    } else if (action === "bullet") {
        textarea.setRangeText(`- ${textarea.value.slice(textarea.selectionStart, textarea.selectionEnd) || "List item"}`, textarea.selectionStart, textarea.selectionEnd, "select");
        textarea.focus();
    }
}

document.querySelectorAll("[data-note-editor]").forEach((editor) => {
    const body = editor.querySelector("[data-note-body]");
    if (!body) {
        return;
    }
    updateNotePreview(editor);
    body.addEventListener("input", () => updateNotePreview(editor));
    editor.querySelectorAll("[data-note-action]").forEach((button) => {
        button.addEventListener("click", () => {
            applyNoteAction(body, button.dataset.noteAction);
            updateNotePreview(editor);
        });
    });
});

document.querySelectorAll("[data-note-render]").forEach((container) => {
    const source = container.textContent || "";
    container.innerHTML = source.trim() ? renderNoteMarkdown(source) : '<p class="meta">This note is empty.</p>';
});
