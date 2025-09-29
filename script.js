const chatInput = document.querySelector(".chat-input textarea");
const sendChatBtn = document.querySelector(".chat-input #send-btn");
const chatbox = document.querySelector(".chatbox");
const fileInput = document.querySelector("#file-upload");
const documentList = document.querySelector(".document-list");
const newChatBtn = document.querySelector(".new-chat-btn");
const newFolderBtn = document.querySelector(".new-folder-btn");
const historyList = document.querySelector(".history-list");
const historyBtn = document.querySelector(".history-btn");
const sidebarHistory = document.querySelector(".sidebar-history");
const profileIcon = document.querySelector(".profile-icon");
const profilePopup = document.querySelector("#profile-popup");
const popupCloseBtn = document.querySelector(".popup-content .close-btn");

const createChatLi = (message, className) => {
  const chatLi = document.createElement("li");
  chatLi.classList.add("chat", className);
  let chatContent = `<p>${message}</p>`;
  chatLi.innerHTML = chatContent;
  return chatLi;
}

const handleChat = () => {
  const userMessage = chatInput.value.trim();
  if (!userMessage) return;

  chatbox.appendChild(createChatLi(userMessage, "outgoing"));
  chatbox.scrollTo(0, chatbox.scrollHeight);

  // TODO: Send userMessage to backend and get a response
  // For now, let's add a simple placeholder response
  setTimeout(() => {
    chatbox.appendChild(createChatLi("Working on it...", "incoming"));
    chatbox.scrollTo(0, chatbox.scrollHeight);
  }, 1000);

  chatInput.value = "";
}

// Function to save the current chat session to history
const saveChatSession = () => {
  const chatMessages = [];
  const chatElements = chatbox.querySelectorAll("li");
  if (chatElements.length <= 1) return; // Don't save empty chats

  chatElements.forEach(chatElement => {
    chatMessages.push({
           content: chatElement.querySelector("p").innerText,
           class: chatElement.classList.contains("incoming") ? "incoming" : "outgoing"
    });
  });

  const firstMessage = chatMessages.length > 1 ? chatMessages[1].content : "New Chat";
  const historyItem = {
    name: firstMessage.length > 30 ? firstMessage.substring(0, 30) + "..." : firstMessage,
    messages: chatMessages
  };

  let chatHistory = JSON.parse(sessionStorage.getItem("chatHistory") || "[]");
  chatHistory.push(historyItem);
  sessionStorage.setItem("chatHistory", JSON.stringify(chatHistory));
};

// Function to render the history list in the sidebar
const renderHistory = () => {
  historyList.innerHTML = "";
  let chatHistory = JSON.parse(sessionStorage.getItem("chatHistory") || "[]");
  chatHistory.forEach((item, index) => {
    const historyLi = document.createElement("li");
    historyLi.textContent = item.name;
    historyLi.setAttribute("data-index", index);
    historyLi.addEventListener("click", () => loadChatSession(index));
    historyList.appendChild(historyLi);
  });
};

// Function to load a specific chat from history
const loadChatSession = (index) => {
  let chatHistory = JSON.parse(sessionStorage.getItem("chatHistory") || "[]");
  const session = chatHistory[index];
  if (session) {
    chatbox.innerHTML = "";
    session.messages.forEach(msg => {
           chatbox.appendChild(createChatLi(msg.content, msg.class));
    });
    chatbox.scrollTo(0, chatbox.scrollHeight);
  }
  // Automatically hide history after loading a session
  sidebarHistory.style.display = 'none';
};

// Function to handle a "New Chat" button click
const handleNewChat = () => {
  saveChatSession();
  renderHistory();
 
  // 1. Clear the chatbox and reset the welcome message
  chatbox.innerHTML = '<li class="chat incoming"><p>Hi there 👋<br>How can I help you today?</p></li>';

  // 2. Clear the text input
  chatInput.value = "";
 
  console.log("New chat started!");
};

// Function to handle a "New Folder" button click
const handleNewFolder = () => {
  // Get the new folder name from the user
  const folderName = prompt("Enter a name for the new folder:");
  if (folderName && folderName.trim() !== "") {
    // Create a new list item for the folder
    const folderItem = document.createElement("li");
    folderItem.textContent = "📁 " + folderName; // Add a folder emoji for visual appeal
    folderItem.classList.add("document-list-item", "folder");

    // Add the new folder to the top of the list
    documentList.prepend(folderItem);
    console.log("New folder created:", folderName);
  }
};

// Function to toggle the visibility of the history section
const toggleHistory = () => {
  const isVisible = sidebarHistory.style.display === 'block';
  sidebarHistory.style.display = isVisible ? 'none' : 'block';
  if (!isVisible) {
    renderHistory();
  }
};

// Function to handle file uploads
fileInput.addEventListener("change", (event) => {
  const files = event.target.files;
  if (files.length > 0) {
    for (const file of files) {
           // Display the uploaded file name in the chat
           const fileMessage = `Uploaded **${file.name}**`;
           chatbox.appendChild(createChatLi(fileMessage, "incoming"));
     
           // Add the file name to the sidebar
           const listItem = document.createElement("li");
           listItem.textContent = file.name;
           documentList.appendChild(listItem);
     
           // TODO: You would typically send the file to your backend here
           console.log(`File uploaded: ${file.name}, size: ${file.size} bytes`);
    }
    chatbox.scrollTo(0, chatbox.scrollHeight);
  }
});

sendChatBtn.addEventListener("click", handleChat);
chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    handleChat();
  }
});

// Add event listeners for the new buttons
newChatBtn.addEventListener("click", handleNewChat);
newFolderBtn.addEventListener("click", handleNewFolder);
historyBtn.addEventListener("click", toggleHistory);

// Add event listeners for the profile pop-up
profileIcon.addEventListener("click", () => {
    profilePopup.classList.add("show-popup");
});

popupCloseBtn.addEventListener("click", () => {
    profilePopup.classList.remove("show-popup");
});

// Initial rendering of the history on page load
renderHistory();