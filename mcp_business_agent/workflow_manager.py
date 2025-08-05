"""
Workflow orchestration for complex multi-step business processes.
Manages workflow execution, dependencies, error recovery, and state persistence.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import uuid
import json

from .models import (
    WorkflowStatus, WorkflowStep, WorkflowDefinition, WorkflowExecution,
    ToolExecutionStatus, WORKFLOW_TEMPLATES
)
from .mcp_client import MCPClient, MCPResponse, MCPError

logger = logging.getLogger(__name__)


class WorkflowError(Exception):
    """Base workflow execution error"""
    pass


class WorkflowTimeoutError(WorkflowError):
    """Workflow execution timeout"""
    pass


class WorkflowStepError(WorkflowError):
    """Error in individual workflow step"""
    pass


class WorkflowDependencyError(WorkflowError):
    """Workflow step dependency error"""
    pass


class WorkflowManager:
    """
    Orchestrates complex multi-step workflows with dependency management,
    error recovery, and state persistence.
    
    Features:
    - Dependency-aware step execution
    - Parallel execution where possible
    - Automatic retry with exponential backoff
    - Workflow state persistence
    - Error recovery and graceful degradation
    - Progress tracking and monitoring
    """
    
    def __init__(self, mcp_client: MCPClient):
        """
        Initialize workflow manager.
        
        Args:
            mcp_client: MCP client for tool execution
        """
        self.mcp_client = mcp_client
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.workflow_definitions: Dict[str, WorkflowDefinition] = {}
        self._load_predefined_workflows()
    
    def _load_predefined_workflows(self):
        """Load predefined workflow templates"""
        for template_id, template_data in WORKFLOW_TEMPLATES.items():
            steps = []
            for step_data in template_data["steps"]:
                step = WorkflowStep(
                    step_id=step_data["step_id"],
                    name=step_data["name"],
                    tool_name=step_data["tool_name"],
                    parameters=step_data["parameters"],
                    depends_on=step_data.get("depends_on", [])
                )
                steps.append(step)
            
            workflow = WorkflowDefinition(
                workflow_id=template_id,
                name=template_data["name"],
                description=template_data["description"],
                steps=steps
            )
            self.workflow_definitions[template_id] = workflow
            
        logger.info(f"Loaded {len(self.workflow_definitions)} predefined workflows")
    
    async def create_workflow(
        self,
        workflow_id: str,
        name: str,
        description: str,
        steps: List[Dict[str, Any]],
        timeout_minutes: int = 30,
        parallel_execution: bool = False
    ) -> WorkflowDefinition:
        """
        Create a new workflow definition.
        
        Args:
            workflow_id: Unique workflow identifier
            name: Human-readable workflow name
            description: Workflow description
            steps: List of step definitions
            timeout_minutes: Workflow timeout in minutes
            parallel_execution: Allow parallel step execution
        
        Returns:
            Created WorkflowDefinition
        """
        workflow_steps = []
        for step_data in steps:
            step = WorkflowStep(
                step_id=step_data["step_id"],
                name=step_data["name"],
                tool_name=step_data["tool_name"],
                parameters=step_data.get("parameters", {}),
                depends_on=step_data.get("depends_on", []),
                max_retries=step_data.get("max_retries", 3)
            )
            workflow_steps.append(step)
        
        # Validate workflow (check for circular dependencies, etc.)
        self._validate_workflow_definition(workflow_steps)
        
        workflow = WorkflowDefinition(
            workflow_id=workflow_id,
            name=name,
            description=description,
            steps=workflow_steps,
            timeout_minutes=timeout_minutes,
            parallel_execution=parallel_execution
        )
        
        self.workflow_definitions[workflow_id] = workflow
        logger.info(f"Created workflow: {workflow_id}")
        
        return workflow
    
    def _validate_workflow_definition(self, steps: List[WorkflowStep]):
        """Validate workflow definition for consistency"""
        step_ids = {step.step_id for step in steps}
        
        # Check for duplicate step IDs
        if len(step_ids) != len(steps):
            raise WorkflowError("Duplicate step IDs found in workflow")
        
        # Check dependencies exist
        for step in steps:
            for dep in step.depends_on:
                if dep not in step_ids:
                    raise WorkflowDependencyError(f"Step {step.step_id} depends on non-existent step {dep}")
        
        # Check for circular dependencies
        self._check_circular_dependencies(steps)
    
    def _check_circular_dependencies(self, steps: List[WorkflowStep]):
        """Check for circular dependencies in workflow"""
        step_map = {step.step_id: step for step in steps}
        
        def has_circular_dependency(step_id: str, visited: Set[str], path: Set[str]) -> bool:
            if step_id in path:
                return True
            if step_id in visited:
                return False
            
            visited.add(step_id)
            path.add(step_id)
            
            step = step_map.get(step_id)
            if step:
                for dep in step.depends_on:
                    if has_circular_dependency(dep, visited, path):
                        return True
            
            path.remove(step_id)
            return False
        
        visited = set()
        for step in steps:
            if step.step_id not in visited:
                if has_circular_dependency(step.step_id, visited, set()):
                    raise WorkflowDependencyError("Circular dependency detected in workflow")
    
    async def execute_workflow(
        self,
        workflow_id: str,
        execution_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """
        Execute a workflow.
        
        Args:
            workflow_id: ID of workflow to execute
            execution_id: Optional execution ID (will generate if not provided)
            parameters: Runtime parameters for workflow
        
        Returns:
            WorkflowExecution with results
        
        Raises:
            WorkflowError: If workflow execution fails
        """
        if workflow_id not in self.workflow_definitions:
            raise WorkflowError(f"Workflow not found: {workflow_id}")
        
        workflow_def = self.workflow_definitions[workflow_id]
        
        if not execution_id:
            execution_id = str(uuid.uuid4())
        
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow_id,
            started_at=datetime.now()
        )
        
        self.active_workflows[execution_id] = execution
        
        try:
            logger.info(f"Starting workflow execution: {workflow_id} ({execution_id})")
            execution.status = WorkflowStatus.IN_PROGRESS
            
            # Apply runtime parameters to steps
            steps = self._apply_runtime_parameters(workflow_def.steps, parameters or {})
            
            # Execute workflow
            if workflow_def.parallel_execution:
                await self._execute_parallel_workflow(execution, steps)
            else:
                await self._execute_sequential_workflow(execution, steps)
            
            # Determine final status
            if all(step.step_id in execution.completed_steps for step in steps):
                execution.status = WorkflowStatus.COMPLETED
            elif execution.failed_steps:
                execution.status = WorkflowStatus.PARTIALLY_COMPLETED
            else:
                execution.status = WorkflowStatus.FAILED
            
            execution.completed_at = datetime.now()
            execution.progress_percentage = 100.0
            
            logger.info(f"Workflow execution completed: {execution_id} ({execution.status.value})")
            
        except asyncio.TimeoutError:
            execution.status = WorkflowStatus.FAILED
            execution.completed_at = datetime.now()
            logger.error(f"Workflow execution timeout: {execution_id}")
            raise WorkflowTimeoutError(f"Workflow {workflow_id} timed out")
        
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.completed_at = datetime.now()
            logger.error(f"Workflow execution failed: {execution_id} - {e}")
            raise WorkflowError(f"Workflow execution failed: {e}")
        
        return execution
    
    def _apply_runtime_parameters(
        self, 
        steps: List[WorkflowStep], 
        parameters: Dict[str, Any]
    ) -> List[WorkflowStep]:
        """Apply runtime parameters to workflow steps"""
        updated_steps = []
        
        for step in steps:
            # Create a copy of the step
            updated_step = WorkflowStep(
                step_id=step.step_id,
                name=step.name,
                tool_name=step.tool_name,
                parameters=step.parameters.copy(),
                depends_on=step.depends_on.copy(),
                max_retries=step.max_retries
            )
            
            # Apply parameter substitution
            for key, value in updated_step.parameters.items():
                if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    param_name = value[2:-1]
                    if param_name in parameters:
                        updated_step.parameters[key] = parameters[param_name]
            
            updated_steps.append(updated_step)
        
        return updated_steps
    
    async def _execute_sequential_workflow(
        self, 
        execution: WorkflowExecution, 
        steps: List[WorkflowStep]
    ):
        """Execute workflow steps sequentially with dependency management"""
        step_map = {step.step_id: step for step in steps}
        remaining_steps = set(step.step_id for step in steps)
        
        while remaining_steps:
            # Find steps that can be executed (all dependencies completed)
            ready_steps = []
            for step_id in remaining_steps:
                step = step_map[step_id]
                if all(dep in execution.completed_steps for dep in step.depends_on):
                    ready_steps.append(step)
            
            if not ready_steps:
                # Check if we're stuck due to failed dependencies
                failed_deps = set()
                for step_id in remaining_steps:
                    step = step_map[step_id]
                    for dep in step.depends_on:
                        if dep in execution.failed_steps:
                            failed_deps.add(step_id)
                
                if failed_deps:
                    logger.warning(f"Skipping steps due to failed dependencies: {failed_deps}")
                    for step_id in failed_deps:
                        execution.failed_steps.append(step_id)
                        remaining_steps.remove(step_id)
                    continue
                else:
                    raise WorkflowError("No ready steps found - possible circular dependency")
            
            # Execute the first ready step
            step = ready_steps[0]
            await self._execute_step(execution, step)
            remaining_steps.remove(step.step_id)
            
            # Update progress
            completed_count = len(execution.completed_steps) + len(execution.failed_steps)
            total_count = len(steps)
            execution.progress_percentage = (completed_count / total_count) * 100
    
    async def _execute_parallel_workflow(
        self, 
        execution: WorkflowExecution, 
        steps: List[WorkflowStep]
    ):
        """Execute workflow steps in parallel where possible"""
        step_map = {step.step_id: step for step in steps}
        remaining_steps = set(step.step_id for step in steps)
        running_tasks = {}
        
        while remaining_steps or running_tasks:
            # Start new tasks for ready steps
            ready_steps = []
            for step_id in remaining_steps:
                step = step_map[step_id]
                if all(dep in execution.completed_steps for dep in step.depends_on):
                    ready_steps.append(step)
            
            # Start tasks for ready steps
            for step in ready_steps:
                task = asyncio.create_task(self._execute_step(execution, step))
                running_tasks[step.step_id] = task
                remaining_steps.remove(step.step_id)
            
            # Wait for at least one task to complete
            if running_tasks:
                done, pending = await asyncio.wait(
                    running_tasks.values(),
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Process completed tasks
                for task in done:
                    step_id = None
                    for sid, t in running_tasks.items():
                        if t == task:
                            step_id = sid
                            break
                    
                    if step_id:
                        del running_tasks[step_id]
                        
                        try:
                            await task  # Get result/exception
                        except Exception as e:
                            logger.error(f"Step {step_id} failed: {e}")
                
                # Update progress
                completed_count = len(execution.completed_steps) + len(execution.failed_steps)
                total_count = len(steps)
                execution.progress_percentage = (completed_count / total_count) * 100
    
    async def _execute_step(self, execution: WorkflowExecution, step: WorkflowStep):
        """Execute a single workflow step with retry logic"""
        logger.info(f"Executing step: {step.step_id} ({step.name})")
        
        execution.current_step = step.step_id
        step.started_at = datetime.now()
        step.status = ToolExecutionStatus.RUNNING
        
        for attempt in range(step.max_retries + 1):
            try:
                # Execute the step
                result = await self._call_mcp_tool(step.tool_name, step.parameters)
                
                # Step succeeded
                step.result = result.data
                step.status = ToolExecutionStatus.COMPLETED
                step.completed_at = datetime.now()
                
                execution.completed_steps.append(step.step_id)
                execution.results[step.step_id] = result.data
                
                logger.info(f"Step completed successfully: {step.step_id}")
                return
            
            except Exception as e:
                step.retry_count = attempt
                step.error = str(e)
                
                if attempt < step.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Step {step.step_id} failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    # All retries exhausted
                    step.status = ToolExecutionStatus.FAILED  
                    step.completed_at = datetime.now()
                    
                    execution.failed_steps.append(step.step_id)
                    execution.errors[step.step_id] = str(e)
                    
                    logger.error(f"Step failed after {step.max_retries} retries: {step.step_id} - {e}")
                    raise WorkflowStepError(f"Step {step.step_id} failed: {e}")
    
    async def _call_mcp_tool(self, tool_name: str, parameters: Dict[str, Any]) -> MCPResponse:
        """Call an MCP tool"""
        try:
            return await self.mcp_client.call_tool(tool_name, parameters)
        except MCPError as e:
            raise WorkflowStepError(f"MCP tool {tool_name} failed: {e}")
    
    def get_workflow_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get current status of a workflow execution"""
        return self.active_workflows.get(execution_id)
    
    def list_active_workflows(self) -> List[str]:
        """List all active workflow execution IDs"""
        return list(self.active_workflows.keys())
    
    def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel a running workflow"""
        if execution_id in self.active_workflows:
            execution = self.active_workflows[execution_id]
            execution.status = WorkflowStatus.CANCELLED
            execution.completed_at = datetime.now()
            logger.info(f"Workflow cancelled: {execution_id}")
            return True
        return False
    
    def cleanup_completed_workflows(self, max_age_hours: int = 24):
        """Clean up old completed workflow executions"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        to_remove = []
        for execution_id, execution in self.active_workflows.items():
            if (execution.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED] 
                and execution.completed_at 
                and execution.completed_at < cutoff_time):
                to_remove.append(execution_id)
        
        for execution_id in to_remove:
            del self.active_workflows[execution_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old workflow executions")
    
    def get_workflow_templates(self) -> Dict[str, str]:
        """Get available workflow templates"""
        return {
            workflow_id: workflow.name 
            for workflow_id, workflow in self.workflow_definitions.items()
        }
    
    async def execute_template_workflow(
        self,
        template_id: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """Execute a predefined workflow template"""
        if template_id not in self.workflow_definitions:
            raise WorkflowError(f"Workflow template not found: {template_id}")
        
        execution_id = f"{template_id}_{int(datetime.now().timestamp())}"
        return await self.execute_workflow(template_id, execution_id, parameters)