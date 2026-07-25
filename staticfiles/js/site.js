document.addEventListener("DOMContentLoaded", () => {
    const oemInputs = document.querySelectorAll(
        "#home-part-search, #part-search-query"
    );

    oemInputs.forEach((input) => {
        input.addEventListener("input", () => {
            const selectionStart = input.selectionStart;
            const selectionEnd = input.selectionEnd;

            input.value = input.value.toUpperCase();

            if (selectionStart !== null && selectionEnd !== null) {
                input.setSelectionRange(selectionStart, selectionEnd);
            }
        });
    });

    const navbar = document.getElementById("navbarNav");

    if (navbar && window.bootstrap) {
        navbar.querySelectorAll("a.nav-link").forEach((link) => {
            link.addEventListener("click", () => {
                if (window.innerWidth < 992 && navbar.classList.contains("show")) {
                    window.bootstrap.Collapse.getOrCreateInstance(navbar).hide();
                }
            });
        });
    }
});
