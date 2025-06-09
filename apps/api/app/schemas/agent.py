"""
Agent schemas for API validation and serialization.
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.models import AgentType


class AgentBase(BaseModel):
    """Base agent schema with common attributes."""
    
    name: str = Field(..., min_length=1, max_length=255)
    type: AgentType
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")  # Semantic versioning
    model: str = Field(..., description="LLM model used by the agent")
    system_prompt: Optional[str] = None
    tools: List[str] = Field(default_factory=list)
    is_active: bool = True


class AgentCreate(AgentBase):
    """Schema for creating a new agent."""
    
    organization_id: str
    graph_definition: Dict = Field(..., description="LangGraph structure definition")
    
    @validator("graph_definition")
    def validate_graph_definition(cls, v):
        """Ensure graph definition has required fields."""
        if not isinstance(v, dict):
            raise ValueError("Graph definition must be a dictionary")
        # Add more specific validation based on LangGraph requirements
        return v


class AgentUpdate(BaseModel):
    """Schema for updating an agent."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    version: Optional[str] = Field(None, pattern=r"^\d+\.\d+\.\d+$")
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    tools: Optional[List[str]] = None
    graph_definition: Optional[Dict] = None
    is_active: Optional[bool] = None


class AgentInDBBase(AgentBase):
    """Base schema for agent stored in database."""
    
    id: str
    organization_id: str
    graph_definition: Dict
    total_executions: int
    avg_execution_time: Optional[int]  # milliseconds
    success_rate: Optional[Decimal]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class Agent(AgentInDBBase):
    """Schema for agent returned in API responses."""
    pass


class AgentWithStats(Agent):
    """Schema for agent with execution statistics."""
    
    recent_executions: int = 0
    recent_success_rate: float = 0.0
    recent_avg_execution_time: int = 0


class AgentCapability(BaseModel):
    """Schema for agent capability."""
    
    capability: str
    description: Optional[str] = None
    required_tools: List[str] = []
    supported_providers: List[str] = []
    supported_chains: List[int] = []  # Blockchain chain IDs


class AgentDecisionBase(BaseModel):
    """Base schema for agent decision."""
    
    decision_type: str
    input: Dict
    reasoning: Dict
    decision: Dict
    confidence: Decimal = Field(..., ge=0, le=1)


class AgentDecisionCreate(AgentDecisionBase):
    """Schema for creating an agent decision."""
    
    agent_id: str
    payment_order_id: Optional[str] = None
    execution_time: int  # milliseconds
    tokens_used: Optional[int] = None


class AgentDecisionUpdate(BaseModel):
    """Schema for updating an agent decision."""
    
    was_overridden: Optional[bool] = None
    overridden_by: Optional[str] = None
    override_reason: Optional[str] = None


class AgentDecision(AgentDecisionBase):
    """Schema for agent decision in API responses."""
    
    id: str
    agent_id: str
    payment_order_id: Optional[str]
    execution_time: int
    tokens_used: Optional[int]
    was_overridden: bool
    overridden_by: Optional[str]
    override_reason: Optional[str]
    created_at: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class AgentSearchFilter(BaseModel):
    """Schema for agent search filters."""
    
    type: Optional[AgentType] = None
    is_active: Optional[bool] = None
    capabilities: Optional[List[str]] = None
    supported_providers: Optional[List[str]] = None
    min_success_rate: Optional[float] = None 