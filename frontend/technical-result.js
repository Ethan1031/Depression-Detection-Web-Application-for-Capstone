// Replace the existing download button event listener with this:
const downloadButton = document.getElementById("download-report");
if (downloadButton) {
  downloadButton.addEventListener("click", async function (e) {
    e.preventDefault();

    try {
      const token = localStorage.getItem("token");
      if (!token) {
        alert("You need to be logged in to download reports.");
        return;
      }

      // Get the latest assessment ID
      const idResponse = await fetch("/api/assessment/latest-assessment-id", {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!idResponse.ok) {
        const errorData = await idResponse.json();
        throw new Error(errorData.detail || "Failed to get assessment ID");
      }

      const idData = await idResponse.json();
      const assessmentId = idData.assessment_id;

      // Download the report using the ID
      window.location.href = `/api/assessment/download-report/${assessmentId}`;
    } catch (error) {
      console.error("Error downloading report:", error);
      alert("Error downloading report: " + error.message);
    }
  });
}

// Function to fetch the latest assessment from the API
async function fetchLatestAssessment() {
  try {
    const token = localStorage.getItem("token");
    if (!token) {
      console.error("No authentication token found");
      displayLocalStorageData(); // Fall back to localStorage if no token
      return;
    }

    // FIXED: Use relative URL path
    const response = await fetch("/api/assessment/assessment-history?limit=1", {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      const assessments = await response.json();
      console.log("Fetched assessment data:", assessments);

      if (assessments && assessments.length > 0) {
        const latestAssessment = assessments[0];

        // Store the latest assessment in localStorage with proper format
        localStorage.setItem(
          "assessmentResult",
          JSON.stringify(latestAssessment)
        );

        // Update the display with the latest data
        updateDisplayWithAssessment(latestAssessment);
      } else {
        console.log("No assessments found from API, checking localStorage");
        displayLocalStorageData();
      }
    } else {
      console.error(
        "Failed to fetch assessment history:",
        await response.text()
      );
      displayLocalStorageData(); // Fall back to localStorage if API fails
    }
  } catch (error) {
    console.error("Error fetching assessment history:", error);
    displayLocalStorageData(); // Fall back to localStorage if API fails
  }
}

// Function to display data from localStorage if API fails
function displayLocalStorageData() {
  // Check if there's a specific assessment ID in the URL
  const urlParams = new URLSearchParams(window.location.search);
  const assessmentId = urlParams.get("id");

  if (assessmentId) {
    // If we have a specific ID, we need to fetch that specific assessment
    // FIXED: No endpoint exists for this in the backend, so we'll show local data instead
    console.log(
      "No API endpoint available for specific assessment, using localStorage data"
    );
  }

  console.log("Displaying data from localStorage");

  // Try to get assessment result from combined storage first
  const assessmentResult = JSON.parse(
    localStorage.getItem("assessmentResult") || "{}"
  );

  if (Object.keys(assessmentResult).length > 0) {
    // We have valid assessment data in localStorage
    updateDisplayWithAssessment(assessmentResult);
  } else {
    // Use separate PHQ9 and model result items
    const phq9Score = localStorage.getItem("phq9Score");
    const phq9Severity = localStorage.getItem("phq9Severity");
    const modelResult = localStorage.getItem("modelResult");

    // Display PHQ-9 data
    displayPhq9Data(phq9Score, phq9Severity);

    // Display model result
    displayModelResult(modelResult);
  }
}

// Function to update the display with assessment data
function updateDisplayWithAssessment(assessment) {
  if (!assessment) return;

  console.log("Updating display with assessment:", assessment);

  // Display PHQ-9 data based on backend format
  if (assessment.phq9_score !== undefined) {
    // Backend format (snake_case)
    displayPhq9Data(assessment.phq9_score, assessment.phq9_category);
  } else if (assessment.phq9Score !== undefined) {
    // Alternate format (camelCase)
    displayPhq9Data(assessment.phq9Score, assessment.phq9Category);
  } else if (assessment.total_score !== undefined) {
    // PHQ9Response format
    displayPhq9Data(assessment.total_score, assessment.category);
  }

  // Display model prediction based on backend format
  if (assessment.prediction !== undefined) {
    const confidence =
      assessment.confidence !== undefined ? assessment.confidence : null;
    displayModelResult(assessment.prediction, confidence);
  }
}

// Function to display PHQ-9 data
function displayPhq9Data(score, severity) {
  const scoreElement = document.getElementById("phq9-score");
  const severityElement = document.getElementById("phq9-severity");

  if (score !== undefined && score !== null) {
    // Format and display the score
    scoreElement.textContent = score + "/27";

    // If we have severity, display it
    if (severity) {
      severityElement.textContent = severity;
    } else {
      // Otherwise calculate severity based on score
      let calculatedSeverity = "Minimal Depression";
      if (score >= 20) calculatedSeverity = "Severe Depression";
      else if (score >= 15) calculatedSeverity = "Moderately Severe Depression";
      else if (score >= 10) calculatedSeverity = "Moderate Depression";
      else if (score >= 5) calculatedSeverity = "Mild Depression";

      severityElement.textContent = calculatedSeverity;
    }
  } else {
    // If no score is available
    scoreElement.textContent = "No PHQ-9 test taken";
    severityElement.textContent = "Not available";
  }
}

// Function to display model result
function displayModelResult(prediction, confidence) {
  const modelResultElement = document.getElementById("model-result");
  const confidenceElement = document.getElementById("confidence-percentage");
  const confidenceFill = document.getElementById("confidence-fill");

  if (prediction) {
    modelResultElement.textContent = prediction;

    // Handle confidence display if available
    if (confidence !== null && confidence !== undefined) {
      // Convert to percentage if it's a decimal
      const confidencePercentage =
        confidence > 1 ? confidence : Math.round(confidence * 100);

      if (confidenceElement)
        confidenceElement.textContent = confidencePercentage + "%";
      if (confidenceFill)
        confidenceFill.style.width = confidencePercentage + "%";
    } else {
      // No confidence value
      if (confidenceElement) confidenceElement.textContent = "N/A";
      if (confidenceFill) confidenceFill.style.width = "0%";
    }
  } else {
    modelResultElement.textContent = "No EEG analysis performed";
    if (confidenceElement) confidenceElement.textContent = "N/A";
    if (confidenceFill) confidenceFill.style.width = "0%";
  }
}
