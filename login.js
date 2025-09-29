document.getElementById('login-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the form from submitting normally

    const usernameInput = document.getElementById('username').value;
    const passwordInput = document.getElementById('password').value;
    const errorMessage = document.getElementById('error-message');

    // Hardcoded credentials for a simple frontend login
    const correctUsername = "user";
    const correctPassword = "pass";

    if (usernameInput === correctUsername && passwordInput === correctPassword) {
        // Correct credentials, redirect to the main chatbot page
        window.location.href = "index.html";
    } else {
        // Incorrect credentials, show an error message
        errorMessage.textContent = "Invalid username or password.";
    }
});