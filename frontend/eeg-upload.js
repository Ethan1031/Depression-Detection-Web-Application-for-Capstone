document.addEventListener("DOMContentLoaded", function () {
  const fileInput = document.getElementById("file-upload");
  const fileNameDisplay = document.getElementById("file-name");
  const submitButton = document.querySelector(".submit-btn");

  // Function to display the selected file name
  function displayFileName() {
    fileNameDisplay.textContent =
      fileInput.files.length > 0 ? fileInput.files[0].name : "No file chosen";
  }

  fileInput.addEventListener("change", displayFileName);

  submitButton.addEventListener("click", async function () {
    if (!fileInput.files.length) {
      alert("Please select a file before uploading.");
      return;
    }

    const file = fileInput.files[0];

    // Validate file type
    if (!file.name.endsWith(".edf")) {
      alert("Invalid file format. Only .edf files are allowed.");
      return;
    }

    // Get PHQ-9 answers from localStorage
    const phq9Answers = JSON.parse(localStorage.getItem("phq9Answers") || "[]");

    if (phq9Answers.length !== 9) {
      alert("Please complete the PHQ-9 questionnaire first.");
      window.location.href = "PHQ.html";
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    // Add PHQ-9 answers to the form data
    for (let i = 0; i < phq9Answers.length; i++) {
      formData.append("phq9_answers", phq9Answers[i]);
    }

    try {
      const token = localStorage.getItem("token");

      // Check if user is logged in
      if (!token) {
        alert("You need to be logged in to submit an assessment.");
        window.location.href = "log-in-page.html";
        return;
      }

      // Call the new combined endpoint
      const response = await fetch(
        "http://localhost:8000/api/assessment/submit-assessment",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        }
      );

      const data = await response.json();

      if (response.ok) {
        // Store the full assessment results
        localStorage.setItem("assessmentResult", JSON.stringify(data));

        // Also store individual components for backward compatibility
        localStorage.setItem("modelResult", data.prediction);

        alert("Assessment completed successfully!");
        window.location.href = "Technical Result.html";
      } else {
        alert("Upload failed: " + (data.detail || "An unknown error occurred"));
      }
    } catch (error) {
      alert("Error: " + error.message);
    }
  });
});
