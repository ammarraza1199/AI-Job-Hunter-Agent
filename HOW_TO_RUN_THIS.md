# How to Successfully Run the AI Job Hunter Agent

Here is the complete, step-by-step guide to setting up and running your AI Job Hunter Agent from scratch.

---

### Step 1: Install Dependencies
Open your terminal (Command Prompt/PowerShell/VS Code Terminal) inside the `Job_scrapping_agent` folder and run the following commands to install required Python packages and the Playwright browser:

```bash
pip install -r requirements.txt
playwright install chromium
```

---

### Step 2: Get Your Free API Keys

**Groq AI (For Resume matching & scoring):**
1. Go to [console.groq.com/keys](https://console.groq.com/keys) and create a free account.
2. Generate an API Key and copy it.

**Google Sheets (For saving your jobs):**
1. Go to the [Google Cloud Console](https://console.cloud.google.com).
2. Create a new project.
3. Search for **"Google Sheets API"** and **"Google Drive API"** in the top search bar and click **Enable** for both.
4. Go to **APIs & Services** > **Credentials** -> **Create Credentials** -> **Service Account**.
5. Once the Service Account is created, click on it, go to the **Keys** tab, click **Add Key** -> **Create new key** (choose JSON format).
6. Rename this downloaded file to exactly `credentials.json` and move it into your `Job_scrapping_agent` folder.

---

### Step 3: Configure the `.env` File
Open the `.env` file in the project folder and fill in your details:

*   `GROQ_API_KEY`: Paste your Groq key here.
*   `GOOGLE_SHEETS_SPREADSHEET_ID`: Open the Google Sheet where you want to save jobs. Look at the URL. It will look like `https://docs.google.com/spreadsheets/d/your-long-id-string/edit`. Copy the `your-long-id-string` part and paste it here.
*   `GOOGLE_SHEETS_WORKSHEET_NAME`: Put `Jobs` (or whatever tab name you want to use, but the app will automatically create a tab named `Jobs` if it doesn't exist).

---

### Step 4: Share Your Google Sheet! (CRUCIAL STEP)
If you skip this step, the app will fail to save the jobs due to missing permissions!

1. Open your `credentials.json` file.
2. Look for the `"client_email"` line (it will look something like `my-project@my-project.iam.gserviceaccount.com`). Copy that email address.
3. Go to your open Google Sheet in your web browser.
4. Click the big **Share** button in the top right.
5. Paste that exact email address in, give it **Editor** permissions, and click Share.

---

### Step 5: Perform the One-Time LinkedIn Login
LinkedIn aggressively blocks unauthenticated scrapers. You need to log in manually *once* so the app can save a "cookie session" to use automatically later.

Run this single command in your terminal:
```bash
python -c "from utils.cookie_manager import prompt_manual_login; prompt_manual_login('linkedin', 'https://www.linkedin.com/login')"
```

1. A visible Chrome browser window will pop up.
2. Log in directly to your LinkedIn account.
3. Once you successfully see your LinkedIn feed, **close the browser window manually**. 
4. The app will capture your cookies and save them in the `sessions/` folder for future runs.

---

### Step 6: Run the AI Job Hunter!
Place your resume (e.g., `resume.pdf` or `resume.docx`) inside the `Job_scrapping_agent` folder.

Then, run the main script in your terminal. 

*Example for a Python Developer located in Hyderabad:*
```bash
python main.py --resume resume.pdf --query "Python Developer" --location "Hyderabad"
```

**(Optional) Scrape Specific Platforms:**
If you only want to scrape Indeed and Naukri (skipping LinkedIn), you can add the `--platforms` flag:
```bash
python main.py --resume resume.pdf --query "Python Developer" --location "Hyderabad" --platforms "indeed,naukri"
```

The app will output its live progress in the terminal. When it completes, check your Google Sheet for beautifully scored and categorized job listings along with custom cover letters!
