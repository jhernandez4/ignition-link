# ignition-link

## Project Setup
### 1. Clone the Repo
```bash
git clone https://github.com/jhernandez4/ignition-link.git
cd ignition-link 
```

### 2. Set Up the Virtual Environment

Create and activate the virtual environment to isolate the project dependencies. 

Once you have the the virtual environment created, you only have to **activate** it
from here on out when you open the project directory.


#### Using macOS/Linux:

```bash
python3 -m venv virtualEnv
source virtualEnv/bin/activate
```

#### Using Windows:

```bash
py -3 -m venv virtualEnv
virtualEnv\Scripts\activate
```

### 3. Install the Dependencies

```bash
pip install -r requirements.txt
```
### 4. Download Postgresql 

https://www.postgresql.org/download/

- Install and set it up.
- Use the default postgresql user or create an "admin" user with all privileges
- Use the following commands in the psql Shell:

```sql
CREATE DATABASE ignition_link;
/connect ignition_link;
```

- In the next step, adjust the database URI value in the .env file to match the credentials and database name you set in this step.

### 5. Move the following files into your directory
- `ignition-link-firebase-adminsdk.json`
- `.env`
- `admin_emails.txt` *(optional)*

Generate the admin SDK private key with Firebase: https://firebase.google.com/docs/admin/setup#python

Ensure that the `.env` file has the following fields:
```env
FIREBASE_KEY_PATH="PATH_TO_FIREBASE_ADMIN_SDK_PRIVATE_KEY"
PSQL_URI="postgresql://username:password@localhost/ignition_link"
BRANDS_TXT_PATH="https://raw.githubusercontent.com/jhernandez4/vehicles_dataset/refs/heads/main/brands.txt"
UNIQUE_VEHICLES_CSV_PATH="https://raw.githubusercontent.com/jhernandez4/vehicles_dataset/refs/heads/main/unique_vehicles.csv"
GEMINI_API_KEY="MY_GEMINI_API_KEY"
CORS_ORIGINS=http://localhost:5173
```
Generate a Gemini API key here: https://ai.google.dev/gemini-api/docs/api-key

### 6. Run the App

```bash
fastapi dev main.py
```
