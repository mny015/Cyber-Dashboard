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
    toggle.setAttribute("aria-expanded", String(!menu.hidden));
});

document.querySelectorAll("[data-profile-picture]").forEach((wrapper) => {
    const toggle = wrapper.querySelector("[data-profile-picture-toggle]");
    const menu = wrapper.querySelector("[data-profile-picture-menu]");
    const uploadButton = wrapper.querySelector("[data-profile-picture-upload]");
    const fileInput = document.querySelector("#profile_image");
    const filename = wrapper.querySelector("[data-profile-picture-filename]");

    if (uploadButton && fileInput) {
        uploadButton.addEventListener("click", () => fileInput.click());
        fileInput.addEventListener("change", () => {
            if (filename) {
                filename.textContent = fileInput.files.length
                    ? `Selected: ${fileInput.files[0].name}`
                    : "No new picture selected.";
            }
        });
    }

    wrapper.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && menu && !menu.hidden) {
            menu.hidden = true;
            toggle.setAttribute("aria-expanded", "false");
            toggle.focus();
        }
    });
});

const navToggle = document.querySelector(".nav-toggle");
const navigation = document.querySelector(".nav-links");

if (navToggle && navigation) {
    const setNavigationOpen = (isOpen) => {
        navToggle.setAttribute("aria-expanded", String(isOpen));
        navToggle.setAttribute("aria-label", `${isOpen ? "Close" : "Open"} main navigation`);
        navigation.classList.toggle("is-open", isOpen);
    };

    navToggle.addEventListener("click", () => {
        const isOpen = navToggle.getAttribute("aria-expanded") === "true";
        setNavigationOpen(!isOpen);
    });

    navigation.addEventListener("click", (event) => {
        if (event.target.closest("a") && window.matchMedia("(max-width: 960px)").matches) {
            setNavigationOpen(false);
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && navToggle.getAttribute("aria-expanded") === "true") {
            setNavigationOpen(false);
            navToggle.focus();
        }
    });
}

const sidebar = document.querySelector("[data-sidebar]");
const sidebarToggle = document.querySelector("[data-sidebar-toggle]");
const sidebarMobileToggle = document.querySelector("[data-sidebar-mobile-toggle]");
const sidebarBackdrop = document.querySelector("[data-sidebar-backdrop]");
const desktopSidebar = window.matchMedia("(min-width: 961px)");

if (sidebar && sidebarToggle) {
    const setSidebarCollapsed = (isCollapsed, persist = true) => {
        document.documentElement.classList.toggle("sidebar-collapsed", isCollapsed);
        sidebarToggle.setAttribute("aria-expanded", String(!isCollapsed));
        const action = isCollapsed ? "Expand" : "Collapse";
        sidebarToggle.setAttribute("aria-label", `${action} navigation`);
        sidebarToggle.setAttribute("title", `${action} navigation`);
        if (persist) {
            localStorage.setItem("cyber-dashboard-sidebar", isCollapsed ? "collapsed" : "expanded");
        }
    };

    const setMobileSidebarOpen = (isOpen) => {
        document.body.classList.toggle("sidebar-open", isOpen);
        if (sidebarMobileToggle) {
            sidebarMobileToggle.setAttribute("aria-expanded", String(isOpen));
            sidebarMobileToggle.setAttribute("aria-label", `${isOpen ? "Close" : "Open"} navigation`);
        }
        if (!isOpen) {
            const accountMenu = sidebar.querySelector(".sidebar-account-menu");
            if (accountMenu) {
                accountMenu.removeAttribute("open");
            }
        }
    };

    setSidebarCollapsed(document.documentElement.classList.contains("sidebar-collapsed"), false);

    sidebarToggle.addEventListener("click", () => {
        if (!desktopSidebar.matches) {
            setMobileSidebarOpen(false);
            if (sidebarMobileToggle) {
                sidebarMobileToggle.focus();
            }
            return;
        }
        setSidebarCollapsed(!document.documentElement.classList.contains("sidebar-collapsed"));
    });

    if (sidebarMobileToggle) {
        sidebarMobileToggle.addEventListener("click", () => {
            const isOpen = document.body.classList.contains("sidebar-open");
            setMobileSidebarOpen(!isOpen);
            if (!isOpen) {
                sidebar.querySelector("a, button, summary")?.focus();
            }
        });
    }

    if (sidebarBackdrop) {
        sidebarBackdrop.addEventListener("click", () => {
            setMobileSidebarOpen(false);
            sidebarMobileToggle?.focus();
        });
    }

    sidebar.addEventListener("click", (event) => {
        if (!desktopSidebar.matches && event.target.closest("a")) {
            setMobileSidebarOpen(false);
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && document.body.classList.contains("sidebar-open")) {
            setMobileSidebarOpen(false);
            sidebarMobileToggle?.focus();
        }
    });

    desktopSidebar.addEventListener("change", () => setMobileSidebarOpen(false));
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
