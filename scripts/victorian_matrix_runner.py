#!/usr/bin/env python3
"""Restartable Studio-only Vitorianas Macabras matrix runner."""
from __future__ import annotations
import csv, hashlib, json, os, re, signal, subprocess, threading, time, urllib.error, urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT=Path(os.environ['VICTORIAN_MATRIX_ROOT']); CLI=Path(os.environ['UNSLOTH_CLI']); PORT=18889
CELL_TIMEOUT_SECONDS=int(os.environ.get('VICTORIAN_CELL_TIMEOUT_SECONDS','1200'))
HANDOFF=ROOT/'handoff.md'; STATE=ROOT/'matrix-state.json'; LOG=ROOT/'logs'; RUNS=ROOT/'runs'
CELLS=[('Q35-9-OFF','Q35-9','off'),('Q35-9-LOW','Q35-9','low'),('Q38-UD-OFF','Q38-UD','off'),('Q38-UD-LOW','Q38-UD','low'),('Q38-Q6-OFF','Q38-Q6','off'),('Q38-Q6-LOW','Q38-Q6','low'),('GLM-OFF','GLM','off'),('GLM-ON','GLM','enabled'),('GEMMA-OFF','GEMMA','off'),('GEMMA-ON','GEMMA','enabled'),('Q38-UD-HIGH','Q38-UD','high'),('Q38-Q6-HIGH','Q38-Q6','high')]
def now(): return datetime.now(UTC).isoformat().replace('+00:00','Z')
def atomic(path,obj):
 t=path.with_suffix(path.suffix+'.tmp');t.write_text(json.dumps(obj,indent=2)+'\n');t.replace(path)
def load_state():
 return json.loads(STATE.read_text()) if STATE.exists() else {'started_at':now(),'cells':{}}
def prompt():
 s=HANDOFF.read_text(); m=re.search(r'```text\n(.*?)\n```\n\n(\| Autora.*?)(?=\n\n## Capture)',s,re.S)
 if not m: raise RuntimeError('exact prompt/table extraction failed')
 return m.group(1)+'\n\n'+m.group(2)
def request(path,body=None,key=None,timeout=CELL_TIMEOUT_SECONDS+5):
 h={'Content-Type':'application/json'}
 if key:h['Authorization']='Bearer '+key
 q=urllib.request.Request(f'http://127.0.0.1:{PORT}{path}',data=json.dumps(body).encode() if body else None,headers=h)
 try:
  with urllib.request.urlopen(q,timeout=timeout) as r:return json.loads(r.read())
 except urllib.error.HTTPError as e:
  raise RuntimeError(f'HTTP {e.code}: {e.read().decode("utf-8", "replace")}') from e
def health():
 try:return request('/api/health',timeout=8)
 except Exception:return None
def terminal(out):
 if not ((out/'terminal.json').exists() and (out/'request.json').exists()): return False
 record=json.loads((out/'terminal.json').read_text())
 return record.get('status') in {'completed','timed_out','behavioral_failure','search_budget_violation','failed'}
def api_key(log_path):
 key_file=ROOT/'api-key'
 if key_file.exists(): return key_file.read_text().strip()
 for _ in range(30):
  match=re.search(r'API Key:\s+(sk-unsloth-[A-Za-z0-9-]+)',log_path.read_text(errors='replace'))
  if match: return match.group(1)
  time.sleep(1)
 raise RuntimeError('Studio started without an API key')
def run_cell(cell,mid,reason,models,state):
 out=RUNS/cell;out.mkdir(parents=True,exist_ok=True)
 if terminal(out): return json.loads((out/'terminal.json').read_text())
 model=models[mid]
 if mid=='GLM': sampling={'temperature':0.7,'top_p':1.0,'min_p':0.01,'repetition_penalty':1.0}
 elif mid=='GEMMA': sampling={'studio_model_detected_defaults':True}
 else: sampling={'temperature':0.7 if reason=='off' else 0.6,'top_p':0.8 if reason=='off' else 0.95,'top_k':20,'min_p':0,'repetition_penalty':1.0}
 record={'id':cell,'model_id':mid,'reasoning':reason,'started_at':now(),'status':'running','model':model,'sampling':sampling,'tool_ceiling':20,'cell_timeout_seconds':CELL_TIMEOUT_SECONDS}
 atomic(out/'request.json',{'prompt':prompt(),'record':record})
 state['cells'][cell]=record;atomic(STATE,state)
 def checkpoint(phase='cell'):
  atomic(ROOT/'status.json',{'updated_at':now(),'phase':phase,'current_cell':cell,'elapsed_seconds':round(time.monotonic()-cell_started,1),'completed':[k for k,v in state['cells'].items() if v.get('status') in {'completed','timed_out','behavioral_failure','search_budget_violation'}]})
 cell_started=time.monotonic(); checkpoint()
 # The runner itself owns the persistent tmux session; never kill that session
 # during per-cell cleanup. The previous cell's Studio subprocess is terminated
 # in this function's finally block.
 env={**os.environ,'HF_HOME':str(ROOT/'huggingface'),'UNSLOTH_STUDIO_SANDBOX_HOME':str(ROOT/'sandbox')}
 slog=(LOG/f'{cell}-studio.log').open('w')
 cli_args=[str(CLI),'run','--model',model['local_path'],'--max-seq-length','65536','--gpu-memory-mode','manual','--host','127.0.0.1','--port',str(PORT),'--api-only','--parallel','1','--enable-tools','--no-cloudflare','--verbose']
 for flag,key in (('--temperature','temperature'),('--top-p','top_p'),('--top-k','top_k'),('--min-p','min_p'),('--repetition-penalty','repetition_penalty')):
  if key in sampling: cli_args += [flag,str(sampling[key])]
 p=subprocess.Popen(cli_args,cwd=ROOT,env=env,stdout=slog,stderr=subprocess.STDOUT)
 try:
  for _ in range(300):
   if health():break
   if p.poll() is not None:raise RuntimeError('Studio died before /api/health')
   time.sleep(2)
  else:raise TimeoutError('Studio health timeout')
  key=api_key(LOG/f'{cell}-studio.log'); (out/'models.json').write_text(json.dumps(request('/v1/models',key=key),indent=2))
  body={'model':'local','messages':[{'role':'user','content':prompt()}],'max_tokens':16384,'stream':False,'enable_tools':True,'enabled_tools':['web_search','web_fetch'],'max_tool_calls_per_message':20,'tool_call_timeout':300,'reasoning_effort':'none' if reason=='off' else reason,'enable_thinking':reason!='off',**{k:v for k,v in sampling.items() if k != 'studio_model_detected_defaults'}}
  stop_checkpoint=threading.Event()
  def checkpoint_loop():
   while not stop_checkpoint.wait(300): checkpoint('cell_running')
  checkpoint_thread=threading.Thread(target=checkpoint_loop,daemon=True); checkpoint_thread.start()
  started=time.monotonic()
  try:
   answer=request('/v1/chat/completions',body,key,timeout=CELL_TIMEOUT_SECONDS+5)
  finally:
   stop_checkpoint.set(); checkpoint_thread.join(timeout=2)
  record.update(status='completed',elapsed_seconds=round(time.monotonic()-started,3)); (out/'response.json').write_text(json.dumps(answer,indent=2)); (out/'final.md').write_text(answer['choices'][0]['message'].get('content',''))
 except Exception as e:
  elapsed=round(time.monotonic()-cell_started,3)
  status='timed_out' if elapsed >= CELL_TIMEOUT_SECONDS else 'failed'
  record.update(status=status,elapsed_seconds=elapsed,failure=f'{type(e).__name__}: {e}');(out/'failure.txt').write_text(record['failure']+'\n')
 finally:
  search_calls=len(re.findall(r'execute_tool: name=web_search', (LOG/f'{cell}-studio.log').read_text(errors='replace')))
  record['executed_web_searches']=search_calls
  if record['status']=='completed' and search_calls>20: record['status']='search_budget_violation'
  record['ended_at']=now(); atomic(out/'terminal.json',record); state['cells'][cell]=record;atomic(STATE,state); p.send_signal(signal.SIGTERM)
  try:p.wait(30)
  except subprocess.TimeoutExpired:p.kill()
  slog.close()
 return record
def main():
 LOG.mkdir(parents=True,exist_ok=True);RUNS.mkdir(parents=True,exist_ok=True); state=load_state(); models={m['id']:m for m in json.loads((ROOT/'download-manifest.json').read_text())}
 rows=[]
 for c,m,r in CELLS: rows.append(run_cell(c,m,r,models,state))
 with (ROOT/'matrix-results.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['id','model_id','reasoning','status','started_at','ended_at','elapsed_seconds','executed_web_searches','failure']);w.writeheader();w.writerows([{k:x.get(k,'') for k in w.fieldnames} for x in rows])
 report=['# Vitorianas Macabras search matrix','',f'Cell timeout: {CELL_TIMEOUT_SECONDS} seconds. Search-budget excesses are recorded as model behavior, not prevented.','', '| Cell | Status | Elapsed s | Executed web searches |','|---|---|---:|---:|']
 report += [f"| {x['id']} | {x.get('status','')} | {x.get('elapsed_seconds','')} | {x.get('executed_web_searches','')} |" for x in rows]
 report += ['', 'Per-cell raw requests, responses, terminal records, and Studio logs are retained under `runs/` and `logs/`.']
 (ROOT/'matrix-report.md').write_text('\n'.join(report)+'\n')
 (ROOT/'matrix-complete').touch();atomic(ROOT/'status.json',{'updated_at':now(),'phase':'matrix_complete','current_cell':None,'completed':[x['id'] for x in rows]})
if __name__=='__main__':main()
