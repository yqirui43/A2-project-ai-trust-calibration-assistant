import os, uuid
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template
from openai import OpenAI

load_dotenv()
app=Flask(__name__)
app.config['MAX_CONTENT_LENGTH']=16384
sessions={}
SOURCE='https://www.nist.gov/pml/special-publication-330/sp-330-section-2'
questions=[
 ('The speed of light in vacuum is exactly 299,792,458 metres per second.',True,'Exactly 299,792,458 m/s.'),
 ('The speed of light in vacuum is exactly 300,000,000 metres per second.',False,'The exact value is 299,792,458 m/s; 300,000,000 is an approximation.'),
 ('The Planck constant is exactly 6.62607015 × 10⁻³⁴ joule seconds.',True,'The SI defining value is exactly 6.62607015 × 10⁻³⁴ J s.'),
 ('The elementary charge is exactly 1.602176634 × 10⁻¹⁹ coulombs.',True,'The SI defining value is exactly 1.602176634 × 10⁻¹⁹ C.'),
 ('The SI defines the speed of light in vacuum as exactly 299,792,458 kilometres per second.',False,'The exact value is 299,792,458 metres per second, not kilometres per second.')]
def compare(choice, truth):
 if choice == 'unsure': return 'unsure'
 return 'matches' if (choice == 'trust') == truth else 'does_not_match'

def fail(msg,code=400): return jsonify(error=msg),code
def current(): return sessions.get(request.headers.get('X-Session-ID'))
def item(data):
 s=current(); return s.get(data.get('id')) if s else None

def generate(text,mode):
 provider=os.getenv('AI_PROVIDER','deepseek').lower().strip()
 if provider not in ('deepseek','openai'): raise ValueError('Set AI_PROVIDER to deepseek or openai.')
 name='DEEPSEEK_API_KEY' if provider=='deepseek' else 'OPENAI_API_KEY'
 key=os.getenv(name,'').strip()
 if not key or key.startswith('replace_with_'): raise ValueError(name+' is missing from your environment or .env file.')
 args={'api_key':key,'timeout':40,'max_retries':0}
 if provider=='deepseek': args['base_url']='https://api.deepseek.com'
 model=os.getenv('DEEPSEEK_MODEL','deepseek-flash') if provider=='deepseek' else os.getenv('OPENAI_MODEL','gpt-4.1-mini')
 r=OpenAI(**args).responses.create(model=model,instructions='Answer in English. Answer the question or assess the claim. Give a '+('short' if mode=='short' else 'detailed')+' explanation. State important uncertainty in words. Use simple Markdown bold and standard LaTeX for mathematics. Do not invent sources or claim to have searched.',input=text,max_output_tokens=600 if mode=='short' else 1200)
 if not r.output_text: raise RuntimeError('Empty response')
 return r.output_text

def search_wiki(query):
 r=requests.get('https://en.wikipedia.org/w/api.php',params={'action':'query','list':'search','srsearch':query,'srlimit':5,'format':'json'},headers={'User-Agent':'TrustCalibrationAssistant/1.0 educational prototype'},timeout=10); r.raise_for_status()
 from html.parser import HTMLParser
 class Parser(HTMLParser):
  def __init__(self): super().__init__(); self.text=[]
  def handle_data(self,d): self.text.append(d)
 result=[]
 for x in r.json().get('query',{}).get('search',[]):
  p=Parser();p.feed(x.get('snippet',''))
  if isinstance(x.get('pageid'),int): result.append({'title':x.get('title','Untitled'),'snippet':''.join(p.text),'url':'https://en.wikipedia.org/?curid='+str(x['pageid'])})
 return result
@app.get('/')
def home(): return render_template('index.html')
@app.post('/api/session')
def session():
 sid=uuid.uuid4().hex;sessions[sid]={};return jsonify(session_id=sid)
@app.get('/api/questions')
def list_questions(): return jsonify([{'id':i,'claim':q[0]} for i,q in enumerate(questions)])
@app.post('/api/ask')
def ask():
 s=current()
 if s is None:return fail('Session expired. Start a new session.',401)
 d=request.get_json(silent=True) or {};qid=d.get('question_id');mode=d.get('mode','short')
 if qid is not None and (type(qid) is not int or qid<0 or qid>=len(questions)):return fail('Invalid evaluation question.')
 text=questions[qid][0] if qid is not None else d.get('question','')
 if not isinstance(text,str) or not text.strip() or len(text)>1000 or mode not in ('short','detailed'):return fail('Enter a question of 1–1000 characters.')
 try: answer=generate(text.strip(),mode)
 except ValueError as e:return fail(str(e),503)
 except Exception:return fail('AI service failed. Check your provider, key, balance, model access and network.',502)
 ident=uuid.uuid4().hex;s[ident]={'id':ident,'question':text,'question_id':qid,'answer':answer,'initial':None,'final':None,'status':'not_searched','sources':[],'viewed':[]}
 return jsonify(id=ident,answer=answer)
@app.post('/api/judgment')
def judgment():
 d=request.get_json(silent=True) or {};x=item(d)
 if not x:return fail('Item not found.',404)
 stage=d.get('stage');choice=d.get('choice')
 if stage not in ('initial','final') or choice not in ('trust','unsure','reject'):return fail('Invalid judgment.')
 if x['final'] or (stage=='initial' and x['initial']) or (stage=='final' and not x['initial']):return fail('Judgment cannot be changed at this stage.')
 x[stage]=choice;result={'ok':True}
 if stage=='final' and x['question_id'] is not None:
  q=questions[x['question_id']];result['evaluation']={'truth':q[1],'correction':q[2],'url':SOURCE,'note':'This reference assesses the fixed claim, not every sentence in the model response.','initial_comparison':compare(x['initial'],q[1]),'final_comparison':compare(x['final'],q[1])}
 return jsonify(result)
@app.post('/api/search')
def search():
 d=request.get_json(silent=True) or {};x=item(d)
 if not x:return fail('Item not found.',404)
 if not x['initial'] or x['final']:return fail('Search is available after the initial judgment and before the final judgment.')
 q=d.get('query','')
 if not isinstance(q,str) or not q.strip() or len(q)>300:return fail('Enter search terms of 1–300 characters.')
 try:
  x['sources']=search_wiki(q);x['status']='results' if x['sources'] else 'no_results'
 except Exception:x['sources']=[];x['status']='failed'
 x['viewed']=[];return jsonify(status=x['status'],sources=x['sources'])
@app.post('/api/view')
def view():
 d=request.get_json(silent=True) or {};x=item(d);n=d.get('index')
 if not x or x['final'] or type(n) is not int or n<0 or n>=len(x['sources']):return fail('Invalid source.')
 if n not in x['viewed']:x['viewed'].append(n)
 return jsonify(ok=True)
@app.get('/api/dashboard')
def dashboard():
 s=current()
 if s is None:return fail('Session expired.',401)
 items=[]
 for x in s.values():
  entry=dict(x)
  if x['final'] and x['question_id'] is not None:
   truth=questions[x['question_id']][1]
   entry['initial_comparison']=compare(x['initial'],truth)
   entry['final_comparison']=compare(x['final'],truth)
  items.append(entry)
 return jsonify(items=items)
if __name__=='__main__':app.run(host='127.0.0.1',port=int(os.getenv('PORT','5000')),debug=False)
