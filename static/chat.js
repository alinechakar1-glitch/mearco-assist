(()=>{
const messages=document.getElementById('chat-messages'),choices=document.getElementById('chat-choices');
let state={},stage=0,submitting=false;
function bubble(text,kind='bot'){const el=document.createElement('div');el.className='chat-bubble '+kind;el.textContent=text;messages.appendChild(el);messages.scrollTop=messages.scrollHeight}
function options(opts){choices.replaceChildren();opts.forEach(([text,value])=>{const b=document.createElement('button');b.type='button';b.textContent=text;b.addEventListener('click',()=>choose(text,value));choices.appendChild(b)})}
function ask(){switch(stage){
case 0:bubble('Hello! Welcome to MEARCO Assist. This is a safe DEMO using fictional cases. How can we assist you?');options([['🚗 Request towing','Towing'],['🚨 Report motor accident','Motor accident'],['📋 Claim follow-up','Claim follow-up'],['💬 Complaint','Complaint']]);break;
case 1:bubble('First, are you and your passengers safe? If anyone is in immediate danger, call emergency services now.');options([['Yes, everyone is safe','Yes'],['No, someone may be in danger','No'],['Not sure','Unsure']]);break;
case 2:bubble('For this demonstration, choose a fictional area. Do not send your real location.');options([['Jbeil','Jbeil'],['Jounieh','Jounieh'],['Beirut','Beirut'],['Batroun','Batroun']]);break;
case 3:bubble('Choose a fictional situation for this test.');options([['Car breakdown','Breakdown'],['Flat tire','Flat tire'],['Collision','Collision'],['Other issue','Other']]);break;
case 4:bubble('Ready to create a DEMO case in MEARCO’s dashboard. No tow truck will be dispatched.');options([['Create demonstration case','send'],['Start again','restart']]);break;
}}
function choose(label,value){if(submitting)return;if(value==='restart'){start();return}bubble(label,'user');choices.replaceChildren();if(stage===0)state.case_type=value;else if(stage===1)state.safe=value;else if(stage===2)state.area=value;else if(stage===3)state.issue=value;else if(stage===4&&value==='send'){submit();return}stage++;if(state.safe==='No'||state.safe==='Unsure')bubble('If you may be in danger, do not wait for a chatbot. Contact emergency services immediately. This is only a simulation.');ask()}
async function submit(){submitting=true;bubble('Creating fictional test case…');try{const r=await fetch('/api/chat-demo/submit',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({...state,csrf_token:window.MEARCO_CSRF})});const d=await r.json();if(!r.ok)throw new Error(typeof d.detail==='string'?d.detail:'Could not register demo request');bubble('✅ DEMO case '+d.case_ref+' created. Sign in to the MEARCO staff dashboard to see it. No real assistance has been requested.');options([['Start another demo','restart']]);}catch(err){bubble('Could not create the demo case: '+err.message);options([['Try again','retry'],['Restart','restart']]);}finally{submitting=false}}
function start(){messages.replaceChildren();state={};stage=0;submitting=false;ask()}
const oldChoose=choose;
document.getElementById('restart').addEventListener('click',start);
// Retry option is handled by a dedicated click handler as no question is pending.
choices.addEventListener('click',event=>{if(event.target.textContent==='Try again'){event.stopImmediatePropagation();submit()}} ,true);
start();
})();