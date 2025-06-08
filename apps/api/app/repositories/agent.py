"""
Agent repository with capability queries.
"""
from typing import Dict, List, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Agent, AgentDecision, AgentType, PaymentOrder
from app.repositories.base import BaseRepository
from app.schemas.agent import AgentCreate, AgentSearchFilter, AgentUpdate


class AgentRepository(BaseRepository[Agent, AgentCreate, AgentUpdate]):
    """Repository for agent-related database operations."""
    
    def __init__(self):
        """Initialize the repository."""
        super().__init__(Agent)
    
    @property
    def _organization_id_field(self) -> Optional[str]:
        """Agents are scoped to organizations."""
        return "organization_id"
    
    async def get_by_type(
        self,
        db: AsyncSession,
        *,
        agent_type: AgentType,
        organization_id: str,
        active_only: bool = True
    ) -> List[Agent]:
        """
        Get agents by type within an organization.
        
        Args:
            db: Database session
            agent_type: Type of agent
            organization_id: Organization ID
            active_only: Only return active agents
            
        Returns:
            List of agents
        """
        query = select(Agent).where(
            and_(
                Agent.type == agent_type,
                Agent.organization_id == organization_id
            )
        )
        
        if active_only:
            query = query.where(Agent.is_active == True)
        
        query = query.order_by(Agent.version.desc())
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_capabilities(
        self,
        db: AsyncSession,
        *,
        capabilities: List[str],
        organization_id: str,
        match_all: bool = True
    ) -> List[Agent]:
        """
        Get agents that have specific capabilities.
        
        Args:
            db: Database session
            capabilities: List of required capabilities
            organization_id: Organization ID
            match_all: If True, agent must have all capabilities. If False, any capability.
            
        Returns:
            List of agents with requested capabilities
        """
        query = select(Agent).where(
            and_(
                Agent.organization_id == organization_id,
                Agent.is_active == True
            )
        )
        
        # Filter by capabilities in tools array
        if match_all:
            # Agent must have all capabilities
            for capability in capabilities:
                query = query.where(
                    func.array_position(Agent.tools, capability).isnot(None)
                )
        else:
            # Agent must have at least one capability
            capability_filters = [
                func.array_position(Agent.tools, cap).isnot(None)
                for cap in capabilities
            ]
            query = query.where(or_(*capability_filters))
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_by_supported_providers(
        self,
        db: AsyncSession,
        *,
        providers: List[str],
        organization_id: str
    ) -> List[Agent]:
        """
        Get agents that support specific payment providers.
        
        Args:
            db: Database session
            providers: List of provider names
            organization_id: Organization ID
            
        Returns:
            List of agents supporting the providers
        """
        # This assumes provider support is stored in graph_definition JSON
        query = select(Agent).where(
            and_(
                Agent.organization_id == organization_id,
                Agent.is_active == True
            )
        )
        
        # Filter by providers in graph_definition
        provider_filters = []
        for provider in providers:
            # Check if provider is in supported_providers array in graph_definition
            provider_filters.append(
                Agent.graph_definition["supported_providers"].astext.contains(provider)
            )
        
        if provider_filters:
            query = query.where(or_(*provider_filters))
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_best_agent_for_task(
        self,
        db: AsyncSession,
        *,
        agent_type: AgentType,
        organization_id: str,
        min_success_rate: Optional[float] = None
    ) -> Optional[Agent]:
        """
        Get the best performing agent for a specific task type.
        
        Args:
            db: Database session
            agent_type: Type of agent needed
            organization_id: Organization ID
            min_success_rate: Minimum acceptable success rate (0-100)
            
        Returns:
            Best agent or None if no suitable agent found
        """
        query = select(Agent).where(
            and_(
                Agent.type == agent_type,
                Agent.organization_id == organization_id,
                Agent.is_active == True
            )
        )
        
        if min_success_rate is not None:
            query = query.where(Agent.success_rate >= min_success_rate)
        
        # Order by success rate and execution time
        query = query.order_by(
            Agent.success_rate.desc().nullslast(),
            Agent.avg_execution_time.asc().nullslast(),
            Agent.version.desc()
        )
        
        result = await db.execute(query.limit(1))
        return result.scalar_one_or_none()
    
    async def update_performance_metrics(
        self,
        db: AsyncSession,
        *,
        agent_id: str,
        execution_time: int,
        success: bool
    ) -> Agent:
        """
        Update agent performance metrics after execution.
        
        Args:
            db: Database session
            agent_id: Agent ID
            execution_time: Execution time in milliseconds
            success: Whether execution was successful
            
        Returns:
            Updated agent
        """
        agent = await self.get_or_404(db, id=agent_id)
        
        # Update execution count
        agent.total_executions += 1
        
        # Update average execution time
        if agent.avg_execution_time is None:
            agent.avg_execution_time = execution_time
        else:
            # Calculate new average
            total_time = agent.avg_execution_time * (agent.total_executions - 1)
            agent.avg_execution_time = (total_time + execution_time) // agent.total_executions
        
        # Update success rate
        if agent.success_rate is None:
            agent.success_rate = 100.0 if success else 0.0
        else:
            # Calculate new success rate
            successful_executions = int(agent.success_rate * (agent.total_executions - 1) / 100)
            if success:
                successful_executions += 1
            agent.success_rate = (successful_executions * 100) / agent.total_executions
        
        db.add(agent)
        await db.flush()
        await db.refresh(agent)
        
        return agent
    
    async def get_recent_decisions(
        self,
        db: AsyncSession,
        *,
        agent_id: str,
        limit: int = 10,
        payment_order_id: Optional[str] = None
    ) -> List[AgentDecision]:
        """
        Get recent decisions made by an agent.
        
        Args:
            db: Database session
            agent_id: Agent ID
            limit: Maximum number of decisions to return
            payment_order_id: Filter by specific payment order
            
        Returns:
            List of recent agent decisions
        """
        query = select(AgentDecision).where(
            AgentDecision.agent_id == agent_id
        )
        
        if payment_order_id:
            query = query.where(AgentDecision.payment_order_id == payment_order_id)
        
        query = query.order_by(AgentDecision.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def search(
        self,
        db: AsyncSession,
        *,
        filters: AgentSearchFilter,
        organization_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Agent]:
        """
        Search agents with multiple filters.
        
        Args:
            db: Database session
            filters: Search filters
            organization_id: Organization ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of matching agents
        """
        query = select(Agent).where(
            Agent.organization_id == organization_id
        )
        
        # Apply filters
        if filters.type is not None:
            query = query.where(Agent.type == filters.type)
        
        if filters.is_active is not None:
            query = query.where(Agent.is_active == filters.is_active)
        
        if filters.capabilities:
            # Agent must have all specified capabilities
            for capability in filters.capabilities:
                query = query.where(
                    func.array_position(Agent.tools, capability).isnot(None)
                )
        
        if filters.supported_providers:
            # Agent must support at least one provider
            provider_filters = []
            for provider in filters.supported_providers:
                provider_filters.append(
                    Agent.graph_definition["supported_providers"].astext.contains(provider)
                )
            if provider_filters:
                query = query.where(or_(*provider_filters))
        
        if filters.min_success_rate is not None:
            query = query.where(Agent.success_rate >= filters.min_success_rate)
        
        # Apply ordering and pagination
        query = query.order_by(
            Agent.type,
            Agent.version.desc()
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def get_agent_stats(
        self,
        db: AsyncSession,
        *,
        agent_id: str,
        days: int = 7
    ) -> Dict:
        """
        Get agent statistics for a specific time period.
        
        Args:
            db: Database session
            agent_id: Agent ID
            days: Number of days to look back
            
        Returns:
            Dictionary with agent statistics
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get recent decisions
        decision_query = select(
            func.count(AgentDecision.id).label("total_decisions"),
            func.count(AgentDecision.id).filter(
                AgentDecision.was_overridden == True
            ).label("overridden_decisions"),
            func.avg(AgentDecision.execution_time).label("avg_execution_time"),
            func.sum(AgentDecision.tokens_used).label("total_tokens")
        ).where(
            and_(
                AgentDecision.agent_id == agent_id,
                AgentDecision.created_at >= cutoff_date
            )
        )
        
        decision_result = await db.execute(decision_query)
        decision_stats = decision_result.one()
        
        # Get success rate from completed payment orders
        order_query = select(
            func.count(PaymentOrder.id).label("total_orders"),
            func.count(PaymentOrder.id).filter(
                PaymentOrder.status == "COMPLETED"
            ).label("successful_orders")
        ).select_from(PaymentOrder).join(
            AgentDecision,
            PaymentOrder.id == AgentDecision.payment_order_id
        ).where(
            and_(
                AgentDecision.agent_id == agent_id,
                AgentDecision.created_at >= cutoff_date
            )
        )
        
        order_result = await db.execute(order_query)
        order_stats = order_result.one()
        
        # Calculate success rate
        success_rate = 0.0
        if order_stats.total_orders > 0:
            success_rate = (order_stats.successful_orders / order_stats.total_orders) * 100
        
        return {
            "period_days": days,
            "total_decisions": decision_stats.total_decisions or 0,
            "overridden_decisions": decision_stats.overridden_decisions or 0,
            "avg_execution_time": float(decision_stats.avg_execution_time or 0),
            "total_tokens_used": decision_stats.total_tokens or 0,
            "total_payment_orders": order_stats.total_orders or 0,
            "successful_orders": order_stats.successful_orders or 0,
            "success_rate": round(success_rate, 2)
        } 