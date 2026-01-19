/**
 * Resume Tailor - LinkedIn Job Scraper
 * content.js
 */

let lastUrl = location.href;

/**
 * Waits for the LAST instance of a selector to appear in the DOM.
 * @param {string} selector - The CSS selector (e.g., "div.mt4")
 * @returns {Promise<Element>}
 */
function waitForLastElement(selector) {
    return new Promise((resolve) => {
        const getLast = () => {
            const elements = document.querySelectorAll(selector);
            return elements.length > 0 ? elements[elements.length - 1] : null;
        };

        const existing = getLast();
        if (existing) return resolve(existing);

        const observer = new MutationObserver(() => {
            const found = getLast();
            if (found) {
                observer.disconnect();
                resolve(found);
            }
        });

        observer.observe(document.body, { childList: true, subtree: true });
    });
}

function sendToBackend(jd) {
    console.log("Handing off to background script...");

    chrome.runtime.sendMessage({ action: 'send_jd', data: jd }, (response) => {
        if (chrome.runtime.lastError) {
            console.error("Chrome Runtime Error:", chrome.runtime.lastError.message);
            alert("Connection Failed: " + chrome.runtime.lastError.message);
            return;
        }

        if (response && response.success) {
            alert("Success: " + response.data);
        } else {
            console.error("Backend failed:", response);
            alert("Error from Backend: " + (response ? response.error : "Unknown Error"));
        }
    });
}

const handleJobChange = () => {
    console.log("Looking for job description...");

    waitForLastElement("div.mt4").then((element) => {
        element.style.border = "5px solid red";
        element.scrollIntoView({ behavior: "smooth", block: "center" });

        const jd = element.innerText;

        if (confirm(`Found Job Description:\n\n${jd}\n\nGenerate Resume?`)) {
            sendToBackend(jd);
        }
    });
};

// --- INITIALIZATION ---

handleJobChange();

new MutationObserver(() => {
    if (location.href !== lastUrl) {
        lastUrl = location.href;
        console.log('URL changed to:', lastUrl);
        setTimeout(handleJobChange, 1000);
    }
}).observe(document, { subtree: true, childList: true });