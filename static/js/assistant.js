/**
 * AI Consumer Assistant Chatbot Script
 * Powers conversational grievance guidance, FAQ recommendations, and real-time status lookup.
 */

document.addEventListener('DOMContentLoaded', () => {
    const assistantBtn = document.getElementById('aiAssistantBtn');
    const assistantDrawer = document.getElementById('aiAssistantDrawer');
    const closeBtn = document.getElementById('aiAssistantClose');
    const chatBody = document.getElementById('aiChatBody');
    const chatInput = document.getElementById('aiChatInput');
    const sendBtn = document.getElementById('aiSendBtn');
    const chips = document.querySelectorAll('.ai-chip');

    if (!assistantBtn || !assistantDrawer) return;

    // Toggle drawer open/close
    assistantBtn.addEventListener('click', () => {
        assistantDrawer.classList.toggle('active');
        if (assistantDrawer.classList.contains('active')) {
            chatInput.focus();
        }
    });

    closeBtn.addEventListener('click', () => {
        assistantDrawer.classList.remove('active');
    });

    // Quick chip click
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            const query = chip.getAttribute('data-query');
            if (query) {
                sendMessage(query);
            }
        });
    });

    // Send on click or Enter key
    sendBtn.addEventListener('click', () => {
        const text = chatInput.value.trim();
        if (text) sendMessage(text);
    });

    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            const text = chatInput.value.trim();
            if (text) sendMessage(text);
        }
    });

    function sendMessage(messageText) {
        // Append user message bubble
        appendMessage(messageText, 'user');
        chatInput.value = '';

        // Show typing indicator
        const typingEl = showTypingIndicator();

        // Call backend API
        fetch('/api/assistant/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ message: messageText })
        })
        .then(res => res.json())
        .then(data => {
            typingEl.remove();
            if (data.reply) {
                appendMessage(data.reply, 'assistant');
            } else {
                appendMessage('Sorry, I encountered an error processing your query. Please try again.', 'assistant');
            }
        })
        .catch(err => {
            console.error('AI Assistant Error:', err);
            typingEl.remove();
            appendMessage('Unable to reach the assistant server right now. Please verify your connection.', 'assistant');
        });
    }

    function appendMessage(rawText, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `ai-msg ai-msg-${sender}`;

        // Format basic markdown (bold, bullets, line breaks)
        let formatted = rawText
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n\n/g, '<br><br>')
            .replace(/\n/g, '<br>');

        msgDiv.innerHTML = formatted;
        chatBody.appendChild(msgDiv);
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    function showTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'ai-msg ai-msg-assistant ai-typing';
        indicator.innerHTML = '<span></span><span></span><span></span>';
        chatBody.appendChild(indicator);
        chatBody.scrollTop = chatBody.scrollHeight;
        return indicator;
    }

    function getCsrfToken() {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, 10) === ('csrftoken=')) {
                    cookieValue = decodeURIComponent(cookie.substring(10));
                    break;
                }
            }
        }
        return cookieValue || '';
    }
});
