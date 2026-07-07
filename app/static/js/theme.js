(() => {
    window.updateFavicon = function updateFavicon(theme) {
        const favicon = document.querySelector("link[rel='icon']");
        if (!favicon) {
            return;
        }

        favicon.href = theme === "dark"
            ? "/static/image/favicon-dark.png"
            : "/static/image/favicon-light.png";
    };

    const savedTheme = localStorage.getItem("cyber-dashboard-theme");
    const preferredTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    const theme = savedTheme || preferredTheme;
    document.documentElement.dataset.theme = theme;
    window.updateFavicon(theme);
    document.addEventListener("DOMContentLoaded", () => {
        document.body.dataset.theme = theme;
        window.updateFavicon(theme);
    });
})();
