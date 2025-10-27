from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
import shutil
import fitz  # PyMuPDF for text extraction

app = FastAPI(title="Secure File Manager with PDF Extractor")

# 🔹 Secret key for session (change to any random string)
app.add_middleware(SessionMiddleware, secret_key="my_super_secret_key")

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ✅ Dummy credentials (you can change)
USERNAME = "admin"
PASSWORD = "12345"


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # If not logged in, show login form
    if not request.session.get("logged_in"):
        return HTMLResponse(content=login_html())

    # If logged in, show file manager
    return HTMLResponse(content=file_manager_html())


@app.post("/login")
async def login(request: Request):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")

    if username == USERNAME and password == PASSWORD:
        request.session["logged_in"] = True
        return RedirectResponse(url="/", status_code=303)
    else:
        return HTMLResponse(login_html(message="❌ Invalid credentials, try again!"))


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")


@app.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    if not request.session.get("logged_in"):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return JSONResponse({"message": "File uploaded successfully"})


@app.get("/list")
async def list_files(request: Request):
    if not request.session.get("logged_in"):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    return os.listdir(UPLOAD_DIR)


@app.get("/download/{filename}")
async def download_file(request: Request, filename: str):
    if not request.session.get("logged_in"):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    file_path = os.path.join(UPLOAD_DIR, filename)
    return FileResponse(file_path, filename=filename)


@app.get("/open/{filename}")
async def open_pdf(request: Request, filename: str):
    if not request.session.get("logged_in"):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        return JSONResponse({"error": "File not found"}, status_code=404)
    return FileResponse(file_path, media_type='application/pdf')


@app.get("/extract/{filename}")
async def extract_text(request: Request, filename: str):
    if not request.session.get("logged_in"):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        return JSONResponse({"error": "File not found"}, status_code=404)
    text = ""
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text("text")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    return JSONResponse({"text": text or "No text found in this PDF."})


@app.delete("/delete/{filename}")
async def delete_file(request: Request, filename: str):
    if not request.session.get("logged_in"):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return JSONResponse({"message": "File deleted"})
    return JSONResponse({"error": "File not found"}, status_code=404)


# 🧩 LOGIN PAGE HTML
def login_html(message: str = ""):
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Login | Secure File Manager</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #bbdefb, #e3f2fd);
                display: flex; justify-content: center; align-items: center;
                height: 100vh; margin: 0;
            }}
            .login-box {{
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.2);
                text-align: center;
                width: 350px;
            }}
            h2 {{ margin-bottom: 20px; color: #1976d2; }}
            input {{
                width: 100%;
                padding: 10px;
                margin: 8px 0;
                border: 1px solid #ccc;
                border-radius: 6px;
            }}
            button {{
                background: #1976d2;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                cursor: pointer;
                width: 100%;
                margin-top: 10px;
            }}
            button:hover {{ background: #1565c0; }}
            p {{ color: red; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="login-box">
            <h2>🔐 Secure Login</h2>
            <form action="/login" method="post">
                <input type="text" name="username" placeholder="Username" required><br>
                <input type="password" name="password" placeholder="Password" required><br>
                <button type="submit">Login</button>
            </form>
            <p>{message}</p>
        </div>
    </body>
    </html>
    """


# 🧩 FILE MANAGER HTML (your original unchanged design)
def file_manager_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>File Manager | FastAPI</title>
<style>
body {
    font-family: "Segoe UI", Roboto, sans-serif;
    background: linear-gradient(135deg, #e3f2fd, #f8f9fa);
    margin: 0; padding: 0;
    display: flex; flex-direction: column;
    align-items: center;
    min-height: 100vh;
}
header {
    background: #1976d2;
    color: white;
    width: 100%;
    text-align: center;
    padding: 20px 0;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2);
}
.container {
    margin-top: 30px;
    width: 80%;
    max-width: 900px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    padding: 30px;
}
h1 { margin: 0; font-size: 28px; }
form {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
    justify-content: center;
}
input[type="file"] {
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 6px;
}
button {
    background: #1976d2;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
    transition: 0.3s;
}
button:hover { background: #125a9e; }
.file-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 15px;
}
.file-card {
    background: #fafafa;
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 15px;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    transition: transform 0.2s, box-shadow 0.2s;
}
.file-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
.file-name {
    font-weight: bold;
    color: #333;
    margin-bottom: 10px;
    word-wrap: break-word;
}
.actions button {
    margin: 3px;
    padding: 6px 12px;
    border-radius: 5px;
    border: none;
}
.open { background: #43a047; }
.download { background: #0288d1; }
.delete { background: #e53935; }
.extract { background: #8e24aa; }
.open:hover { background: #2e7d32; }
.download:hover { background: #0277bd; }
.delete:hover { background: #c62828; }
.extract:hover { background: #6a1b9a; }
footer {
    margin-top: auto;
    background: #1976d2;
    color: white;
    width: 100%;
    text-align: center;
    padding: 15px 0;
    font-size: 14px;
}
#textOutput {
    margin-top: 20px;
    padding: 20px;
    background: #f9f9f9;
    border-radius: 10px;
    border: 1px solid #ddd;
    max-height: 400px;
    overflow-y: auto;
    white-space: pre-wrap;
}
.logout {
    position: absolute;
    top: 20px;
    right: 20px;
    background: #e53935;
    padding: 8px 12px;
    border-radius: 6px;
    color: white;
    text-decoration: none;
}
.logout:hover { background: #c62828; }
</style>
</head>
<body>
<header>
<h1>📁 FastAPI File Manager</h1>
<a href="/logout" class="logout">Logout</a>
</header>
<div class="container">
<form id="uploadForm">
<input type="file" name="file" />
<button type="submit">Upload</button>
<button type="button" onclick="loadFiles()">Refresh</button>
</form>
<div id="fileList" class="file-list"></div>
<div id="textOutput"></div>
</div>
<footer>Built with ❤️ using FastAPI</footer>
<script>
async function uploadFile(event) {
    event.preventDefault();
    const formData = new FormData(document.getElementById('uploadForm'));
    const res = await fetch('/upload', { method: 'POST', body: formData });
    if (res.ok) {
        alert('✅ File uploaded successfully!');
        loadFiles();
    } else {
        alert('❌ Upload failed!');
    }
}
async function loadFiles() {
    const res = await fetch('/list');
    const files = await res.json();
    const container = document.getElementById('fileList');
    container.innerHTML = '';
    if (files.length === 0) {
        container.innerHTML = '<p style="text-align:center; color:#777;">No files uploaded yet.</p>';
        return;
    }
    files.forEach(file => {
        let openButton = '';
        let extractButton = '';
        if (file.toLowerCase().endsWith('.pdf')) {
            openButton = `<a href="/open/${file}" target="_blank"><button class="open">Open</button></a>`;
            extractButton = `<button class="extract" onclick="extractText('${file}')">Extract Text</button>`;
        }
        const div = document.createElement('div');
        div.className = 'file-card';
        div.innerHTML = `
            <div class="file-name">${file}</div>
            <div class="actions">
                ${openButton}
                ${extractButton}
                <a href="/download/${file}"><button class="download">Download</button></a>
                <button class="delete" onclick="deleteFile('${file}')">Delete</button>
            </div>
        `;
        container.appendChild(div);
    });
}
async function deleteFile(filename) {
    const confirmDelete = confirm(`Are you sure you want to delete "${filename}"?`);
    if (!confirmDelete) return;
    await fetch('/delete/' + filename, { method: 'DELETE' });
    loadFiles();
}
async function extractText(filename) {
    const res = await fetch('/extract/' + filename);
    if (!res.ok) {
        alert('❌ Failed to extract text');
        return;
    }
    const data = await res.json();
    const output = document.getElementById('textOutput');
    output.innerHTML = "<h3>📜 Extracted Text:</h3><pre>" + data.text + "</pre>";
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
}
document.getElementById('uploadForm').addEventListener('submit', uploadFile);
loadFiles();
</script>
</body>
</html>
"""
