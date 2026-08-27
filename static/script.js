let savedPapers = JSON.parse(
    localStorage.getItem("researchAI_savedPapers")
) || [];


// Latest search results
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


        const responseText = await response.text();

        let data;

        try {

            data = JSON.parse(responseText);

        } catch (parseError) {

            throw new Error(
                response.ok
                    ? "The server returned an invalid response."
                    : `Upload failed (HTTP ${response.status}). Please try again.`
            );

        }


        if (!response.ok) {

            throw new Error(
                data.message ||
                `Upload failed (HTTP ${response.status}).`
            );

        }


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