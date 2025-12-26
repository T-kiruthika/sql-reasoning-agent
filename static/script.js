document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('db-modal');
    const openModalBtn = document.getElementById('open-modal-btn');
    const closeModalBtn = document.querySelector('.close-btn');
    const dbConnectionForm = document.getElementById('db-connection-form');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');
    const connectionStatus = document.getElementById('connection-status');
    const sendBtn = document.getElementById('send-btn');
    const dbTypeSelect = document.getElementById('db_type');
    const hostInput = document.getElementById('host');
    const portInput = document.getElementById('port');
    const darkModeToggle = document.getElementById('dark-mode-checkbox');

    const usernameInput = document.getElementById('username');
    const dbNameInput = document.getElementById('db_name');
    const usernameSuggestions = document.getElementById('username-suggestions');
    const dbNameSuggestions = document.getElementById('dbname-suggestions');
    const querySuggestions = document.getElementById('query-suggestions');

    displayMessage("Hello! I'm your intelligent data assistant. Please click 'New Connection' to begin.", 'bot');

    darkModeToggle.addEventListener('change', () => {
        document.body.classList.toggle('light-mode', !darkModeToggle.checked);
        document.body.classList.toggle('dark-mode', darkModeToggle.checked);
    });

    openModalBtn.addEventListener('click', () => {
        modal.style.display = 'flex'; 
        dbTypeSelect.dispatchEvent(new Event('change'));
    });
    closeModalBtn.addEventListener('click', () => modal.style.display = 'none');
    window.addEventListener('click', (event) => {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    });

    const portMap = { mysql: '3306', postgresql: '5432', sqlite: '' };
    dbTypeSelect.addEventListener('change', () => {
        const selectedType = dbTypeSelect.value;
        const isSqlite = selectedType === 'sqlite';

        hostInput.value = isSqlite ? '' : 'localhost';
        portInput.value = portMap[selectedType];

        hostInput.disabled = isSqlite;
        portInput.disabled = isSqlite;
        document.getElementById('db_name').placeholder = isSqlite ? 'Database File Path' : 'Database Name';
    });

    const setupSuggestions = (inputElement, suggestionBox, storageKey, filterOnKeyUp = false) => {
        const showSuggestions = (filter = '') => {
            const items = JSON.parse(localStorage.getItem(storageKey)) || [];
            const filteredItems = filter ? items.filter(item => item.toLowerCase().includes(filter.toLowerCase())) : items;

            if (filteredItems.length > 0) {
                suggestionBox.innerHTML = filteredItems.map(item => `<div>${item}</div>`).join('');
                suggestionBox.style.display = 'block';
            } else {
                suggestionBox.style.display = 'none';
            }
        };

        inputElement.addEventListener('focus', () => showSuggestions(inputElement.value));

        if (filterOnKeyUp) {
            inputElement.addEventListener('keyup', () => showSuggestions(inputElement.value));
        } else {
            inputElement.addEventListener('mouseover', () => showSuggestions());
        }

        suggestionBox.addEventListener('click', (e) => {
            if (e.target.tagName === 'DIV') {
                inputElement.value = e.target.textContent;
                suggestionBox.style.display = 'none';
                inputElement.focus();
            }
        });

        document.addEventListener('click', (e) => {
            if (!inputElement.contains(e.target) && !suggestionBox.contains(e.target)) {
                suggestionBox.style.display = 'none';
            }
        });
    };

    const saveToLocalStorage = (key, value) => {
        if (!value) return; 
        let items = JSON.parse(localStorage.getItem(key)) || [];
        items = items.filter(item => item !== value);
        items.unshift(value);
        items = items.slice(0, 20);
        localStorage.setItem(key, JSON.stringify(items));
    };

    setupSuggestions(usernameInput, usernameSuggestions, 'usernames');
    setupSuggestions(dbNameInput, dbNameSuggestions, 'dbnames');
    setupSuggestions(userInput, querySuggestions, 'queries', true);

    dbConnectionForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        connectionStatus.textContent = 'Connecting...';
        const db_type = dbTypeSelect.value;
        const host = hostInput.value;
        const port = portInput.value;
        const username = usernameInput.value;
        const password = document.getElementById('password').value;
        const db_name = dbNameInput.value;

        try {
            const response = await fetch('/connect_db', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ db_type, host, port, username, password, db_name }),
            });
            const data = await response.json();

            if (response.ok) {
                modal.style.display = 'none';
                userInput.disabled = false;
                sendBtn.disabled = false;
                userInput.placeholder = "Ask a question about your data...";
                displayMessage(`Successfully connected to '${db_name}'. You can start asking questions now.`, 'bot');

                saveToLocalStorage('usernames', username);
                saveToLocalStorage('dbnames', db_name);

            } else {
                connectionStatus.textContent = data.error;
            }
        } catch (error) {
            connectionStatus.textContent = 'An unexpected error occurred.';
        }
    });

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;

        displayMessage(message, 'user');
        saveToLocalStorage('queries', message); 
        userInput.value = '';
        querySuggestions.style.display = 'none'; 
        showTypingIndicator();

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message }),
            });

            const data = await response.json();
            removeTypingIndicator();

            if (response.ok) {
                displayMessage(data.response, 'bot');
            } else {
                displayMessage(`<p><strong>Error:</strong> ${data.error}</p>`, 'bot');
            }
        } catch (error) {
            removeTypingIndicator();
            displayMessage('<p>An unexpected error occurred while fetching the response.</p>', 'bot');
        }
    });

    function displayMessage(message, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);

        const messageContent = document.createElement('span');
        messageContent.innerHTML = message;
        messageElement.appendChild(messageContent);

        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-btn';
        copyBtn.textContent = 'Copy';
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(messageContent.innerText).then(() => {
                copyBtn.textContent = 'Copied!';
                setTimeout(() => {
                    copyBtn.textContent = 'Copy';
                }, 2000);
            });
        });
        messageElement.appendChild(copyBtn);

        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function showTypingIndicator() {
        if (document.getElementById('typing-indicator')) return;
        const typingIndicator = document.createElement('div');
        typingIndicator.id = 'typing-indicator';
        typingIndicator.classList.add('message', 'bot-message');
        typingIndicator.innerHTML = '● ● ●';
        chatBox.appendChild(typingIndicator);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
});
