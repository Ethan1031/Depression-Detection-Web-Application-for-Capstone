document.addEventListener("DOMContentLoaded", function () {
  // Get user info
  const userData = JSON.parse(localStorage.getItem("loggedInUser") || "{}");
  if (userData.name) {
    const userNameElement = document.getElementById("user-name");
    if (userNameElement) {
      userNameElement.textContent = userData.name;
    }
  }

  // Fetch the latest assessment data - this is the main function we call
  fetchLatestAssessment();

  // Configure download button
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

        // Try to get the assessment ID from localStorage first (most reliable)
        let assessmentId = localStorage.getItem("latestAssessmentId");

        // If no ID in localStorage, try to get it from the API
        if (!assessmentId) {
          console.log("No assessment ID in localStorage, fetching from API");
          try {
            const idResponse = await fetch(
              "/api/assessment/assessment-history?limit=1",
              {
                method: "GET",
                headers: {
                  Authorization: `Bearer ${token}`,
                  "Content-Type": "application/json",
                },
              }
            );

            if (idResponse.ok) {
              const assessments = await idResponse.json();
              if (assessments && assessments.length > 0) {
                assessmentId = assessments[0].id;
                console.log(
                  "Retrieved assessment ID from history:",
                  assessmentId
                );
              } else {
                throw new Error("No assessments found in your history");
              }
            } else {
              const errorText = await idResponse.text();
              console.error("Failed to get assessment history:", errorText);
              throw new Error("Failed to retrieve assessment data");
            }
          } catch (error) {
            console.error("Error getting assessment ID:", error);
            alert(
              "Could not find your assessment. Please complete a PHQ-9 assessment first."
            );
            return;
          }
        }

        if (!assessmentId) {
          alert(
            "No assessment found. Please complete a PHQ-9 assessment first."
          );
          return;
        }

        console.log("Downloading report for assessment ID:", assessmentId);

        // Use fetch with authentication header to get the report
        const response = await fetch(
          `/api/assessment/download-report/${assessmentId}`,
          {
            method: "GET",
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (!response.ok) {
          const errorData = await response.text();
          console.error("Download error:", errorData);
          throw new Error("Failed to download report");
        }

        // Convert the response to a blob
        const blob = await response.blob();

        // Create a download link and trigger it
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.style.display = "none";
        a.href = url;
        a.download = `mindloom_assessment_${
          new Date().toISOString().split("T")[0]
        }.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } catch (error) {
        console.error("Error downloading report:", error);
        alert("Error downloading report: " + error.message);
      }
    });
  }
});

// Function to fetch the latest assessment from the API
async function fetchLatestAssessment() {
  try {
    const token = localStorage.getItem("token");
    if (!token) {
      console.error("No authentication token found");
      displayLocalStorageData(); // Fall back to localStorage if no token
      return;
    }

    // Add logging to help troubleshoot
    console.log("Fetching latest assessment data with token");

    // FIXED: Use relative URL path with better logging
    const response = await fetch("/api/assessment/assessment-history?limit=1", {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    // Log the raw response for debugging
    console.log("Response status:", response.status);

    if (response.ok) {
      const assessments = await response.json();
      console.log("Fetched assessment data:", assessments);

      if (assessments && assessments.length > 0) {
        const latestAssessment = assessments[0];
        console.log("Using latest assessment:", latestAssessment);

        // Store the latest assessment in localStorage with proper format
        localStorage.setItem(
          "assessmentResult",
          JSON.stringify(latestAssessment)
        );

        // Also store the assessment ID for the download functionality
        localStorage.setItem("latestAssessmentId", latestAssessment.id);

        // Update the display with the latest data
        updateDisplayWithAssessment(latestAssessment);
      } else {
        console.log("No assessments found from API, checking localStorage");
        displayLocalStorageData();
      }
    } else {
      // Log the error response for debugging
      const errorText = await response.text();
      console.error("Failed to fetch assessment history:", errorText);
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

  if (scoreElement && score !== undefined && score !== null) {
    // Format and display the score
    scoreElement.textContent = score + "/27";

    // If we have severity, display it
    if (severityElement) {
      if (severity) {
        severityElement.textContent = severity;
      } else {
        // Otherwise calculate severity based on score
        let calculatedSeverity = "Minimal Depression";
        if (score >= 20) calculatedSeverity = "Severe Depression";
        else if (score >= 15)
          calculatedSeverity = "Moderately Severe Depression";
        else if (score >= 10) calculatedSeverity = "Moderate Depression";
        else if (score >= 5) calculatedSeverity = "Mild Depression";

        severityElement.textContent = calculatedSeverity;
      }
    }
  } else if (scoreElement) {
    // If no score is available
    scoreElement.textContent = "No PHQ-9 test taken";
    if (severityElement) {
      severityElement.textContent = "Not available";
    }
  }
}

// Function to display model result
function displayModelResult(prediction, confidence) {
  const modelResultElement = document.getElementById("model-result");
  const confidenceElement = document.getElementById("confidence-percentage");
  const confidenceFill = document.getElementById("confidence-fill");

  if (modelResultElement && prediction) {
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
  } else if (modelResultElement) {
    modelResultElement.textContent = "No EEG analysis performed";
    if (confidenceElement) confidenceElement.textContent = "N/A";
    if (confidenceFill) confidenceFill.style.width = "0%";
  }
}
