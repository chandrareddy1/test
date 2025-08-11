import json
import os
from a2a.types import AgentCard
from a2a.client import A2ACardResolver, A2AClient
import httpx

class AgentDiscovery:
    """
    Discovers A2A Agents by reading a registry file of URLs and
    querying each one's /.well-known/agent.json endpoint to retrieve
    an AgentCard

    Attributes:
        registry_file (str): Path to the agent registry file.
        base_urls (List[str]): List of base URLs for A2A Agents.
    """

    def __init__(self, registry_file: str = None):
        """
        Initialise the AgentDiscovery

        Args:
            registry_file (str): Path to the agent registry file.
                Defaults to 'utilities/a2a/agent_registry.json'.
        """

        if registry_file:
            self.registry_file = registry_file
        else:
            self.registry_file = os.path.join(
                os.path.dirname(__file__),
                'agent_registry.json'
            )
        self.base_urls = self._load_registry()

    def _load_registry(self) -> list[str]:
        """
        Load and parse the registry JSON file into a list of URLs
        
        Returns:
            list[str]: List of base URLs for A2A Agents.
        """
        try:
            with open(self.registry_file, 'r') as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Registry file must contain a list of URLs")
            return data
        except FileNotFoundError:
            print(f"Registry file not found: {self.registry_file}")
            return []
        except json.JSONDecodeError:
            print(f"Invalid JSON in registry file: {self.registry_file}")
            return []

    async def discover_agents(self) -> dict[str, AgentCard]:
        """
        Discover all agents from the registry
        
        Returns:
            dict[str, AgentCard]: Dictionary mapping agent names to their AgentCard objects
        """
        agents = {}
        
        async with httpx.AsyncClient(timeout=30.0) as httpx_client:
            for base_url in self.base_urls:
                try:
                    # Quiet discovery - only show final results
                    resolver = A2ACardResolver(
                        base_url=base_url.rstrip('/'),
                        httpx_client=httpx_client
                    )
                    agent_card = await resolver.get_agent_card()
                    if agent_card:
                        agent_name = agent_card.name or base_url
                        agents[agent_name] = agent_card
                        # Condensed success message
                        port = base_url.split(':')[-1] if ':' in base_url else base_url
                        print(f"   ✓ {agent_name} (:{port})")
                except Exception as e:
                    # Condensed error message
                    port = base_url.split(':')[-1] if ':' in base_url else base_url
                    if "Connection" in str(e) or "Network" in str(e):
                        print(f"   ✗ Port {port} unavailable")
                    else:
                        print(f"   ✗ Port {port} error")
                    
        return agents

    async def get_agent_card(self, agent_url: str) -> AgentCard | None:
        """
        Get the AgentCard for a specific agent URL
        
        Args:
            agent_url (str): The base URL of the agent
            
        Returns:
            AgentCard | None: The AgentCard object or None if not found
        """
        async with httpx.AsyncClient(timeout=30.0) as httpx_client:
            resolver = A2ACardResolver(
                base_url=agent_url.rstrip('/'),
                httpx_client=httpx_client
            )
            
            try:
                return await resolver.get_agent_card()
            except Exception as e:
                print(f"Failed to get agent card for {agent_url}: {e}")
                return None
