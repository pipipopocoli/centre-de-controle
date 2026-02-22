from app.services.task_planner import build_plan

def test_task_limit():
    # Setup: Create an intake with explicit tasks > 12
    # Since build_plan generates tasks based on stack, we'll need to manually
    # force a large list or mock the internal logic.
    # However, build_plan currently HARDCODES the tasks based on stack.
    # To test the limit effectively with the CURRENT implementation, we need to
    # simulate a scenario where many agents/tasks are added.
    # But wait, looking at the code, it adds tasks based on "stack".
    # Let's try to add enough stack items to trigger it, OR manually inject tasks if possible?
    # Actually, the function is `build_plan(intake, answers)`.
    # It constructs `plan["tasks"]` list.
    # We might need to monkeypatch or just rely on the logic we added.
    # The logic is:
    # if len(plan["tasks"]) > MAX_TASKS: ...
    
    # As the current `build_plan` implementation is very static (only adds ~3-5 tasks max based on stack),
    # verifying it requires EITHER:
    # 1. Modifying the test to monkeypatch the internal list before the check (fragile).
    # 2. Or, assuming the logic is correct by code inspection (risky).
    # 3. Or, creating a "clean" way to inject many tasks.
    
    # Let's try to simulate high load by answering with many items if that path existed,
    # but the current code only adds fixed items.
    # Actually, let's just create a dummy internal list to verify the LOGIC part?
    # No, that changes the code.
    
    # Better approach: We can fake the "stack" to include many items if that drove task creation loop?
    # No, it checks `if "python" in stack`, etc.
    
    # Okay, for this verification, I will manually constructing a plan object and running the logic block?
    # No, I should test the FUNCTION.
    # Since I cannot easily force `build_plan` to produce 13 items with the current simple implementation,
    # I will rely on a slightly modified test that mocks the list *during* execution? No.
    
    # WAIT. I can just verify that for a SMALL list, it does NOT truncate.
    # And then, I'll temporarily lower the limit in the test to 2 to verify truncation works?
    
    import app.services.task_planner
    original_max = app.services.task_planner.MAX_TASKS
    
    try:
        # Lower limit to 2 to force truncation with standard inputs
        app.services.task_planner.MAX_TASKS = 2
        
        intake = {
            "project_name": "Test Project",
            "stack": ["python", "node", "go", "rust"] # Should generate Clems, Victor, Leo, Agent-1, Agent-2...
            # Actually standard is Clems, Victor, Leo (3) + Agent-1 (Python) + Agent-2 (Node) = 5 tasks.
        }
        
        plan = build_plan(intake)
        tasks = plan["tasks"]
        
        print(f"Generated {len(tasks)} tasks with limit 2.")
        
        # Expectation: 2 items + 1 system item = 3 items total
        # List[:2] + [System]
        assert len(tasks) == 3
        assert tasks[-1]["agent_id"] == "system"
        assert "Truncated" in tasks[-1]["scope"]
        
        print("Truncation logic verification passed!")
        
    finally:
        app.services.task_planner.MAX_TASKS = original_max

if __name__ == "__main__":
    try:
        test_task_limit()
        print("\nAll task cap tests passed.")
    except Exception as e:
        print(f"\nTest failed: {e}")
        exit(1)
