"use client";
import {FormEvent,useEffect,useRef,useState} from "react";
import {askBrain,BrainMessage} from "../lib/brain";
type Recognition={lang:string;continuous:boolean;interimResults:boolean;start():void;stop():void;onresult:((e:any)=>void)|null;onend:(()=>void)|null;onerror:((e:any)=>void)|null};
export default function Home(){
 const [messages,setMessages]=useState<BrainMessage[]>([]);
 const [speaking,setSpeaking]=useState(false);
 const [voiceError,setVoiceError]=useState("");
 const [input,setInput]=useState(""),[chatOpen,setChatOpen]=useState(true),[calling,setCalling]=useState(false),[muted,setMuted]=useState(false),[cameraOn,setCameraOn]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(""),[interim,setInterim]=useState("");
 const audio=useRef<MediaStream|null>(null),video=useRef<MediaStream|null>(null),preview=useRef<HTMLVideoElement|null>(null),rec=useRef<Recognition|null>(null),running=useRef(false),mutedRef=useRef(false),messagesRef=useRef<BrainMessage[]>([]),sending=useRef(false),speechId=useRef(0),playback=useRef<HTMLAudioElement|null>(null),speechAbort=useRef<AbortController|null>(null),speechUrl=useRef<string|null>(null),lastRecognized=useRef<{text:string;at:number}>({text:"",at:0});
 useEffect(()=>{messagesRef.current=messages},[messages]);
 useEffect(()=>()=>{running.current=false;rec.current?.stop();audio.current?.getTracks().forEach(t=>t.stop());video.current?.getTracks().forEach(t=>t.stop());window.speechSynthesis?.cancel();speechAbort.current?.abort();playback.current?.pause();if(speechUrl.current)URL.revokeObjectURL(speechUrl.current)},[]);
 const speakingRef=useRef(false),recognitionPaused=useRef(false);
 function pauseRecognition(){recognitionPaused.current=true;try{rec.current?.stop()}catch{}setInterim("")}
 function resumeRecognition(){recognitionPaused.current=false;if(running.current&&!mutedRef.current&&!sending.current){try{rec.current?.start()}catch{}}}
 function stopSpeech(){speechId.current++;window.speechSynthesis?.cancel();speechAbort.current?.abort();speechAbort.current=null;playback.current?.pause();playback.current?.dispatchEvent(new Event("noa-stop"));playback.current=null;if(speechUrl.current){URL.revokeObjectURL(speechUrl.current);speechUrl.current=null}speakingRef.current=false;setSpeaking(false);resumeRecognition()}
 function splitSpeech(text:string):string[]{
  const sentences=text.split(/(?<=[.!?。！？])\s+|\n+/).filter(Boolean);
  const chunks:string[]=[];let current="";
  for(const sentence of sentences){const piece=sentence.trim();if(!piece)continue;
   if((current+" "+piece).length>450&&current){chunks.push(current);current=""}
   if(piece.length>450){for(let i=0;i<piece.length;i+=450)chunks.push(piece.slice(i,i+450))}
   else current=current?current+" "+piece:piece;
  }
  if(current)chunks.push(current);
  return chunks.slice(0,20);
 }
 async function speak(text:string){
  stopSpeech();setVoiceError("");pauseRecognition();
  const id=speechId.current;
  const controller=new AbortController();speechAbort.current=controller;
  const chunks=splitSpeech(text);
  let completed=0;
  try{
   for(const chunk of chunks){
    if(id!==speechId.current||controller.signal.aborted)return;
    const res=await fetch("/api/tts",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:chunk}),signal:controller.signal});
    if(!res.ok){const e=await res.json().catch(()=>({}));throw new Error([e.error,e.detail].filter(Boolean).join(" — ")||"TTS không khả dụng")}
    const blob=await res.blob();if(id!==speechId.current)return;
    const url=URL.createObjectURL(blob);speechUrl.current=url;
    try{
     await new Promise<void>((resolve,reject)=>{
      const player=new Audio(url);playback.current=player;
      player.onended=()=>resolve();player.addEventListener("noa-stop",()=>resolve(),{once:true});
      player.onerror=()=>reject(new Error("Không phát được âm thanh tiếng Việt."));
      player.play().then(()=>{if(id===speechId.current){speakingRef.current=true;setSpeaking(true)}}).catch(reject);
     });
    }finally{playback.current=null;URL.revokeObjectURL(url);if(speechUrl.current===url)speechUrl.current=null}
    completed++;
   }
  }catch(e){
   if(id!==speechId.current||controller.signal.aborted)return;
   const reason=e instanceof Error?e.message:"Không thể phát giọng NOA";
   setVoiceError(reason+" — đang sử dụng giọng dự phòng của trình duyệt.");
   if("speechSynthesis" in window){
    await new Promise<void>(resolve=>{
     const remaining=chunks.slice(completed).join(" ");
     if(!remaining){resolve();return}
     const utterance=new SpeechSynthesisUtterance(remaining.slice(0,3000));
     utterance.lang="vi-VN";utterance.rate=1;
     const vi=window.speechSynthesis.getVoices().find(v=>v.lang.toLowerCase().startsWith("vi"));
     if(vi)utterance.voice=vi;
     utterance.onstart=()=>{if(id===speechId.current){speakingRef.current=true;setSpeaking(true)}};
     utterance.onend=()=>resolve();utterance.onerror=()=>resolve();
     window.speechSynthesis.cancel();window.speechSynthesis.speak(utterance);
    });
   }
  }finally{if(id===speechId.current){speakingRef.current=false;setSpeaking(false);resumeRecognition()}}
 }
 async function send(text:string){const message=text.trim();if(!message||sending.current)return;sending.current=true;setBusy(true);setError("");setInterim("");const previous=messagesRef.current;const history=[...previous,{role:"user" as const,content:message}];messagesRef.current=history;setMessages(history);try{const answer=await askBrain(message,previous);const next=[...history,{role:"assistant" as const,content:answer.text}];messagesRef.current=next;setMessages(next);void speak(answer.text)}catch(e){setError(e instanceof Error?e.message:"Không thể kết nối NOA")}finally{sending.current=false;setBusy(false);if(!speakingRef.current&&!recognitionPaused.current)resumeRecognition()}}
 function beginRecognition(){const w=window as any;const Constructor=w.SpeechRecognition||w.webkitSpeechRecognition;if(!Constructor){setError("Trình duyệt chưa hỗ trợ nhận diện giọng nói. Bạn vẫn có thể nhập chữ.");return}const r:Recognition=new Constructor();r.lang="vi-VN";r.continuous=true;r.interimResults=true;r.onresult=e=>{let live="";for(let i=e.resultIndex;i<e.results.length;i++){const t=e.results[i][0].transcript;if(e.results[i].isFinal){const clean=t.trim();const now=Date.now();if(!recognitionPaused.current&&!speakingRef.current&&!sending.current&&clean&&(clean!==lastRecognized.current.text||now-lastRecognized.current.at>4000)){lastRecognized.current={text:clean,at:now};void send(clean)}}else live+=t}setInterim(live)};r.onerror=e=>{if(e.error!=="no-speech"&&e.error!=="aborted")setError("Micro: "+e.error)};r.onend=()=>{if(running.current&&!mutedRef.current&&!recognitionPaused.current&&!speakingRef.current&&!sending.current){try{r.start()}catch{}}};rec.current=r;try{r.start()}catch{}}
 async function startCall(){stopSpeech();setError("");try{const s=await navigator.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true}});audio.current=s;running.current=true;mutedRef.current=false;setMuted(false);setCalling(true);beginRecognition()}catch(e){setError(e instanceof Error?"Không thể mở micro: "+e.message:"Không thể mở micro. Bạn vẫn có thể chat bằng chữ.")}}
 function endCall(){running.current=false;stopSpeech();rec.current?.stop();rec.current=null;audio.current?.getTracks().forEach(t=>t.stop());audio.current=null;stopCamera();setCalling(false);setInterim("")}
 function toggleMute(){const next=!muted;setMuted(next);mutedRef.current=next;audio.current?.getAudioTracks().forEach(t=>t.enabled=!next);if(next){rec.current?.stop();setInterim("")}else if(calling&&!recognitionPaused.current){beginRecognition()}}
 function stopCamera(){video.current?.getTracks().forEach(t=>t.stop());video.current=null;if(preview.current)preview.current.srcObject=null;setCameraOn(false)}
 async function toggleCamera(){if(cameraOn){stopCamera();return}try{const s=await navigator.mediaDevices.getUserMedia({video:true});video.current=s;setCameraOn(true);setTimeout(()=>{if(preview.current){preview.current.srcObject=s;void preview.current.play().catch(()=>{})}},0)}catch{setError("Không thể mở camera.")}}
 async function share(){if(!navigator.mediaDevices.getDisplayMedia){setError("Trình duyệt không hỗ trợ chia sẻ màn hình.");return}try{const s=await navigator.mediaDevices.getDisplayMedia({video:true});s.getTracks().forEach(t=>t.addEventListener("ended",()=>{}));setError("Đã bật chia sẻ màn hình (bản thử nghiệm).");}catch{setError("Đã hủy chia sẻ màn hình.")}}
 function submit(e:FormEvent){e.preventDefault();const text=input;if(!text.trim()||sending.current)return;stopSpeech();setInput("");void send(text)}
 return <main className="person"><div className="stage"><header className="topbar"><div className="brand"><strong>N<span>O</span>A</strong><small>Financial intelligence</small></div><div className="top-actions"><span className="online"><i/> {calling?"Đang trong cuộc gọi":"Sẵn sàng"}</span><button className="icon-btn" aria-label="Ẩn hiện hội thoại" onClick={()=>setChatOpen(v=>!v)}>☷</button></div></header><div className="avatar-area"><div className="avatar-halo"/><div className="avatar-silhouette"><div className="head"/><div className="shoulders"/></div><div className="avatar-label"><b>NOA</b><span>{busy?"Đang suy nghĩ…":speaking?"Đang nói…":calling?"Đang lắng nghe…":"Trợ lý AI của bạn"}</span></div></div><div className="bottom"><div className="call-actions"><button onClick={calling?toggleMute:startCall} title={calling?(muted?"Bật mic":"Tắt mic"):"Bắt đầu gọi"}><span>{calling?(muted?"⊘":"🎙"):"🎙"}</span><small>{calling?(muted?"Bật mic":"Tắt mic"):"Gọi thoại"}</small></button><button onClick={toggleCamera} title="Camera"><span>▣</span><small>{cameraOn?"Tắt camera":"Bật camera"}</small></button><button className="hangup" onClick={endCall} disabled={!calling&&!cameraOn}><span>☎</span><small>Kết thúc</small></button><button onClick={stopSpeech} title="Dừng giọng nói" disabled={!speaking}><span>◼</span><small>Dừng nói</small></button><button onClick={share} title="Chia sẻ màn hình"><span>▤</span><small>Chia sẻ</small></button></div><form className="message-form" onSubmit={submit}><input value={input} onChange={e=>setInput(e.target.value)} placeholder="Nhập câu hỏi cho NOA…" aria-label="Nhập câu hỏi" disabled={busy}/><button type="submit" disabled={busy||!input.trim()} aria-label="Gửi">➤</button></form></div>{cameraOn&&<div className="self-preview"><video ref={preview} autoPlay muted playsInline/><span>Camera của bạn</span></div>}{chatOpen&&<aside className="chat-overlay"><div className="chat-head"><b>Trò chuyện</b><button onClick={()=>setChatOpen(false)} aria-label="Đóng hội thoại">×</button></div><div className="conversation">{messages.length===0&&<p className="empty-chat">Chào bạn, tôi là NOA. Hãy bắt đầu cuộc trò chuyện.</p>}{messages.map((m,i)=><div className={"bubble "+m.role} key={i}><small>{m.role==="user"?"Bạn":"NOA"}</small><p>{m.content}</p></div>)}{busy&&<p className="typing">NOA đang trả lời…</p>}{interim&&<p className="typing">Đang nghe: {interim}</p>}</div>{error&&<div className="chat-error" role="alert">{error}</div>}{voiceError&&<div className="chat-error" role="status">Giọng nói tạm thời không khả dụng. Nội dung chat vẫn hoạt động. <button onClick={()=>{const last=messagesRef.current.at(-1);if(last?.role==="assistant")void speak(last.content)}}>Thử đọc lại</button></div>}</aside>}{!chatOpen&&error&&<div className="floating-error" role="alert">{error}</div>}</div></main>
}