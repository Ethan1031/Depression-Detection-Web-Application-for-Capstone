# Depression-Detection-Web-Application-for-Capstone

Backend Part:
Part 1: In the app folder:

1. Schemas.py: Validate the input data of API is same as the format we predifined in class. For example, a client sends a request to create a user, FastAPI will check if the incoming data follows the UserCreate schema.

2. config.py: Uses Pydantic's BaseSettings to automatically read and validate values from an .env file, ensuring that critical configurations (e.g., database credentials and security settings) are properly set before your app runs.

3. database.py: Sets up SQLAlchemy database connection

4. models.py: Defines column for each database tables, which handles relationships between models and database schema

5. app/auth.py: provide the function of checking passwords, implements JWT authentication, provides password hashing and verification

Part 2: In the routers folder

1. routers/auth.py: Defines FastAPI routes (endpoints) related to authentication (e.g., login, signup, token refresh) here, it will handles requests and gives access by calling function from app/auth.py.

2. routers/users.py: Provides endpoints for user profile management, manages user-related operations and handles user data updates

3. routers/phq9_prediction.py: Provides endpoints for viewing test history, handles test submission and scoring, Manages PHQ-9 depression assessment tests. Provides endpoints for viewing and deleting predictions, handles EEG file upload and analysis and manages prediction history

Part 3: In the ml folder

1. ml/model.py: ML model file, which handles the prediction function by using trained neural network to processes EEG data and predicts result

2. ml/preprocessing.py: Handles data preprocessing logic, preparing data for model prediction.

Frontend part:
Part 1: HTML Files (Frontend Pages)
contact-us.html - Likely contains a contact form for users to reach out.
dashboard.html - The main user dashboard displaying relevant data.
EEG Upload.html - Page for uploading EEG data for analysis.
landing-page.html - The main landing page, typically the homepage of the site.
log-in-page.html - User login page.
PHQ.html - Likely a PHQ-9 depression screening questionnaire.
privacy-policy.html - Displays privacy policy information.
profile-settings.html - User profile settings page for updating information.
Result History.html - Displays a user's past results or reports.
sign-up-page.html - User registration/sign-up page.
Technical Result.html - Displays technical results, likely related to EEG data.
terms-and-conditions.html - Displays the terms and conditions of the website.

Part 2: JavaScript Files (Frontend Logic)
auth.js - Handles authentication logic (login, signup, session management).
eeg-upload.js - Handles EEG data upload functionality.
phq.js - Manages logic related to the PHQ questionnaire.
profile-settings.js - Controls user profile settings updates.
technical-history.js - Likely handles displaying historical technical results.
technical-result.js - Handles logic for showing technical EEG results.

Part 3: CSS File
styles.css - Contains the styling rules for the entire frontend.

Part 4: Other Folders
images/ - Stores image assets for the website.
extra/ - Could be additional files or resources.

Run frontend:
cd cp2\ -\ updated
python -m http.server 8080

http://localhost:8080/landing-page.html

Run backend:
uvicorn app.main:app --reload

http://127.0.0.1:8000/health
