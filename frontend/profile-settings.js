document.addEventListener("DOMContentLoaded", function () {
  const editButton = document.querySelector(".profile-edit");
  const deleteButton = document.querySelector(".profile-delete");
  const saveButton = document.querySelector(".profile-save");
  const logoutButton = document.querySelector(".profile-logout");

  // Add a console log to verify the button was found
  console.log("Logout button found:", logoutButton);

  const usernameInput = document.getElementById("username");
  const phoneInput = document.getElementById("phone");
  const emailInput = document.getElementById("email");

  // Fetch User Data from localStorage (or API if applicable)
  const user = JSON.parse(localStorage.getItem("loggedInUser"));

  if (user) {
    usernameInput.value = user.username;
    phoneInput.value = user.phone;
    emailInput.value = user.email;
  } else {
    alert("No user data found! Redirecting to login...");
    window.location.href = "log-in-page.html"; // No leading slash
  }

  // Enable input fields when clicking "Edit"
  if (editButton) {
    editButton.addEventListener("click", function () {
      usernameInput.disabled = false;
      phoneInput.disabled = false;
      emailInput.disabled = false;
    });
  }

  // Clear input fields when clicking "Delete"
  if (deleteButton) {
    deleteButton.addEventListener("click", function () {
      usernameInput.value = "";
      phoneInput.value = "";
      emailInput.value = "";
    });
  }

  // Save changes and update localStorage
  if (saveButton) {
    saveButton.addEventListener("click", function () {
      const updatedUser = {
        username: usernameInput.value,
        phone: phoneInput.value,
        email: emailInput.value,
      };

      localStorage.setItem("loggedInUser", JSON.stringify(updatedUser));
      usernameInput.disabled = true;
      phoneInput.disabled = true;
      emailInput.disabled = true;

      alert("Profile saved successfully!");
    });
  }

  // Improved Log Out and Clear User Data with additional error handling
  if (logoutButton) {
    logoutButton.addEventListener("click", function (event) {
      event.preventDefault(); // Prevent any default behavior

      if (confirm("Are you sure you want to log out?")) {
        console.log("Logging out...");

        try {
          // Clear all authentication-related data
          localStorage.removeItem("loggedInUser");
          localStorage.removeItem("token");
          localStorage.removeItem("phq9Score");
          localStorage.removeItem("phq9Answers");
          localStorage.removeItem("phq9Severity");
          localStorage.removeItem("modelResult");
          localStorage.removeItem("assessmentResult");

          console.log("All localStorage items cleared");
          console.log("Redirecting to log-in-page.html");

          // Try different redirection methods
          window.location.href = "log-in-page.html";

          // Use a timeout as fallback
          setTimeout(function () {
            // If we're still here, try another approach
            console.log("Trying secondary redirect method");
            window.location.replace("log-in-page.html");

            // As a last resort
            setTimeout(function () {
              console.log("Trying tertiary redirect method");
              window.location = "log-in-page.html";

              // If absolutely nothing works, try with full path
              setTimeout(function () {
                console.log("Trying with full path");
                window.location.href =
                  window.location.origin + "/log-in-page.html";
              }, 100);
            }, 100);
          }, 100);
        } catch (error) {
          console.error("Error during logout:", error);
          alert("Error during logout: " + error.message);

          // Try direct redirect even if there was an error
          window.location.href = "log-in-page.html";
        }
      }
    });
  } else {
    console.error("Logout button not found! Check your HTML structure.");
  }
});
