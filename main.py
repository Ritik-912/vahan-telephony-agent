# Copyright (c) 2025, Vahan
"""
This is telephony bot agent.
It first defines the flow nodes config and there functions then intializes services and pipeline.
Then it defines the runner and Backend Server for handling the audio streaming between client and bot.
"""
from os import getenv
from fastapi import WebSocket, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pipecat_flows import FlowArgs, FlowManager, NodeConfig, ContextStrategyConfig, ContextStrategy
from pipecat.serializers.plivo import PlivoFrameSerializer
from pipecat.transports.network.fastapi_websocket import FastAPIWebsocketParams, FastAPIWebsocketTransport
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.services.deepgram.stt import DeepgramSTTService, LiveOptions
from pipecat.transcriptions.language import Language
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.pipeline.runner import PipelineRunner
from typing import Literal
from plivo import RestClient
from asyncio import Event
from json import loads
from loguru import logger
from sys import stderr
from dotenv import load_dotenv
from uvicorn import run
load_dotenv(dotenv_path="./.env", stream=None, verbose=True, override=True, interpolate=True, encoding="utf-8")
STT_MODEL = "nova-2-phonecall"
LLM_MODEL = "gpt-4o-mini"
ELEVENLABS_VOICE_ID = "6xtFDpt8a8lTgY0wO0Nb"
TTS_MODEL = "eleven_flash_v2_5"
PUBLIC_URL = ""

logger.remove(handler_id=0)
logger.add(sink=stderr,level="DEBUG")

async def toIntroductionNode(flow_manager: FlowManager) -> tuple[None, NodeConfig]:
    """Function handler that on getting valid response from user move's the conversation logic to the introduction node."""
    logger.debug("Called `toIntroductionNode`")
    return None, create_intro_node()

def create_greeting_node() -> NodeConfig:
    """Initial Node for greeting and waiting for user response"""
    return {
        "name": "greeting",
        "role_messages": [
            {
                "role": "system",
                "content": "You are Ritik, An Outbounding Telephony agent at Vahan.\
                Your task is to know the intent of user in working as an delivery person job and whther \
                they owns driving license or not in case of being interested for doing delivery person job.\
                You have to call a given number, greet them, wait for their response and when they respond\
                you have to introduce them in a mix of hindi and basic english like\
                `I am Ritik from Vahan, Mere paas aapke liye ek badhiya job offer hai.`\
                If user says profanity words or ask any FAQs, answer them accordingly like an polite proffessional telephony agent\
                and then being stick to your point ask them like `kya aap delivery job karne mein interested hain`.\
                Ask this question only when the user ask directly about the job details, don't tell the full response in one go.\
                You have to communicate with user politely and proffessionaly so that user not feels this as artificial conversation.\
                If user gives positive answer that clearly specifies that user is interested then ask them about the availability of driving license like\
                `kya aapke paas driving license hai` and on getting the information finish the conversation with warm and pleasure greeting like\
                `Jaankari k liye dhanyawaad, Aapka din shubh ho!`."
            }
        ],
        "task_messages": [
            {
                "role": "system",
                "content": "Wait for User response. If user respond to you directly and not in there environment then only it will be a valid response for you.\
                If user not speaks anything to you greet them with words like `Hello!` or `Namaste!` or `Namaskarah!` and confirm by asking them whether\
                they are able to listen you or not like `kya aap mujhe soon paa rahe hain`. If user responds to you anything then call the function `toIntroductionNode`."
            }
        ],
        "functions": [toIntroductionNode],
        "pre_actions": [
            {
                "type": "tts_say",
                "text": "Hello!"
            }
        ],
        "respond_immediately": False
    }

async def toInterestNode(flow_manager: FlowManager) -> tuple[None, NodeConfig]:
    """Funtion handler for moving to the interest asking node"""
    logger.debug("Called `toInterestNode`")
    return None, create_interest_node()

def create_intro_node() -> NodeConfig:
    """Introduction to User"""
    return {
        "name": "introduction",
        "task_messages": [
            {
                "role": "system",
                "content": "Introduce yourself to the user in mix of hindi and english language like a casual speaker\
                but being proffessional and polite and tell them that you have an wonderful job opportunity for them.\
                You can Introduce like `I am Ritik from Vahan aur mere paas aapke liye ek badhiya job offer hai`.\
                Then you have to let the user ask about what is Job Opportunity.  If user tells any profanity words\
                or ask any FAQs then reply them your answer relevantly. For any FAQs asked by user like `What is Salary` or `What is working hours`\
                or any other question; answer them as per what is expected from a typical delivery expert job and that they may get the accurate answer\
                from our executives. If the user not ask about the job, then ask Are they willing to know about the job like `Kya aap job k baare m janna chahte hai?`\
                If user asked themselves about the job profile or reply positively to know about the job after you asked them that they want to know about job; then\
                call the funtion `toInterestNode` to move ahead in the conversation."
            }
        ],
        "functions": [toInterestNode]
    }

async def setInterest(flow_manager: FlowManager, isInterest: Literal["yes", "no"]) -> tuple[None, NodeConfig]:
    """Functon handler for setting the interest of user in job opportunity and transitioning to next phase of conversation depending upon the interest."""
    logger.debug("Called `setInterest`")
    flow_manager.state["userInterest"] = isInterest
    if flow_manager.state.get("userInterest") == "yes":
        logger.debug("`userInterest = yes`\n Moving to license node.")
        return None, create_license_node()
    else:
        logger.debug("`userInterest != yes` Moving to end node.")
        return None, create_end_node()

def create_interest_node() -> NodeConfig:
    return {
        "name": "interest",
        "task_messages": [
            {
                "role": "system",
                "content": "Tell user that the job is of deliery person in companies like zomato, swiggy, and similar ones. Be proffessional and polite.\
                You have to maintain a Hindi-English tone because you are talking to a blue collar work candidate. Then Ask the user clearly whether they are interested\
                in this job opportunity or not. You can ask like `Kya aap iss Job mein Interested hai?`. If you got clear response from user regarding their interest\
                in this job opportunity call the function `setInterest` with appropriate keyword argument of `isInterest` with either `yes` or `no` depending upon\
                user's clear response for their interest in this job opportunity for which you have called them."
            }
        ],
        "functions": [setInterest]
    }

async def setLicense(flow_manager: FlowManager, isLicense: Literal["yes", "no"]) -> tuple[None, NodeConfig]:
    """Function handler for setting user's availaibility of driving license and transitioning to the end phase of conversation."""
    flow_manager.state["haveLicense"] = isLicense
    logger.debug("Called `setLicense`")
    return None, create_end_node()

def create_license_node() -> NodeConfig:
    """Asking about availability of driving license"""
    return {
        "name": "license",
        "task_messages": [
            {
                "role": "system",
                "content": "Now as the user is interested for doing delivery person job, you have to ask the user in professionaly politely Hindi-English tone\
                that does they owns a valid driving license, you can ask like `kya aap k paas driving license hai?`. If user didn't give clear answer\
                and ask anything else or with profanity, give them polite proffessional reply and ask and confirm from them clearly about the availability of driving license.\
                If you got clear answer regarding the availabiliy of driving license, then call the function `setLicense` with appropriate keyword argument `isLicense`\
                with value either `yes` or `no` based on user response whenever you got clear indication of user's response about there availaibility of license."
            }
        ],
        "functions": [setLicense]
    }

async def postInfo(args: FlowArgs, flow_manager: FlowManager) -> tuple[None, None]:
    global callData
    logger.debug("Called `postInfo`")
    callData["userInterest"], callData["haveLicense"] = flow_manager.state.get("userInterest"), flow_manager.state.get("haveLicense")
    callData["conversation"] = str([message for message in flow_manager.get_current_context() if message["role"] in ["user", "assistant"]])
    callData["event"].set()
    logger.debug("Conversation Event Completed.")

def create_end_node() -> NodeConfig:
    """Complete conversation with warm greeting and saving the conversation, interest and driving license details."""
    return {
        "name": "end",
        "task_messages": [
            {
                "role": "system",
                "content": "Now as the conversation comes to an end, Thanks the user for there time and greet them for the day.\
                You can greet them like `Jaankaari k liye dhanyawaad, aapka din shubh ho!`."
            }
        ],
        "post_actions": [{"type": "function", "handler": postInfo}]
    }

async def run_bot(websocket: WebSocket, stream_id: str, call_id: str) -> dict:
    """Run bot for a specific call"""
    logger.debug("Intialising Services.")
    plivoFrameSerializer = PlivoFrameSerializer(stream_id=stream_id, call_id=call_id, auth_id=getenv("PLIVO_AUTH_ID"), auth_token=getenv("PLIVO_AUTH_TOKEN"))
    fastApiWStransport = FastAPIWebsocketTransport(websocket=websocket, params=FastAPIWebsocketParams(audio_out_enabled=True,audio_in_enabled=True,vad_analyzer=SileroVADAnalyzer(),serializer=plivoFrameSerializer,session_timeout=30))
    sttProcessor = DeepgramSTTService(api_key=getenv("DEEPGRAM_API_KEY"), live_options=LiveOptions(model=STT_MODEL,language=Language.EN_IN,smart_format=True))
    textProcessor = OpenAILLMService(model=LLM_MODEL,api_key=getenv("OPENAI_API_KEY"),params=OpenAILLMService.InputParams(temperature=0.75))
    llmContextAggregator = textProcessor.create_context_aggregator(OpenAILLMContext())
    ttsProcessor = ElevenLabsTTSService(api_key=getenv("ELEVENLABS_API_KEY"),voice_id=ELEVENLABS_VOICE_ID,model=TTS_MODEL,params=ElevenLabsTTSService.InputParams(language=Language.EN,stability=0.7,similarity_boost=0.8,style=0.5,use_speaker_boost=True,speed=1.1))
    pipeline = Pipeline([fastApiWStransport.input(),sttProcessor,llmContextAggregator.user(),textProcessor,ttsProcessor,fastApiWStransport.output(),llmContextAggregator.assistant()])
    pipelineTask = PipelineTask(pipeline=pipeline,params=PipelineParams(allow_interruptions=True,audio_in_sample_rate=8000,audio_out_sample_rate=8000,enable_metrics=True,enable_usage_metrics=True,report_only_initial_ttfb=True,send_initial_empty_metrics=False))
    flowManager = FlowManager(task=pipelineTask,llm=textProcessor,context_aggregator=llmContextAggregator,context_strategy=ContextStrategyConfig(strategy=ContextStrategy.APPEND,summary_prompt="You are outbounding telephony agent at Vahan, and your task is to call to candidate and ask them whether they are interested in doing delivery person job at companies like swiggy, zomato, etc. and if interested, do they have driving license or not."),transport=fastApiWStransport)
    logger.debug("All Services Initialised successfully.")

    @fastApiWStransport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        """When participant joined at first"""
        logger.debug(f"pipeline flow initialising. With Transport = {transport} \n and Client = {client}")
        await flowManager.initialize(create_greeting_node())

    @fastApiWStransport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        """When participant left the call"""
        logger.debug(f"Call Disconnected. with Transport = {transport} \n and Client = {client}")

    @fastApiWStransport.event_handler("on_session_timeout")
    async def on_session_timeout(transport, client):
        logger.debug(f"Session Timeout. Transport = {transport} \n Client = {client}")

    await PipelineRunner(handle_sigint=True,handle_sigterm=True,force_gc=True).run(task=pipelineTask)

runnerApp = FastAPI(debug=True,title="Vahan Telephony Agent for Interest Classification of given user.",summary="pipecat-ai flows telephony bot agent for asking interest and driving license details from user.",description="Runner app for the Voice AI bot that asks user interest in working as delivery agent and their availaibility of driving license fr a given number and returns their response.")
runnerApp.add_middleware(middleware_class=CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
callData = dict(userInterest=None,haveLicense=None,conversation=None,event=Event())

@runnerApp.post("/callStream")
async def sendCallStream_xml():
    """Endpoint for sending the xml configuration to plivo for setting call streaming"""
    return HTMLResponse(content=f"""<?xml version="1.0" encoding="UTF-8"?><Response><Stream keepCallAlive="true" bidirectional="true" contentType="audio/x-mulaw;rate=8000"> wss://{PUBLIC_URL.replace("https://","")}/ws </Stream></Response>""",media_type="application/xml")

@runnerApp.get(path="/getData/{phone}")
async def getData(phone: str) -> JSONResponse:
    """Call the given number, run bot and return the interest json to the client, The steps would be as follows:
    - dialout
    - run bot
    - return response
    """
    plivoClient = RestClient(auth_id=getenv("PLIVO_AUTH_ID"),auth_token=getenv("PLIVO_AUTH_TOKEN"),timeout=9).calls
    callQueuedId = plivoClient.create(from_=getenv("PLIVO_PHONE_NUMBER"),to_=phone,answer_url=f"{PUBLIC_URL}/callStream",caller_name="VAHAN")["request_uuid"]
    logger.debug(f"Call Initiated with call_uuid={callQueuedId}")
    await callData["event"].wait()
    plivoClient.delete(call_uuid=callQueuedId)
    return JSONResponse(content=dict(userInterest=callData["userInterest"],haveLicense=callData["haveLicense"],conversation=callData["conversation"]),media_type="application/json")

@runnerApp.websocket(path="/ws",name="call_streaming_endpoint")
async def callStreaming(websocket: WebSocket):
    """Handle websocket connection for audio streaming"""
    await websocket.accept()
    init_config = loads(s=await websocket.iter_text().__anext__()).get("start",{})
    streamId, callId = init_config.get("streamId"), init_config.get("callId")
    await run_bot(websocket=websocket,stream_id=streamId,call_id=callId)

if __name__=="__main__":
    run(app=runnerApp,host="127.0.0.1",port=8080)