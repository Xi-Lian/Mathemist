"""
测试前端消息处理
"""
import requests
import json

API_URL = "http://localhost:8000"
ASSISTANT_ID = "math-agent"

def test_frontend_message_processing():
    """测试前端消息处理"""
    print("========== 测试前端消息处理 ==========")
    
    # 创建线程
    thread_response = requests.post(
        f"{API_URL}/threads",
        headers={"Content-Type": "application/json"},
        json={}
    )
    
    if thread_response.status_code != 200:
        print(f"创建线程失败: {thread_response.status_code}")
        print(thread_response.text)
        return
    
    thread_data = thread_response.json()
    thread_id = thread_data["thread_id"]
    print(f"线程 ID: {thread_id}")
    
    # 创建运行（流式）
    run_request = {
        "assistant_id": ASSISTANT_ID,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": "查找指数函数相关资源"
                }
            ]
        }
    }
    
    print(f"\n发送请求: {json.dumps(run_request, ensure_ascii=False, indent=2)}")
    
    stream_response = requests.post(
        f"{API_URL}/threads/{thread_id}/runs/stream",
        json=run_request,
        headers={"Content-Type": "application/json"},
        stream=True
    )
    
    if stream_response.status_code != 200:
        print(f"创建运行失败: {stream_response.status_code}")
        print(stream_response.text)
        return
    
    print(f"\n开始接收流式响应...")
    
    # 解析 SSE 事件
    messages_received = []
    for line in stream_response.iter_lines():
        if line:
            line = line.decode('utf-8')
            print(f"收到: {line}")
            
            if line.startswith("event:"):
                event_type = line[6:].strip()
                print(f"\n📦 事件类型: {event_type}")
            elif line.startswith("data:"):
                data = line[5:].strip()
                try:
                    data_json = json.loads(data)
                    print(f"📄 数据: {json.dumps(data_json, ensure_ascii=False, indent=2)}")
                    
                    # 检查是否是 messages 事件
                    if event_type == "messages":
                        print(f"\n✅ 收到 messages 事件！")
                        print(f"消息内容: {data_json}")
                        
                        # 检查消息格式
                        if isinstance(data_json, list) and len(data_json) == 2:
                            message, metadata = data_json
                            print(f"\n📌 消息对象:")
                            print(f"  - type: {message.get('type')}")
                            print(f"  - id: {message.get('id')}")
                            print(f"  - content type: {type(message.get('content'))}")
                            print(f"  - content length: {len(message.get('content', ''))}")
                            
                            # 检查 content 字段
                            content = message.get('content')
                            if isinstance(content, str):
                                print(f"  - content (前100字符): {content[:100]}")
                            elif isinstance(content, list):
                                print(f"  - content (数组): {len(content)} 项")
                                for i, item in enumerate(content[:3]):
                                    print(f"    [{i}] {item}")
                            
                            messages_received.append(message)
                except json.JSONDecodeError as e:
                    print(f"JSON 解析失败: {e}")
                    print(f"原始数据: {data}")
    
    print(f"\n========== 总结 ==========")
    print(f"总共收到 {len(messages_received)} 条消息")
    for i, message in enumerate(messages_received):
        print(f"\n消息 {i+1}:")
        print(f"  - type: {message.get('type')}")
        print(f"  - id: {message.get('id')}")
        print(f"  - content length: {len(message.get('content', ''))}")

if __name__ == "__main__":
    test_frontend_message_processing()