export type BrainMessage={role:"user"|"assistant";content:string};
export type BrainReply={text:string};
export async function askBrain(message:string,history:BrainMessage[]=[]):Promise<BrainReply>{
 const res=await fetch("/api/brain",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message,history})});
 const data=await res.json();
 if(!res.ok)throw new Error(data.error||"Brain request failed");
 return {text:data.text};
}