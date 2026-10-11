import {NextResponse} from "next/server";
export async function POST(request:Request){
 const key=process.env.OPENAI_API_KEY;
 if(!key)return NextResponse.json({error:"Chưa cấu hình OPENAI_API_KEY"},{status:503});
 try{
  const body=await request.json();
  const message=typeof body.message==="string"?body.message.trim():"";
  if(!message)return NextResponse.json({error:"Thiếu nội dung"},{status:400});
  const history=Array.isArray(body.history)?body.history.slice(-10):[];
  const input=history.filter((x:any)=>["user","assistant"].includes(x.role)&&typeof x.content==="string").map((x:any)=>({role:x.role,content:x.content.slice(0,4000)}));
  if(input.at(-1)?.role!=="user"||input.at(-1)?.content!==message)input.push({role:"user",content:message});
  const response=await fetch("https://api.openai.com/v1/responses",{method:"POST",headers:{"Content-Type":"application/json",Authorization:"Bearer "+key},body:JSON.stringify({model:process.env.NOA_BRAIN_MODEL||"gpt-5-mini",instructions:"Bạn là NOA Person, một trợ lý AI thân thiện. Trò chuyện tự nhiên bằng tiếng Việt, thường ngắn gọn. Không tự nhận là con người. Chưa tích hợp FIE nên không giả vờ có dữ liệu tài chính nội bộ.",input,max_output_tokens:900}),signal:AbortSignal.timeout(30000)});
  const result=await response.json();
  if(!response.ok)return NextResponse.json({error:result?.error?.message||"Lỗi dịch vụ AI"},{status:502});
  const text=(result.output||[]).flatMap((x:any)=>x.content||[]).filter((x:any)=>x.type==="output_text").map((x:any)=>x.text).join("\n");
  if(!text)return NextResponse.json({error:"AI chưa tạo được câu trả lời. Hãy thử lại với câu hỏi ngắn hơn.",reason:result.status||"empty_output"},{status:502});
  return NextResponse.json({text});
 }catch{return NextResponse.json({error:"Không thể kết nối dịch vụ AI"},{status:502})}
}