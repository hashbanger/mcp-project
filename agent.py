from dataclasses import dataclass, field
from agents import Agent, Runner, function_tool
from pydantic import BaseModel
from dotenv import load_dotenv
from agents.mcp import MCPServerStdio

import requests

load_dotenv()

def log_current_tool_execution(run_result):
    for item in run_result.new_items:
        # Case 1: Handoff occurred
        if item.type == "handoff_call_item":
            # Get the agent name (if available)
            if hasattr(item, "target_agent"):
                print(f"\n[LOG] Handoff to agent: {item.target_agent.name}")
            else:
                print("\n[LOG] Handoff occurred, but target agent not found.")

        # Case 2: Tool is being called
        elif item.type == "tool_call_item":
            tool_name = getattr(item.raw_item, "name", "unknown_tool")
            args = getattr(item.raw_item, "arguments", "{}")
            agent_name = getattr(item.agent, "name", "unknown_agent")
            print(f"\n[LOG] Agent '{agent_name}' is invoking tool '{tool_name}' with arguments: {args}")

        # Case 3: Tool execution output
        elif item.type == "tool_call_output_item":
            output = getattr(item, "output", None)
            agent_name = getattr(item.agent, "name", "unknown_agent")
            print(f"\n[LOG] Agent '{agent_name}' received output: {output} from tool call")

        # Case 4: Assistant final message
        elif item.type == "message_output_item":
            content = (
                item.raw_item.content[0].text
                if getattr(item.raw_item, "content", None)
                else "[no message content]"
            )
            agent_name = getattr(item.agent, "name", "unknown_agent")
            print(f"\n[LOG] Agent '{agent_name}' responded with: \"{content}\"")

@function_tool
def get_weather(city: str) -> str:
    """
    Returns the current weather condition and temperature in Celsius for a given city.
    """
    # First, get the coordinates of the city using geocoding
    geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}"
    geo_resp = requests.get(geocode_url).json()

    if "results" not in geo_resp:
        return f"City '{city}' not found."

    lat = geo_resp["results"][0]["latitude"]
    lon = geo_resp["results"][0]["longitude"]

    # Now get the weather
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&current_weather=true"
    )
    weather_resp = requests.get(weather_url).json()

    if "current_weather" not in weather_resp:
        return f"Weather data unavailable for '{city}'."

    weather = weather_resp["current_weather"]
    return (
        f"In {city}, it is currently {weather['temperature']}°C with "
        f"winds of {weather['windspeed']} km/h."
    )

class ResponseStructure(BaseModel):
    message: str

@dataclass
class ChatContext:
    user_name: str
    history: list = field(default_factory=list)

weather_agent = Agent(
    name="Weather Assistant",
    instructions="You're a helpful assistant, remember to always use the provided tools whenever possible. Do not rely on your own knowledge too much and instead use your tools to answer queries.",
    model="gpt-4o",
    tools=[get_weather],
)

mcp_server = MCPServerStdio(
    params={"command": "uv", "args": ["run", "research_server.py"]},
    cache_tools_list=True
)

main_agent = Agent[ChatContext](
    name="Main Agent",
    instructions="You are Jonas, You are always cheerful and happy to help. Always greet user with their name. Help the user with their questions. You have access to the tool: Calculator. Whenever you don't understand the users's question, ask questions back to understand the user's questions",
    model="gpt-4o",
    output_type=ResponseStructure,
    # tools=[
    #     weather_agent.as_tool(tool_name="weather", tool_description="Tool to fetch weather forecast.")
    # ],
    mcp_servers=[mcp_server]
)

async def handle_message(user_message: str, context: ChatContext):
    context.history.append({"role": "user", "content": user_message})

    result = await Runner.run(
        starting_agent=main_agent,
        input=context.history,
        context=context
    )
    # log_current_tool_execution(result)
    context.history.append({"role": "assistant", "content": str(result.final_output)})

    return result

async def main():
    user_name = input("Enter username: ")
    context = ChatContext(user_name=user_name)
    user_message = None

    async with mcp_server:
        while user_message not in ["exit", "quit"]:
            user_message = input("\nUser: ")
            response = await handle_message(user_message, context)
            print("\nBot:", response.final_output.message)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())