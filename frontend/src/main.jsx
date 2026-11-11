import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Sparkles, LayoutDashboard, FileText, Clock3, Settings, LogOut, UploadCloud, WandSparkles, Copy, Download, Presentation, FileCheck2, MessageSquareText, Newspaper, Instagram, Menu, X, ArrowUpRight, CheckCircle2, AlertCircle, LoaderCircle, ShieldCheck } from "lucide-react";
import "./styles.css";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";
const formats = [
  {name:"Blog",desc:"Long-form articles",icon:Newspaper},
  {name:"Report",desc:"Structured reports",icon:FileCheck2},
  {name:"PPT",desc:"Slide-by-slide decks",icon:Presentation},
  {name:"FAQ",desc:"Questions and answers",icon:MessageSquareText},
  {name:"Summary",desc:"Executive overviews",icon:FileText},
  {name:"Social Media",desc:"Platform-ready posts",icon:Instagram}
];

function App(){
  const [token,setToken]=useState(localStorage.getItem("forma_token")||"");
  const [user,setUser]=useState(JSON.parse(localStorage.getItem("forma_user")||"null"));
  const [authMode,setAuthMode]=useState("login");
  const [auth,setAuth]=useState({name:"",email:"",password:""});
  const [page,setPage]=useState("studio");
  const [mobile,setMobile]=useState(false);
  const [source,setSource]=useState("");
  const [file,setFile]=useState(null);
  const [format,setFormat]=useState("Blog");
  const [audience,setAudience]=useState("General audience");
  const [tone,setTone]=useState("Professional");
  const [detail,setDetail]=useState("Medium");
  const [output,setOutput]=useState("");
  const [outputTitle,setOutputTitle]=useState("Generated content");
  const [busy,setBusy]=useState(false);
  const [notice,setNotice]=useState(null);
  const [history,setHistory]=useState([]);
  const [selected,setSelected]=useState(null);
  const [health,setHealth]=useState({mongodb:false,ai_configured:false});

  const headers=useMemo(()=>({Authorization:`Bearer ${token}`}),[token]);
  const notify=(kind,text)=>{setNotice({kind,text});window.clearTimeout(window.__noticeTimer);window.__noticeTimer=window.setTimeout(()=>setNotice(null),5000)};
  async function api(path,options={}){
    const response=await fetch(API+path,{...options,headers:{...(options.body instanceof FormData?{}:{"Content-Type":"application/json"}),...(options.headers||{}),...(token?headers:{})}});
    const data=await response.json().catch(()=>({}));
    if(!response.ok) throw new Error(data.error||`Request failed (${response.status})`);
    return data;
  }
  async function checkHealth(){try{const h=await api("/api/health");setHealth(h)}catch{}}
  async function loadHistory(){try{const d=await api("/api/history");setHistory(d.items||[])}catch(e){notify("error",e.message)}}
  useEffect(()=>{checkHealth();},[]);
  useEffect(()=>{if(token){loadHistory();}},[token]);
  function logout(){localStorage.removeItem("forma_token");localStorage.removeItem("forma_user");setToken("");setUser(null);setOutput("");setHistory([])}
  async function submitAuth(e){
    e.preventDefault();
    try{
      const d=await api(`/api/auth/${authMode}`,{method:"POST",body:JSON.stringify(auth)});
      setToken(d.token);setUser(d.user);localStorage.setItem("forma_token",d.token);localStorage.setItem("forma_user",JSON.stringify(d.user));notify("success",`Welcome ${d.user.name}`);
    }catch(e){notify("error",e.message)}
  }
  async function generate(e){
    e.preventDefault();if(!source.trim()&&!file){notify("error","Add source text or choose a document.");return}
    setBusy(true);setOutput("");
    const body=new FormData();body.append("source",source);body.append("format",format);body.append("audience",audience);body.append("tone",tone);body.append("detail",detail);if(file)body.append("file",file);
    try{const d=await api("/api/generate",{method:"POST",body});setOutput(d.output);setOutputTitle(`${format} · ${new Date().toLocaleDateString()}`);notify("success","Your content has been generated and saved.");loadHistory()}
    catch(e){notify("error",e.message)}finally{setBusy(false)}
  }
  async function exportFile(type){
    try{
      const response=await fetch(API+"/api/export",{method:"POST",headers:{"Content-Type":"application/json",...headers},body:JSON.stringify({content:output,type,title:outputTitle})});
      if(!response.ok){const d=await response.json();throw new Error(d.error||"Export failed")}
      const blob=await response.blob();const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download=type==="pptx"?"generated_presentation.pptx":`generated_content.${type}`;a.click();URL.revokeObjectURL(url);
    }catch(e){notify("error",e.message)}
  }
  async function openHistory(id){try{const d=await api(`/api/history/${id}`);setSelected(d.item);setOutput(d.item.output);setOutputTitle(`${d.item.format} · Saved output`);setPage("studio")}catch(e){notify("error",e.message)}}
  async function copyOutput(){try{await navigator.clipboard.writeText(output);notify("success","Copied to clipboard.")}catch{notify("error","Clipboard access was blocked by the browser.")}}

  if(!token)return <div className="auth-shell"><div className="auth-art"><div className="orb orb-a"/><div className="orb orb-b"/><div className="art-content"><div className="brand brand-light"><span className="brand-mark"><Sparkles size={19}/></span> forma<span className="brand-ai">AI</span></div><div className="art-copy"><span className="eyebrow">YOUR INTELLIGENT CONTENT STUDIO</span><h1>One source.<br/><em>Every format.</em></h1><p>Turn ideas, documents and research into polished content assets with one intelligent workflow.</p><div className="art-pills"><span>✦ Blogs</span><span>▤ Reports</span><span>▣ Presentations</span><span>↗ Social</span></div></div><div className="art-foot">GENERATIVE WORKFLOW PLATFORM <span>•</span> 2026</div></div></div><div className="auth-panel"><div className="auth-card"><div className="mobile-brand brand"><span className="brand-mark"><Sparkles size={18}/></span> forma<span className="brand-ai">AI</span></div><span className="eyebrow">WELCOME TO FORMA AI</span><h2>{authMode==="login"?"Sign in to your workspace":"Create your workspace"}</h2><p className="muted">{authMode==="login"?"Continue creating content that moves work forward.":"Start transforming your content with AI."}</p><form onSubmit={submitAuth} className="stack-form">{authMode==="register"&&<label>Full name<input required value={auth.name} onChange={e=>setAuth({...auth,name:e.target.value})} placeholder="Your name"/></label>}<label>Email address<input type="email" required value={auth.email} onChange={e=>setAuth({...auth,email:e.target.value})} placeholder="you@example.com"/></label><label>Password<input type="password" minLength="8" required value={auth.password} onChange={e=>setAuth({...auth,password:e.target.value})} placeholder="At least 8 characters"/></label><button className="primary full">{authMode==="login"?"Sign in":"Create account"} <ArrowUpRight size={17}/></button></form><p className="switch-auth">{authMode==="login"?"New to Forma AI?":"Already have an account?"} <button onClick={()=>setAuthMode(authMode==="login"?"register":"login")}>{authMode==="login"?"Create account":"Sign in"}</button></p><div className="secure-note"><ShieldCheck size={14}/> Protected workspace · JWT authentication</div></div></div>{notice&&<Toast notice={notice}/>}</div>;

  return <div className="app-shell">
    <aside className={`sidebar ${mobile?"show":""}`}><div className="brand"><span className="brand-mark"><Sparkles size={18}/></span> forma<span className="brand-ai">AI</span></div><div className="workspace-label">WORKSPACE</div><nav><button className={page==="studio"?"active":""} onClick={()=>{setPage("studio");setMobile(false)}}><LayoutDashboard size={17}/> Content studio</button><button className={page==="history"?"active":""} onClick={()=>{setPage("history");setMobile(false);loadHistory()}}><Clock3 size={17}/> History <span className="nav-count">{history.length||""}</span></button></nav><div className="sidebar-bottom"><div className="health-card"><div className="health-title"><span className="live-dot"/> SYSTEM STATUS</div><div className="health-row"><span>AI provider</span><b className={health.ai_configured?"ok":"warn"}>{health.ai_configured?"Configured":"API key needed"}</b></div><div className="health-row"><span>Database</span><b className={health.mongodb?"ok":"warn"}>{health.mongodb?"Connected":"Offline"}</b></div><button className="refresh-health" onClick={checkHealth}>Refresh status</button></div><div className="profile"><div className="avatar">{(user?.name||"U").slice(0,1).toUpperCase()}</div><div className="profile-info"><b>{user?.name||"User"}</b><small>{user?.email}</small></div><button className="icon-btn" title="Sign out" onClick={logout}><LogOut size={17}/></button></div></div></aside>
    <main className="main-area"><header className="topbar"><button className="mobile-menu icon-btn" onClick={()=>setMobile(!mobile)}>{mobile?<X/>:<Menu/>}</button><div className="breadcrumb">Workspace <span>/</span> <b>{page==="studio"?"Content studio":"Transformation history"}</b></div><div className="topbar-right"><span className="top-status"><span className="live-dot"/> AI WORKSPACE</span><div className="avatar small-avatar">{(user?.name||"U").slice(0,1).toUpperCase()}</div></div></header>
    <div className="page-content">
      {page==="studio"?<><section className="page-heading"><div><span className="eyebrow">GENERATIVE CONTENT WORKFLOW</span><h1>Content studio<span className="heading-period">.</span></h1><p>Transform your source material into clear, compelling content for every channel.</p></div><div className="heading-chip"><Sparkles size={15}/> POWERED BY GPT + LANGCHAIN</div></section>
      <div className="studio-grid"><section className="card input-card"><div className="card-heading"><div><span className="step-label">01 / SOURCE</span><h2>Start with your content</h2><p>Paste text or upload a source document.</p></div><div className="card-icon"><FileText size={19}/></div></div><textarea className="source-area" value={source} onChange={e=>setSource(e.target.value)} placeholder="Paste an article, report, announcement, research notes or any source content here..."/><label className="upload-zone"><input type="file" accept=".txt,.pdf,.docx" onChange={e=>setFile(e.target.files?.[0]||null)}/><span className="upload-icon"><UploadCloud size={20}/></span><span><b>{file?file.name:"Upload a document"}</b><small>{file?`${(file.size/1024).toFixed(0)} KB · Click to replace`:"PDF, DOCX or TXT · Up to 12 MB"}</small></span><span className="browse-link">Browse files</span></label><div className="input-foot"><span>{source.length.toLocaleString()} characters</span><button className="text-button" onClick={()=>{setSource("");setFile(null)}}>Clear input</button></div></section>
      <section className="card config-card"><div className="card-heading"><div><span className="step-label">02 / CONFIGURE</span><h2>Shape the output</h2><p>Choose a format and tailor the result.</p></div><div className="card-icon"><Settings size={19}/></div></div><label className="field-label">OUTPUT FORMAT</label><div className="format-grid">{formats.map(f=>{const Icon=f.icon;return <button key={f.name} className={`format-option ${format===f.name?"selected":""}`} onClick={()=>setFormat(f.name)}><Icon size={17}/><span><b>{f.name}</b><small>{f.desc}</small></span>{format===f.name&&<CheckCircle2 size={15} className="selected-check"/>}</button>})}</div><div className="config-fields"><label>Target audience<select value={audience} onChange={e=>setAudience(e.target.value)}><option>General audience</option><option>Students</option><option>Business professionals</option><option>Technical audience</option><option>Government officials</option><option>Marketing teams</option></select></label><label>Tone<select value={tone} onChange={e=>setTone(e.target.value)}><option>Professional</option><option>Formal</option><option>Friendly</option><option>Persuasive</option><option>Simple</option><option>Academic</option></select></label><label className="detail-field">Level of detail<select value={detail} onChange={e=>setDetail(e.target.value)}><option>Concise</option><option>Medium</option><option>Detailed</option></select></label></div><button className="primary generate-btn" onClick={generate} disabled={busy}>{busy?<><LoaderCircle className="spin" size={17}/> Generating...</>:<><WandSparkles size={17}/> Generate content <ArrowUpRight size={17}/></>}</button><p className="micro-note"><ShieldCheck size={13}/> Your generated output is saved to your private history.</p></section></div>
      <section className="card output-card"><div className="output-top"><div><span className="step-label">03 / RESULT</span><h2>Your generated content</h2><p>Review, copy and export your AI-generated deliverable.</p></div>{output&&<div className="export-actions"><button className="secondary-btn" onClick={copyOutput}><Copy size={15}/> Copy</button><button className="secondary-btn" onClick={()=>exportFile("txt")}><Download size={15}/> TXT</button><button className="secondary-btn" onClick={()=>exportFile("pdf")}><Download size={15}/> PDF</button>{format==="PPT"&&<button className="secondary-btn accent-btn" onClick={()=>exportFile("pptx")}><Presentation size={15}/> PPTX</button>}</div>}</div>{output?<div className="generated-output"><div className="output-meta"><span className="output-pill"><Sparkles size={12}/> {format}</span><span>Generated just now</span></div><pre>{output}</pre></div>:<div className="empty-output"><div className="empty-illustration"><div className="empty-icon"><WandSparkles size={25}/></div><span className="spark s1">✦</span><span className="spark s2">✧</span></div><b>Your next great deliverable starts here</b><p>Add your source, select a format and generate to see the result.</p></div>}</section></>:<><section className="page-heading"><div><span className="eyebrow">YOUR WORKSPACE</span><h1>Transformation history<span className="heading-period">.</span></h1><p>Revisit the content you've created in your workspace.</p></div><button className="secondary-btn" onClick={loadHistory}>↻ Refresh</button></section><section className="card history-card">{history.length?history.map(item=><button className="history-row" key={item.id} onClick={()=>openHistory(item.id)}><div className="history-format-icon"><FileText size={18}/></div><div className="history-main"><b>{item.format}</b><small>{item.audience} · {item.tone} · {item.detail}</small></div><time>{new Date(item.created_at).toLocaleString()}</time><ArrowUpRight size={17}/></button>):<div className="empty-output"><Clock3 size={30}/><b>No transformations yet</b><p>Your generated content will appear here.</p><button className="primary" onClick={()=>setPage("studio")}>Go to content studio</button></div>}</section></>}
      <footer className="footer"><span>FORMA AI <i>•</i> CONTENT TRANSFORMATION PLATFORM</span><span>Built with React · Flask · LangChain · OpenAI · MongoDB</span></footer>
    </div></main>{notice&&<Toast notice={notice}/>}</div>
}
function Toast({notice}){return <div className={`toast ${notice.kind}`}><span>{notice.kind==="error"?<AlertCircle size={17}/>:<CheckCircle2 size={17}/>}</span>{notice.text}</div>}
createRoot(document.getElementById("root")).render(<App/>);
