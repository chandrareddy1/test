from typing import Any
from uuid import uuid4
from a2a.types import (
    AgentCard, 
    Task,
    SendMessageRequest,
    MessageSendParams
)
import httpx
from a2a.client import A2AClient

class AgentConnector:
    """
    Connects to a remote A2A agent and provides a uniform method to delegate tasks
    """

    def __init__(self, agent_card: AgentCard):
        self.agent_card = agent_card

    async def send_task(self, message: str, session_id: str) -> str:
        """
        Send a task to the agent and return the Task object
        
        Args:
            message (str): The message to send to the agent
            session_id (str): The session ID for tracking the task

        Returns:
            str: The response from the agent
        """

        async with httpx.AsyncClient(timeout=120.0) as httpx_client:  # Increased timeout
            a2a_client = A2AClient(
                httpx_client=httpx_client,
                agent_card=self.agent_card,
            )

            send_message_payload: dict[str, Any] = {
                'message': {
                    'role': 'user',
                    'messageId': str(uuid4()),
                    'parts': [
                        {
                            'text': message,
                            'kind': 'text'
                        }
                    ]
                }
            }

            request = SendMessageRequest(
                id=str(uuid4()),
                params=MessageSendParams(
                    **send_message_payload
                )
            )

            print(f"🔄 Sending request to {self.agent_card.url}")
            response = await a2a_client.send_message(
                request=request
            )

            response_data = response.model_dump(mode='json', exclude_none=True)
            print(f"✅ Response received, processing...")

            try:
                agent_response = response_data['result']['status']['message']['parts'][0]['text']
            except (KeyError, IndexError) as e:
                print(f"⚠️ Response structure issue: {e}")
                print(f"🔍 Full response: {response_data}")
                agent_response = f"Response received but couldn't extract text. Full response: {response_data}"

            return agent_response
