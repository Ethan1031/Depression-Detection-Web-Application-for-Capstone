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
    // Map the fields correctly based on your schema
    usernameInput.value = user.name || "";
    phoneInput.value = user.phone_number || "";
    emailInput.value = user.email || "";
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
      saveButton.style.display = "inline-block";
    });
  }

  // Delete account when clicking "Delete"
  if (deleteButton) {
    deleteButton.addEventListener("click", async function () {
      if (
        confirm(
          "Are you sure you want to delete your account? This action cannot be undone."
        )
      ) {
        try {
          const token = localStorage.getItem("token");
          if (!token) {
            alert("You must be logged in to delete your account");
            return;
          }

          const response = await fetch("/api/users/delete", {
            method: "DELETE",
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
          });

          if (response.ok) {
            // Clear all auth data
            localStorage.removeItem("loggedInUser");
            localStorage.removeItem("token");
            localStorage.removeItem("phq9Score");
            localStorage.removeItem("phq9Answers");
            localStorage.removeItem("phq9Severity");
            localStorage.removeItem("modelResult");
            localStorage.removeItem("assessmentResult");

            alert("Account deleted successfully");
            window.location.href = "log-in-page.html";
          } else {
            const errorData = await response.json();
            alert(
              "Failed to delete account: " +
                (errorData.detail || "Unknown error")
            );
          }
        } catch (error) {
          console.error("Error deleting account:", error);
          alert("Error deleting account: " + error.message);
        }
      }
    });
  }

  // Save changes to API and update localStorage
  if (saveButton) {
    saveButton.addEventListener("click", async function () {
      try {
        const token = localStorage.getItem("token");
        if (!token) {
          alert("You must be logged in to update your profile");
          return;
        }

        // Map the fields correctly based on your schema
        const updatedUser = {
          name: usernameInput.value,
          phone_number: phoneInput.value,
          email: emailInput.value,
        };

        // Send update to backend
        const response = await fetch("/api/users/me", {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify(updatedUser),
        });

        if (response.ok) {
          // Get updated user from response
          const updatedUserData = await response.json();

          // Update localStorage with new data
          localStorage.setItem("loggedInUser", JSON.stringify(updatedUserData));

          // Disable form fields
          usernameInput.disabled = true;
          phoneInput.disabled = true;
          emailInput.disabled = true;
          saveButton.style.display = "none";

          alert("Profile saved successfully!");
        } else {
          const errorData = await response.json();
          alert(
            "Failed to update profile: " + (errorData.detail || "Unknown error")
          );
        }
      } catch (error) {
        console.error("Error updating profile:", error);
        alert("Error updating profile: " + error.message);
      }
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
