document.addEventListener("DOMContentLoaded", function () {
    const messageForm = document.getElementById("messageForm");
    const messageInput = document.getElementById("message");
    const messagesDiv = document.getElementById("messages");

    // בדיקת תמיכה בהתראות
    function checkNotificationSupport() {
        if (!("Notification" in window)) {
            console.warn("הדפדפן שלך לא תומך בהתראות");
            return false;
        }
        return true;
    }

    // בקשת אישור להתראות
    function requestNotificationPermission() {
        if (checkNotificationSupport() && Notification.permission !== "granted") {
            Notification.requestPermission().then(function (permission) {
                if (permission === "granted") {
                    console.log("התקבל אישור להתראות");
                } else {
                    alert("לא התקבל אישור להתראות");
                }
            });
        }
    }

    // שליחת התראה
    function showNotification(message, timestamp) {
        if (checkNotificationSupport() && Notification.permission === "granted") {
            const notification = new Notification("הודעה חדשה", {
                body: `${message}\n(נשלח ב-${timestamp})`,
                icon: "📢"
            });

            // סגירה אוטומטית לאחר 5 שניות
            notification.onclick = function() {
                notification.close();
            };

            setTimeout(() => notification.close(), 5000);
        }
    }

    // טעינת הודעות ראשונית
    fetchMessages();

    // בקשת אישור התראות
    requestNotificationPermission();

    // אירוע שליחת טופס
    messageForm.addEventListener("submit", function (event) {
        event.preventDefault();
        const message = messageInput.value.trim();

        if (!message) {
            alert("אנא הזן הודעה");
            return;
        }

        fetch("/input_text", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: message })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('שגיאה בשליחת ההודעה');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // קבלת זמן נוכחי
                const currentTimestamp = new Date().toLocaleString('he-IL', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });

                // ניקוי שדה הטקסט
                messageInput.value = '';

                // הצגת התראה
                showNotification(message, currentTimestamp);

                // רענון הודעות
                fetchMessages();
            }
        })
        .catch(error => {
            console.error('שגיאה:', error);
            alert('אירעה שגיאה בשליחת ההודעה');
        });
    });

    // פונקציה לטעינת הודעות
    function fetchMessages() {
        fetch("/get_messages")
            .then(response => {
                if (!response.ok) {
                    throw new Error('שגיאה בטעינת הודעות');
                }
                return response.json();
            })
            .then(data => {
                // ניקוי DIV ההודעות
                messagesDiv.innerHTML = '';

                // אם אין הודעות
                if (data.messages.length === 0) {
                    const noMessagesEl = document.createElement("p");
                    noMessagesEl.textContent = "אין הודעות זמינות";
                    noMessagesEl.style.color = "#888";
                    messagesDiv.appendChild(noMessagesEl);
                    return;
                }

                // יצירת אלמנטים להודעות
                data.messages.forEach(msg => {
                    const messageEl = document.createElement("div");
                    messageEl.classList.add("message-item");

                    const textEl = document.createElement("div");
                    textEl.classList.add("message-text");
                    textEl.textContent = msg.text;

                    const timestampEl = document.createElement("div");
                    timestampEl.classList.add("message-timestamp");
                    timestampEl.textContent = msg.timestamp;

                    messageEl.appendChild(textEl);
                    messageEl.appendChild(timestampEl);
                    messagesDiv.appendChild(messageEl);
                });
            })
            .catch(error => {
                console.error('שגיאה:', error);
                messagesDiv.innerHTML = '<p style="color: red;">אירעה שגיאה בטעינת הודעות</p>';
            });
    }

    // רענון אוטומטי כל 30 שניות
    setInterval(fetchMessages, 30000);
});