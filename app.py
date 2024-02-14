import gradio as gr
from typing import Optional, Tuple
from queue import Empty, Queue
from threading import Thread
from bot.web_scrapping.crawler_and_indexer import content_crawler_and_index
from bot.utils.callbacks import QueueCallback
from bot.utils.constanst import set_api_key, stop_api_key
from bot.utils.show_log import logger
from bot.web_scrapping.default import *
from langchain.chat_models import ChatOpenAI
from langchain.prompts import HumanMessagePromptTemplate
from langchain.schema import AIMessage, BaseMessage, HumanMessage, SystemMessage


def apply_api_key(api_key):
    api_key = set_api_key(api_key=api_key)
    return f'Successfully set {api_key}'


human_message_prompt_template = HumanMessagePromptTemplate.from_template("{text}")


def bot_learning(urls, file_formats, llm, prompt, chat_mode=False):
    index = content_crawler_and_index(url=str(urls), llm=llm, prompt=prompt, file_format=file_formats)
    if chat_mode:
        return index
    else:
        return 'Training Completed'


def chat_start(
        chat: Optional[ChatOpenAI],
        message: str,
        chatbot_messages: ChatHistory,
        messages: List[BaseMessage], ) -> Tuple[str, str, ChatOpenAI, ChatHistory, List[BaseMessage]]:
    if not chat:
        queue = Queue()
        chat = ChatOpenAI(
            model_name=MODELS_NAMES[0],
            temperature=DEFAULT_TEMPERATURE,
            streaming=True,
            callbacks=([QueueCallback(queue)])
        )
    else:
        queue = chat.callbacks[0].queue

    job_done = object()
    messages.append(HumanMessage(content=f':{message}'))
    chatbot_messages.append((message, ""))
    index = bot_learning(urls='NO_URL', file_formats='txt', llm=chat, prompt=message, chat_mode=True)

    def query_retrieval():
        response = index.query()
        chatbot_message = AIMessage(content=response)
        messages.append(chatbot_message)
        queue.put(job_done)

    t = Thread(target=query_retrieval)
    t.start()
    content = ""
    while True:
        try:
            next_token = queue.get(True, timeout=1)
            if next_token is job_done:
                break
            content += next_token
            chatbot_messages[-1] = (message, content)
            yield chat, "", chatbot_messages, messages
        except Empty:
            continue
    messages.append(AIMessage(content=content))
    return chat, "", chatbot_messages, messages


def system_prompt_handler(value: str) -> str:
    return value


def on_clear_button_click(system_prompt: str) -> Tuple[str, List, List]:
    return "", [], [SystemMessage(content=system_prompt)]


def on_apply_settings_button_click(
        system_prompt: str, model_name: str, temperature: float
):
    logger.info(
        f"Applying settings: model_name={model_name}, temperature={temperature}"
    )
    chat = ChatOpenAI(
        model_name=model_name,
        temperature=temperature,
        streaming=True,
        callbacks=[QueueCallback(Queue())],
        max_tokens=1000,
    )
    chat.callbacks[0].queue.empty()
    return chat, *on_clear_button_click(system_prompt)


def main():
    with gr.Blocks() as demo:
        system_prompt = gr.State(default_system_prompt)
        messages = gr.State([SystemMessage(content=default_system_prompt)])
        chat = gr.State(None)

        with gr.Column(elem_id="col_container"):
            gr.Markdown("# Welcome to OWN-GPT! 🤖")
            gr.Markdown(
                "Demo Chat Bot Platform"
            )

            chatbot = gr.Chatbot()
            with gr.Column():
                message = gr.Textbox(label="Type some message")
                message.submit(
                    chat_start,
                    [chat, message, chatbot, messages],
                    [chat, message, chatbot, messages],
                    queue=True,
                )
                message_button = gr.Button("Submit", variant="primary")
                message_button.click(
                    chat_start,
                    [chat, message, chatbot, messages],
                    [chat, message, chatbot, messages],
                )
            with gr.Column():
                learning_status = gr.Textbox(label='Training Status')
                url = gr.Textbox(label="URL to Documents")
                file_format = gr.Textbox(label="Set your file format:", placeholder='Example: pdf, txt')
                url.submit(
                    bot_learning,
                    [url, file_format, chat, message],
                    [learning_status]
                )
                training_button = gr.Button("Training", variant="primary")
                training_button.click(
                    bot_learning,
                    [url, file_format, chat, message],
                    [learning_status]
                )
            with gr.Row():
                with gr.Column():
                    clear_button = gr.Button("Clear")
                    clear_button.click(
                        on_clear_button_click,
                        [system_prompt],
                        [message, chatbot, messages],
                        queue=False,
                    )
                with gr.Accordion("Settings", open=False):
                    model_name = gr.Dropdown(
                        choices=MODELS_NAMES, value=MODELS_NAMES[0], label="model"
                    )
                    temperature = gr.Slider(
                        minimum=0.0,
                        maximum=1.0,
                        value=0.7,
                        step=0.1,
                        label="temperature",
                        interactive=True,
                    )
                    apply_settings_button = gr.Button("Apply")
                    apply_settings_button.click(
                        on_apply_settings_button_click,
                        [system_prompt, model_name, temperature],
                        [chat, message, chatbot, messages],
                    )
            with gr.Row():
                with gr.Column():
                    status = gr.Textbox(label='API KEY STATUS')
                    api_key_set = gr.Textbox(label='Set your OPENAI API KEY')
                    api_key_set_button = gr.Button("Set API key")
                    api_key_set_button.click(
                        apply_api_key,
                        [api_key_set],
                        [status]
                    )
                with gr.Column():
                    status_2 = gr.Textbox(label='STOP API KEY STATUS')
                    stop_api_button = gr.Button('Stop API key')
                    stop_api_button.click(
                        stop_api_key,
                        [],
                        [status_2])
            with gr.Column():
                system_prompt_area = gr.TextArea(
                    default_system_prompt, lines=4, label="prompt", interactive=True
                )
                system_prompt_area.input(
                    system_prompt_handler,
                    inputs=[system_prompt_area],
                    outputs=[system_prompt],
                )
                system_prompt_button = gr.Button("Set")
            system_prompt_button.click(
                on_apply_settings_button_click,
                [system_prompt, model_name, temperature],
                [chat, message, chatbot, messages],
            )

    return demo


if __name__ == '__main__':
    demo = main()
    demo.queue()
    demo.launch(share=True)
    