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
- Set the password to 123 or something you can remember
- Use the commands in the psql Shell:

```sql
CREATE DATABASE ignition_link;
/connect ignition_link;
```

- Replace the database URI in the .env to match the credentials and database name you set.

### 5. Move the following files into your directory
- ignition-link-firebase-adminsdk.json
- .env 

These will **not** be checked into GitHub but they'll be posted in the discord server.

### 6. Run the App

```bash
fastapi dev main.py
```
