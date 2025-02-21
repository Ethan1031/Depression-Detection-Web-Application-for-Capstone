# Depression-Detection-Web-Application-for-Capstone

Part 1: In the app folder:

1. Schemas.py: Validate the input data of API is same as the format we predifined in class. For example, a client sends a request to create a user, FastAPI will check if the incoming data follows the UserCreate schema.

2. config.py: Uses Pydantic's BaseSettings to automatically read and validate values from an .env file, ensuring that critical configurations (e.g., database credentials and security settings) are properly set before your app runs.

3. database.py: Sets up SQLAlchemy database connection

4. models.py: Defines column for each database tables, which handles relationships between models and database schema

5. app/auth.py: provide the function of checking passwords, implements JWT authentication, provides password hashing and verification

Part 2: In the routers folder

1. routers/auth.py: Defines FastAPI routes (endpoints) related to authentication (e.g., login, signup, token refresh) here, it will handles requests and gives access by calling function from app/auth.py.

2. routers/users.py: Provides endpoints for user profile management, manages user-related operations and handles user data updates

3. routers/predictions.py: Provides endpoints for viewing and deleting predictions, handles EEG file upload and analysis and manages prediction history

4. routers/phq9.py: Provides endpoints for viewing test history, handles test submission and scoring, Manages PHQ-9 depression assessment tests

Part 3: In the ml folder

1. ml/model.py: ML model file, which handles the prediction function by using trained neural network to processes EEG data and predicts result

2. ml/preprocessing.py: Handles data preprocessing logic, preparing data for model prediction.
