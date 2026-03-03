Steps to run this in EC2

# 1. Update the server
sudo apt update && sudo apt upgrade -y

# 2. Install Python virtual environment tools
sudo apt install python3-venv git -y

# 3. Clone your code from GitHub 
git clone YOUR_GITHUB_REPO_URL
cd YOUR_PROJECT_FOLDER_NAME

#4.Create and store the required environment variables
nano .env

Install Dependencies - Create a fresh clean room (virtual environment) on the server and install your packages:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Run the App Forever
# Open a background terminal named "backend"
tmux new -s backend

# Run your code
source venv/bin/activate
python backend.py
Press CTRL+B, then press D to safely detach and leave it running in the background.

Start the Frontend:
# Open a second background terminal named "frontend"
tmux new -s frontend

# Run Streamlit
source venv/bin/activate
streamlit run frontend.py

Press CTRL+B, then press D to detach.

