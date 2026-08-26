let savedPapers = JSON.parse(
    localStorage.getItem("researchAI_savedPapers")
) || [];


// Latest search/PDF results
let currentPapers = [];



// ======================================================
// SEARCH PAPERS
// ======================================================

async function searchPapers() {

    const input =
        document.getElementById("searchInput");

    const query =
        input.value.trim();

    const sort =
        document.getElementById("sortFilter").value;

    const category =
        document.getElementById("categoryFilter").value;

    const container =
        document.getElementById("papersContainer");

    const loading =
        document.getElementById("loading");

    const error =
        document.getElementById("error");

    const resultCount =
        document.getElementById("resultCount");


    if (!query) {

        error.textContent =
            "Enter a research topic to begin.";

        return;
    }


    container.innerHTML = "";

    error.textContent = "";

    resultCount.textContent = "";

    loading.style.display = "flex";


    try {

        const url =
            `/api/search?query=${encodeURIComponent(query)}` +
            `&sort=${encodeURIComponent(sort)}` +
            `&category=${encodeURIComponent(category)}`;


        const response =
            await fetch(url);


        const data =
            await response.json();


        if (!data.success) {

            throw new Error(
                data.message || "Search failed."
            );

        }


        currentPapers =
            data.papers || [];


        resultCount.textContent =
            `${currentPapers.length} papers selected from ${data.candidate_papers} candidates`;


        displayClusters(
            data.clusters
        );


        displayPapers(
            currentPapers
        );

    }

    catch (err) {

        console.error(err);

        error.textContent =
            err.message ||
            "Something went wrong.";

    }

    finally {

        loading.style.display = "none";

    }

}



// ======================================================
// PDF UPLOAD / ANALYSIS
// ======================================================

async function uploadPaper() {

    const fileInput =
        document.getElementById("pdfInput");

    const status =
        document.getElementById("uploadStatus");

    const container =
        document.getElementById("papersContainer");

    const error =
        document.getElementById("error");

    const resultCount =
        document.getElementById("resultCount");


    const file =
        fileInput.files[0];


    if (!file) {

        status.innerHTML = `

            <span class="upload-error">

                ✕ Please select a PDF first.

            </span>

        `;

        return;

    }


    if (
        !file.name
            .toLowerCase()
            .endsWith(".pdf")
    ) {

        status.innerHTML = `

            <span class="upload-error">

                ✕ Only PDF files are supported.

            </span>

        `;

        return;

    }


    status.innerHTML = `

        <div class="analysis-status">

            <div class="loader"></div>

            <span>
                Reading paper and finding similar research...
            </span>

        </div>

    `;


    container.innerHTML = "";

    error.textContent = "";

    resultCount.textContent = "";


    try {

        const formData =
            new FormData();


        formData.append(
            "file",
            file
        );


        const response =
            await fetch(
                "/api/upload",
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        if (!data.success) {

            throw new Error(
                data.message ||
                "PDF analysis failed."
            );

        }


        // Store PDF results

        currentPapers =
            data.papers || [];


        status.innerHTML = `

            <div class="analysis-complete">

                <span class="success-icon">
                    ✓
                </span>

                <div>

                    <strong>
                        Analysis complete
                    </strong>

                    <span>
                        ${escapeHTML(
                            data.filename
                        )}
                    </span>

                </div>

            </div>

        `;


        resultCount.textContent =
            `${currentPapers.length} similar papers found`;


        // Display research clusters

        displayClusters(
            data.clusters
        );


        // Apply current filters

        applyFiltersToCurrentPapers();


        // Scroll to results

        document
            .getElementById("topics")
            .scrollIntoView({
                behavior: "smooth"
            });

    }

    catch (err) {

        console.error(err);

        status.innerHTML = `

            <span class="upload-error">

                ✕ ${escapeHTML(
                    err.message ||
                    "PDF analysis failed."
                )}

            </span>

        `;

    }

}



// ======================================================
// APPLY FILTERS
// ======================================================

function applyFiltersToCurrentPapers() {

    if (!currentPapers.length) {

        displayPapers([]);

        return;

    }


    const sort =
        document.getElementById(
            "sortFilter"
        ).value;


    const category =
        document.getElementById(
            "categoryFilter"
        ).value;


    let filtered =
        [...currentPapers];


    // --------------------------------------------------
    // CATEGORY FILTER
    // --------------------------------------------------

    if (category !== "all") {

        filtered =
            filtered.filter(
                paper => {

                    const categories =
                        paper.categories || [];


                    return categories.includes(
                        category
                    );

                }
            );

    }


    // --------------------------------------------------
    // SORT
    // --------------------------------------------------

    if (sort === "newest") {

        filtered.sort(
            (a, b) => {

                return (
                    (b.published || "")
                        .localeCompare(
                            a.published || ""
                        )
                );

            }
        );

    }


    else if (sort === "oldest") {

        filtered.sort(
            (a, b) => {

                return (
                    (a.published || "")
                        .localeCompare(
                            b.published || ""
                        )
                );

            }
        );

    }


    else {

        // AI relevance

        filtered.sort(
            (a, b) => {

                return (
                    (b.similarity_score || 0) -
                    (a.similarity_score || 0)
                );

            }
        );

    }


    displayPapers(
        filtered
    );


    const resultCount =
        document.getElementById(
            "resultCount"
        );


    resultCount.textContent =
        `${filtered.length} papers shown`;

}



// ======================================================
// FILTER EVENTS
// ======================================================

const sortFilter =
    document.getElementById(
        "sortFilter"
    );


const categoryFilter =
    document.getElementById(
        "categoryFilter"
    );


if (sortFilter) {

    sortFilter.addEventListener(
        "change",
        function () {

            if (currentPapers.length) {

                applyFiltersToCurrentPapers();

            }

        }
    );

}


if (categoryFilter) {

    categoryFilter.addEventListener(
        "change",
        function () {

            if (currentPapers.length) {

                applyFiltersToCurrentPapers();

            }

        }
    );

}



// ======================================================
// DISPLAY RESEARCH CLUSTERS
// ======================================================

function displayClusters(
    clusters
) {

    const container =
        document.getElementById(
            "clustersContainer"
        );


    if (!container) {

        return;

    }


    container.innerHTML = "";


    if (
        !clusters ||
        clusters.length === 0
    ) {

        return;

    }


    clusters.forEach(
        (cluster, index) => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "cluster-card";


            card.innerHTML = `

                <div class="cluster-number">

                    ${String(
                        index + 1
                    ).padStart(2, "0")}

                </div>


                <div class="cluster-info">

                    <h3>

                        ${escapeHTML(
                            cluster.name
                        )}

                    </h3>


                    <p>

                        ${cluster.size}
                        papers in this cluster

                    </p>

                </div>

            `;


            container.appendChild(
                card
            );

        }
    );

}



// ======================================================
// DISPLAY PAPERS
// ======================================================

function displayPapers(
    papers
) {

    const container =
        document.getElementById(
            "papersContainer"
        );


    if (!container) {

        return;

    }


    container.innerHTML = "";


    if (
        !papers ||
        papers.length === 0
    ) {

        container.innerHTML = `

            <div class="paper-card">

                <div class="paper-title">

                    No papers found.

                </div>


                <p class="paper-authors">

                    No papers match the selected filters.

                </p>

            </div>

        `;

        return;

    }


    papers.forEach(
        (paper, index) => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "paper-card";


            const authors =
                paper.authors &&
                paper.authors.length

                    ? paper.authors.join(", ")

                    : "Unknown authors";


            const categories =
                paper.categories &&
                paper.categories.length

                    ? paper.categories.join(", ")

                    : "Research";


            const publishedDate =
                paper.published

                    ? paper.published.substring(
                        0,
                        10
                    )

                    : "Unknown";


            const similarity =
                typeof paper.similarity_score ===
                "number"

                    ? paper.similarity_score

                    : 0;


            // ==========================================
            // RELEVANCE SCORE OUT OF 10
            // ==========================================

            const maxSimilarity = Math.max(
                ...papers.map(
                    p =>
                        typeof p.similarity_score === "number"
                            ? p.similarity_score
                            : 0
                ),
                0.01
            );


            const scoreOutOf10 = Math.min(
                10,
                (similarity / maxSimilarity) * 10
            );


            const scoreDisplay =
                scoreOutOf10.toFixed(1);


            const scoreWidth =
                Math.min(
                    100,
                    scoreOutOf10 * 10
                );


            const isSaved =
                savedPapers.some(
                    saved =>
                        saved.id === paper.id
                );


            card.innerHTML = `

                <div class="paper-index">

                    ${String(
                        index + 1
                    ).padStart(2, "0")}

                </div>


                <div class="paper-title">

                    ${escapeHTML(
                        paper.title
                    )}

                </div>


                <div class="paper-authors">

                    ${escapeHTML(
                        authors
                    )}

                </div>


                <div class="paper-date">

                    ${publishedDate}

                    ·

                    ${escapeHTML(
                        categories
                    )}

                </div>


                <div class="ai-score">

                    <div class="ai-score-header">

                        <span>
                            RELEVANCE MATCH
                        </span>

                        <strong>
                            ${scoreDisplay}/10
                        </strong>

                    </div>


                    <div class="score-bar">

                        <div
                            class="score-fill"
                            style="
                                width: ${scoreWidth}%
                            "
                        ></div>

                    </div>

                </div>


                <div class="paper-abstract">

                    ${escapeHTML(
                        paper.abstract
                    )}

                </div>


                <div class="paper-actions">

                    ${
                        paper.paper_url
                            ? `

                                <a
                                    class="read-paper"
                                    href="${paper.paper_url}"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >

                                    Read Paper →

                                </a>

                            `
                            : ""
                    }


                    ${
                        paper.pdf_url
                            ? `

                                <a
                                    class="read-pdf"
                                    href="${paper.pdf_url}"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >

                                    PDF

                                </a>

                            `
                            : ""
                    }


                    <button
                        class="
                            save-paper
                            ${isSaved ? "saved" : ""}
                        "
                        onclick="toggleSavePaper(
                            ${JSON.stringify(
                                paper
                            ).replace(
                                /"/g,
                                "&quot;"
                            )}
                        )"
                    >

                        ${
                            isSaved
                                ? "✓ Saved"
                                : "☆ Save"
                        }

                    </button>

                </div>

            `;


            container.appendChild(
                card
            );

        }
    );

}



// ======================================================
// SAVE PAPER
// ======================================================

function toggleSavePaper(
    paper
) {

    const existingIndex =
        savedPapers.findIndex(
            saved =>
                saved.id === paper.id
        );


    if (
        existingIndex !== -1
    ) {

        savedPapers.splice(
            existingIndex,
            1
        );

    }

    else {

        savedPapers.push(
            paper
        );

    }


    localStorage.setItem(
        "researchAI_savedPapers",
        JSON.stringify(
            savedPapers
        )
    );


    displaySavedPapers();


    // Refresh currently displayed results

    if (currentPapers.length) {

        applyFiltersToCurrentPapers();

    }

}



// ======================================================
// DISPLAY SAVED PAPERS
// ======================================================

function displaySavedPapers() {

    const container =
        document.getElementById(
            "savedPapersContainer"
        );


    const count =
        document.getElementById(
            "savedCount"
        );


    if (!container || !count) {

        return;

    }


    count.textContent =
        `${savedPapers.length} saved`;


    container.innerHTML = "";


    if (
        savedPapers.length === 0
    ) {

        container.innerHTML = `

            <div class="empty-library">

                <div class="empty-icon">
                    ☆
                </div>


                <h3>
                    Nothing saved yet
                </h3>


                <p>
                    Save interesting papers while exploring.
                </p>

            </div>

        `;

        return;

    }


    savedPapers.forEach(
        paper => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "saved-paper";


            card.innerHTML = `

                <div>

                    <h3>

                        ${escapeHTML(
                            paper.title
                        )}

                    </h3>


                    <p>

                        ${escapeHTML(
                            paper.authors
                                ? paper.authors.join(", ")
                                : "Unknown authors"
                        )}

                    </p>

                </div>


                <div class="saved-actions">

                    ${
                        paper.paper_url
                            ? `

                                <a
                                    href="${paper.paper_url}"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >

                                    View →

                                </a>

                            `
                            : ""
                    }


                    <button
                        onclick="removeSavedPaper(
                            '${encodeURIComponent(
                                paper.id
                            )}'
                        )"
                    >

                        Remove

                    </button>

                </div>

            `;


            container.appendChild(
                card
            );

        }
    );

}



// ======================================================
// REMOVE SAVED PAPER
// ======================================================

function removeSavedPaper(
    id
) {

    const decodedId =
        decodeURIComponent(id);


    savedPapers =
        savedPapers.filter(
            paper =>
                paper.id !== decodedId
        );


    localStorage.setItem(
        "researchAI_savedPapers",
        JSON.stringify(
            savedPapers
        )
    );


    displaySavedPapers();

}



// ======================================================
// SEARCH SUGGESTIONS
// ======================================================

function setSearch(
    query
) {

    const input =
        document.getElementById(
            "searchInput"
        );


    input.value = query;

    input.focus();

    searchPapers();

}



// ======================================================
// DARK / LIGHT THEME
// ======================================================

function toggleTheme() {

    const isLight =
        document.body.classList.toggle(
            "light-theme"
        );


    localStorage.setItem(
        "researchAI_theme",
        isLight
            ? "light"
            : "dark"
    );


    updateThemeButton();

}


function updateThemeButton() {

    const button =
        document.querySelector(
            ".nav-icon"
        );


    if (!button) {

        return;

    }


    const isLight =
        document.body.classList.contains(
            "light-theme"
        );


    button.textContent =
        isLight
            ? "☀"
            : "◐";


    button.title =
        isLight
            ? "Switch to dark mode"
            : "Switch to light mode";

}



// ======================================================
// ESCAPE HTML
// ======================================================

function escapeHTML(
    text
) {

    if (!text) {

        return "";

    }


    return String(text)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );

}



// ======================================================
// PDF FILE SELECTION
// ======================================================

const pdfInput =
    document.getElementById(
        "pdfInput"
    );


const uploadZone =
    document.getElementById(
        "uploadZone"
    );


const uploadStatus =
    document.getElementById(
        "uploadStatus"
    );


// When user chooses a file

if (pdfInput) {

    pdfInput.addEventListener(
        "change",
        function () {

            const file =
                this.files[0];


            if (!file) {

                uploadStatus.innerHTML = "";

                return;

            }


            if (
                !file.name
                    .toLowerCase()
                    .endsWith(".pdf")
            ) {

                uploadStatus.innerHTML = `

                    <span class="upload-error">

                        ✕ Only PDF files are supported.

                    </span>

                `;

                this.value = "";

                return;

            }


            const sizeMB =
                (
                    file.size /
                    (1024 * 1024)
                ).toFixed(2);


            uploadStatus.innerHTML = `

                <div class="selected-file">

                    <div class="selected-file-icon">

                        PDF

                    </div>


                    <div class="selected-file-info">

                        <strong>

                            ${escapeHTML(
                                file.name
                            )}

                        </strong>


                        <span>

                            ${sizeMB} MB · Ready for analysis

                        </span>

                    </div>


                    <button
                        type="button"
                        class="remove-file"
                        onclick="removeSelectedFile()"
                    >

                        ×

                    </button>

                </div>

            `;

        }
    );

}



// ======================================================
// REMOVE SELECTED PDF
// ======================================================

function removeSelectedFile() {

    if (pdfInput) {

        pdfInput.value = "";

    }


    if (uploadStatus) {

        uploadStatus.innerHTML = "";

    }

}



// ======================================================
// DRAG & DROP PDF
// ======================================================

if (uploadZone) {

    uploadZone.addEventListener(
        "dragover",
        function (event) {

            event.preventDefault();

            uploadZone.classList.add(
                "drag-active"
            );

        }
    );


    uploadZone.addEventListener(
        "dragleave",
        function () {

            uploadZone.classList.remove(
                "drag-active"
            );

        }
    );


    uploadZone.addEventListener(
        "drop",
        function (event) {

            event.preventDefault();

            uploadZone.classList.remove(
                "drag-active"
            );


            const files =
                event.dataTransfer.files;


            if (!files.length) {

                return;

            }


            const file =
                files[0];


            if (
                !file.name
                    .toLowerCase()
                    .endsWith(".pdf")
            ) {

                uploadStatus.innerHTML = `

                    <span class="upload-error">

                        ✕ Please drop a PDF file.

                    </span>

                `;

                return;

            }


            try {

                const dataTransfer =
                    new DataTransfer();


                dataTransfer.items.add(file);


                pdfInput.files =
                    dataTransfer.files;


                pdfInput.dispatchEvent(
                    new Event("change")
                );

            }

            catch (error) {

                console.error(
                    "Drag/drop error:",
                    error
                );

            }

        }
    );

}



// ======================================================
// ENTER KEY SEARCH
// ======================================================

const searchInput =
    document.getElementById(
        "searchInput"
    );


if (searchInput) {

    searchInput.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Enter"
            ) {

                searchPapers();

            }

        }
    );

}



// ======================================================
// RESTORE THEME
// ======================================================

const savedTheme =
    localStorage.getItem(
        "researchAI_theme"
    );


if (savedTheme === "light") {

    document.body.classList.add(
        "light-theme"
    );

}


updateThemeButton();



// ======================================================
// INITIALIZE
// ======================================================

displaySavedPapers();