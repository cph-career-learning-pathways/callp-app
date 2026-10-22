const sidebar = document.getElementById("sidebar");
const sidebarOpenButton = document.getElementById("sidebar-open");
const sidebarCloseButton = document.getElementById("sidebar-close");


function openSidebar() {
    sidebar.classList.add("is-open");
    sidebar.setAttribute("aria-hidden", "false");
}


function closeSidebar() {
    sidebar.classList.remove("is-open");
    sidebar.setAttribute("aria-hidden", "true");
}


// Existing sidebar behavior is retained. Guards keep the script safe if a
// future page includes main.js without rendering the sidebar controls.
if (sidebar && sidebarOpenButton) {
    sidebarOpenButton.addEventListener("click", openSidebar);
}

if (sidebar && sidebarCloseButton) {
    sidebarCloseButton.addEventListener("click", closeSidebar);
}


// ---------------------------------------------------------
// Category dropdowns
// ---------------------------------------------------------

const categoryDropdowns =
    document.querySelectorAll("[data-category-dropdown]");


function closeCategoryDropdown(dropdown) {
    const button = dropdown.querySelector("[data-dropdown-button]");
    const menu = dropdown.querySelector("[data-dropdown-menu]");

    if (!button || !menu) {
        return;
    }

    button.setAttribute("aria-expanded", "false");
    menu.hidden = true;
}


function openCategoryDropdown(dropdown) {
    categoryDropdowns.forEach((otherDropdown) => {
        if (otherDropdown !== dropdown) {
            closeCategoryDropdown(otherDropdown);
        }
    });

    closeSearchModeDropdown();

    const button = dropdown.querySelector("[data-dropdown-button]");
    const menu = dropdown.querySelector("[data-dropdown-menu]");

    if (!button || !menu) {
        return;
    }

    button.setAttribute("aria-expanded", "true");
    menu.hidden = false;
}


// Show the number of checked items on each category button.
function updateSelectionCount(dropdown) {
    const button = dropdown.querySelector("[data-dropdown-button]");
    const count = dropdown.querySelector("[data-selection-count]");

    const checkedCount = dropdown.querySelectorAll(
        'input[type="checkbox"]:checked'
    ).length;

    if (!button || !count) {
        return;
    }

    count.textContent = checkedCount;
    count.hidden = checkedCount === 0;

    button.classList.toggle(
        "has-selection",
        checkedCount > 0
    );
}


categoryDropdowns.forEach((dropdown) => {
    const button = dropdown.querySelector("[data-dropdown-button]");

    const checkboxes =
        dropdown.querySelectorAll('input[type="checkbox"]');

    if (!button) {
        return;
    }

    button.addEventListener("click", () => {
        const isOpen =
            button.getAttribute("aria-expanded") === "true";

        if (isOpen) {
            closeCategoryDropdown(dropdown);
        } else {
            openCategoryDropdown(dropdown);
        }
    });

    checkboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", () => {
            updateSelectionCount(dropdown);
        });
    });
});

// ---------------------------------------------------------
// Sidebar filter dropdowns
// ---------------------------------------------------------

const sidebarDropdowns =
    document.querySelectorAll("[data-sidebar-dropdown]");


function closeSidebarFilterDropdown(dropdown) {
    const button = dropdown.querySelector(
        "[data-sidebar-dropdown-button]"
    );

    const menu = dropdown.querySelector(
        "[data-sidebar-dropdown-menu]"
    );

    if (!button || !menu) {
        return;
    }

    button.setAttribute("aria-expanded", "false");
    menu.hidden = true;
}


function openSidebarFilterDropdown(dropdown) {
    sidebarDropdowns.forEach((otherDropdown) => {
        if (otherDropdown !== dropdown) {
            closeSidebarFilterDropdown(otherDropdown);
        }
    });

    categoryDropdowns.forEach(closeCategoryDropdown);
    closeSearchModeDropdown();

    const button = dropdown.querySelector(
        "[data-sidebar-dropdown-button]"
    );

    const menu = dropdown.querySelector(
        "[data-sidebar-dropdown-menu]"
    );

    if (!button || !menu) {
        return;
    }

    button.setAttribute("aria-expanded", "true");
    menu.hidden = false;
}


function updateSidebarSelectionCount(dropdown) {
    const count = dropdown.querySelector(
        "[data-sidebar-selection-count]"
    );

    const checkedCount = dropdown.querySelectorAll(
        'input[type="checkbox"]:checked'
    ).length;

    if (!count) {
        return;
    }

    count.textContent = checkedCount;
    count.hidden = checkedCount === 0;
}


sidebarDropdowns.forEach((dropdown) => {
    const button = dropdown.querySelector(
        "[data-sidebar-dropdown-button]"
    );

    const checkboxes = dropdown.querySelectorAll(
        'input[type="checkbox"]'
    );

    if (!button) {
        return;
    }

    button.addEventListener("click", () => {
        const isOpen =
            button.getAttribute("aria-expanded") === "true";

        if (isOpen) {
            closeSidebarFilterDropdown(dropdown);
        } else {
            openSidebarFilterDropdown(dropdown);
        }
    });

    checkboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", () => {
            updateSidebarSelectionCount(dropdown);
        });
    });

    updateSidebarSelectionCount(dropdown);
});


// ---------------------------------------------------------
// Synchronize topbar and sidebar filters
// ---------------------------------------------------------

const sharedFilterNames = [
    "skill",
    "degree_program",
    "career_field",
];


function synchronizeSharedFilter(filterName, value, checked) {
    const matchingInputs = document.querySelectorAll(
        `input[name="${filterName}"][value="${CSS.escape(value)}"]`
    );

    matchingInputs.forEach((input) => {
        input.checked = checked;
    });

    // Update the topbar count.
    categoryDropdowns.forEach((dropdown) => {
        updateSelectionCount(dropdown);
    });

    // Update the sidebar count.
    sidebarDropdowns.forEach((dropdown) => {
        updateSidebarSelectionCount(dropdown);
    });
}


document.querySelectorAll(
    'input[type="checkbox"][name="skill"], ' +
    'input[type="checkbox"][name="degree_program"], ' +
    'input[type="checkbox"][name="career_field"]'
).forEach((input) => {

    input.addEventListener("change", () => {
        synchronizeSharedFilter(
            input.name,
            input.value,
            input.checked
        );
    });

});

// ---------------------------------------------------------
// Search mode selector
// ---------------------------------------------------------

/*
 * ADDED:
 * The search field supports two search modes:
 *
 * Collections:
 *     Search collections already available in the application.
 *
 * Web:
 *     Search the web for resources through Resource Discovery.
 *
 * The selected mode is stored in the hidden search_mode input so
 * Django receives either:
 *
 *     search_mode=collections
 *
 * or:
 *
 *     search_mode=web
 */
const searchModeDropdown =
    document.querySelector("[data-search-mode-selector]");

const searchModeButton =
    document.querySelector("[data-search-mode-button]");

const searchModeMenu =
    document.querySelector("[data-search-mode-menu]");

const searchModeInput =
    document.getElementById("search-mode");

const searchModeLabel =
    document.querySelector("[data-search-mode-label]");

const searchInput =
    document.getElementById("search");

const searchModeOptions =
    document.querySelectorAll("[data-search-mode-option]");


/*
 * The placeholder immediately communicates which type of search
 * will be performed.
 */
const searchModePlaceholders = {
    collections: "Search available collections...",
    web: "Search web for resources..."
};


const searchModeLabels = {
    collections: "Collections",
    web: "Web"
};


function closeSearchModeDropdown() {
    if (!searchModeButton || !searchModeMenu) {
        return;
    }

    searchModeButton.setAttribute(
        "aria-expanded",
        "false"
    );

    searchModeMenu.hidden = true;
}


function openSearchModeDropdown() {
    if (!searchModeButton || !searchModeMenu) {
        return;
    }

    // Keep only one type of dropdown open at a time.
    categoryDropdowns.forEach(closeCategoryDropdown);

    searchModeButton.setAttribute(
        "aria-expanded",
        "true"
    );

    searchModeMenu.hidden = false;
}


/*
 * UPDATED:
 * The HTML stores the selected mode directly in
 * data-search-mode-option="collections" or "web".
 *
 * This function updates:
 * 1. The hidden form value.
 * 2. The visible mode label.
 * 3. The search placeholder.
 */
function setSearchMode(mode) {
    if (
        !searchModeInput ||
        !searchModeLabel ||
        !searchInput ||
        !searchModeLabels[mode]
    ) {
        return;
    }

    searchModeInput.value = mode;
    searchModeLabel.textContent = searchModeLabels[mode];
    searchInput.placeholder = searchModePlaceholders[mode];

    closeSearchModeDropdown();

    // Return focus to the search field so the user can immediately type.
    searchInput.focus();
}


if (searchModeButton && searchModeMenu) {
    searchModeButton.addEventListener("click", () => {
        const isOpen =
            searchModeButton.getAttribute("aria-expanded") === "true";

        if (isOpen) {
            closeSearchModeDropdown();
        } else {
            openSearchModeDropdown();
        }
    });
}


/*
 * CORRECTED:
 * Read the mode from the actual attribute used by topbar.html:
 *
 *     data-search-mode-option="collections"
 *     data-search-mode-option="web"
 */
searchModeOptions.forEach((option) => {
    option.addEventListener("click", () => {
        const mode = option.dataset.searchModeOption;

        setSearchMode(mode);
    });
});


// ---------------------------------------------------------
// Global dropdown dismissal
// ---------------------------------------------------------

// Clicking outside a dropdown closes it without clearing selections.
document.addEventListener("click", (event) => {
    categoryDropdowns.forEach((dropdown) => {
        if (!dropdown.contains(event.target)) {
            closeCategoryDropdown(dropdown);
        }
    });

    sidebarDropdowns.forEach((dropdown) => {
        if (!dropdown.contains(event.target)) {
            closeSidebarFilterDropdown(dropdown);
        }
    });

    if (
        searchModeDropdown &&
        !searchModeDropdown.contains(event.target)
    ) {
        closeSearchModeDropdown();
    }
});


// Escape closes every open dropdown.
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        categoryDropdowns.forEach(closeCategoryDropdown);
        sidebarDropdowns.forEach(closeSidebarFilterDropdown);
        closeSearchModeDropdown();
    }
});


const searchForm = document.getElementById("search-form");
const sidebarElement = document.getElementById("sidebar");

if (searchForm && sidebarElement) {
    searchForm.addEventListener("formdata", (event) => {
        const formData = event.formData;

        // Sidebar-only filters are not otherwise part of the form.
        const sidebarOnlyFilters = [
            "price",
            "source",
            "resource_type",
            "format",
            "difficulty"
        ];

        sidebarOnlyFilters.forEach((name) => {
            formData.delete(name);

            sidebarElement
                .querySelectorAll(
                    `input[type="checkbox"][name="${name}"]:checked`
                )
                .forEach((input) => {
                    formData.append(name, input.value);
                });
        });

        // The topbar owns the three shared category filters.
        // Their values are already synchronized by main.js,
        // so sidebar copies must not be submitted again.
    });
}


/* =========================================================
   RIGHT DETAIL SIDEBAR
   Issue #35 - Open / Close Behavior
   ========================================================= */

const detailSidebar = document.getElementById("detail-sidebar");
const detailOverlay = document.getElementById("detail-overlay");
const detailCloseButton = document.getElementById("detail-sidebar-close");

const collectionCards = document.querySelectorAll(
    ".collection-card[data-collection-id]"
);

let detailSidebarOpen = false;
let activeDetailCard = null;
let previousDetailFocus = null;


/**
 * Move the selected collection card left if the
 * right sidebar would otherwise cover it.
 */
function positionSelectedDetailCard(card) {
    const shell = card.closest(".collection-card-shell");

    if (!shell) {
        return;
    }

    const drawerWidth = window.innerWidth * 0.5;
    const drawerLeft = window.innerWidth - drawerWidth;

    const cardRect = shell.getBoundingClientRect();

    // Leave a small gap between the card and drawer.
    const margin = 24;

    const overlap = cardRect.right - (drawerLeft - margin);

    if (overlap > 0) {
        shell.style.setProperty(
            "--detail-card-offset",
            `${-overlap}px`
        );
    } else {
        shell.style.setProperty(
            "--detail-card-offset",
            "0px"
        );
    }

    shell.classList.add("is-detail-active");
}


/**
 * Open the right sidebar.
 */
function openDetailSidebar(card) {
    if (
        !detailSidebar ||
        !detailOverlay ||
        detailSidebarOpen
    ) {
        return;
    }

    detailSidebarOpen = true;
    activeDetailCard = card;
    previousDetailFocus = document.activeElement;

    // Make the overlay and sidebar visible.
    detailOverlay.hidden = false;
    detailSidebar.hidden = false;

    // Apply open-state styling.
    detailOverlay.classList.add("is-visible");
    detailSidebar.classList.add("is-open");

    // Highlight the selected collection card.
    card.classList.add("is-detail-selected");
    positionSelectedDetailCard(card);

    // Update accessibility state.
    detailSidebar.setAttribute("aria-hidden", "false");

    // Move keyboard focus into the sidebar.
    detailCloseButton?.focus();
}


/**
 * Close the right sidebar.
 */
function closeDetailSidebar() {
    if (!detailSidebar || !detailSidebarOpen) {
        return;
    }

    detailSidebarOpen = false;

    detailSidebar.classList.remove("is-open");
    detailOverlay.classList.remove("is-visible");

    detailSidebar.setAttribute("aria-hidden", "true");

    // Remove card highlighting.
    if (activeDetailCard) {
        const shell = activeDetailCard.closest(
            ".collection-card-shell"
        );

        activeDetailCard.classList.remove("is-detail-selected");

        if (shell) {
            shell.classList.remove("is-detail-active");
            shell.style.removeProperty("--detail-card-offset");
        }

        activeDetailCard = null;
    }

    // Hide elements after the closing animation.
    const closingSidebar = detailSidebar;

    const finishClose = () => {
        if (!detailSidebarOpen) {
            closingSidebar.hidden = true;
            detailOverlay.hidden = true;
        }
    };

    closingSidebar.addEventListener(
        "transitionend",
        finishClose,
        { once: true }
    );

    // Restore keyboard focus to the previous element.
    if (previousDetailFocus?.isConnected) {
        previousDetailFocus.focus();
    }
}


/* ---------------------------------------------------------
   Collection card click handlers
   --------------------------------------------------------- */

collectionCards.forEach((card) => {
    card.addEventListener("click", () => {
        openDetailSidebar(card);
    });

    // Support Enter and Space for keyboard users.
    card.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openDetailSidebar(card);
        }
    });
});


/* ---------------------------------------------------------
   Closing interactions
   --------------------------------------------------------- */

// Close button
detailCloseButton?.addEventListener(
    "click",
    closeDetailSidebar
);

// Clicking the dimmed background
detailOverlay?.addEventListener(
    "click",
    closeDetailSidebar
);

// Escape key
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && detailSidebarOpen) {
        event.preventDefault();
        closeDetailSidebar();
    }
});


/* =========================================================
   RIGHT SIDEBAR - COLLECTION AND RESOURCE DETAILS
   ========================================================= */

const detailContent = document.getElementById(
    "detail-sidebar-content"
);
const detailTitle = document.getElementById(
    "detail-sidebar-title"
);
const detailLabel = document.getElementById(
    "detail-sidebar-label"
);
const detailLoading = document.getElementById(
    "detail-sidebar-loading"
);
const detailError = document.getElementById(
    "detail-sidebar-error"
);
const detailNavigation = document.getElementById(
    "detail-sidebar-navigation"
);
const detailBackButton = document.getElementById(
    "detail-sidebar-back"
);

const collectionDetailCache = new Map();

let currentDetailCollection = null;
let detailRequestController = null;


/* ---------------------------------------------------------
   Helpers
   --------------------------------------------------------- */

function formatDuration(seconds) {
    if (seconds === null || seconds === undefined || seconds === "") {
        return "Not specified";
    }

    const total = Number(seconds);

    if (!Number.isSafeInteger(total) || total < 0) {
        return "Not specified";
    }

    const hours = Math.floor(total / 3600);
    const minutes = Math.floor((total % 3600) / 60);
    const remaining = total % 60;

    if (hours > 0) {
        return `${hours}:${String(minutes).padStart(2, "0")}:${String(remaining).padStart(2, "0")}`;
    }

    return `${minutes}:${String(remaining).padStart(2, "0")}`;
}


function createDetailElement(tag, className, text) {
    const element = document.createElement(tag);

    if (className) {
        element.className = className;
    }

    if (text !== undefined && text !== null) {
        element.textContent = String(text);
    }

    return element;
}


function appendDetailField(container, label, value) {
    if (value === null || value === undefined || value === "") {
        return;
    }

    const row = createDetailElement("div", "detail-field");

    row.appendChild(
        createDetailElement("dt", "detail-field-label", label)
    );

    row.appendChild(
        createDetailElement("dd", "detail-field-value", value)
    );

    container.appendChild(row);
}


function appendDetailTags(container, title, items) {
    if (!Array.isArray(items) || items.length === 0) {
        return;
    }

    const section = createDetailElement(
        "section",
        "detail-tag-section"
    );

    section.appendChild(
        createDetailElement("h3", "detail-section-title", title)
    );

    const tags = createDetailElement(
        "div",
        "detail-tag-list"
    );

    items.forEach((item) => {
        const tag = createDetailElement(
            "span",
            "detail-tag",
            item.name
        );

        tags.appendChild(tag);
    });

    section.appendChild(tags);
    container.appendChild(section);
}


/* ---------------------------------------------------------
   Render collection details
   --------------------------------------------------------- */

function renderCollectionDetails(collection) {
    if (!detailContent) {
        return;
    }

    currentDetailCollection = collection;

    detailContent.replaceChildren();

    detailLabel.textContent = "COLLECTION";
    detailTitle.textContent = collection.name;

    detailNavigation.hidden = true;

    const container = createDetailElement(
        "div",
        "detail-collection"
    );

    if (collection.description) {
        container.appendChild(
            createDetailElement(
                "p",
                "detail-description",
                collection.description
            )
        );
    }

    const resources = collection.resources || [];

    container.appendChild(
        createDetailElement(
            "h3",
            "detail-section-title",
            `Resources (${resources.length})`
        )
    );

    if (resources.length === 0) {
        container.appendChild(
            createDetailElement(
                "p",
                "detail-empty",
                "This collection has no available resources."
            )
        );
    }

    const list = createDetailElement(
        "div",
        "detail-resource-list"
    );

    resources.forEach((resource, index) => {
        const button = createDetailElement(
            "button",
            "detail-resource-item"
        );

        button.type = "button";

        button.appendChild(
            createDetailElement(
                "span",
                "detail-resource-number",
                String(index + 1)
            )
        );

        const info = createDetailElement(
            "div",
            "detail-resource-info"
        );

        info.appendChild(
            createDetailElement(
                "span",
                "detail-resource-name",
                resource.title
            )
        );

        const metadata = [
            resource.resource_type,
            resource.resource_format,
            resource.source
        ].filter(Boolean).join(" · ");

        if (metadata) {
            info.appendChild(
                createDetailElement(
                    "span",
                    "detail-resource-meta",
                    metadata
                )
            );
        }

        button.appendChild(info);

        button.appendChild(
            createDetailElement(
                "span",
                "detail-resource-arrow",
                "→"
            )
        );

        button.addEventListener("click", () => {
            renderResourceDetails(resource);
        });

        list.appendChild(button);
    });

    container.appendChild(list);
    detailContent.appendChild(container);
    detailContent.scrollTop = 0;
}


/* ---------------------------------------------------------
   Render individual resource details
   --------------------------------------------------------- */

function renderResourceDetails(resource) {
    if (!detailContent) {
        return;
    }

    detailContent.replaceChildren();

    detailLabel.textContent = "RESOURCE";
    detailTitle.textContent = resource.title;

    detailNavigation.hidden = false;

    const container = createDetailElement(
        "div",
        "detail-resource"
    );

    if (resource.description) {
        container.appendChild(
            createDetailElement(
                "p",
                "detail-description",
                resource.description
            )
        );
    }

    const fields = createDetailElement(
        "dl",
        "detail-fields"
    );

    appendDetailField(
        fields,
        "Resource type",
        resource.resource_type
    );

    appendDetailField(
        fields,
        "Format",
        resource.resource_format
    );

    appendDetailField(
        fields,
        "Duration",
        formatDuration(resource.duration)
    );

    appendDetailField(
        fields,
        "Source",
        resource.source
    );

    appendDetailField(
        fields,
        "Price",
        resource.price_model
    );

    if (resource.publication_date) {
        const date = new Date(resource.publication_date);

        if (!Number.isNaN(date.getTime())) {
            appendDetailField(
                fields,
                "Published",
                date.toLocaleDateString()
            );
        }
    }

    container.appendChild(fields);

    appendDetailTags(
        container,
        "Categories",
        resource.categories
    );

    appendDetailTags(
        container,
        "Additional information",
        resource.filters
    );

    if (resource.url) {
        try {
            const url = new URL(resource.url);

            if (["https:", "http:"].includes(url.protocol)) {
                const link = createDetailElement(
                    "a",
                    "detail-external-link",
                    "Open Resource ↗"
                );

                link.href = url.href;
                link.target = "_blank";
                link.rel = "noopener noreferrer";

                container.appendChild(link);
            }
        } catch {
            // Do not create links for invalid URLs.
        }
    }

    detailContent.appendChild(container);
    detailContent.scrollTop = 0;

    detailBackButton?.focus();
}


/* ---------------------------------------------------------
   Fetch collection details from Django
   --------------------------------------------------------- */

async function loadCollectionDetails(card) {
    const url = card.dataset.detailUrl;

    if (!url || !detailContent) {
        return;
    }

    // Cancel any previous request.
    detailRequestController?.abort();

    const controller = new AbortController();
    detailRequestController = controller;

    detailContent.replaceChildren();
    detailNavigation.hidden = true;
    detailError.hidden = true;

    detailLabel.textContent = "COLLECTION";
    detailTitle.textContent = "Collection Details";

    // Use cached data if available.
    if (collectionDetailCache.has(url)) {
        detailLoading.hidden = true;

        renderCollectionDetails(
            collectionDetailCache.get(url)
        );

        return;
    }

    detailLoading.hidden = false;

    try {
        const response = await fetch(url, {
            method: "GET",
            credentials: "same-origin",
            signal: controller.signal,
            headers: {
                "Accept": "application/json"
            }
        });

        if (!response.ok) {
            throw new Error(
                `Collection request failed: ${response.status}`
            );
        }

        const collection = await response.json();

        if (controller.signal.aborted || !detailSidebarOpen) {
            return;
        }

        collectionDetailCache.set(url, collection);

        detailLoading.hidden = true;
        renderCollectionDetails(collection);

    } catch (error) {
        if (error.name === "AbortError") {
            return;
        }

        console.error(
            "Unable to load collection details:",
            error
        );

        if (!detailSidebarOpen) {
            return;
        }

        detailLoading.hidden = true;
        detailError.hidden = false;

    } finally {
        if (detailRequestController === controller) {
            detailRequestController = null;
        }
    }
}


/* ---------------------------------------------------------
   Back navigation
   --------------------------------------------------------- */

detailBackButton?.addEventListener("click", () => {
    if (currentDetailCollection) {
        renderCollectionDetails(currentDetailCollection);
        detailBackButton.hidden = false;
        detailCloseButton?.focus();
    }
});
