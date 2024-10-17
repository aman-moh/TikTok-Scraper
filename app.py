from flask import Flask, render_template, request, jsonify
from camel.agents.chat_agent import ChatAgent
from camel.configs.openai_config import ChatGPTConfig
from camel.messages.base import BaseMessage
from camel.models import ModelFactory
from camel.tasks.task import Task
from camel.toolkits import OpenAIFunction, SearchToolkit
from camel.types import ModelPlatformType, ModelType
from camel.workforce import Workforce
import nest_asyncio
import json
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret_key")

nest_asyncio.apply()

# Initialize the search toolkit
search_toolkit = SearchToolkit()
search_tools = [
    OpenAIFunction(search_toolkit.search_google),
    OpenAIFunction(search_toolkit.search_duckduckgo),
]

def create_workforce():
    # Create chat agents
    hook_segmentor = ChatAgent(
        system_message=BaseMessage.make_assistant_message(
            role_name="hook_segmentor",
            content="You are to find the hook of the transcript provided, your output should just be the hook_script and nothing else",
        ),
        model=ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict=ChatGPTConfig().as_dict(),
        ),
        tools=search_tools,
    )

    hook_classifier = ChatAgent(
        system_message=BaseMessage.make_assistant_message(
            role_name="hook_age_classifier",
            content="you need to classify the reading age of the hook and nothing else",
        ),
        model=ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict=ChatGPTConfig().as_dict(),
        ),
        tools=search_tools,
    )

    hook_type_classifier = ChatAgent(
        system_message=BaseMessage.make_assistant_message(
            role_name="hook_type_classifier",
            content="you need to classify the type of the hook and nothing else"
        ),
        model=ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict=ChatGPTConfig().as_dict(),
        ),
    )

    proof_checker_agent = ChatAgent(
        BaseMessage.make_assistant_message(
            role_name="Proof checker agent",
            content="You are you to proof check this tweet",
        ),
        model=ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4O,
            model_config_dict=ChatGPTConfig().as_dict(),
        ),
    )

    # Create and configure the workforce
    workforce = Workforce('packaging_analysis_workforce')

    workforce.add_single_agent_worker(
        "Proof checker agent, an agent that can check for grammer and spelling mistkes in tweets",
        worker=proof_checker_agent,
    ).add_single_agent_worker(
        "hook_classifier, this agent classifys parts of a hook", worker=hook_classifier
    ).add_single_agent_worker(
        "An agent who finds the hook in transcripts", worker=hook_segmentor
    ).add_single_agent_worker(
        "An agent who finds the type hook in transcripts", worker=hook_type_classifier
    )

    return workforce

@app.route('/', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        tiktok_link = request.form.get('tiktok_link')
        if tiktok_link:
            # Here you would typically fetch the transcript from the TikTok link
            # For this example, we'll use a dummy transcript
            transcript = """Hacker funds can be so powerful for growth. Here's what you need to know about hosting hackathons. After hosting my first one, I want to break down what happened and three valuable lessons that I wish on you before. As we did make some mistakes, but in the end, I think it ended up quite unique."""
            
            human_task = Task(
                content=(
                    "You are to do deep analysis on the transcript of a social media video. "
                    "You are to first find the hook of the video and then you should get insights on the hook: (hook type, reading age and hook length). "
                    "The output should be a JSON formatted exactly like this but in JSON format,:\n\n"
                    "{\n"
                    "  \"worker_node\": 139550241668976,\n"
                    "  \"task\": \"assessing the length of hooks to evaluate their effectiveness and engagement potential\",\n"
                    "  \"hook_script\": {\n"
                    "    \"content\": \"Hacker funds can be so powerful for growth. Here's what you need to know about hosting hackathons.\",\n"
                    "    \"sentences\": [\n"
                    "      {\n"
                    "        \"sentence\": \"Hacker funds can be so powerful for growth.\",\n"
                    "        \"length_in_words\": 8\n"
                    "      },\n"
                    "      {\n"
                    "        \"sentence\": \"Here's what you need to know about hosting hackathons.\",\n"
                    "        \"length_in_words\": 9\n"
                    "      }\n"
                    "    ],\n"
                    "    \"total_length_in_words\": 17\n"
                    "  }\n"
                    "}"
                ),
                additional_info=transcript,
                id='0',
            )

            workforce = create_workforce()
            task = workforce.process_task(human_task)
            
            try:
                result = json.loads(task.result)
            except json.JSONDecodeError:
                # If the result is not valid JSON, return it as plain text
                return jsonify({
                    'error': 'Invalid JSON result',
                    'raw_result': task.result
                })
            
            return jsonify(result)
        else:
            return jsonify({'error': 'Please enter a TikTok link.'}), 400
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(port=8080)
