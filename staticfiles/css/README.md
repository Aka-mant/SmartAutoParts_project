# SmartAutoParts CSS components

Главный файл `style.css` импортирует компоненты в порядке исходного каскада.

## Структура

- `components/_base.css` — CSS-переменные и глобальные правила.
- `components/_navbar.css` — header, navbar и dropdown.
- `components/_hero.css` — hero и форма поиска.
- `components/_sections.css` — общие секции и заголовки.
- `components/_cards.css` — базовые правила карточек.
- `components/_feature_card.css`, `_pricing_card.css`, `_review_card.css` — карточки главной страницы.
- `components/_footer.css` — footer.
- `components/_legal_document.css` — юридические страницы.
- `components/_auth.css` — вход и регистрация.
- `components/_account.css` — оболочка аккаунта, empty state, pagination.
- `components/_profile.css`, `_profile_edit.css` — профиль и редактирование.
- `components/_history_card.css` — общая карточка истории.
- `components/_search_history_card.css` — оформление истории поиска.
- `components/_repair_history_card.css` — оформление истории ремонта.
- `media/_media992.css`, `_media768.css`, `_media576.css` — адаптивные правила.
- `media/_print.css` — печатная версия.

Файл `_part_card.css` не создан: в исходном CSS отсутствуют селекторы карточки запчасти. Его следует добавить после появления соответствующих классов в шаблоне, не смешивая их с универсальным `.card`.
