import os,sys
sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
import app as m
import pytest

@pytest.fixture
def client(monkeypatch):
 m.app.config['TESTING']=True;m.sessions.clear();monkeypatch.setattr(m,'generate',lambda text,mode:'Test response')
 with m.app.test_client() as c:yield c

def test_evaluation_and_free_question(client):
 h={'X-Session-ID':client.post('/api/session').json['session_id']}
 assert len(client.get('/api/questions').json)==5
 assert 'truth' not in client.get('/api/questions').json[0]
 i=client.post('/api/ask',headers=h,json={'question_id':1}).json['id']
 assert client.post('/api/judgment',headers=h,json={'id':i,'stage':'final','choice':'reject'}).status_code==400
 client.post('/api/judgment',headers=h,json={'id':i,'stage':'initial','choice':'trust'})
 r=client.post('/api/judgment',headers=h,json={'id':i,'stage':'final','choice':'reject'})
 assert r.json['evaluation']['truth'] is False
 j=client.post('/api/ask',headers=h,json={'question':'Why?'}).json['id']
 client.post('/api/judgment',headers=h,json={'id':j,'stage':'initial','choice':'unsure'})
 assert 'evaluation' not in client.post('/api/judgment',headers=h,json={'id':j,'stage':'final','choice':'trust'}).json

def test_search_states(client,monkeypatch):
 h={'X-Session-ID':client.post('/api/session').json['session_id']};i=client.post('/api/ask',headers=h,json={'question':'light'}).json['id']
 client.post('/api/judgment',headers=h,json={'id':i,'stage':'initial','choice':'unsure'})
 monkeypatch.setattr(m,'search_wiki',lambda q:[{'title':'Light','snippet':'Example','url':'https://en.wikipedia.org/?curid=1'}])
 assert client.post('/api/search',headers=h,json={'id':i,'query':'light'}).json['status']=='results'
 assert client.post('/api/view',headers=h,json={'id':i,'index':0}).status_code==200
 monkeypatch.setattr(m,'search_wiki',lambda q:[])
 assert client.post('/api/search',headers=h,json={'id':i,'query':'light'}).json['status']=='no_results'
 def bad(q):raise RuntimeError()
 monkeypatch.setattr(m,'search_wiki',bad)
 assert client.post('/api/search',headers=h,json={'id':i,'query':'light'}).json['status']=='failed'

def test_provider(monkeypatch):
 calls={}
 class Responses:
  def create(self,**kw):calls['request']=kw;return type('R',(),{'output_text':'ok'})()
 class Client:
  def __init__(self,**kw):calls['client']=kw;self.responses=Responses()
 monkeypatch.setattr(m,'OpenAI',Client);monkeypatch.setenv('AI_PROVIDER','deepseek');monkeypatch.setenv('DEEPSEEK_API_KEY','test');monkeypatch.delenv('DEEPSEEK_MODEL',raising=False)
 assert m.generate('hi','short')=='ok'
 assert calls['client']['base_url']=='https://api.deepseek.com'
 assert calls['request']['model']=='deepseek-flash'
 monkeypatch.setenv('AI_PROVIDER','openai');monkeypatch.setenv('OPENAI_API_KEY','test');m.generate('hi','short');assert 'base_url' not in calls['client']

def test_feedback_is_hidden_until_final_and_counts_unsure_separately(client):
 h={'X-Session-ID':client.post('/api/session').json['session_id']}
 i=client.post('/api/ask',headers=h,json={'question_id':0}).json['id']
 client.post('/api/judgment',headers=h,json={'id':i,'stage':'initial','choice':'reject'})
 before=client.get('/api/dashboard',headers=h).json['items'][0]
 assert 'initial_comparison' not in before
 r=client.post('/api/judgment',headers=h,json={'id':i,'stage':'final','choice':'unsure'})
 assert r.json['evaluation']['initial_comparison']=='does_not_match'
 assert r.json['evaluation']['final_comparison']=='unsure'
 after=client.get('/api/dashboard',headers=h).json['items'][0]
 assert after['final_comparison']=='unsure'
 assert m.compare('trust',True)=='matches'
 assert m.compare('reject',False)=='matches'
 assert m.compare('trust',False)=='does_not_match'
