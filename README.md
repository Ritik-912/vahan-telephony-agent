# Vahan telephony bot agent

This agent is made using **`pipecat-ai-flows`** and **`plivo`** is used as telephony service provider.

This is an outbounding calling agent that provides endpoint for sending a number and then it calls that number ask the reciever about there interest and availability of driving license, then sends back the conversation and summary in json format.

* For Speech to Text **`Deepgram`** is used.
* For Conversation Text Processing and Large Language Model **`OpenAI`** is used.
* For Text to Speech **`ElevenLabs`** is used.

Sample Conversation responses are as follows:-

---

```json
{
  "userInterest": "yes",
  "haveLicense": "no",
  "conversation": "[{'role': 'user', 'content': 'Call.'}, {'role': 'assistant', 'tool_calls': [{'id': 'call_iVGWEO5vJMthqp43qFAFVrcM', 'function': {'name': 'toIntroductionNode', 'arguments': '{}'}, 'type': 'function'}]}, {'role': 'assistant', 'content': 'Namaste! I am Ritik from Vah an aur mere paas aapke liye ek badhiya job offer hai. Kya aap job k baare m janna chahte hai?'}, {'role': 'user', 'content': 'Hello?'}, {'role': 'assistant', 'tool_calls': [{'id': 'call_5M1vzAn4RbbYJNM9ZVoGY6aV', 'function': {'name': 'toInterestNode', 'arguments': '{}'}, 'type': 'function'}]}, {'role': 'assistant', 'content': 'Is job mein aapko delivery person ki position ke liye kaam karna hoga, j ahan aap companies jaise Zomato, Swiggy, aur similar ones ke liye delivery karte hain. Kya aap iss job mein interested hai?'}, {'role': 'user', 'content': 'High interested.'}, {'role': 'assistant', 'tool_calls': [{'id': 'call_CVeujFplFnGJVKNU34tdpEOJ', 'function': {'name': 'setInterest', 'arguments': '{\"isInterest\": \"yes\"}'}, 'type': 'function'}]}, {'role': 'assistant', 'content': 'Kya aapke paas drivin g license hai?'}, {'role': 'user', 'content': 'Hello. Power on.'}, {'role': 'assistant', 'tool_calls': [{'id': 'call_ftMk6u5NZ9stVjRdjcgGGaOJ', 'function': {'name': 'setLicense', 'arguments': '{\"isLicense\": \"no\"}'}, 'type': 'function'}]}, {'role': 'assistant', 'content': 'Jaankari k liye dhany awaad, aapka din shubh ho!'}]"
}
```

---

```json
{
  "userInterest": "no",
  "haveLicense": null,
  "conversation": "[{'role': 'user', 'content': 'Hello?'}, {'role': 'assistant', 'content': 'Namaste! Kya aap mujhe soon p aa rahe hain?'}, {'role': 'user', 'content': 'Hello?'}, {'role': 'assistant', 'tool_calls': [{'id': 'call_jZkTO3sQojaaqLHbCCUo5cjZ', 'function': {'name': 'toIntroductionNode', 'arguments': '{}'}, 'type': 'function'}]}, {'role': 'assistant', 'content': 'I'}, {'role': 'user', 'content': 'Hello?'}, {'role': 'assistant', 'content': 'I am Ritik from Va han aur mere paas aapke liye ek badhiya job offer hai. Kya aap job ke baare mein janna chahte hain?'}, {'role': 'user', 'content': 'Hello?'}, {'role': 'assistant', 'content': 'Namaste! Kya aap mujhe soon paa rahe hain?'}, {'role': 'user', 'content': 'How may I contact you?'}, {'role': 'assistant', 'content': 'Aap mujhe yahan par h i baat karke contact kar sakte hain. Kya aap job ke baare mein janna chahte hain?'}, {'role': 'user', 'content': 'Please.'}, {'role': 'assistant', 'tool_calls': [{'id': 'call_Wm42ZBkQUxugXcCOGT0T7g4b', 'function': {'name': 'toInterestNode', 'arguments': '{}'}, 'type': 'function'}]}, {'role': 'assistant', 'content': 'Yeh job delivery pe rson ki hai, companies jaise Zomato, Swiggy aur similar ones ke liye. Kya aap iss job mein interested hain?'}, {'role': 'user', 'content': \"Oh, no. Actually, am I interested to know you or the like me further to I'll inform you.\"}, {'role': 'assistant', 'tool_calls': [{'id': 'call_QQZsFDxQy841CiiShCgn7QB5', 'function': {'name': 'setInterest', 'arguments': '{\"isInterest\": \"no\"}'}, 'type': 'function'}]}, {'role': 'assistant', 'content': 'Jaankari k liye dhany awaad, aapka din shubh ho!'}]"
}
```

The project was initialised as follows:-

```bash
uv init vahan-telephony-agent
cd vahan-telephony-agent
uv venv --python 3.12
source .venv/bin/activate
uv add "pipecat-ai[deepgram, elevenlabs, openai, silero]" pipecat-ai-flows python-dotenv plivo fastapi "uvicorn[standard]"
```

Then all code is in main.py and the important required API keys are to be placed in **`.env`** file whose format can be easily seen from **`.env.example`** file.

For plivo to stream the audio responses to public url, we created ngrok server instance that sends all requests coming to that url to our localhost port in which our application is listening.

To run and execute the app follow below steps:-

```bash
git clone https://github.com/Ritik-912/vahan-telephony-agent
cd vahan-telephony-agent
uv sync # or pip install -r requirements.txt `Python version >= 3.12`
```

Add API Keys in `.env` file, then create account on ngrok, install ngrok into your device, add ngrok auth-token to your system and run the following command into seperate terminal window.

```bash
ngrok http http://localhost:8080 # port value is dependent on which our app is listening
```

Then command terminal app will be running that shows an url ending with `ngrok.app`, Paste the url in `main.py` as the value of *`PUBLIC_URL`*.
Now in the same terminal in which performed git cloning and uv sync, just run the `main.py`

```bash
python main.py # or uv run python main.py
```