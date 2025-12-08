// --- Filename: script.js (Final Production Version) ---

document.addEventListener("DOMContentLoaded", () => {
    const sendBtn = document.getElementById("send-btn");
    const userInput = document.getElementById("user-input");
    const chatBox = document.getElementById("chat-box");
    const categoryBtnContainer = document.getElementById("category-buttons");
    const chatBtns = document.querySelectorAll(".chat-btn");
    const refreshBtn = document.getElementById("refresh-btn");

    let sessionId;

    // --- Event Listeners ---
    sendBtn.addEventListener("click", sendChatMessage);

    userInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendChatMessage();
    });

    chatBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            userInput.value = btn.innerText;
            sendChatMessage();
        });
    });

    refreshBtn.addEventListener("click", startNewSession);

    // --- Start/reset chat ---
    function startNewSession() {
        chatBox.innerHTML = "";
        sessionId = "session_" + Date.now();

        if (categoryBtnContainer) {
            categoryBtnContainer.style.display = "flex";
        }

        addMessageToChatbox("Hello! I'm the SLCI assistant (Tara). How can I help you today?", "bot");
    }

    // --- Send message ---
    async function sendChatMessage() {
        const userText = userInput.value.trim();
        if (userText === "") return;

        if (!sessionId) startNewSession();
        if (categoryBtnContainer) categoryBtnContainer.style.display = "none";

        addMessageToChatbox(userText, "user");
        userInput.value = "";

        addMessageToChatbox("Typing...", "bot", "typing-indicator-wrapper");

        try {
            const response = await fetch("http://127.0.0.1:5000/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: userText, session_id: sessionId }),
            });

            if (!response.ok) throw new Error("API request failed");
            const data = await response.json();

            removeTypingIndicator();

            // If table exists
            if (data.table && data.table.length > 0) {
                addTableToChat(data.table, data.meta || null);
                return;
            }

            // Normal text reply
            if (data.reply && data.reply.trim() !== "") {
                addMessageToChatbox(data.reply, "bot");
            }

        } catch (error) {
            console.error("Chat Error:", error);
            removeTypingIndicator();
            addMessageToChatbox("Sorry, I'm having trouble connecting. Please try again.", "bot");
        }
    }

    // --- Add Text message to chatbox ---
    function addMessageToChatbox(text, sender, id = null) {
        if (id !== "typing-indicator-wrapper") removeTypingIndicator();

        const wrapper = document.createElement("div");
        wrapper.classList.add(sender === "user" ? "user-message" : "bot-message");

        if (id) wrapper.id = id;

        const avatar = document.createElement("img");
        avatar.src = sender === "user" ? "/static/user.png" : "/static/tara.png";
        avatar.classList.add("avatar");

        const messageElement = document.createElement("div");
        messageElement.classList.add("message-text");
        messageElement.innerHTML = text.replace(/<img[^>]*>/g, '').trim();

        if (id) messageElement.id = "typing-indicator";

        if (sender === "bot") {
            wrapper.appendChild(avatar);
            wrapper.appendChild(messageElement);
        } else {
            wrapper.appendChild(messageElement);
            wrapper.appendChild(avatar);
        }

        chatBox.appendChild(wrapper);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // --- Add Wage Table Card + Meta ---
    function addTableToChat(tableData, meta = null) {
        const wrapper = document.createElement("div");
        wrapper.classList.add("bot-message");

        const avatar = document.createElement("img");
        avatar.src = "/static/tara.png";
        avatar.classList.add("avatar");

        const card = document.createElement("div");
        card.classList.add("message-text", "wage-card");

        // --- META Section ---
        if (meta) {
            const metaBox = document.createElement("div");
            metaBox.classList.add("meta-box");

            metaBox.innerHTML = `
                <b>📍 State:</b> ${meta.state}<br>
                <b>🏷 Act:</b> ${meta.act_name}<br>
                <b>🧮 DA:</b> ${meta.da}<br>
                <b>🗓 Effective From:</b> ${meta.effective_from}<br>
                
                <br>
            `;

            if (meta.pdf_url) {
                const linkBtn = document.createElement("a");
                linkBtn.href = meta.pdf_url;
                linkBtn.target = "_blank";
                linkBtn.classList.add("download-btn");
                linkBtn.innerHTML = "📄 Govt Notification PDF";
                metaBox.appendChild(linkBtn);
            }

            card.appendChild(metaBox);
        }

        // --- TABLE ---
        const tableContainer = document.createElement("div");
        tableContainer.id = "wage-table-content";

        let tableHTML = `<table class="wage-table">`;
        tableHTML += `<tr>${tableData[0].map(h => `<th>${h}</th>`).join("")}</tr>`;

        for (let i = 1; i < tableData.length; i++) {
            tableHTML += `<tr>${tableData[i].map(col => `<td>${col}</td>`).join("")}</tr>`;
        }

        tableHTML += `</table>`;
        tableContainer.innerHTML = tableHTML;
        card.appendChild(tableContainer);

        // --- PDF Button ---
        const pdfButton = document.createElement("button");
        pdfButton.classList.add("download-btn");
        pdfButton.innerHTML = "⬇️ Download Table (PDF)";

        pdfButton.dataset.tabledata = JSON.stringify(tableData);
        pdfButton.dataset.meta = JSON.stringify(meta);

        pdfButton.addEventListener("click", function () {
            downloadTableAsPDF(
                JSON.parse(this.dataset.tabledata),
                JSON.parse(this.dataset.meta)
            );
        });

        card.appendChild(pdfButton);

        wrapper.appendChild(avatar);
        wrapper.appendChild(card);
        chatBox.appendChild(wrapper);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // --- PDF Generator ---
    window.downloadTableAsPDF = function (tableData, meta = null) {
        try {
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF('p', 'mm', 'a4');
            let yPos = 12;

            // --- Company Title ---
            doc.setFontSize(18);
            doc.setTextColor(0, 100, 0);
            doc.text("Shakti Legal Compliance India (SLCI)", 14, yPos);
            yPos += 10;

            // --- PDF Title ---
            doc.setFontSize(15);
            doc.setTextColor(0, 0, 0);
            doc.text("Minimum Wage Details Report", 14, yPos);
            yPos += 8;

            // --- META INFO ---
            if (meta) {
                doc.setFontSize(11);
                doc.text(`State: ${meta.state}`, 14, yPos); yPos += 6;
                doc.text(`Effective From: ${meta.effective_from}`, 14, yPos); yPos += 6;
                // doc.text(`Updated As On: ${meta.updated_as_on}`, 14, yPos); yPos += 8;
                if (meta.pdf_url) {
                    doc.setTextColor(0, 0, 255);
                    doc.text(`Govt Notification PDF: ${meta.pdf_url}`, 14, yPos);
                    doc.setTextColor(0, 0, 0);
                    yPos += 10;
                }
            }

            // --- TABLE ---
            doc.autoTable({
                head: [tableData[0]],
                body: tableData.slice(1),
                startY: yPos,
                styles: { fontSize: 9 },
                headStyles: { fillColor: [16, 185, 129] }
            });

            // --- Disclaimer ---
            const finalY = doc.lastAutoTable.finalY + 12;
            doc.setFontSize(10);
            doc.setTextColor(180, 0, 0);
            doc.text(
                "Disclaimer: This data is fetched automatically via API. Please verify with official State Labour Department website or government published PDF.",
                14,
                finalY,
                { maxWidth: 180 }
            );

            doc.save(`Wage_Details_${meta?.state || ""}.pdf`);

        } catch (err) {
            console.error("PDF Error:", err);
            alert("PDF generation failed. Check console.");
        }
    };

    function removeTypingIndicator() {
        const el = document.getElementById("typing-indicator-wrapper");
        if (el) el.remove();
    }

    startNewSession();
});
