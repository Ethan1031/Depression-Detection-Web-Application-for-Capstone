// This file checks authentication state and redirects accordingly
document.addEventListener("DOMContentLoaded", function () {
  // Check if user is authenticated
  function isAuthenticated() {
    return (
      localStorage.getItem("token") && localStorage.getItem("loggedInUser")
    );
  }

  // Get current page
  const currentPage = window.location.pathname.split("/").pop();

  // Pages that require authentication
  const authRequiredPages = [
    "dashboard.html",
    "PHQ.html",
    "EEG Upload.html",
    "Result History.html",
    "Technical Result.html",
    "profile-settings.html",
  ];

  // Pages that should redirect to dashboard if already logged in
  const nonAuthPages = ["log-in-page.html", "sign-up-page.html"];

  // Update user display in navbar if it exists
  const profileNameElement = document.querySelector(".profile-name");
  if (profileNameElement) {
    if (isAuthenticated()) {
      const userData = JSON.parse(localStorage.getItem("loggedInUser"));
      profileNameElement.textContent = userData.username;
    } else {
      profileNameElement.textContent = "Login or Sign Up";
      // Make it clickable to login page if not authenticated
      const profileLink = document.querySelector(".profile-link");
      if (profileLink) {
        profileLink.href = "log-in-page.html";
      }
    }
  }

  // Handle authentication redirects
  if (authRequiredPages.includes(currentPage) && !isAuthenticated()) {
    // Redirect to login if trying to access protected page without auth
    alert("Please log in to access this page");
    window.location.href = "log-in-page.html";
    return;
  } else if (nonAuthPages.includes(currentPage) && isAuthenticated()) {
    // Redirect to dashboard if trying to access login/signup while authenticated
    window.location.href = "dashboard.html";
    return;
  }

  // Update Get Started button functionality on landing page
  const ctaButton = document.querySelector(".cta-button");
  if (ctaButton) {
    // Remove any existing event listeners
    const newButton = ctaButton.cloneNode(true);
    ctaButton.parentNode.replaceChild(newButton, ctaButton);

    // Add new event listener
    newButton.addEventListener("click", function (e) {
      e.preventDefault();
      console.log(
        "Get Started button clicked, authenticated:",
        isAuthenticated()
      );
      if (isAuthenticated()) {
        window.location.href = "dashboard.html";
      } else {
        window.location.href = "sign-up-page.html";
      }
    });
  }
});
