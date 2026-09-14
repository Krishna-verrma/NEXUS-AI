import pytest
import sys
import asyncio
import tempfile
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.agents.orchestrator import orchestrator
from app.services.task_service import TaskService
from app.services.chat_service import ChatService
from app.database.repository import Repository

FORBIDDEN_DEMO_STRINGS = [
    "Strategic Revenue & Market Analysis",
    "European customer retention",
    "customer retention collapsed",
    "Executive SWAT Team",
    "Sovereign EU Cloud",
    "demo_sales.csv",
    "-37.2% revenue contraction",
]

@pytest.mark.asyncio
async def test_1_docker_explanation():
    """Test 1: 'Explain Docker and how containers work' -> produces container/Docker explanation, no sales data."""
    prompt = "Explain Docker and how containers work"
    task = await TaskService.create_and_run_task(prompt=prompt, is_demo=False)
    task_id = task["id"]

    # Wait for completion
    for _ in range(30):
        await asyncio.sleep(0.1)
        curr = Repository.get_task(task_id)
        if curr["status"] in ("completed", "failed"):
            break

    final = Repository.get_task(task_id)
    assert final["status"] == "completed"
    result_text = final["final_result"]
    assert result_text is not None

    # Verify task-specific Docker contents
    lower_res = result_text.lower()
    assert "docker" in lower_res
    assert "container" in lower_res
    assert any(term in lower_res for term in ["namespaces", "cgroups", "isolation", "kernel", "image"])

    # Verify NO European sales data
    for bad in FORBIDDEN_DEMO_STRINGS:
        assert bad.lower() not in lower_res, f"Found forbidden demo text: {bad}"

    # Verify workflow steps: only research and reviewer
    step_agents = [s["agent_id"] for s in final["steps"]]
    assert "research" in step_agents
    assert "reviewer" in step_agents
    assert "data_analyst" not in step_agents, "Data Analyst should not run for Docker explanation"

@pytest.mark.asyncio
async def test_2_cpp_binary_search():
    """Test 2: 'Write a binary search algorithm in C++' -> produces C++ code for binary search with explanation. No sales data."""
    prompt = "Write a binary search algorithm in C++"
    task = await TaskService.create_and_run_task(prompt=prompt, is_demo=False)
    task_id = task["id"]

    for _ in range(30):
        await asyncio.sleep(0.1)
        curr = Repository.get_task(task_id)
        if curr["status"] in ("completed", "failed"):
            break

    final = Repository.get_task(task_id)
    assert final["status"] == "completed"
    result_text = final["final_result"]
    assert result_text is not None

    # Verify C++ code and binary search semantics
    assert "binarySearch" in result_text or "binary_search" in result_text
    assert "vector" in result_text
    assert "low" in result_text and "high" in result_text
    assert "```cpp" in result_text or "```c++" in result_text or "C++" in result_text

    # Verify NO sales data
    lower_res = result_text.lower()
    for bad in FORBIDDEN_DEMO_STRINGS:
        assert bad.lower() not in lower_res, f"Found forbidden demo text: {bad}"

    # Verify workflow: coding + reviewer
    step_agents = [s["agent_id"] for s in final["steps"]]
    assert "coding" in step_agents
    assert "reviewer" in step_agents
    assert "report" not in step_agents, "Report agent should not run for simple code generation"

@pytest.mark.asyncio
async def test_3_eco_friendly_logistics_startup_ideas():
    """Test 3: 'Give me 3 startup ideas for eco-friendly logistics' -> produces 3 logistics startup ideas. No sales data."""
    prompt = "Give me 3 startup ideas for eco-friendly logistics"
    task = await TaskService.create_and_run_task(prompt=prompt, is_demo=False)
    task_id = task["id"]

    for _ in range(30):
        await asyncio.sleep(0.1)
        curr = Repository.get_task(task_id)
        if curr["status"] in ("completed", "failed"):
            break

    final = Repository.get_task(task_id)
    assert final["status"] == "completed"
    result_text = final["final_result"]
    assert result_text is not None

    lower_res = result_text.lower()
    assert "logistics" in lower_res
    assert any(term in lower_res for term in ["startup", "eco-friendly", "emissions", "freight", "packaging", "delivery"])

    # Verify NO European sales churn
    for bad in FORBIDDEN_DEMO_STRINGS:
        assert bad.lower() not in lower_res, f"Found forbidden demo text: {bad}"

@pytest.mark.asyncio
async def test_4_custom_dataset_analysis(tmp_path):
    """Test 4: Upload custom CSV -> analyzes the actual custom columns, not demo_sales.csv."""
    custom_csv = tmp_path / "server_metrics.csv"
    custom_csv.write_text(
        "ServerID,Region,CPU_Usage,Memory_GB,Latency_ms\n"
        "srv-01,US-East,45.2,16.0,12.4\n"
        "srv-02,US-West,88.9,32.0,45.1\n"
        "srv-03,EU-Central,62.1,24.0,22.8\n"
        "srv-04,AP-South,95.6,64.0,88.4\n"
        "srv-05,US-East,38.0,16.0,10.2\n",
        encoding="utf-8"
    )

    prompt = "Analyze this server metrics dataset and identify high load nodes"
    files = [{
        "file_path": str(custom_csv),
        "filename": "server_metrics.csv",
        "file_type": "csv"
    }]

    # Direct orchestrator execution with files
    import uuid
    task_id = str(uuid.uuid4())
    Repository.create_task(task_id, "Server Metrics Analysis", prompt, "moderate", False)
    Repository.create_file(
        file_id=str(uuid.uuid4()),
        filename="server_metrics.csv",
        original_name="server_metrics.csv",
        file_type="csv",
        file_size=custom_csv.stat().st_size,
        file_path=str(custom_csv),
        task_id=task_id
    )

    await orchestrator.execute_task(task_id)
    final = Repository.get_task(task_id)

    assert final["status"] == "completed"
    result_text = final["final_result"]

    # Verify actual custom columns were processed
    lower_res = result_text.lower()
    assert "cpu_usage" in lower_res or "latency_ms" in lower_res or "serverid" in lower_res
    assert "records" in lower_res or "metric" in lower_res

    # Must NOT mention demo sales fields
    assert "customer retention" not in lower_res
    assert "revenue contracted" not in lower_res

@pytest.mark.asyncio
async def test_5_consecutive_distinct_tasks():
    """Test 5: Run 2 different tasks in sequence -> task 1 and task 2 produce completely different, topic-specific results."""
    # Task A: C++ Binary Search
    task_a = await TaskService.create_and_run_task("Write binary search in C++", is_demo=False)
    for _ in range(30):
        await asyncio.sleep(0.1)
        if Repository.get_task(task_a["id"])["status"] in ("completed", "failed"):
            break

    # Task B: Docker Architecture
    task_b = await TaskService.create_and_run_task("Explain how Docker containerization works", is_demo=False)
    for _ in range(30):
        await asyncio.sleep(0.1)
        if Repository.get_task(task_b["id"])["status"] in ("completed", "failed"):
            break

    res_a = Repository.get_task(task_a["id"])
    res_b = Repository.get_task(task_b["id"])

    assert res_a["id"] != res_b["id"]
    assert res_a["final_result"] != res_b["final_result"]

    # Task A has code, Task B has container explanation
    assert "binarysearch" in res_a["final_result"].lower() or "binary_search" in res_a["final_result"].lower()
    assert "docker" in res_b["final_result"].lower() or "container" in res_b["final_result"].lower()

    # Neither has demo sales data
    for bad in FORBIDDEN_DEMO_STRINGS:
        assert bad.lower() not in res_a["final_result"].lower()
        assert bad.lower() not in res_b["final_result"].lower()

@pytest.mark.asyncio
async def test_6_task_intelligence_chat_grounding():
    """Test 6: Ask follow-up question in task chat -> answers about the current task, not European sales."""
    # Run a coding task
    task = await TaskService.create_and_run_task("Write a binary search algorithm in C++", is_demo=False)
    task_id = task["id"]
    for _ in range(30):
        await asyncio.sleep(0.1)
        if Repository.get_task(task_id)["status"] in ("completed", "failed"):
            break

    # Send follow-up: "Explain the code optimizations and why you chose this algorithm"
    chat_resp = await ChatService.send_message(
        message="Explain the code optimizations and why you chose this algorithm",
        task_id=task_id
    )

    assert chat_resp is not None
    content = chat_resp["content"]
    lower_content = content.lower()

    # Verify grounding in C++ binary search
    assert any(term in lower_content for term in ["binary search", "overflow", "log n", "optimization", "mid", "pointer", "iterative", "c++"])

    # Verify NO mention of European sales or customer churn SWAT team
    assert "european" not in lower_content
    assert "swat team" not in lower_content
    assert "retention collapsed" not in lower_content
