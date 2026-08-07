import React, { useState, useEffect } from 'react';
import './App.css'; 

const API_BASE_URL = "http://localhost:10000";

export default function App() {
  const [view, setView] = useState('admin'); 
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [role, setRole] = useState(localStorage.getItem('role') || null);
  const [empId, setEmpId] = useState(localStorage.getItem('empId') || null);

  const handleLogin = (data) => {
    setToken(data.access_token);
    setRole(data.role);
    try {
      const payload = JSON.parse(atob(data.access_token.split('.')[1]));
      setEmpId(payload.empid);
      localStorage.setItem('empId', payload.empid);
    } catch (e) {
      console.error("Failed to parse token payload");
    }
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('role', data.role);
  };

  const handleLogout = () => {
    setToken(null);
    setRole(null);
    setEmpId(null);
    localStorage.clear();
    setView('admin'); 
  };

  return (
    <div className="app-container">
      <nav className="navbar">
        <h1>AI Task Manager</h1>
        <div className="user-info">
          {token ? (
            <>
              <span>ID: <strong>{empId}</strong> ({role?.toUpperCase()})</span>
              <button onClick={handleLogout} className="btn btn-danger">Logout</button>
            </>
          ) : (
            <div style={{ display: 'flex', gap: '10px' }}>
              <button 
                onClick={() => setView('admin')} 
                style={{ backgroundColor: view === 'admin' ? '#1d4ed8' : '#3b82f6', color: 'white', padding: '8px 16px', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
              >
                Public Admin (Upload)
              </button>
              <button 
                onClick={() => setView('staff')} 
                style={{ backgroundColor: view === 'staff' ? '#1d4ed8' : '#3b82f6', color: 'white', padding: '8px 16px', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
              >
                Secure Staff Portal
              </button>
            </div>
          )}
        </div>
      </nav>

      <main className="main-content">
        {token ? (
          role === 'qa' ? <QADashboard token={token} /> : <EmployeeDashboard token={token} />
        ) : (
          view === 'admin' ? <AdminDashboard /> : <LoginView onLogin={handleLogin} />
        )}
      </main>
    </div>
  );
}

// ==========================================
// SECURE LOGIN COMPONENT
// ==========================================
function LoginView({ onLogin }) {
  const [email, setEmail] = useState('');
  const [employeeId, setEmployeeId] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      const res = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, employee_id: employeeId })
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Login failed');
      
      onLogin(data);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="login-wrapper">
      <div className="login-card">
        <h2>Staff Portal Login</h2>
        <p>Enter your Email and Employee ID to manage your assigned tasks.</p>
        
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <input 
            type="email" placeholder="Email Address" 
            value={email} onChange={(e) => setEmail(e.target.value)}
            className="file-input" required
          />
          <input 
            type="text" placeholder="Employee ID (e.g. EMP001)" 
            value={employeeId} onChange={(e) => setEmployeeId(e.target.value)}
            className="file-input" required
          />
          <button type="submit" className="btn btn-primary">Login</button>
        </form>
        {error && <p style={{ color: 'red', marginTop: '1rem' }}>{error}</p>}
      </div>
    </div>
  );
}

// ==========================================
// PUBLIC ADMIN DASHBOARD
// ==========================================
function AdminDashboard() {
  const [file, setFile] = useState(null);
  const [tasksFiles, setTasksFiles] = useState([]);
  const [statusMsg, setStatusMsg] = useState("");

  const fetchTasksFiles = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tasks`);
      const data = await response.json();
      const sortedData = data.sort((a, b) => new Date(b.uploaded_at) - new Date(a.uploaded_at));
      setTasksFiles(sortedData);
    } catch (error) {
      console.error("Failed to fetch files:", error);
    }
  };

  useEffect(() => { fetchTasksFiles(); }, []);

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
      const response = await fetch(`${API_BASE_URL}/api/upload-excel`, {
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
      <h2 className="dashboard-header">Public Admin Panel</h2>
      <p style={{marginBottom: "20px", color: "#4b5563"}}>Upload task lists here. The AI will automatically parse the Excel file, assign tasks to employees in MongoDB, and email them.</p>
      
      <div className="card">
        <h3>Upload New Task Excel</h3>
        <form onSubmit={handleUpload} style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <input 
            type="file" accept=".xlsx, .xls" 
            onChange={(e) => setFile(e.target.files[0])}
            className="file-input"
          />
          <button type="submit" className="btn btn-upload">Upload & Auto-Assign</button>
        </form>
        {statusMsg && <p className="status-msg">{statusMsg}</p>}
      </div>

      <div className="card">
        <h3>Recent Excel Task Files</h3>
        {tasksFiles.length === 0 ? (
          <p style={{ color: '#6b7280' }}>No task files uploaded yet.</p>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr><th>File ID</th><th>Filename</th><th>Status</th><th>Uploaded At</th></tr>
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

// ==========================================
// EMPLOYEE DASHBOARD
// ==========================================
function EmployeeDashboard({ token }) {
  const [tasks, setTasks] = useState([]);
  const [updateText, setUpdateText] = useState({}); 

  const fetchTasks = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/tasks/my`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) setTasks(await res.json());
    } catch (err) { console.error(err); }
  };

  useEffect(() => { fetchTasks(); }, []);

  const handleProgress = async (taskId) => {
    if (!updateText[taskId]) return; 

    try {
      const res = await fetch(`${API_BASE_URL}/tasks/${taskId}/progress`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ taskupdate: updateText[taskId] })
      });
      if (res.ok) {
        setUpdateText({ ...updateText, [taskId]: "" });
        fetchTasks();
      } else {
        const error = await res.json();
        alert(error.detail);
      }
    } catch (err) { alert("Failed to update"); }
  };

  const handleComplete = async (taskId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/tasks/${taskId}/complete`, {
        method: 'PATCH',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        alert("Task Sent to QA!");
        fetchTasks();
      } else {
        const error = await res.json();
        alert(error.detail);
      }
    } catch (err) { alert("Failed to complete"); }
  };

  const formatDueDate = (dateStr) => {
    if (!dateStr) return "Not Specified";
    
    const d = new Date(dateStr);
    
    // If it is NOT a valid calendar date (e.g., the AI just output the word "tuesday" or "ASAP")
    // This will capitalize the first letter so it looks nice!
    if (isNaN(d.getTime())) {
      return dateStr.charAt(0).toUpperCase() + dateStr.slice(1);
    } 
    
    // If it IS a valid calendar date, format it to show the Day AND the Date!
    return d.toLocaleDateString('en-US', {
      weekday: 'long',   // Shows "Monday", "Tuesday", etc.
      month: 'short',    // Shows "Jan", "Feb", "Aug", etc.
      day: 'numeric',    // Shows "11", "12", etc.
      year: 'numeric'    // Shows "2026"
    });
  };

  return (
    <div>
      <h2 className="dashboard-header">My Tasks</h2>
      <div className="card">
        {tasks.length === 0 ? <p>No tasks assigned yet.</p> : (
          <div className="table-container">
            <table className="data-table">
              <thead><tr><th>Task</th><th>Status</th><th>Due Date</th><th>QA Remarks</th><th>Action</th></tr></thead>
              <tbody>
                {tasks.map(t => (
                  <tr key={t._id}>
                    <td>{t.task}</td>
                    <td>
                      <span className="badge" style={{
                        backgroundColor: t.status === 'In Progress' ? '#dcfce7' : '#fef08a',
                        color: t.status === 'In Progress' ? '#166534' : '#854d0e'
                      }}>
                        {t.status}
                      </span>
                    </td>
                    <td>{formatDueDate(t.duedate)}</td>
                    <td>
                      <div style={{ 
                        color: '#b91c1c', fontSize: '12px', whiteSpace: 'pre-wrap', 
                        maxHeight: '80px', overflowY: 'auto', width: '220px',
                        backgroundColor: t.remarks ? '#fee2e2' : 'transparent',
                        padding: t.remarks ? '6px' : '0', borderRadius: '4px'
                      }}>
                        {t.remarks || 'None'}
                      </div>
                    </td>
                    <td>
                      {['Assigned', 'In Progress', 'Rework Required'].includes(t.status) ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          {t.taskupdate && (
                            <div style={{ 
                              fontSize: '12px', background: '#f9fafb', border: '1px solid #e5e7eb',
                              padding: '6px', borderRadius: '4px', whiteSpace: 'pre-wrap', 
                              maxHeight: '80px', overflowY: 'auto', width: '250px'
                            }}>
                              {t.taskupdate}
                            </div>
                          )}
                          <input 
                            type="text" placeholder="Add new update..." 
                            className="file-input" style={{ width: '250px' }}
                            value={updateText[t._id] || ''}
                            onChange={(e) => setUpdateText({...updateText, [t._id]: e.target.value})}
                          />
                          <button onClick={() => handleProgress(t._id)} className="btn btn-upload" style={{ padding: '4px' }}>Save Progress</button>
                          {t.status === 'In Progress' && (
                             <button onClick={() => handleComplete(t._id)} className="btn btn-success" style={{ padding: '4px' }}>Mark Done (Send to QA)</button>
                          )}
                        </div>
                      ) : (
                        <div style={{ fontSize: '12px', whiteSpace: 'pre-wrap' }}>{t.taskupdate}</div>
                      )}
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

// ==========================================
// QA DASHBOARD
// ==========================================
function QADashboard({ token }) {
  const [tasks, setTasks] = useState([]);
  const [remarks, setRemarks] = useState({});

  const fetchQueue = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/tasks/qa-queue`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) setTasks(await res.json());
    } catch (err) { console.error(err); }
  };

  useEffect(() => { fetchQueue(); }, []);

  const handleReview = async (taskId, status) => {
    try {
      const res = await fetch(`${API_BASE_URL}/tasks/${taskId}/review`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ remarks: remarks[taskId] || "Reviewed", status: status })
      });
      if (res.ok) {
        alert(`Task marked as ${status}`);
        fetchQueue();
      } else {
        const error = await res.json();
        alert(error.detail);
      }
    } catch (err) { alert("Review failed"); }
  };

  return (
    <div>
      <h2 className="dashboard-header">QA Workspace & History</h2>
      <div className="card">
        {tasks.length === 0 ? <p>No tasks in the QA system.</p> : (
          <div className="table-container">
            <table className="data-table">
              <thead><tr><th>EmpID</th><th>Task</th><th>Status</th><th>Employee Update</th><th>Review Action / History</th></tr></thead>
              <tbody>
                {tasks.map(t => (
                  <tr key={t._id}>
                    <td>{t.empid}</td>
                    <td>{t.task}</td>
                    <td>
                      <span className="badge" style={{
                        backgroundColor: t.status === 'Approved' ? '#dcfce7' : (t.status === 'Under QA Review' ? '#fef08a' : '#fee2e2'),
                        color: t.status === 'Approved' ? '#166534' : (t.status === 'Under QA Review' ? '#854d0e' : '#b91c1c')
                      }}>
                        {t.status}
                      </span>
                    </td>
                    <td>
                      <div style={{ 
                         fontSize: '12px', background: '#f9fafb', border: '1px solid #e5e7eb',
                         padding: '6px', borderRadius: '4px', whiteSpace: 'pre-wrap', 
                         maxHeight: '120px', overflowY: 'auto', width: '250px'
                      }}>
                        {t.taskupdate || 'No update provided'}
                      </div>
                    </td>
                    <td>
                      {t.status === 'Under QA Review' ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                          <textarea 
                            placeholder="QA Feedback / Remarks" 
                            className="file-input" style={{ width: '250px', height: '60px', resize: 'vertical' }}
                            value={remarks[t._id] || ''}
                            onChange={(e) => setRemarks({...remarks, [t._id]: e.target.value})}
                          />
                          <div style={{ display: 'flex', gap: '10px' }}>
                            <button onClick={() => handleReview(t._id, 'Approved')} className="btn btn-success" style={{ padding: '6px' }}>Approve</button>
                            <button onClick={() => handleReview(t._id, 'Rework Required')} className="btn btn-danger" style={{ padding: '6px' }}>Reject (Rework)</button>
                          </div>
                        </div>
                      ) : (
                        <div style={{ 
                          color: '#b91c1c', fontSize: '12px', whiteSpace: 'pre-wrap', 
                          maxHeight: '120px', overflowY: 'auto', width: '250px',
                          backgroundColor: '#fee2e2', padding: '6px', borderRadius: '4px'
                        }}>
                          {t.remarks}
                        </div>
                      )}
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