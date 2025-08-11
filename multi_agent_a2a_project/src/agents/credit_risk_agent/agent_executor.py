import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater

from src.agents.credit_risk_agent.agent import CreditRiskAgent
from a2a.utils import (
    new_task,
    new_agent_text_message
)

from a2a.utils.errors import ServerError

from a2a.types import (
    Task,
    TaskState,
    UnsupportedOperationError
)

import asyncio
import json

class CreditRiskAgentExecutor(AgentExecutor):
    """
    Implements the AgentExecutor interface to integrate the 
    credit_risk_agent with the A2A framework.
    """

    def __init__(self):
        self.agent = CreditRiskAgent()

    async def create(self):
        """
        Factory method to create and asynchronously initialize the CreditRiskAgentExecutor.
        """
        await self.agent.create()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Executes the credit risk agent with the provided context and event queue.
        """
        query = context.get_user_input()
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        # Get context_id from different possible sources
        context_id = getattr(task, 'contextId', None) or getattr(context, 'context_id', None) or "default-context"
        
        updater = TaskUpdater(event_queue, task.id, context_id)
        
        try:
            # Parse input as document data for credit risk analysis
            document_data = {}
            try:
                # Try to parse as JSON first
                document_data = json.loads(query)
            except json.JSONDecodeError:
                # If not JSON, try to extract JSON from text like "Perform assessment on: {JSON_DATA}"
                import re
                json_match = re.search(r'(\{.*\})', query, re.DOTALL)
                if json_match:
                    try:
                        document_data = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        # If extraction fails, create basic structure
                        document_data = {
                            "text_input": query,
                            "source": "user_input"
                        }
                else:
                    # No JSON found, treat as text input
                    document_data = {
                        "text_input": query,
                        "source": "user_input"
                    }
            
            await updater.update_status(
                TaskState.working,
                new_agent_text_message("Analyzing credit risk factors...", context_id, task.id)
            )
            
            # Process the document data through credit risk analysis
            risk_assessment = await self.agent.process_document_data(document_data)
            
            await updater.update_status(
                TaskState.working,
                new_agent_text_message("Generating risk assessment report...", context_id, task.id)
            )
            
            # Format the final result
            final_result = {
                "risk_analysis": risk_assessment,
                "input_data": document_data,
                "agent": "CreditRiskAgent"
            }
            
            await updater.update_status(
                TaskState.completed,
                new_agent_text_message(json.dumps(final_result, indent=2), context_id, task.id)
            )

            await asyncio.sleep(0.1)  # Allow time for the message to be processed

        except Exception as e:
            error_message = f"Credit risk analysis failed: {str(e)}"
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(error_message, context_id, task.id)
            )
            raise

    async def cancel(self, request: RequestContext, event_queue: EventQueue) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())
