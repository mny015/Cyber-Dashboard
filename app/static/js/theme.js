(() => {
    const savedTheme = localStorage.getItem("cyber-dashboard-theme");
    const preferredTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    const theme = savedTheme || preferredTheme;
    document.documentElement.dataset.theme = theme;
    document.addEventListener("DOMContentLoaded", () => {
        document.body.dataset.theme = theme;
    });
})();
