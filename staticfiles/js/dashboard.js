"use strict";

/**
 * Dashboard SmartAutoParts
 *
 * Bootstrap 5
 * Автор: SmartAutoParts
 */

document.addEventListener("DOMContentLoaded", () => {
    initializeTooltips();
    initializePopovers();
    initializeProgressAnimation();
    initializeSearch();
    initializeCards();
    initializeAlerts();
    initializeAutoRefresh();
    initializePartSearchInputs();
});


/**
 * Bootstrap Tooltips
 */
function initializeTooltips() {

    document
        .querySelectorAll('[data-bs-toggle="tooltip"]')
        .forEach((element) => {

            new bootstrap.Tooltip(element);

        });

}


/**
 * Bootstrap Popovers
 */
function initializePopovers() {

    document
        .querySelectorAll('[data-bs-toggle="popover"]')
        .forEach((element) => {

            new bootstrap.Popover(element);

        });

}


/**
 * Анимация ProgressBar
 */
function initializeProgressAnimation() {

    const bars = document.querySelectorAll(".progress-bar");

    bars.forEach((bar) => {

        const width = bar.style.width;

        bar.style.width = "0";

        requestAnimationFrame(() => {

            setTimeout(() => {

                bar.style.transition =
                    "width .9s ease";

                bar.style.width = width;

            }, 150);

        });

    });

}


/**
 * Поиск OEM
 */
function initializeSearch() {

    const input = document.getElementById(
        "dashboard-part-search"
    );

    if (!input) {

        return;

    }

    input.addEventListener(
        "keyup",
        function () {

            this.value = this.value.toUpperCase();

        }
    );

}


/**
 * Hover карточек
 */
function initializeCards() {

    document
        .querySelectorAll(".card")
        .forEach((card) => {

            card.addEventListener(
                "mouseenter",
                () => {

                    card.classList.add(
                        "shadow-lg"
                    );

                }
            );

            card.addEventListener(
                "mouseleave",
                () => {

                    card.classList.remove(
                        "shadow-lg"
                    );

                }
            );

        });

}


/**
 * Автоматическое скрытие уведомлений
 */
function initializeAlerts() {

    const alerts = document.querySelectorAll(
        ".alert"
    );

    alerts.forEach((alert) => {

        setTimeout(() => {

            const instance =
                bootstrap.Alert.getOrCreateInstance(
                    alert
                );

            instance.close();

        }, 6000);

    });

}


/**
 * Обновление Dashboard
 */
function initializeAutoRefresh() {

    const refreshEnabled = false;

    if (!refreshEnabled) {

        return;

    }

    setInterval(() => {

        location.reload();

    }, 300000);

}


/**
 * Копирование текста
 */
function copyToClipboard(text) {

    navigator.clipboard
        .writeText(text)
        .then(() => {

            console.log("Скопировано");

        });

}


/**
 * Уведомление Bootstrap Toast
 */
function showToast(message, type = "success") {

    const container = document.createElement("div");

    container.className =
        "toast-container position-fixed top-0 end-0 p-3";

    container.innerHTML = `
        <div class="toast text-bg-${type}" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>

                <button
                    type="button"
                    class="btn-close btn-close-white me-2 m-auto"
                    data-bs-dismiss="toast"
                ></button>
            </div>
        </div>
    `;

    document.body.appendChild(container);

    const toastElement =
        container.querySelector(".toast");

    const toast =
        new bootstrap.Toast(toastElement);

    toast.show();

    toastElement.addEventListener(
        "hidden.bs.toast",
        () => {

            container.remove();

        }
    );

}


/**
 * Плавная прокрутка
 */
document
    .querySelectorAll('a[href^="#"]')
    .forEach((anchor) => {

        anchor.addEventListener(
            "click",
            function (event) {

                event.preventDefault();

                const target =
                    document.querySelector(
                        this.getAttribute("href")
                    );

                if (!target) {

                    return;

                }

                target.scrollIntoView({

                    behavior: "smooth",

                    block: "start",

                });

            }
        );

    });


/**
 * Возвращает форматированную дату.
 */
function formatDate(date) {

    return new Intl.DateTimeFormat(

        "ru-RU",

        {

            day: "2-digit",

            month: "2-digit",

            year: "numeric",

            hour: "2-digit",

            minute: "2-digit",

        }

    ).format(date);

}

function initializePartSearchInputs() {
    const searchInputs = document.querySelectorAll(
        'input[name="q"]'
    );

    searchInputs.forEach((input) => {
        input.addEventListener("input", () => {
            input.value = input.value.toUpperCase();
        });
    });
}