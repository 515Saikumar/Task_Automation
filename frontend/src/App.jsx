import React, { useState, useEffect, useRef } from 'react';
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
      {/* --- Sidebar Navigation --- */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span style={{ fontSize: '1.8rem' }}>⚡</span> Task Manager
        </div>
        
        <div className="sidebar-menu">
          {token ? (
            <button className="sidebar-btn active">
              <span style={{ fontSize: '1.2rem' }}>💻</span> My Workspace
            </button>
          ) : (
              <>
                <button 
                  className={`sidebar-btn ${view === 'admin' ? 'active' : ''}`} 
                  onClick={() => setView('admin')}
                >
                  <span style={{ fontSize: '1.2rem' }}>👑</span> Public Admin
                </button>
                <button 
                  className={`sidebar-btn ${view === 'staff' ? 'active' : ''}`} 
                  onClick={() => setView('staff')}
                >
                  <span style={{ fontSize: '1.2rem' }}>🔒</span> Staff Portal
                </button>
              </>
            )}
          </div>

          <div className="user-profile">
            {token && (
              <>
                <div style={{fontSize: '0.85rem', color: 'var(--text-muted)'}}>Logged in as:</div>
                <div style={{fontWeight: 'bold', color: 'white', marginBottom: '10px'}}>{empId} <span style={{fontSize:'0.8rem', color:'var(--accent-primary)'}}>({role?.toUpperCase()})</span></div>
                <button onClick={handleLogout} className="btn btn-danger" style={{ width: '100%' }}>Logout</button>
              </>
            )}
          </div>
        </aside>

      {/* --- Main Content Area --- */}
      <main className="main-content custom-scroll">
        {token ? (
          role === 'qa' ? <QADashboard token={token} /> : <EmployeeDashboard token={token} />
        ) : (
          view === 'admin' ? <AdminDashboard /> : <LoginView onLogin={handleLogin} />
        )}
      </main>

      {/* NEW: Floating AI Chatbot Widget */}
      <AIChatbot />
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
  const [adminTab, setAdminTab] = useState('overview'); // 'overview' or 'upload'
  const [taskFilter, setTaskFilter] = useState('all'); // 'all', 'ongoing', 'completed'
  const [file, setFile] = useState(null);
  const [tasksFiles, setTasksFiles] = useState([]);
  const [taskOverview, setTaskOverview] = useState({ total_tasks: 0, completed_tasks: 0, ongoing_tasks: 0, tasks: [] });
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

  const fetchTaskOverview = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/tasks-overview`);
      const data = await response.json();
      setTaskOverview(data);
    } catch (error) {
      console.error("Failed to fetch task overview:", error);
    }
  };

  useEffect(() => { 
    fetchTasksFiles(); 
    fetchTaskOverview();
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
      const response = await fetch(`${API_BASE_URL}/api/upload-excel`, {
        method: "POST",
        body: formData,
      });
      const result = await response.json();
      
      if (result.success) {
        setStatusMsg("✅ Upload successful! AI is processing in the background.");
        setFile(null);
        fetchTasksFiles(); 
        fetchTaskOverview();
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
      
      <div className="tab-container">
        <button onClick={() => setAdminTab('overview')} className={adminTab === 'overview' ? 'tab-active' : 'tab-inactive'}>Global Task Overview</button>
        <button onClick={() => setAdminTab('upload')} className={adminTab === 'upload' ? 'tab-active' : 'tab-inactive'}>Upload & Files</button>
        <button onClick={() => setAdminTab('manual')} className={adminTab === 'manual' ? 'tab-active' : 'tab-inactive'}>Manual Allocation</button>
      </div>

      {adminTab === 'manual' && (
        <div className="card">
          <h3>Manual Task Allocation</h3>
          <p style={{marginBottom: '15px', color: '#6b7280', fontSize: '14px'}}>Assign a task to an employee directly without an Excel file.</p>
          <ManualAllocationForm onAllocated={() => {
            fetchTaskOverview();
            setStatusMsg("Task manually assigned successfully!");
            setTimeout(() => setStatusMsg(""), 3000);
          }} />
          {statusMsg && <p className="status-msg" style={{color: 'green', marginTop: '10px'}}>{statusMsg}</p>}
        </div>
      )}

      {adminTab === 'upload' && (
        <>
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
                        <td>
                          <span className={`badge ${
                            f.status === 'Completed' || f.status === 'Processed' ? 'badge-success' : 'badge-warning'
                          }`}>
                            {f.status}
                          </span>
                        </td>
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
        </>
      )}

      {adminTab === 'overview' && (
        <div className="card">
          <h3>Global Task Overview</h3>
          <p style={{marginBottom: '15px', color: '#6b7280', fontSize: '14px'}}>Click on a card below to filter the table.</p>
          <div style={{ display: 'flex', gap: '20px', marginBottom: '30px' }}>
            <div 
              onClick={() => setTaskFilter('all')}
              className={`metric-card ${taskFilter === 'all' ? 'active' : ''}`}>
              <h4>Total Tasks</h4>
              <p>{taskOverview.total_tasks}</p>
            </div>
            <div 
              onClick={() => setTaskFilter('ongoing')}
              className={`metric-card ${taskFilter === 'ongoing' ? 'active' : ''}`}>
              <h4>Ongoing</h4>
              <p style={{background: 'linear-gradient(135deg, #f59e0b, #fbbf24)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent'}}>{taskOverview.ongoing_tasks}</p>
            </div>
            <div 
              onClick={() => setTaskFilter('completed')}
              className={`metric-card ${taskFilter === 'completed' ? 'active' : ''}`}>
              <h4>Completed</h4>
              <p style={{background: 'linear-gradient(135deg, #10b981, #34d399)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent'}}>{taskOverview.completed_tasks}</p>
            </div>
          </div>

          {taskOverview.tasks.length === 0 ? (
            <p style={{ color: '#6b7280' }}>No tasks found in the database.</p>
          ) : (
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Task Name</th>
                    <th>Assigned To</th>
                    <th>QA Reviewer</th>
                    <th>Status</th>
                    <th>Due Date</th>
                  </tr>
                </thead>
                <tbody>
                  {taskOverview.tasks.filter(t => {
                    if (taskFilter === 'all') return true;
                    const isCompleted = t.status === "Approved" || t.status === "Done";
                    if (taskFilter === 'completed') return isCompleted;
                    if (taskFilter === 'ongoing') return !isCompleted;
                    return true;
                  }).map((t) => (
                    <tr key={t._id}>
                      <td style={{ fontWeight: '500' }}>{t.task}</td>
                      <td>{t.empname || t.empid}</td>
                      <td>{t.qa_name || "-"}</td>
                      <td>
                        <span className={`badge ${
                          t.status === 'Approved' || t.status === 'Done' ? 'badge-success' : 'badge-warning'
                        }`}>
                          {t.status}
                        </span>
                      </td>
                      <td style={{ fontSize: '0.875rem', color: '#4b5563' }}>
                        {new Date(t.duedate).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

    </div>
  );
}

// ==========================================
// EMPLOYEE DASHBOARD
// ==========================================
function EmployeeDashboard({ token }) {
  const [tasks, setTasks] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [updateText, setUpdateText] = useState({}); 
  const [reassignId, setReassignId] = useState({}); 

  const fetchTasks = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/tasks/my`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) setTasks(await res.json());
    } catch (err) { console.error(err); }
  };

  const fetchEmployees = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/emp`);
      if (res.ok) setEmployees(await res.json());
    } catch (err) { console.error(err); }
  };

  useEffect(() => { 
    fetchTasks(); 
    fetchEmployees();
  }, []);

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

  const handleReassign = async (taskId) => {
    const newEmpId = reassignId[taskId];
    if (!newEmpId) return alert("Please select an employee to reassign to.");
    
    try {
      const res = await fetch(`${API_BASE_URL}/tasks/${taskId}/reassign`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ new_empid: newEmpId })
      });
      if (res.ok) {
        alert("Task Reassigned!");
        fetchTasks();
      } else {
        const error = await res.json();
        alert(error.detail || "Failed to reassign task");
      }
    } catch (err) { alert("Failed to reassign"); }
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
              <thead><tr><th>Task</th><th>Status</th><th>Due Date</th><th>QA Reviewer</th><th>QA Remarks</th><th>Action</th></tr></thead>
              <tbody>
                {tasks.map(t => (
                  <tr key={t._id}>
                    <td>{t.task}</td>
                    <td>
                      <span className={`badge ${
                        t.status === 'In Progress' ? 'badge-success' : 'badge-warning'
                      }`}>
                        {t.status}
                      </span>
                    </td>
                    <td>{formatDueDate(t.duedate)}</td>
                    <td style={{ fontSize: '0.875rem', color: '#4b5563', fontWeight: '500' }}>{t.qa_name || <span style={{color: '#9ca3af', fontStyle: 'italic'}}>Pending...</span>}</td>
                    <td>
                      <div style={{ 
                        color: '#f87171', fontSize: '12px', whiteSpace: 'pre-wrap', 
                        maxHeight: '80px', overflowY: 'auto', width: '220px',
                        backgroundColor: t.remarks ? 'rgba(239, 68, 68, 0.1)' : 'transparent',
                        padding: t.remarks ? '6px' : '0', borderRadius: '6px',
                        border: t.remarks ? '1px solid rgba(239, 68, 68, 0.2)' : 'none'
                      }}>
                        {t.remarks || 'None'}
                      </div>
                    </td>
                    <td>
                      {['Assigned', 'In Progress', 'Rework Required'].includes(t.status) ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                          {t.taskupdate && (
                            <div style={{ 
                              fontSize: '12px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)',
                              padding: '8px', borderRadius: '6px', whiteSpace: 'pre-wrap', 
                              maxHeight: '80px', overflowY: 'auto', width: '250px',
                              color: 'var(--text-main)'
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
                          <div style={{ display: 'flex', gap: '5px', marginTop: '5px' }}>
                            <select 
                              className="file-input" style={{ width: '150px', padding: '4px' }}
                              value={reassignId[t._id] || ""}
                              onChange={(e) => setReassignId({...reassignId, [t._id]: e.target.value})}
                            >
                              <option value="">Select Colleague</option>
                              {employees
                                .filter(e => e.employee_id !== t.empid && (!t.category || e.primary_category === t.category))
                                .map(e => (
                                <option key={e.employee_id} value={e.employee_id}>{e.name} ({e.primary_category})</option>
                              ))}
                            </select>
                            <button onClick={() => handleReassign(t._id)} className="btn btn-danger" style={{ padding: '4px' }}>Reassign</button>
                          </div>
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
                      <span className={`badge ${
                        t.status === 'Approved' ? 'badge-success' : (t.status === 'Under QA Review' ? 'badge-warning' : 'badge-danger')
                      }`}>
                        {t.status}
                      </span>
                    </td>
                    <td>
                      <div style={{ 
                         fontSize: '12px', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)',
                         padding: '8px', borderRadius: '6px', whiteSpace: 'pre-wrap', 
                         maxHeight: '120px', overflowY: 'auto', width: '250px',
                         color: 'var(--text-main)'
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
                          color: '#f87171', fontSize: '12px', whiteSpace: 'pre-wrap', 
                          maxHeight: '120px', overflowY: 'auto', width: '250px',
                          backgroundColor: 'rgba(239, 68, 68, 0.1)', padding: '8px', borderRadius: '6px',
                          border: '1px solid rgba(239, 68, 68, 0.2)'
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

// ==========================================
// NEW: FLOATING AI CHATBOT COMPONENT
// ==========================================
function AIChatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'ai', text: 'Hello! Ask me about employee work progress.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: userMessage.text,
          history: messages.map(m => ({ role: m.role, text: m.text }))
        })
      });
      
      const data = await res.json();
      setMessages((prev) => [...prev, { role: 'ai', text: data.response }]);
    } catch (error) {
      setMessages((prev) => [
        ...prev, 
        { role: 'ai', text: 'Error connecting to the AI backend. Is it running?' }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {/* Chatbot Toggle Button */}
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="chatbot-toggle-btn"
        style={{
          position: 'fixed', bottom: '30px', right: '30px',
          backgroundColor: '#2563eb', color: 'white', border: 'none',
          borderRadius: '50%', width: '60px', height: '60px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)', cursor: 'pointer',
          fontSize: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center',
          zIndex: 1000
        }}
        title="Chat with AI"
      >
        {isOpen ? '✕' : '💬'}
      </button>

      {/* Chatbot Window */}
      {isOpen && (
        <div className="chat-window-container" style={{
          position: 'fixed', bottom: '100px', right: '30px',
          width: '500px', height: '600px',
          borderRadius: '16px', display: 'flex', flexDirection: 'column', zIndex: 1000,
          overflow: 'hidden'
        }}>
          {/* Header */}
          <div className="chat-header" style={{
            padding: '18px', fontWeight: 'bold', display: 'flex', justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1.2rem' }}>✨</span> 
              <span style={{ background: 'linear-gradient(135deg, #60a5fa, #a78bfa)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', fontSize: '1.1rem' }}>AI Progress Assistant</span>
            </div>
            <button onClick={() => setIsOpen(false)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.2rem' }}>✕</button>
          </div>

          {/* Messages Area */}
          <div className="chat-messages-area custom-scroll" style={{
            flex: 1, padding: '20px', overflowY: 'auto',
            display: 'flex', flexDirection: 'column', gap: '15px'
          }}>
            {messages.map((msg, index) => (
              <div key={index} style={{
                display: 'flex', width: '100%',
                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'
              }}>
                <div className={`chatbot-message ${msg.role === 'user' ? 'chat-user-msg' : 'chat-ai-msg'}`} style={{
                  maxWidth: '85%', padding: '12px 16px', borderRadius: '16px',
                  borderBottomRightRadius: msg.role === 'user' ? '4px' : '16px',
                  borderBottomLeftRadius: msg.role === 'ai' ? '4px' : '16px',
                  whiteSpace: msg.role === 'user' ? 'pre-wrap' : 'normal',
                  overflowX: 'auto',
                  boxShadow: msg.role === 'user' ? '0 4px 15px rgba(59, 130, 246, 0.2)' : '0 4px 15px rgba(0,0,0,0.1)'
                }}>
                  {msg.role === 'user' ? (
                    msg.text
                  ) : (
                    <div dangerouslySetInnerHTML={{ __html: msg.text }} />
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div className="chat-ai-msg typing-dots" style={{
                  padding: '12px 20px', borderRadius: '16px', fontSize: '14px',
                  borderBottomLeftRadius: '4px', fontStyle: 'italic', letterSpacing: '2px'
                }}>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input Area */}
          <div className="chat-input-area" style={{
            padding: '18px', display: 'flex', gap: '12px'
          }}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask AI anything..."
              className="file-input"
              style={{ flex: 1, borderRadius: '12px' }}
            />
            <button 
              onClick={handleSend} disabled={isLoading}
              className="btn btn-primary"
              style={{
                padding: '0 20px', borderRadius: '12px',
                opacity: isLoading ? 0.7 : 1
              }}
            >
              Send
            </button>
          </div>
        </div>
      )}
    </>
  );
}

// ==========================================
// MANUAL TASK ALLOCATION FORM
// ==========================================
function ManualAllocationForm({ onAllocated }) {
  const [formData, setFormData] = useState({
    empid: '',
    task: '',
    description: '',
    priority: 'Normal',
    category: 'General',
    due_date: ''
  });
  const [employees, setEmployees] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`${API_BASE_URL}/emp`)
      .then(res => res.json())
      .then(data => setEmployees(data))
      .catch(err => console.error("Failed to load employees"));
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      const res = await fetch(`${API_BASE_URL}/tasks/allocate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Allocation failed');
      }
      
      setFormData({
        empid: '', task: '', description: '', priority: 'Normal', category: 'General', due_date: ''
      });
      onAllocated();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px', maxWidth: '500px' }}>
      <select name="empid" value={formData.empid} onChange={handleChange} className="file-input" required>
        <option value="">Select Employee</option>
        {employees.map(emp => (
          <option key={emp.employee_id} value={emp.employee_id}>
            {emp.name} ({emp.employee_id} - {emp.primary_category})
          </option>
        ))}
      </select>
      
      <input type="text" name="task" value={formData.task} onChange={handleChange} placeholder="Task Title" className="file-input" required />
      
      <textarea name="description" value={formData.description} onChange={handleChange} placeholder="Detailed Description (Optional)" className="file-input" style={{ minHeight: '80px', resize: 'vertical' }} />
      
      <div style={{ display: 'flex', gap: '10px' }}>
        <select name="priority" value={formData.priority} onChange={handleChange} className="file-input" style={{ flex: 1 }}>
          <option value="Low">Low Priority</option>
          <option value="Normal">Normal Priority</option>
          <option value="High">High Priority</option>
          <option value="Urgent">Urgent Priority</option>
        </select>
        
        <input type="date" name="due_date" value={formData.due_date} onChange={handleChange} className="file-input" style={{ flex: 1 }} />
      </div>
      
      <input type="text" name="category" value={formData.category} onChange={handleChange} placeholder="Category (e.g., AI/ML, Backend)" className="file-input" />
      
      {error && <p style={{ color: 'red', margin: 0, fontSize: '14px' }}>{error}</p>}
      
      <button type="submit" className="btn btn-primary" disabled={isLoading} style={{ marginTop: '10px' }}>
        {isLoading ? 'Allocating...' : 'Allocate Task'}
      </button>
    </form>
  );
}