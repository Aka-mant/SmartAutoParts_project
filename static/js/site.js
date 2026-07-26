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

    document.querySelectorAll(".ai-request-form").forEach((form) => {
        form.addEventListener("submit", () => {
            const status = form.querySelector(".ai-request-status");
            const button = form.querySelector("button[type='submit']");
            if (!status) {
                return;
            }

            status.hidden = false;
            const bar = status.querySelector(".progress-bar");
            if (bar) {
                bar.style.width = "12%";
                bar.setAttribute("aria-valuenow", "12");
                window.setTimeout(() => {
                    bar.style.width = "48%";
                    bar.setAttribute("aria-valuenow", "48");
                }, 350);
                window.setTimeout(() => {
                    bar.style.width = "78%";
                    bar.setAttribute("aria-valuenow", "78");
                }, 1200);
                window.setTimeout(() => {
                    bar.style.width = "92%";
                    bar.setAttribute("aria-valuenow", "92");
                }, 2600);
            }
            if (button) {
                button.disabled = true;
                button.setAttribute("aria-busy", "true");
            }
        });
    });
});
