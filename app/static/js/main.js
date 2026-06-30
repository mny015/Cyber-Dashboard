document.addEventListener("submit", (event) => {
    const form = event.target;
    const message = form.dataset.confirm;
    if (message && !window.confirm(message)) {
        event.preventDefault();
    }
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
