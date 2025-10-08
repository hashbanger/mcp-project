import gradio as gr
import asyncio
from agent import handle_message, ChatContext, init

# Initialize chat context
context = ChatContext(user_name="Prashant")

# Ensure MCP server is connected before handling messages
loop = asyncio.get_event_loop()
loop.run_until_complete(init())

# Async Gradio-compatible wrapper
async def chat_async(message, history):
    response = await handle_message(message, context)
    return response.final_output.message

# Sync wrapper for Gradio
def chat_wrapper(message, history):
    return asyncio.run(chat_async(message, history))

# Gradio UI
with gr.Blocks(title="Jonas Chat Assistant") as demo:
    gr.Markdown("### 💬 Jonas - Your cheerful assistant")
    gr.ChatInterface(chat_wrapper)

# Launch Gradio app
demo.launch()
