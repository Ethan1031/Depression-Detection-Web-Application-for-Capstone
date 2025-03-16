document.addEventListener("DOMContentLoaded", function () {
  function selectOption(element) {
    let parent = element.parentNode;
    let options = parent.querySelectorAll(".option");

    // Remove 'selected' from all options within the same question
    options.forEach((opt) => opt.classList.remove("selected"));

    // Add 'selected' to the clicked option
    element.classList.add("selected");
  }

  async function calculateScore() {
    let questions = document.querySelectorAll(".question");
    let totalScore = 0;
    let phq9Answers = [];
    let allAnswered = true;

    questions.forEach((question) => {
      let selectedOption = question.querySelector(".option.selected");
      if (!selectedOption) {
        allAnswered = false; // If any question is unanswered, set flag to false
      } else {
        let score = parseInt(selectedOption.getAttribute("data-score"));
        phq9Answers.push(score);
        totalScore += score;
      }
    });

    if (!allAnswered) {
      alert("Please answer all the questions before submitting.");
      return;
    }

    // Store both score and individual answers in localStorage
    localStorage.setItem("phq9Score", totalScore);
    localStorage.setItem("phq9Answers", JSON.stringify(phq9Answers));

    // Determine severity based on score
    let severity = "Minimal Depression";
    if (totalScore >= 20) {
      severity = "Severe Depression";
    } else if (totalScore >= 15) {
      severity = "Moderately Severe Depression";
    } else if (totalScore >= 10) {
      severity = "Moderate Depression";
    } else if (totalScore >= 5) {
      severity = "Mild Depression";
    }

    // Store severity in localStorage
    localStorage.setItem("phq9Severity", severity);

    // Check if the user is logged in
    const token = localStorage.getItem("token");
    if (!token) {
      alert("You need to be logged in to submit PHQ-9 results.");
      window.location.href = "log-in-page.html";
      return;
    }

    try {
      // Save PHQ-9 test to database
      const response = await fetch("/api/assessment/submit-phq9", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          answers: phq9Answers,
          total_score: totalScore,
          category: severity,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        console.log("PHQ-9 test saved successfully:", data);
        // Redirect to EEG Upload page
        window.location.href = "EEG Upload.html";
      } else {
        console.error("Error saving PHQ-9 test:", data);
        alert(
          "There was an error saving your PHQ-9 test. " +
            (data.detail || "Please try again.")
        );
        // Still redirect to EEG Upload page
        window.location.href = "EEG Upload.html";
      }
    } catch (error) {
      console.error("Error saving PHQ-9 test:", error);
      alert("There was an error saving your PHQ-9 test. Please try again.");
      // Still redirect to EEG Upload page
      window.location.href = "EEG Upload.html";
    }
  }

  window.selectOption = selectOption;
  window.calculateScore = calculateScore;
});
