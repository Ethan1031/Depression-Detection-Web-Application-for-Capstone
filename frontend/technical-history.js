document.addEventListener("DOMContentLoaded", function () {
  // Update user name in profile
  updateUserProfile();

  // Fetch and display test history
  fetchTestHistory();
});

// Update the user profile display
function updateUserProfile() {
  const userData = JSON.parse(localStorage.getItem("loggedInUser") || "{}");
  const profileNameEl = document.getElementById("profile-name");

  if (userData.username && profileNameEl) {
    profileNameEl.textContent = userData.username;
  }
}

// Fetch test history from the backend
async function fetchTestHistory() {
  try {
    const token = localStorage.getItem("token");
    if (!token) {
      console.error("No authentication token found");
      displayDemoHistory(); // Show demo data if no token
      return;
    }

    // FIXED: Use relative URL path
    const response = await fetch("/api/assessment/assessment-history", {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      const assessments = await response.json();
      console.log("Fetched assessment history:", assessments);

      if (assessments && assessments.length > 0) {
        displayAssessmentHistory(assessments);
      } else {
        console.log("No assessment history found");
        displayNoHistoryMessage();
      }
    } else {
      console.error(
        "Failed to fetch assessment history:",
        await response.text()
      );
      displayDemoHistory(); // Show demo data if API fails
    }
  } catch (error) {
    console.error("Error fetching assessment history:", error);
    displayDemoHistory(); // Show demo data if API fails
  }
}

// Display actual assessment history from API
function displayAssessmentHistory(assessments) {
  const historyContainer =
    document.querySelector(".results-container") ||
    document.getElementById("history-container");
  if (!historyContainer) return;

  // Clear any existing history items
  const existingResultSection = document.querySelector(".history-list");
  if (existingResultSection) {
    existingResultSection.innerHTML = "";
  } else {
    // Create a new section for history items
    const historySection = document.createElement("div");
    historySection.className = "history-list";
    historyContainer.appendChild(historySection);
  }

  const historyList = document.querySelector(".history-list");

  // Add each assessment to the list
  assessments.forEach((assessment) => {
    // Format date
    const date = new Date(assessment.created_at);
    const formattedDate = date.toLocaleDateString();
    const formattedTime = date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

    // Create list item
    const listItem = document.createElement("div");
    listItem.className = "result-section";

    const dateDisplay = document.createElement("h3");
    dateDisplay.textContent = `Test from ${formattedDate} at ${formattedTime}`;

    // FIXED: Since we don't have an endpoint to get a specific assessment,
    // We'll store the assessment data in localStorage before redirecting
    const resultLink = document.createElement("a");
    resultLink.href = "javascript:void(0);";
    resultLink.className = "back-button";
    resultLink.textContent = "View Result";
    resultLink.onclick = function () {
      // Store this specific assessment in localStorage
      localStorage.setItem("assessmentResult", JSON.stringify(assessment));
      window.location.href = "Technical Result.html";
    };

    // Add summary information
    const summary = document.createElement("div");
    summary.className = "result-card";

    let summaryContent = "";

    // Check which properties are available (handle both snake_case and camelCase)
    if (
      assessment.phq9_score !== undefined ||
      assessment.phq9Score !== undefined
    ) {
      const score =
        assessment.phq9_score !== undefined
          ? assessment.phq9_score
          : assessment.phq9Score;
      const category =
        assessment.phq9_category !== undefined
          ? assessment.phq9_category
          : assessment.phq9Category;

      summaryContent += `<p><strong>PHQ-9 Score:</strong> ${score}/27</p>`;
      summaryContent += `<p><strong>Category:</strong> ${category}</p>`;
    }

    if (assessment.prediction) {
      summaryContent += `<p><strong>EEG Prediction:</strong> ${assessment.prediction}</p>`;
    }

    summary.innerHTML = summaryContent;

    // Assemble list item
    listItem.appendChild(dateDisplay);
    listItem.appendChild(summary);
    listItem.appendChild(resultLink);

    // Add to the list
    historyList.appendChild(listItem);
  });
}

// Display a message when no history is found
function displayNoHistoryMessage() {
  const historyContainer =
    document.querySelector(".results-container") ||
    document.getElementById("history-container");
  if (!historyContainer) return;

  // Clear loading indicator
  const loadingIndicator = document.getElementById("loading-indicator");
  if (loadingIndicator) {
    loadingIndicator.remove();
  }

  const historyList = document.querySelector(".history-list");
  if (historyList) {
    historyList.innerHTML = `
          <div class="result-section">
              <h2>No Test History Found</h2>
              <p>You haven't taken any assessments yet. Go to the dashboard to take a PHQ-9 test or upload an EEG file.</p>
              <button class="back-button" onclick="window.location.href='dashboard.html'">Go to Dashboard</button>
          </div>
      `;
  }
}

// Display demo history data (for development/testing)
function displayDemoHistory() {
  const demoData = [
    {
      id: 1,
      created_at: "2023-07-11T20:10:00Z",
      phq9_score: 12,
      phq9_category: "Moderate Depression",
      prediction: "Major Depressive Disorder",
      confidence: 0.85,
    },
    {
      id: 2,
      created_at: "2023-09-11T04:10:00Z",
      phq9_score: 8,
      phq9_category: "Mild Depression",
      prediction: "No Depression Detected",
      confidence: 0.76,
    },
    {
      id: 3,
      created_at: "2024-02-01T04:10:00Z",
      phq9_score: 18,
      phq9_category: "Moderately Severe Depression",
      prediction: "Major Depressive Disorder",
      confidence: 0.91,
    },
  ];

  displayAssessmentHistory(demoData);
}
