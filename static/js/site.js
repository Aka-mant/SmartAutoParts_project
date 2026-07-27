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
        form.addEventListener("submit", (event) => {
            const confirmation = form.dataset.confirm;
            if (confirmation && !window.confirm(confirmation)) {
                event.preventDefault();
                return;
            }

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

    const pasteImageButton = document.getElementById(
        "paste-image-button"
    );
    const imageInput = document.getElementById("id_image");
    const pasteImageStatus = document.getElementById(
        "paste-image-status"
    );

    if (pasteImageButton && imageInput && pasteImageStatus) {
        const maxImageBytes = 5 * 1024 * 1024;

        const setClipboardImage = (blob) => {
            if (!blob || !blob.type.startsWith("image/")) {
                pasteImageStatus.textContent = (
                    "В буфере обмена нет изображения."
                );
                return false;
            }
            if (blob.size > maxImageBytes) {
                pasteImageStatus.textContent = (
                    "Изображение из буфера превышает 5 МБ."
                );
                return false;
            }

            const extension = blob.type.split("/")[1]
                .replace("jpeg", "jpg")
                .replace("svg+xml", "svg");
            const file = new File(
                [blob],
                `clipboard-image.${extension}`,
                { type: blob.type }
            );
            const transfer = new DataTransfer();
            transfer.items.add(file);
            imageInput.files = transfer.files;
            imageInput.dispatchEvent(
                new Event("change", { bubbles: true })
            );
            pasteImageStatus.textContent = (
                `Изображение вставлено: ${file.name}`
            );
            return true;
        };

        pasteImageButton.addEventListener("click", async () => {
            pasteImageStatus.textContent = "Читаем буфер обмена…";
            if (!navigator.clipboard?.read) {
                pasteImageStatus.textContent = (
                    "Браузер не разрешает чтение по кнопке. "
                    + "Скопируйте изображение и нажмите Ctrl+V."
                );
                return;
            }

            try {
                const clipboardItems = await navigator.clipboard.read();
                for (const item of clipboardItems) {
                    const imageType = item.types.find((type) => (
                        type.startsWith("image/")
                    ));
                    if (imageType) {
                        const blob = await item.getType(imageType);
                        setClipboardImage(blob);
                        return;
                    }
                }
                pasteImageStatus.textContent = (
                    "В буфере обмена нет изображения."
                );
            } catch (error) {
                pasteImageStatus.textContent = (
                    "Не удалось прочитать буфер. "
                    + "Разрешите доступ или нажмите Ctrl+V."
                );
            }
        });

        document.addEventListener("paste", (event) => {
            const clipboardFiles = Array.from(
                event.clipboardData?.files || []
            );
            const image = clipboardFiles.find((file) => (
                file.type.startsWith("image/")
            ));
            if (image && setClipboardImage(image)) {
                event.preventDefault();
            }
        });
    }
});
