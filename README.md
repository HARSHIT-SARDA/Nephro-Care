# NephroCare — corrected academic project

## Project structure

```text
NephroCare/
├── app.py
├── database.py
├── model_service.py
├── train_model.py
├── requirements.txt
├── database/
│   ├── nephrocare.sql
│   └── reset_database.sql
├── dataset/
│   └── kidney_disease.csv
├── model/
│   └── model.pkl
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── prediction.html
│   ├── result.html
│   ├── history.html
│   ├── profile.html
│   ├── about.html
│   ├── services.html
│   └── contact.html
├── static/
│   ├── css/
│   ├── js/
│   └── images/
└── tests/
```

## Technology stack
- Front end: HTML, CSS, Bootstrap 5, JavaScript
- Back end: Python and Flask
- Database: MySQL
- Machine learning: pandas, NumPy, scikit-learn Random Forest
- PDF reports: ReportLab

## Recommended environment
Use **Python 3.11** (or 3.12) for this pinned dependency set. Do not use an old virtual environment created under another Python version.

## Windows setup

Open PowerShell in the project root (the folder containing `app.py`).

If an old `venv` was created using another Python version, close VS Code terminals and delete that project's `venv` folder first. Then run:

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, use this command for the current terminal only, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

## MySQL setup

1. Start MySQL Server and open MySQL Workbench.
2. Open `database/nephrocare.sql` and execute it. It creates the database and required tables without dropping an existing database.
3. The app defaults to host `localhost`, port `3306`, user `root`, password `1234`, database `nephrocare`. If your local password is different, set it before running the app:

```powershell
$env:MYSQL_PASSWORD = "your_mysql_password"
```

Optional environment variables: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_DATABASE`, `SECRET_KEY`.

**Warning:** `database/reset_database.sql` deletes the existing `nephrocare` database. Only use it if you have backed up anything important and intentionally want to erase old data.

## Retrain the model for the installed scikit-learn version

Because pickle model files can be version-sensitive, after installing the requirements run this once from the project root:

```powershell
python train_model.py
```

This recreates `model/model.pkl` from `dataset/kidney_disease.csv`.

## Start the app

```powershell
python database.py
python app.py
```

Open `http://127.0.0.1:5000`.

## Tests

From the project root:

```powershell
python -m pytest -q
```

## Important notes
- Passwords are stored as hashes.
- Prediction history and report downloads are scoped to the signed-in user.
- `confidence` is the model's confidence in the predicted class; `probability` is the estimated probability of the CKD class.
- Risk labels are application-defined and are not a clinically validated severity score.
- This project is an academic screening prototype, not a medical diagnosis. Consult a qualified healthcare professional for diagnosis or treatment.
