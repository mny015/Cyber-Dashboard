(() => {
    const savedTheme = localStorage.getItem("cyber-dashboard-theme");
    const preferredTheme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    const theme = savedTheme || preferredTheme;
    const savedSidebar = localStorage.getItem("cyber-dashboard-sidebar");
    document.documentElement.classList.toggle("sidebar-collapsed", savedSidebar === "collapsed");
    document.documentElement.dataset.theme = theme;
    document.addEventListener("DOMContentLoaded", () => {
        document.body.dataset.theme = theme;
    });
})();
