import React, { useState, useEffect } from 'react';
import './App.css'; // Import the custom CSS file

export default function App() {
  const [role, setRole] = useState(null);

  if (!role) {
    return <LoginView setRole={setRole} />;
  }

  return (
    <div className="app-container">
      <nav className="navbar">
        <h1>AI Task Manager</h1>
        <div className="user-info">
          <span>Logged in as: <strong>{role.toUpperCase()}</strong></span>
          <button onClick={() => setRole(null)} className="btn btn-danger">
            Logout
          </button>
        </div>
      </nav>

      <main className="main-content">
        {role === 'admin' ? <AdminDashboard /> : <EmployeeDashboard />}
      </main>
    </div>
  );
}

function LoginView({ setRole }) {
  return (
    <div className="login-wrapper">
      <div className="login-card">
        <h2>System Login</h2>
        <p>Select your portal to continue.</p>
        <button onClick={() => setRole('admin')} className="btn btn-primary">
          Login as Admin
        </button>
        <button onClick={() => setRole('employee')} className="btn btn-success">
          Login as Employee
        </button>
      </div>
    </div>
  );
}

function AdminDashboard() {
  const [file, setFile] = useState(null);
  const [tasksFiles, setTasksFiles] = useState([]);
  const [statusMsg, setStatusMsg] = useState("");

  const API_BASE_URL = "http://localhost:10000/api";

  const fetchTasksFiles = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/tasks`);
      const data = await response.json();
      
      const sortedData = data.sort((a, b) => new Date(b.uploaded_at) - new Date(a.uploaded_at));
      setTasksFiles(sortedData);
    } catch (error) {
      console.error("Failed to fetch files:", error);
    }
  };

  useEffect(() => {
    fetchTasksFiles();
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setStatusMsg("Please select an Excel file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setStatusMsg("Uploading and triggering AI Allocation...");
      const response = await fetch(`${API_BASE_URL}/upload-excel`, {
        method: "POST",
        body: formData,
      });
      const result = await response.json();
      
      if (result.success) {
        setStatusMsg("✅ Upload successful! AI is processing in the background.");
        setFile(null);
        fetchTasksFiles(); 
      } else {
        setStatusMsg("❌ Upload failed.");
      }
    } catch (error) {
      setStatusMsg("❌ Server error during upload.");
    }
  };

  return (
    <div>
      <h2 className="dashboard-header">Admin Control Panel</h2>
      
      <div className="card">
        <h3>Upload New Task Excel</h3>
        <form onSubmit={handleUpload} className="upload-form">
          <input 
            type="file" 
            accept=".xlsx, .xls" 
            onChange={(e) => setFile(e.target.files[0])}
            className="file-input"
          />
          <button type="submit" className="btn btn-upload">
            Upload to MongoDB
          </button>
        </form>
        {statusMsg && <p className="status-msg">{statusMsg}</p>}
      </div>

      <div className="card">
        <h3>Recent Task Files in Database (Latest First)</h3>
        {tasksFiles.length === 0 ? (
          <p style={{ color: '#6b7280' }}>No task files uploaded yet.</p>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>File ID</th>
                  <th>Filename</th>
                  <th>Status</th>
                  <th>Uploaded At</th>
                </tr>
              </thead>
              <tbody>
                {tasksFiles.map((f) => (
                  <tr key={f._id}>
                    <td style={{ fontSize: '0.875rem', color: '#6b7280' }}>{f._id}</td>
                    <td style={{ fontWeight: '500' }}>{f.filename}</td>
                    <td><span className="badge">{f.status}</span></td>
                    <td style={{ fontSize: '0.875rem', color: '#4b5563' }}>
                      {new Date(f.uploaded_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function EmployeeDashboard() {
  return (
    <div className="card" style={{ textAlign: 'center' }}>
      <h2 className="dashboard-header">Employee Workspace</h2>
      <p style={{ color: '#4b5563', lineHeight: '1.6' }}>
        Welcome! When the Admin uploads an Excel file, the AI backend automatically allocates tasks and emails you. 
        You will see your assigned tasks here in a future update.
      </p>
    </div>
  );
}