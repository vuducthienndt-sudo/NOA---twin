import {NextRequest,NextResponse} from "next/server";
import {spawn} from "node:child_process";
import {mkdtemp,readFile,rm} from "node:fs/promises";
import {tmpdir} from "node:os";
import {join} from "node:path";
import {createHash} from "node:crypto";

export const runtime="nodejs";
const VOICE="vi-VN-HoaiMyNeural";
const TIMEOUT_MS=18000;
const MAX_CACHE=32;
const cache=new Map<string,Uint8Array>();

function remember(key:string,audio:Uint8Array){
 if(cache.has(key))cache.delete(key);
 cache.set(key,audio);
 while(cache.size>MAX_CACHE){const oldest=cache.keys().next().value;if(oldest)cache.delete(oldest);else break}
}
function render(python:string,args:string[]):Promise<void>{
 return new Promise((resolve,reject)=>{
  const child=spawn(python,args,{windowsHide:true,stdio:["ignore","ignore","pipe"]});
  let stderr="";let settled=false;
  const finish=(error?:Error)=>{
   if(settled)return;settled=true;clearTimeout(timer);
   if(error)reject(error);else resolve();
  };
  const timer=setTimeout(()=>{child.kill();finish(new Error("TTS_TIMEOUT"))},TIMEOUT_MS);
  child.stderr.on("data",(data:Buffer)=>{stderr+=data.toString().slice(0,1500)});
  child.on("error",(error:NodeJS.ErrnoException)=>finish(new Error(error.code==="ENOENT"?"PYTHON_NOT_FOUND":error.message)));
  child.on("close",code=>finish(code===0?undefined:new Error(stderr.trim()||"EDGE_TTS_EXIT_"+code)));
 });
}
function describe(error:unknown){
 const detail=error instanceof Error?error.message:"Unknown error";
 if(detail==="PYTHON_NOT_FOUND")return {error:"Không tìm thấy Python. Cài Python hoặc đặt NOA_PYTHON.",code:"PYTHON_NOT_FOUND",detail};
 if(detail.includes("No module named edge_tts"))return {error:"Chưa cài edge-tts. Chạy: python -m pip install edge-tts",code:"EDGE_TTS_MISSING",detail};
 if(detail==="TTS_TIMEOUT")return {error:"Dịch vụ giọng nói phản hồi quá chậm.",code:"TTS_TIMEOUT",detail};
 return {error:"Dịch vụ tạo giọng đang không khả dụng.",code:"TTS_UNAVAILABLE",detail};
}
export async function POST(req:NextRequest){
 let dir="";
 try{
  const body=await req.json();
  const text=typeof body.text==="string"?body.text.trim():"";
  if(!text||text.length>1500)return NextResponse.json({error:"Văn bản phải có từ 1 đến 1500 ký tự."},{status:400});
  const key=createHash("sha256").update(VOICE+"\n"+text).digest("hex");
  const cached=cache.get(key);
  if(cached)return new NextResponse(new Uint8Array(cached),{headers:{"Content-Type":"audio/mpeg","Cache-Control":"no-store","X-NOA-TTS-Cache":"HIT"}});
  dir=await mkdtemp(join(tmpdir(),"noa-voice-"));
  const output=join(dir,"speech.mp3");
  const python=process.env.NOA_PYTHON||"python";
  const args=["-m","edge_tts","--voice",VOICE,"--text",text,"--write-media",output];
  let failure:unknown;
  for(let attempt=0;attempt<2;attempt++){
   try{
    await render(python,args);
    const data=await readFile(output);
    if(!data.length)throw new Error("EMPTY_AUDIO");
    const audio=new Uint8Array(data);
    remember(key,audio);
    return new NextResponse(new Uint8Array(audio),{headers:{"Content-Type":"audio/mpeg","Cache-Control":"no-store","X-NOA-TTS-Cache":"MISS"}});
   }catch(error){
    failure=error;
    const message=error instanceof Error?error.message:"";
    if(message==="PYTHON_NOT_FOUND"||message.includes("No module named edge_tts"))break;
   }
  }
  const info=describe(failure);
  return NextResponse.json({...info,detail:process.env.NODE_ENV==="development"?info.detail:undefined},{status:503});
 }catch(error){
  const info=describe(error);
  return NextResponse.json({...info,detail:process.env.NODE_ENV==="development"?info.detail:undefined},{status:503});
 }finally{
  if(dir)await rm(dir,{recursive:true,force:true}).catch(()=>{});
 }
}
