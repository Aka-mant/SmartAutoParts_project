(function () {
    "use strict";

    const viewer = document.getElementById("project-image-viewer");
    if (!viewer) {
        return;
    }

    const viewerImage = viewer.querySelector("[data-viewer-image]");
    const viewerCounter = viewer.querySelector("[data-viewer-counter]");
    const viewerThumbnails = viewer.querySelector(
        "[data-viewer-thumbnails]"
    );
    const viewerPrevious = viewer.querySelector("[data-viewer-previous]");
    const viewerNext = viewer.querySelector("[data-viewer-next]");
    const viewerClose = viewer.querySelector(".image-viewer__close");

    let viewerItems = [];
    let viewerIndex = 0;
    let lastFocusedElement = null;
    const touchStarts = new WeakMap();

    function galleryItems(gallery) {
        const items = Array.from(
            gallery.querySelectorAll("[data-gallery-thumbnail]")
        ).map(function (button) {
            return {
                url: button.getAttribute("data-image-url"),
                alt: button.getAttribute("data-image-alt") || "",
                button: button,
            };
        }).filter(function (item) {
            return Boolean(item.url);
        });

        if (items.length === 0) {
            const image = gallery.querySelector("[data-gallery-main]");
            if (image && image.getAttribute("src")) {
                items.push({
                    url: image.getAttribute("src"),
                    alt: image.getAttribute("alt") || "",
                    button: null,
                });
            }
        }
        return items;
    }

    function normalizedIndex(index, length) {
        return ((index % length) + length) % length;
    }

    function showInGallery(gallery, requestedIndex) {
        const items = galleryItems(gallery);
        const mainImage = gallery.querySelector("[data-gallery-main]");
        if (!mainImage || items.length === 0) {
            return;
        }

        const index = normalizedIndex(requestedIndex, items.length);
        const selected = items[index];
        gallery.setAttribute("data-gallery-index", String(index));
        mainImage.setAttribute("src", selected.url);
        mainImage.setAttribute("alt", selected.alt);

        items.forEach(function (item, itemIndex) {
            if (!item.button) {
                return;
            }
            const active = itemIndex === index;
            item.button.classList.toggle("is-active", active);
            item.button.setAttribute(
                "aria-current",
                active ? "true" : "false"
            );
        });

        const counter = gallery.querySelector("[data-gallery-counter]");
        if (counter) {
            counter.textContent = (index + 1) + " / " + items.length;
        }

        const singleImage = items.length < 2;
        const previous = gallery.querySelector("[data-gallery-previous]");
        const next = gallery.querySelector("[data-gallery-next]");
        if (previous) {
            previous.hidden = singleImage;
        }
        if (next) {
            next.hidden = singleImage;
        }
    }

    function moveInGallery(gallery, step) {
        const index = Number.parseInt(
            gallery.getAttribute("data-gallery-index") || "0",
            10
        );
        showInGallery(gallery, index + step);
    }

    function renderViewer() {
        if (viewerItems.length === 0) {
            return;
        }

        viewerIndex = normalizedIndex(viewerIndex, viewerItems.length);
        const item = viewerItems[viewerIndex];
        viewerImage.setAttribute("src", item.url);
        viewerImage.setAttribute("alt", item.alt);
        viewerCounter.textContent = (
            (viewerIndex + 1) + " / " + viewerItems.length
        );

        Array.from(viewerThumbnails.children).forEach(
            function (thumbnail, index) {
                thumbnail.classList.toggle(
                    "is-active",
                    index === viewerIndex
                );
                thumbnail.setAttribute(
                    "aria-current",
                    index === viewerIndex ? "true" : "false"
                );
            }
        );

        viewerPrevious.hidden = viewerItems.length < 2;
        viewerNext.hidden = viewerItems.length < 2;
    }

    function openViewer(gallery) {
        viewerItems = galleryItems(gallery);
        if (viewerItems.length === 0) {
            return;
        }

        viewerIndex = Number.parseInt(
            gallery.getAttribute("data-gallery-index") || "0",
            10
        );
        lastFocusedElement = document.activeElement;
        viewerThumbnails.replaceChildren();

        viewerItems.forEach(function (item, index) {
            const button = document.createElement("button");
            const image = document.createElement("img");
            button.type = "button";
            button.className = "image-viewer__thumbnail";
            button.setAttribute(
                "aria-label",
                "Открыть изображение " + (index + 1)
            );
            button.addEventListener("click", function () {
                viewerIndex = index;
                renderViewer();
            });
            image.src = item.url;
            image.alt = "";
            image.loading = "lazy";
            button.appendChild(image);
            viewerThumbnails.appendChild(button);
        });

        viewer.hidden = false;
        document.body.classList.add("has-image-viewer");
        renderViewer();
        viewerClose.focus();
    }

    function closeViewer() {
        viewer.hidden = true;
        viewerImage.removeAttribute("src");
        document.body.classList.remove("has-image-viewer");
        if (lastFocusedElement && lastFocusedElement.focus) {
            lastFocusedElement.focus();
        }
    }

    function moveViewer(step) {
        if (viewerItems.length > 1) {
            viewerIndex += step;
            renderViewer();
        }
    }

    document.querySelectorAll("[data-photo-gallery]").forEach(
        function (gallery) {
            showInGallery(gallery, 0);
        }
    );

    document.addEventListener("click", function (event) {
        const target = event.target.closest(
            "[data-gallery-thumbnail],"
            + "[data-gallery-previous],"
            + "[data-gallery-next],"
            + "[data-gallery-fullscreen],"
            + "[data-gallery-main]"
        );
        if (!target) {
            return;
        }

        const gallery = target.closest("[data-photo-gallery]");
        if (!gallery) {
            return;
        }
        event.preventDefault();
        event.stopPropagation();

        if (target.hasAttribute("data-gallery-thumbnail")) {
            const buttons = Array.from(
                gallery.querySelectorAll("[data-gallery-thumbnail]")
            );
            showInGallery(gallery, buttons.indexOf(target));
        } else if (target.hasAttribute("data-gallery-previous")) {
            moveInGallery(gallery, -1);
        } else if (target.hasAttribute("data-gallery-next")) {
            moveInGallery(gallery, 1);
        } else {
            openViewer(gallery);
        }
    });

    viewerPrevious.addEventListener("click", function () {
        moveViewer(-1);
    });
    viewerNext.addEventListener("click", function () {
        moveViewer(1);
    });
    viewer.querySelectorAll("[data-viewer-close]").forEach(
        function (button) {
            button.addEventListener("click", closeViewer);
        }
    );

    document.addEventListener("keydown", function (event) {
        if (!viewer.hidden) {
            if (event.key === "ArrowLeft") {
                event.preventDefault();
                moveViewer(-1);
            } else if (event.key === "ArrowRight") {
                event.preventDefault();
                moveViewer(1);
            } else if (event.key === "Escape") {
                event.preventDefault();
                closeViewer();
            }
            return;
        }

        const gallery = document.activeElement.closest
            ? document.activeElement.closest("[data-photo-gallery]")
            : null;
        if (!gallery) {
            return;
        }
        if (event.key === "ArrowLeft") {
            event.preventDefault();
            moveInGallery(gallery, -1);
        } else if (event.key === "ArrowRight") {
            event.preventDefault();
            moveInGallery(gallery, 1);
        } else if (event.key === "Enter") {
            event.preventDefault();
            openViewer(gallery);
        }
    });

    document.addEventListener("touchstart", function (event) {
        const area = event.target.closest(
            "#project-image-viewer:not([hidden]), [data-photo-gallery]"
        );
        const startX = event.changedTouches[0]
            ? event.changedTouches[0].clientX
            : null;
        if (area && typeof startX === "number") {
            touchStarts.set(area, startX);
        }
    }, { passive: true });

    document.addEventListener("touchend", function (event) {
        const area = event.target.closest(
            "#project-image-viewer:not([hidden]), [data-photo-gallery]"
        );
        if (!area || !touchStarts.has(area)) {
            return;
        }
        const startX = touchStarts.get(area);
        const endX = event.changedTouches[0]
            ? event.changedTouches[0].clientX
            : null;
        touchStarts.delete(area);
        if (typeof endX !== "number" || Math.abs(endX - startX) < 45) {
            return;
        }
        const step = endX > startX ? -1 : 1;
        if (area === viewer) {
            moveViewer(step);
        } else {
            moveInGallery(area, step);
        }
    }, { passive: true });
}());
