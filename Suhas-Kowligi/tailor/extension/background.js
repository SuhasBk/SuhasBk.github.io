chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'send_jd') {

        console.log("Background received JD, sending to Python...");

        fetch('http://localhost:8000/tailor', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ job_description: message.data })
        })
        .then(async response => {
            const text = await response.text(); 
            
            console.log("Status Code:", response.status);
            console.log("Response Body:", text);

            if (!response.ok) {
                throw new Error(`Server ${response.status}: ${text}`);
            }
            return text;
        })
        .then(data => {
            console.log("Success:", data);
            // This now works because we kept the channel open
            sendResponse({ success: true, data: data });
        })
        .catch(error => {
            console.error("Detailed Fetch Error:", error);
            sendResponse({ success: false, error: error.message });
        });

        // CRITICAL: This line tells Chrome "Wait! I will send a response asynchronously."
        return true; 
    }
});