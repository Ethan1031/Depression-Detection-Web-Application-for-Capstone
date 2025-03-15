// Function to register the user with new fields
async function registerUser(name, ic_number, phone_number, email, password) {
  try {
    const response = await fetch("/api/auth/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: name,
        ic_number: ic_number,
        phone_number: phone_number,
        email: email,
        password: password,
        date_of_birth: new Date().toISOString(), // Temporary default value
      }),
    });

    const data = await response.json();
    console.log("Response data:", data);

    if (response.ok) {
      alert("Signup successful! You can now log in.");
      window.location.href = "log-in-page.html";
    } else {
      // Improved error handling for FastAPI validation errors
      if (data.detail) {
        if (Array.isArray(data.detail)) {
          const errorMessage = data.detail
            .map((err) => `${err.loc.join(".")}: ${err.msg}`)
            .join("\n");
          alert(`Signup failed:\n${errorMessage}`);
        } else {
          alert("Signup failed: " + data.detail);
        }
      } else {
        alert("Signup failed: An unknown error occurred.");
      }
    }
  } catch (error) {
    console.error("Error during signup:", error);
    alert("Error: " + error.message);
  }
}

// Function to log in the user
async function loginUser(email, password) {
  try {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email, password: password }),
    });

    const data = await response.json();

    if (response.ok) {
      // Save token for authentication
      localStorage.setItem("token", data.access_token);

      // Fetch user profile information
      await fetchUserProfile();

      alert("Login successful!");
      window.location.href = "dashboard.html"; // Redirect to dashboard
    } else {
      alert("Login failed: " + (data.detail || "Invalid credentials."));
    }
  } catch (error) {
    alert("Error: " + error.message);
  }
}

// Function to fetch user profile information
async function fetchUserProfile() {
  try {
    const token = localStorage.getItem("token");

    if (!token) {
      console.error("No authentication token found");
      return;
    }

    const response = await fetch("/api/auth/profile", {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();

    if (response.ok) {
      // Store user profile data
      localStorage.setItem(
        "loggedInUser",
        JSON.stringify({
          username: data.name,
          phone: data.phone_number,
          email: data.email,
        })
      );
    } else {
      console.error("Failed to fetch profile:", data.detail);
    }
  } catch (error) {
    console.error("Error fetching profile:", error);
  }
}

// Add a function to verify token validity
async function verifyToken() {
  const token = localStorage.getItem("token");
  if (!token) {
    return false;
  }

  try {
    const response = await fetch("/api/auth/profile", {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    return response.ok;
  } catch (error) {
    console.error("Token verification failed:", error);
    // Clear invalid token
    localStorage.removeItem("token");
    localStorage.removeItem("loggedInUser");
    return false;
  }
}

function showPassword() {
  const x = document.getElementById("signup-password");
  if (x.type === "password") {
    x.type = "text";
  } else {
    x.type = "password";
  }
}

// Wait until the DOM is loaded before attaching event listeners
document.addEventListener("DOMContentLoaded", function () {
  // Verify token when page loads
  verifyToken().then((isValid) => {
    if (!isValid) {
      // If on a protected page and token is invalid, redirect to login
      const currentPage = window.location.pathname.split("/").pop();
      const authRequiredPages = [
        "dashboard.html",
        "PHQ.html",
        "EEG Upload.html",
        "Result History.html",
        "Technical Result.html",
        "profile-settings.html",
      ];

      if (authRequiredPages.includes(currentPage)) {
        window.location.href = "log-in-page.html";
      }
    }
  });

  const signupForm = document.getElementById("signupForm");
  const loginForm = document.getElementById("loginForm");

  if (signupForm) {
    signupForm.addEventListener("submit", function (event) {
      event.preventDefault();

      // Get form values
      const fullName = document.getElementById("full-name").value.trim();
      const ic_number = document.getElementById("ic-number").value.trim();
      const phone = document.getElementById("signup-phone").value;
      const email = document.getElementById("signup-email").value.trim();
      const password = document.getElementById("signup-password").value;
      const confirmPassword = document.getElementById("confirm-password").value;
      const agreeTerms = document.getElementById("agree-terms").checked;

      // Validate input fields
      if (fullName === "") {
        alert("Please enter your full name.");
        return;
      }

      if (ic_number.length > 12) {
        alert("IC number is above 12 digits");
        return;
      }

      if (password !== confirmPassword) {
        alert("Passwords do not match.");
        return;
      }

      if (!agreeTerms) {
        alert("You must agree to the Terms & Conditions.");
        return;
      }

      // Call API function to register the user
      registerUser(fullName, ic_number, phone, email, password);
    });
  }

  if (loginForm) {
    loginForm.addEventListener("submit", function (event) {
      event.preventDefault();

      const email = document.getElementById("email").value.trim();
      const password = document.getElementById("password").value;

      loginUser(email, password);
    });
  }
});
