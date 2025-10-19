from dotenv import load_dotenv
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio
import nest_asyncio

nest_asyncio.apply()

load_dotenv()

class ChatbotMCP:
    def __init__(self, server_filepath, model="claude-3-5-haiku-20241022", max_tokens=1024):
        self.session = None
        self.server_filepath = server_filepath
        self.anthropic = Anthropic()
        self.available_tools = []
        self.model = model
        self.max_tokens = max_tokens
        self.context = []

    async def process_query(self, query):
        messages = self.context
        messages.append({"role": "user", "content": query})

        # print("---------------------------------------")
        # print(messages)
        # print("---------------------------------------")
        response = self.anthropic.messages.create(
                    model=self.model,
                    tools=self.available_tools,
                    max_tokens=self.max_tokens,
                    messages=messages)

        process_query = True
        while process_query:
            assistant_content = []
            for content in response.content:
                if content.type == "text":
                    assistant_content.append(content)
                    if (len(response.content)==1):
                        process_query = False
                elif content.type == "tool_use":
                    assistant_content.append(content)
                    messages.append({"role": "assistant", "content": assistant_content})
                    tool_id = content.id
                    tool_args = content.input
                    tool_name = content.name

                    print(f"\n[LOG]: Calling tool {tool_name} with args {tool_args}\n")

                    result = await self.session.call_tool(tool_name, arguments=tool_args)
                    print(f"[LOG]: Tool {tool_name} returned result: `{result.content}`\n")
                    messages.append(
                        {
                            "role": "user", 
                            "content": [{"type": "tool_result", "tool_use_id": tool_id, "content": result.content}]
                        })

                    # print("---------------------------------------")
                    # print(messages)
                    # print("---------------------------------------")
                    response = self.anthropic.messages.create(
                        model=self.model,
                        max_tokens=self.max_tokens,
                        messages=messages)
                        
                    messages.append({"role": "assistant", "content": response.content})

                if (len(response.content) == 1 and response.content[0].type == "text"):
                    process_query = False
                    print(f"Assistant: {response.content[0].text}")

    async def chat_loop(self):
        print(".:MCP Chatbot Server Started:.")

        while True:
            try:
                query = input("\nUser: ").strip()
                if query.lower() in ['quit', 'exit']:
                    print("...Chat Ended...")
                    break
                await self.process_query(query)
                print("\n")
            except Exception as e:
                print(f"An error occurred: {e}")

    async def connect_to_server_and_run(self):
        server_params = StdioServerParameters(
            command="uv",
            args=["run", self.server_filepath],
            env=None
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                self.session = session
                await session.initialize()

                response = await session.list_tools()

                tools = response.tools
                print("\nConnected to server with tools:", [tool.name for tool in tools])

                self.available_tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    } for tool in response.tools]
                
                await self.chat_loop()

async def main():
    chatbot = ChatbotMCP(server_filepath="dummy_server.py")
    await chatbot.connect_to_server_and_run()

if __name__ == "__main__":
    asyncio.run(main())