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