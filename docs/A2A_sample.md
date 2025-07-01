Google의 에이전트 간 (A2A) 프로토콜은 서로 다른 AI 에이전트가 프레임워크나 공급 업체에 관계없이 소통하고 협력할 수 있도록 해주는 오픈 표준입니다 (GitHub - google/A2A). 간단히 말해, A2A는 에이전트 간 상호작용을 위한 공통 언어를 제공합니다. 이 튜토리얼에서는 A2A 프로토콜을 사용하여 통신하는 두 개의 간단한 Python 에이전트를 만드는 방법을 단계별로 안내합니다. 한 에이전트는 A2A 서버 역할을 하고 다른 하나는 A2A 클라이언트 역할을 합니다. 우리는 설정을 다루고, A2A가 기본적으로 어떻게 작동하는지 설명하며, 두 에이전트의 주석 처리된 코드 예제를 제공합니다. A2A에 대한 사전 경험이 필요하지 않으며, 복잡한 도구 체인이나 다중 에이전트 오케스트레이션과 같은 고급 개념은 피하고 초보자가 쉽게 이해할 수 있도록 도와드리겠습니다.

A2A 프로토콜이란?
A2A는 에이전트 간 메시지, 요청 및 데이터를 교환하는 방식을 표준화하는 프로토콜(HTTP 기반)입니다. A2A의 몇 가지 핵심 개념은 다음과 같습니다.

에이전트 카드: 에이전트의 기능, 스킬, 엔드포인트 URL 및 인증 요구 사항을 설명하는 공개 메타데이터 파일입니다 (일반적으로 /.well-known/agent.json에 호스팅됨). 다른 에이전트나 클라이언트는 에이전트가 무엇을 할 수 있는지 발견하기 위해 이 카드를 가져옵니다 (GitHub - google/A2A). 에이전트 네트워크에서 에이전트의 "명함"이라고 할 수 있습니다.
A2A 서버: A2A 메소드를 구현하는 HTTP API 엔드포인트를 노출하는 에이전트입니다 (예: 작업을 보내는 엔드포인트). 요청을 수신하여 다른 에이전트를 대신하여 작업을 실행합니다 (GitHub - google/A2A).
A2A 클라이언트: 작업이나 대화를 시작하기 위해 A2A 서버의 URL로 요청을 보내는 애플리케이션 또는 에이전트입니다 (GitHub - google/A2A). 에이전트 간 시나리오에서, 한 에이전트의 클라이언트 구성 요소가 A2A를 통해 다른 에이전트의 서버 구성 요소를 호출합니다.
작업: A2A에서의 근본적인 작업 단위입니다. 클라이언트는 메시지 (tasks/send 요청 사용)를 에이전트에게 보내 작업을 시작합니다. 각 작업에는 고유한 ID가 있으며 submitted, working, input-required, completed 등의 상태를 가지고 있습니다 (GitHub - google/A2A).
메시지: 클라이언트 (역할 "user")와 에이전트 (역할 "agent") 간의 통신에서의 단일 턴입니다. 클라이언트의 요청은 메시지 ("user"로부터)이며, 에이전트의 응답은 메시지 ("agent"로부터)입니다 (GitHub - google/A2A).
파트: 메시지 내의 콘텐츠 조각입니다. 메시지는 하나 이상의 파트로 구성됩니다. 파트는 텍스트, 파일 또는 구조화된 데이터일 수 있습니다. 예를 들어, TextPart는 일반 텍스트를 전송하는 반면, 파일 파트는 이미지나 기타 이진 데이터를 전송할 수 있습니다 (GitHub - google/A2A). 이 튜토리얼에서는 명확성을 위해 간단한 텍스트 파트만 사용합니다.
A2A 통신 작동 방식 (기본 흐름): 한 에이전트가 A2A를 통해 다른 에이전트와 통신하고자 할 때, 상호작용은 일반적으로 다음과 같은 표준화된 흐름을 따릅니다.

발견: 클라이언트 에이전트는 먼저 서버의 /.well-known/agent.json URL에서 에이전트 카드를 가져와 다른 에이전트를 발견합니다 (GitHub - google/A2A). 이 카드는 클라이언트에게 에이전트의 이름, 기능 및 요청을 어디로 보내야 하는지 알려줍니다.
시작: 이후 클라이언트는 POST를 통해 tasks/send 엔드포인트에 요청을 보내 작업을 시작합니다. 이 초기 요청에는 고유한 작업 ID와 첫 번째 사용자 메시지 (예: 질문 또는 명령)가 포함됩니다 (GitHub - google/A2A).
처리: 서버 에이전트는 작업 요청을 수신하고 처리합니다. 에이전트가 스트리밍 응답을 지원한다면 작업 중간에 중간 업데이트를 스트리밍할 수 있습니다 (Server-Sent Events 사용). 단순한 예제이므로 스트리밍은 사용하지 않습니다. 그 대신, 에이전트는 작업을 처리하고 완료되면 최종 응답을 보냅니다 (GitHub - google/A2A). 응답은 작업의 결과를 포함하게 되며, 이는 일반적으로 에이전트의 메시지들로 구성됩니다 (또한 작업의 일부라면 파일 등 아티팩트도 포함될 수 있습니다). 기본 텍스트 상호작용의 경우 최종 응답은 에이전트의 메시지 답변만 포함합니다.
요약하면, A2A는 에이전트 간의 명확한 요청-응답 사이클을 정의합니다: 클라이언트가 에이전트의 기능을 찾고 (에이전트 카드), 작업을 보내며 (초기 사용자 메시지와 함께), 에이전트의 응답 (메시지 및 아티팩트로서)을 요청하여, 일관된 JSON 형식을 따릅니다. 이제 우리의 환경을 설정하고 이 프로세스가 어떻게 작동하는지 보기 위해 최소한의 예제를 만들어 봅시다.

MCP는 AI 개발을 위한 유사한 프로토콜로, AI가 기존 도구, 웹 API 또는 데이터에 액세스할 수 있도록 합니다. MCP에 관심이 있으시면, MCP 튜토리얼을 확인해보세요 How to Build a MCP service for your blog site.

설치 및 설정
코드를 작성하기 전에 필요한 도구가 설치되어 있는지 확인하세요:

Python 3.12 이상 – A2A 샘플은 호환성을 위해 Python 3.12+ (심지어 Python 3.13)을 권장합니다 (A2A/samples/python/hosts/cli at main · google/A2A · GitHub).
UV (Python 패키지 관리자) – A2A 프로젝트는 종속성을 관리하고 샘플을 실행하기 위해 이 도구를 권장합니다 (A2A/samples/python/hosts/cli at main · google/A2A · GitHub). UV는 현대적인 패키지 관리자입니다. 하지만 선호한다면 pip/venv를 사용해 종속성을 수동으로 설치할 수도 있습니다. 이 튜토리얼에서는 표준 Python 도구를 사용하여 간단히 진행하겠습니다.
Google A2A 저장소 – GitHub 저장소를 클론하여 공식 A2A 코드를 얻으세요:
git clone https://github.com/google/A2A.git
이는 프로젝트를 로컬 머신에 다운로드할 것입니다. 튜토리얼 코드는 이 저장소의 일부 (특히 샘플 A2A 클라이언트 유틸리티) 참조할 것입니다.
종속성 – UV를 사용하면 종속성을 자동으로 관리할 수 있습니다. 예를 들어, 저장소의 samples/python 디렉토리에서 uv sync을 실행하여 종속성을 설치하거나 공식 README에 나와 있는 uv run ... 명령어를 실행할 수 있습니다. pip을 사용한다면, 예제 코드를 위해 필요한 라이브러리를 설치하세요:
pip install flask requests
Flask 라이브러리는 에이전트용 간단한 HTTP 서버를 만드는 데 사용되고, requests는 클라이언트가 에이전트를 호출하는 데 사용됩니다. (공식 A2A 샘플 코드는 FastAPI/UVICorn과 내부 클라이언트 라이브러리를 사용하지만, 초보자 친화적인 접근 방식으로 Flask와 requests를 사용합니다.)
간단한 A2A 서버 에이전트 만들기
먼저, 서버 측을 구축해봅시다: 들어오는 작업을 듣고 응답하는 에이전트입니다. 우리의 에이전트는 매우 간단합니다 – 텍스트 프롬프트를 수신하여 그것을 친절한 메시지와 함께 에코할 것입니다. 비록 간단하지만, A2A 프로토콜 구조를 따를 것이므로 어떤 A2A 클라이언트와도 통신할 수 있습니다.

에이전트 기능과 에이전트 카드: 우리의 에이전트가 발견될 수 있도록, 에이전트 카드를 제공해야 합니다. 실제 배포에서는 서버의 /.well-known/agent.json에 JSON 파일을 호스팅할 것입니다. 우리의 Flask 앱에서는 이 데이터를 엔드포인트를 통해 제공합니다. 에이전트 카드는 일반적으로 에이전트의 이름, 설명, A2A 엔드포인트의 URL, 지원 기능 등과 같은 필드를 포함합니다 (GitHub - google/A2A). 우리는 몇 가지 주요 필드로 최소한의 에이전트 카드를 구성할 것입니다.

tasks/send 엔드포인트: A2A는 에이전트가 특정 API 엔드포인트를 구현할 것을 기대합니다. 가장 중요한 것은 클라이언트가 새로운 작업 (사용자 메시지와 함께)을 에이전트에게 보내기 위해 호출할 (HTTP POST) tasks/send입니다 (GitHub - google/A2A). 우리의 Flask 앱은 이러한 요청을 처리하기 위한 /tasks/send 경로를 정의할 것입니다. 들어오는 JSON (작업 ID와 사용자의 메시지 포함)을 구문 분석하고, 그것을 처리하며 (우리의 경우 단순히 에코 응답 생성) A2A 형식에 맞는 JSON 응답을 반환할 것입니다.

Flask를 사용하여 간단한 A2A 서버 에이전트 코드를 작성해 봅시다:

from flask import Flask, request, jsonify
 
app = Flask(__name__)
 
# Define the Agent Card data (metadata about this agent)
AGENT_CARD = {
    "name": "EchoAgent",
    "description": "A simple agent that echoes back user messages.",
    "url": "http://localhost:5000",  # The base URL where this agent is hosted
    "version": "1.0",
    "capabilities": {
        "streaming": False,           # This agent doesn't support streaming responses
        "pushNotifications": False    # No push notifications in this simple example
    }
    # (In a full Agent Card, there could be more fields like authentication info, etc.)
}
 
# Serve the Agent Card at the well-known URL.
@app.get("/.well-known/agent.json")
def get_agent_card():
    """Endpoint to provide this agent's metadata (Agent Card)."""
    return jsonify(AGENT_CARD)
 
# Handle incoming task requests at the A2A endpoint.
@app.post("/tasks/send")
def handle_task():
    """Endpoint for A2A clients to send a new task (with an initial user message)."""
    task_request = request.get_json()  # parse incoming JSON request
    # Extract the task ID and the user's message text from the request.
    task_id = task_request.get("id")
    user_message = ""
    try:
        # According to A2A spec, the user message is in task_request["message"]["parts"][0]["text"]
        user_message = task_request["message"]["parts"][0]["text"]
    except Exception as e:
        return jsonify({"error": "Invalid request format"}), 400
 
    # For this simple agent, the "processing" is just echoing the message back.
    agent_reply_text = f"Hello! You said: '{user_message}'"
 
    # Formulate the response in A2A Task format.
    # We'll return a Task object with the final state = 'completed' and the agent's message.
    response_task = {
        "id": task_id,
        "status": {"state": "completed"},
        "messages": [
            task_request.get("message", {}),             # include the original user message in history
            {
                "role": "agent",                        # the agent's reply
                "parts": [{"text": agent_reply_text}]   # agent's message content as a TextPart
            }
        ]
        # We could also include an "artifacts" field if the agent returned files or other data.
    }
    return jsonify(response_task)
 
# Run the Flask app (A2A server) if this script is executed directly.
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
서버 코드 이해하기: 위의 코드에서는 다음과 같은 일들이 일어납니다:

우리는 Flask 앱을 만들고 전역 변수 AGENT_CARD를 정의했습니다. 여기에 우리의 에이전트에 대한 기본 정보가 포함됩니다. 특히, 이름, 설명, URL (localhost와 포트 5000을 지칭), 그리고 기능들 (capabilities) 섹션이 있습니다. 스트리밍을 지원하지 않으므로 streaming: False로 설정했습니다 (스트리밍을 지원하는 에이전트라면 tasks/sendSubscribe를 처리하고, 여기서는 다루지 않을 부분적인 결과 스트리밍을 지원해야 할 것입니다).
/.well-known/agent.json 경로를 설정하고, 이 경로에서 에이전트 카드 JSON을 제공합니다. 이는 에이전트 카드가 발견되기를 기대하는 표준 위치를 따라 설정하는 것입니다 (GitHub - google/A2A).
tasks/send에 대한 POST 경로를 정의합니다. A2A 클라이언트가 작업을 보낼 때, Flask가 handle_task()를 호출합니다. 이 함수 내부에서:
요청의 JSON 본문을 task_request로 구문 분석합니다. A2A 스키마에 따르면, 여기에는 "id" (작업 ID)와 "message" 객체 (사용자의 초기 메시지)가 포함됩니다.
사용자의 메시지 텍스트를 추출합니다. A2A에서는 메시지가 여러 부분으로 구성될 수 있으며 (예: 텍스트, 파일), 첫 번째 부분이 텍스트라는 가정을 하고 task_request["message"]["parts"][0]["text"]를 가져옵니다. 보다 강력한 구현에서는 부분의 유형을 확인하고 오류를 처리할 것입니다 (우리의 코드는 단순한 try/except로 기대한 형식이 아닐 경우 오류 코드 400을 반환합니다).
우리는 에이전트의 응답을 생성합니다. 우리의 로직은 단순합니다: 사용자 텍스트를 가져와 `"Hello! You said: ..."을 앞에 붙이는 것입니다. 실제 에이전트에서는 여기서 핵심 AI 로직이 들어갈 것입니다 (LLM 호출, 계산 수행 등).
그다음, 응답 Task 객체를 구성합니다. 반드시 id를 반환하여 (클라이언트에게 어떤 작업인지 알리기 위해), status.state를 "completed"로 설정하고 (작업을 완료한 경우), messages 목록을 제공합니다. 사용자 메시지를 (컨텍스트/역사로서) 포함하고, 에이전트의 응답을 또 하나 메시지로 추가합니다. 각 메시지는 role ("user" 또는 "agent")과 parts 리스트를 가집니다. 에이전트의 메시지에 대한 응답 텍스트가 포함된 단일 TextPart를 사용합니다.
마지막으로 JSON으로 반환합니다. Flask는 파이썬 dict를 JSON으로 직렬화해 줄 것입니다.
이 서버가 실행되면, 에이전트는 http://localhost:5000에 "실시간"으로 존재하게 됩니다. 에이전트 카드를 제공하고 작업 요청을 처리할 수 있습니다.

간단한 A2A 클라이언트 에이전트 만들기
에이전트 서버가 준비되었으니, 이제 그것과 통신할 수 있는 클라이언트를 만들어 보겠습니다. 이 클라이언트는 다른 에이전트일 수도 있고 단순히 사용자 인터페이스 애플리케이션일 수도 있습니다. A2A 용어로, 이는 A2A 클라이언트입니다. A2A 클라이언트는 에이전트 서버의 A2A API를 소비합니다 (GitHub - google/A2A). 우리의 튜토리얼에서는 사용자를 위해 질문을 보내고 EchoAgent의 응답을 받는 역할을 하는 작은 Python 스크립트를 작성할 것입니다.

클라이언트 수행 단계:

에이전트 발견: 클라이언트는 서버 에이전트의 에이전트 카드를 가져와 그 엔드포인트와 기능을 알아내야 합니다. 우리는 이미 에이전트 카드가 http://localhost:5000/.well-known/agent.json에 있다는 것을 알고 있습니다. Python requests 라이브러리를 사용하여 이 URL을 가져올 수 있습니다.
작업 전송: 그 다음, 클라이언트는 JSON 페이로드를 담아 에이전트의 tasks/send 엔드포인트로 POST 요청을 보낼 것입니다. 이 페이로드는 다음을 포함해야 합니다:
작업의 고유한 "id" (임의의 고유 문자열 또는 숫자. 예를 들어, "task1"),
"message" 객체와 role: "user"가 포함된 parts 목록으로 사용자 질의를 텍스트 파트로 담습니다.
응답 수신: 에이전트는 작업 (에이전트의 응답 메시지를 포함한)을 나타내는 JSON을 응답할 것입니다. 클라이언트는 이 응답을 읽고 에이전트의 응답을 추출해야 합니다.
이 단계들을 수행할 클라이언트 코드를 작성해 봅시다:

import requests
import uuid
 
# 1. Discover the agent by fetching its Agent Card
AGENT_BASE_URL = "http://localhost:5000"
agent_card_url = f"{AGENT_BASE_URL}/.well-known/agent.json"
response = requests.get(agent_card_url)
if response.status_code != 200:
    raise RuntimeError(f"Failed to get agent card: {response.status_code}")
agent_card = response.json()
print("Discovered Agent:", agent_card["name"], "-", agent_card.get("description", ""))
 
# 2. Prepare a task request for the agent
task_id = str(uuid.uuid4())  # generate a random unique task ID
user_text = "What is the meaning of life?"
task_payload = {
    "id": task_id,
    "message": {
        "role": "user",
        "parts": [
            {"text": user_text}
        ]
    }
}
print(f"Sending task {task_id} to agent with message: '{user_text}'")
 
# 3. Send the task to the agent's tasks/send endpoint
tasks_send_url = f"{AGENT_BASE_URL}/tasks/send"
result = requests.post(tasks_send_url, json=task_payload)
if result.status_code != 200:
    raise RuntimeError(f"Task request failed: {result.status_code}, {result.text}")
task_response = result.json()
 
# 4. Process the agent's response
# The response should contain the task ID, status, and the messages (including the agent's reply).
if task_response.get("status", {}).get("state") == "completed":
    # The last message in the list should be the agent's answer (since our agent included history in messages).
    messages = task_response.get("messages", [])
    if messages:
        agent_message = messages[-1]  # last message (from agent)
        agent_reply_text = ""
        # Extract text from the agent's message parts
        for part in agent_message.get("parts", []):
            if "text" in part:
                agent_reply_text += part["text"]
        print("Agent's reply:", agent_reply_text)
    else:
        print("No messages in response!")
else:
    print("Task did not complete. Status:", task_response.get("status"))
클라이언트 코드 이해하기: 다음과 같은 작업을 수행합니다:

requests.get을 사용하여 http://localhost:5000/.well-known/agent.json에서 에이전트 카드를 가져옵니다. 성공하면 JSON을 구문 분석하고, 에이전트의 이름과 설명을 인쇄하여 올바른 에이전트를 찾았음을 확인합니다.
uuid.uuid4()를 사용하여 고유 작업 ID를 생성합니다. 이는 단순히 ID를 재사용하지 않기 위함이며, 실제 상황에서는 클라이언트가 보내는 각 작업이 고유한 ID를 가져야 합니다.
파이썬 딕셔너리로 작업 페이로드를 만듭니다. 이 페이로드는 A2A 스키마를 따릅니다: "id" (우리의 생성된 ID)와 사용자의 질의에 대한 "message"입니다. 메시지에는 role: "user"와 텍스트 "What is the meaning of life?"가 포함된 하나의 부분이 있습니다 (이 텍스트는 변경 가능하며 EchoAgent가 그것을 에코할 것입니다).
requests.post를 사용하여 에이전트의 tasks/send 엔드포인트로 이 페이로드를 보냅니다. json=... 매개변수를 사용하여 requests 라이브러리가 딕셔너리를 JSON으로 전송하도록 합니다.
상태가 200 OK인지 확인합니다. 상태가 200이 아니면 오류를 발생합니다. (보다 유연한 스크립트에서는 200이 아닌 응답을 더 우아하게 처리할 수 있습니다).
호출이 성공하면 JSON 응답을 task_response로 구문 분석합니다. 이 응답은 에이전트가 반환한 Task 객체일 것입니다. 우리는 이것을 조사합니다:
status.state가 "completed"인지 확인합니다 – 우리의 설계에서 에이전트는 하나의 응답 후 작업을 완료할 것입니다. 예를 들어, 에이전트가 더 많은 입력이 필요하거나 ("input-required"), 실패할 경우는 다르게 처리해야 합니다. 간단히 완료됨을 가정합니다.
응답에서 messages 리스트를 가져옵니다. 우리는 이 리스트의 마지막 메시지가 에이전트의 응답이라 예상합니다 (우리의 서버 코드가 사용자의 메시지 이후 에이전트의 메시지를 추가했으므로). 우리는 에이전트의 메시지 부분에서 텍스트를 추출합니다. 이 경우, 우리가 구성한 에코 응답이 될 것입니다.
마지막으로, 에이전트의 응답을 출력합니다.
이 시점에서, 클라이언트는 에이전트로부터 받은 응답을 출력하게 될 것입니다. 다음 섹션에서는 서버와 클라이언트를 실행하여 전체 상호 작용을 확인할 것입니다.

에이전트 실행 및 테스트
우리의 두 에이전트를 테스트하기 위해 다음 단계를 따릅니다:

서버 에이전트 시작: Flask 서버 스크립트 (echo_agent.py라고 칩시다)를 실행합니다. 예를 들어, 터미널에서:

python echo_agent.py
이렇게 하면 Flask 개발 서버가 http://localhost:5000에서 시작됩니다. "Running on http://0.0.0.0:5000/"와 같은 메시지가 나타날 것입니다. 에이전트가 이제 요청을 듣고 있습니다. (포트 5000을 사용하는 다른 것이 없다면, 그렇지 않으면 코드에서 포트를 변경하세요).

클라이언트 스크립트 실행: 다른 터미널을 열고 클라이언트 스크립트 (client_agent.py)를 실행합니다:

python client_agent.py
클라이언트는 다음과 같은 메시지를 출력해야 합니다:

Discovered Agent: EchoAgent – A simple agent that echoes back user messages.
Sending task 3f8ae8ac-... to agent with message: 'What is the meaning of life?'
Agent's reply: Hello! You said: 'What is the meaning of life?'
이는 클라이언트가 성공적으로 에이전트를 발견하고, 질문을 보냈으며, 답변을 받았음을 나타냅니다. 에이전트의 응답은 예상대로 에코된 메시지입니다.

상호 작용 확인: 서버의 콘솔 출력도 확인할 수 있습니다. Flask는 처리한 요청을 로깅합니다. /.well-known/agent.json에 대한 GET 요청과 /tasks/send에 대한 POST 요청, 그리고 각각의 200 상태를 확인할 수 있습니다. 이는 프로토콜 흐름을 확인합니다:

발견 (클라이언트 GET 에이전트 카드) → 시작 (클라이언트 POST 작업) → 처리/완료 (서버가 응답으로 결과 전달).
축하합니다! Google의 A2A 프로토콜을 사용하여 기본 에이전트 간의 통신을 구현하였습니다. 한 에이전트는 서비스 역할 (EchoAgent), 다른 하나는 질의한 클라이언트 역할을 했습니다. 이 예제는 단순히 입력을 반영하는 (에코하는) "AI"였지만, 어떤 A2A 상호 작용에도 필요한 설정을 보여줍니다.

A2A 클라이언트 라이브러리 사용하기 (선택 사항)
우리의 클라이언트 코드에서는 requests를 사용하여 HTTP 요청을 수동으로 작성했습니다. 공식 A2A GitHub 저장소는 이 과정을 단순화하는 헬퍼 클래스를 제공합니다. 예를 들어, A2AClient 클래스는 에이전트 카드 가져오기와 작업 전송을 자동 처리할 수 있으며, A2ACardResolver를 통해 에이전트의 카드를 발견할 수 있습니다. (보다 관습적인 접근 방식을 원하는 분들을 위한 것입니다.)

import asyncio
from samples.python.common.client import A2AClient, A2ACardResolver
from samples.python.common.types import TaskSendParams, Message, TextPart
 
async def query_agent(agent_url, user_text):
    # Fetch agent card automatically
    card_resolver = A2ACardResolver(agent_url)
    agent_card = card_resolver.get_agent_card()
    print("Discovered Agent:", agent_card.name)
    # Create A2A client with the agent's card
    client = A2AClient(agent_card=agent_card)
    # Prepare Task parameters (using A2A type classes)
    payload = TaskSendParams(
        id=str(uuid.uuid4()),
        message=Message(role="user", parts=[TextPart(text=user_text)])
    )
    # Send the task and wait for completion
    result_task = await client.send_task(payload)  # send_task is an async method
    # Extract agent's reply from result_task
    if result_task.status.state.value == "completed":
        # The A2A Task object can be inspected for messages and artifacts
        for msg in result_task.messages:
            if msg.role == "agent":
                # Print text parts of agent's message
                print("Agent's reply:", " ".join(part.text for part in msg.parts if hasattr(part, "text")))
위의 코드에서는 A2ACardResolver와 A2AClient가 A2A 샘플 라이브러리에서 가져온 것입니다 (저장소의 samples/python/common 디렉토리). TaskSendParams, Message, TextPart는 A2A JSON 스키마의 일부에 해당하는 데이터 클래스입니다. 이를 사용하면 사전을 수동으로 만들 필요 없이 Python 객체를 생성하고, 라이브러리가 JSON 직렬화와 HTTP 호출을 처리할 것입니다. 클라이언트의 send_task 메소드는 비동기이며 (따라서 await 사용), Task 객체를 반환합니다. 우리의 예시에서는 이 객체로부터 에이전트의 응답을 가져오는 방법을 보여줍니다.

참고: 위의 코드는 설명을 위한 것이며, A2A 저장소 코드를 Python 경로에서 사용할 수 있어야 합니다. 저장소를 클론하고 필요한 요구사항을 설치했다면 (UV 또는 pip를 통해), 이를 클라이언트에 통합할 수 있습니다. A2A 저장소의 공식 CLI 도구는 이 단계들을 처리하며, 에이전트 카드를 읽어들여 작업을 전송하고 응답을 출력하는 반복 입력 모드 (REPL)와 유사한 대화를 시작합니다 (A2A/samples/python/hosts/cli at main · google/A2A · GitHub).

Google의 A2A 프로토콜을 사용한 두 개의 Python 에이전트 빌드하기 - 단계별 튜토리얼
2025년 파이썬에서 가장 성장하는 상위 10개 데이터 시각화 라이브러리
PyGWalker: 판다 데이터프레임을 Tableau 스타일 UI로 변환하여 시각적 데이터 분석 수행
RATH를 소개합니다: ChatGPT 기반 개인 데이터 분석가
결론
이 튜토리얼에서 우리는 Google의 A2A 프로토콜의 기본을 다루고 두 가지 에이전트 간의 간단한 통신을 시연했습니다. 최소한의 A2A 서버 (EchoAgent)와 상호작용하는 클라이언트를 설정했습니다. 이 과정에서, 에이전트 카드 (발견용)와 A2A에서 작업과 메시지가 어떻게 구조화되는지 배웠습니다.

우리의 예제는 단순한 에코 에이전트였지만, 이제 더 복잡한 에이전트를 만들 수 있는 기초를 가지게 되었습니다. 예를 들어, 에코 논리를 언어 모델 호출이나 API 호출로 대체하여 에이전트가 실제로 문제를 해결하거나 질문에 대답하도록 만들 수 있습니다. A2A의 장점은 에이전트가 프로토콜을 준수하는 한 (에이전트 카드를 제공하고 작업 엔드포인트를 구현) 다른 A2A 호환 에이전트나 도구와 통합할 수 있다는 것입니다.

다음 단계: 공식 A2A 저장소의 샘플을 통해 더 고급 패턴을 탐구할 수 있습니다. 예를 들어, Google의 샘플에는 텍스트로 이미지를 생성하고 그것을 이미지 아티팩트로 반환하는 에이전트가 포함되어 있습니다 (A2A/samples/python/agents/crewai/README.md at main · google/A2A · GitHub), 다중 턴 형식 작성 대화를 처리하는 또 다른 에이전트도 있습니다. 제공된 커맨드 라인 인터페이스 (CLI)나 웹 데모를 사용하여 에이전트와 채팅해 보는 것도 좋습니다. UV와 저장소 설정이 완료된 경우 EchoAgent와 함께 CLI를 사용하려면 uv run hosts/cli --agent http://localhost:5000을 실행하여 에이전트와 대화를 시작할 수 있습니다 (A2A/samples/python/hosts/cli at main · google/A2A · GitHub).

에이전트 통신을 표준화함으로써 A2A는 상호운용 가능한 AI 에이전트의 풍부한 생태계를 열어줍니다. 우리는 여기서 간단한 예제로만 다뤘습니다. A2A와 함께 실험하며 에이전트가 협력적으로 작동하기를 바랍니다!

출처:

Google A2A GitHub – Agent2Agent Protocol README (Conceptual Overview) (GitHub - google/A2A) (GitHub - google/A2A) (GitHub - google/A2A) (GitHub - google/A2A)
Google A2A GitHub – Samples and CLI Usage (A2A/samples/python/hosts/cli at main · google/A2A · GitHub) (A2A/samples/python/hosts/cli at main · google/A2A · GitHub)
Google A2A GitHub – CrewAI Sample README (agent capabilities via A2A) (A2A/samples/python/agents/crewai/README.md at main · google/A2A · GitHub) (for further exploration)