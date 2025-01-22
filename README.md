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
### 4. Download MySQL 

https://dev.mysql.com/downloads/mysql/

- Install and set it up.
- Use the root user to create an "admin" user with all privileges
- Set the admin password to 123 or something you can remember
- Use the commands:

```sql
CREATE DATABASE ignition_link;
USE ignition_link;
```

- Replace the database URI in the .env to match the credentials and database name you set.
- Make sure the database status is **Running** under Management > Server Status
### 5. Move the .env file and Firebase .json credentials files into the directory root
These will not be checked into GitHub but they'll be available in the discord server.

### 6. Run the App

```bash
fastapi dev main.py
```
