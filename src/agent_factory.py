from src.agents import create_calendar_agent
import autogen

def create_agents():
    calendar_assistant, calendar_functions = create_calendar_agent()
    
    # Create the user proxy agent
    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        human_input_mode="ALWAYS",
        max_consecutive_auto_reply=1,
        is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
        code_execution_config={
            "work_dir": "workspace",
            "use_docker": False,
            "last_n_messages": 3,
            "execution_timeout": 60,
            "function_call_auto_approve": True
        },
        llm_config=False
    )

    # Register calendar functions
    for function_name, (function, description) in calendar_functions.items():
        autogen.register_function(
            function,
            caller=calendar_assistant,
            executor=user_proxy,
            name=function_name,
            description=description,
        )
    
    return calendar_assistant, user_proxy