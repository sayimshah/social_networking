# social_networking

Prerequisites
Python: Ensure Python is installed on your system. You can download and install Python from the official website.
Steps
Clone Repository: Clone the repository containing your Django project to your local machine.
git clone https://github.com/sayimshah/social_networking.git

Navigate to Project Directory: Change directory to your project directory.

Set Up Virtual Environment (Optional): It's recommended to create a virtual environment to isolate your project dependencies.
# Create a virtual environment named venv
python -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On Unix/Linux
venv\Scripts\activate      # On Windows

Install Dependencies: Install the project dependencies specified in the requirements.txt file.
pip install -r requirements.txt

Run Database Migrations: Apply database migrations to set up the database schema.
python manage.py migrate

Start Django Development Server: Run the Django development server to serve your application locally.
python manage.py runserver

Postman API collection link 
https://documenter.getpostman.com/view/20269822/2sA3Qv7Adh



