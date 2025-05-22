from flask import Flask, request, render_template_string, jsonify
import requests
import logging
import os

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Use environment variables for sensitive data
SHARE_KEY = os.environ.get("VAPI_SHARE_KEY", "edeeca07-1e75-4e0e-9dd2-483557c843ed")
ASSISTANT_ID = os.environ.get("VAPI_ASSISTANT_ID", "2adaf889-b0ec-45fe-b2b3-aaaffcaf65d5")
VAPI_BASE_URL = "https://api.vapi.ai"

INTERVIEW_PAGE = f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\" />
    <title>Interview: {{{{ name }}}}</title>
    <script src=\"https://cdn.tailwindcss.com\"></script>
    <style>
        .bar {{
            position: absolute;
            bottom: 0;
            border-radius: 4px 4px 0 0;
            transition: height 0.05s ease-out;
        }}
        .vapi-widget-button, .vapi-widget-container, .vapi-widget-fab {{
            display: none !important;
        }}
    </style>
</head>
<body class=\"bg-gray-900 text-white p-6 flex flex-col items-center\">
    <h1 class=\"text-4xl font-bold mb-2\">Interview for {{{{ name }}}}</h1>
    <p class=\"text-lg text-gray-400 mb-2\">Job Title: {{{{ job_title }}}}</p>
    <p class=\"text-lg text-gray-400 mb-6\">Position: {{{{ job }}}}</p>
    <!-- Interview Me Button -->
    <button id=\"interviewMeBtn\" class=\"bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded mb-6\" style=\"display: none;\">
        Interview Me 🎤
    </button>
    <!-- Visualizer -->
    <div id=\"visualizer\" class=\"w-full max-w-3xl h-40 bg-gray-800 rounded relative mb-4\"></div>
    <button id=\"startBtn\" class=\"bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded\">
        Start Visualizer
    </button>
    <script>
        // Load Vapi SDK
        const assistantId = '{ASSISTANT_ID}';
        const apiKey = '{SHARE_KEY}';
        let vapiInstance = null;
        let audioContext, analyser, animationId;
        let micSource = null;
        const bars = [];
        const barCount = 64;
        const visualizer = document.getElementById('visualizer');
        for (let i = 0; i < barCount; i++) {{
            const bar = document.createElement('div');
            bar.className = 'bar';
            bar.style.left = `${{(100 / barCount) * i}}%`;
            bar.style.width = `${{100 / barCount - 1}}%`;
            bar.style.background = 'linear-gradient(to top, #3b82f6, #8b5cf6)';
            bar.style.position = 'absolute';
            bar.style.height = '0px';
            visualizer.appendChild(bar);
            bars.push(bar);
        }}
        function startVisualizer() {{
            if (!audioContext || audioContext.state === 'closed') {{
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }}
            if (!analyser) {{
                analyser = audioContext.createAnalyser();
            }}
            function draw() {{
                const dataArray = new Uint8Array(analyser.frequencyBinCount);
                analyser.getByteFrequencyData(dataArray);
                bars.forEach((bar, i) => {{
                    const value = dataArray[i] || 0;
                    bar.style.height = `${{value / 2}}px`;
                }});
                animationId = requestAnimationFrame(draw);
            }}
            draw();
        }}
        async function connectMic() {{
            try {{
                const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                if (!audioContext || audioContext.state === 'closed') {{
                    audioContext = new (window.AudioContext || window.webkitAudioContext)();
                }}
                if (!analyser) {{
                    analyser = audioContext.createAnalyser();
                }}
                micSource = audioContext.createMediaStreamSource(stream);
                micSource.connect(analyser);
                startVisualizer();
            }} catch (err) {{
                console.error('Error accessing microphone:', err);
            }}
        }}
        // Debug: Log all <audio> elements every 2 seconds
        setInterval(() => {{
            const audios = document.querySelectorAll('audio');
            console.log('Audio elements:', audios);
            audios.forEach((audio, idx) => {{
                console.log(`Audio[${{idx}}] src:`, audio.src, audio);
            }});
        }}, 2000);
        // MutationObserver to connect new Vapi assistant audio elements with gain boost
        function connectVapiAudioWithObserver() {{
            const observer = new MutationObserver((mutationsList) => {{
                for (const mutation of mutationsList) {{
                    for (const node of mutation.addedNodes) {{
                        console.log('MutationObserver saw node:', node);
                        if (node.tagName === 'AUDIO') {{
                            try {{
                                if (!window.audioContext || window.audioContext.state === 'closed') {{
                                    window.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                                }}
                                if (!window.analyser) {{
                                    window.analyser = window.audioContext.createAnalyser();
                                }}
                                // Add a gain node to boost assistant audio
                                const gainNode = window.audioContext.createGain();
                                gainNode.gain.value = 2.5; // Adjust as needed

                                const vapiSource = window.audioContext.createMediaElementSource(node);
                                vapiSource.connect(gainNode);
                                gainNode.connect(window.analyser);
                                window.analyser.connect(window.audioContext.destination);
                                startVisualizer();
                                console.log('Connected new assistant audio element to visualizer!');
                            }} catch (e) {{
                                console.log('Error connecting audio element:', e);
                            }}
                        }}
                    }}
                }}
            }});
            observer.observe(document.body, {{ childList: true, subtree: true }});
        }}
        document.getElementById('startBtn').onclick = connectMic;
        (function (d, t) {{
            const s = d.createElement(t);
            s.src = \"https://cdn.jsdelivr.net/gh/VapiAI/html-script-tag@latest/dist/assets/index.js\";
            s.async = true;
            s.defer = true;
            s.onload = () => {{
                vapiInstance = window.vapiSDK.run({{
                    apiKey: apiKey,
                    assistant: assistantId,
                    config: {{ style: {{ display: 'none' }} }}
                }});
                // Hook up Interview Me button
                document.getElementById('interviewMeBtn').onclick = () => {{
                    if (vapiInstance && typeof vapiInstance.startConversation === 'function') {{
                        vapiInstance.startConversation({{
                            message: \"Hello! I'm your virtual interviewer. Let's begin.\"
                        }});
                        // No need for setTimeout, observer will handle audio
                    }}
                }};
                // Start observing for assistant audio
                connectVapiAudioWithObserver();
            }};
            d.head.appendChild(s);
        }})(document, \"script\");
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name")
        job_title = request.form.get("job_title")
        job = request.form.get("job")
        resume = request.files.get("resume")
        # Optionally save/process the resume here
        return render_template_string(INTERVIEW_PAGE, 
            name=name, 
            job_title=job_title,
            job=job, 
            share_key=SHARE_KEY,
            assistant_id=ASSISTANT_ID
        )
    return render_template_string(INDEX_PAGE)

INDEX_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Interview App</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white min-h-screen flex items-center justify-center p-6">
    <form method="POST" enctype="multipart/form-data" class="bg-gray-800 p-8 rounded-lg shadow-md w-full max-w-lg space-y-6">
        <h1 class="text-3xl font-bold mb-4">Candidate Details</h1>
        <input type="text" name="name" placeholder="Candidate Name" required
            class="input-field w-full p-3 rounded bg-gray-700 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500" />
        <input type="text" name="job_title" placeholder="Job Title" required
            class="input-field w-full p-3 rounded bg-gray-700 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500" />
        <input type="text" name="job" placeholder="Job Description" required
            class="input-field w-full p-3 rounded bg-gray-700 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500" />
        <input type="file" name="resume" accept=".pdf,.doc,.docx" required
            class="input-field w-full p-3 rounded bg-gray-700 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500" />
        <button type="submit"
            class="w-full bg-blue-600 hover:bg-blue-700 py-3 rounded font-bold transition duration-300">Submit</button>
    </form>

    <script>
        // Change input background to gray when user finishes entering (on blur)
        document.querySelectorAll('.input-field').forEach(input => {
            input.addEventListener('blur', () => {
                if (input.value || input.type === 'file') {
                    input.style.backgroundColor = '#e5e7eb'; // Tailwind's gray-200
                    input.style.color = 'black';
                }
            });
        });
    </script>
</body>
</html>
"""

@app.route("/vapi-proxy", methods=["POST"])
def vapi_proxy():
    """Proxy endpoint for Vapi API calls"""
    try:
        data = request.get_json()
        endpoint = data.get("endpoint", "")
        method = data.get("method", "POST")
        payload = data.get("payload", {})
        
        headers = {
            "Authorization": f"Bearer {SHARE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Handle different endpoint types
        if endpoint == '/call/web':
            # For initial call creation
            url = f"{VAPI_BASE_URL}/call/web"
        elif '/transcript' in endpoint:
            # For transcript endpoints, use the same base endpoint
            url = f"{VAPI_BASE_URL}/call/web"
            # Add the call ID to the payload
            parts = endpoint.split('/')
            if len(parts) >= 3:
                call_id = parts[2]
                payload['callId'] = call_id
            else:
                return jsonify({"error": "Invalid transcript endpoint format"}), 400
        else:
            # For other endpoints
            url = f"{VAPI_BASE_URL}{endpoint}"
            
        logger.debug(f"Original endpoint: {endpoint}")
        logger.debug(f"Final URL: {url}")
        logger.debug(f"Request method: {method}")
        logger.debug(f"Request headers: {headers}")
        logger.debug(f"Request payload: {payload}")
        
        response = requests.request(method, url, json=payload, headers=headers)
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        logger.debug(f"Response body: {response.text}")
        
        if response.status_code >= 400:
            error_response = {
                "error": f"API request failed: {response.status_code}",
                "details": response.text,
                "url": url,
                "endpoint": endpoint
            }
            logger.error(f"API error: {error_response}")
            return jsonify(error_response), response.status_code
            
        return jsonify(response.json() if response.text else {}), response.status_code
    except Exception as e:
        logger.error(f"Proxy error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/vapi_test", methods=["GET", "POST"])
def vapi_test():
    web_call_url = ""
    if request.method == "POST":
        headers = {
            "Authorization": f"Bearer {SHARE_KEY}",
            "Content-Type": "application/json"
        }
        body = {
            "assistantId": ASSISTANT_ID
        }
        try:
            response = requests.post(f"{VAPI_BASE_URL}/call/web", headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
            web_call_url = data.get("webCallUrl", "No URL returned")
        except Exception as e:
            web_call_url = f"Error: {e}"
    return render_template_string("""
        <html>
        <head><title>Test Vapi Assistant</title></head>
        <body style="font-family:sans-serif; padding: 40px;">
            <h2>🎙️ Vapi Voice Assistant Test</h2>
            <form method="post">
                <button type="submit">Start Call</button>
            </form>
            {% if web_call_url %}
                <p><strong>Call URL:</strong> <a href="{{ web_call_url }}" target="_blank">{{ web_call_url }}</a></p>
            {% endif %}
        </body>
        </html>
    """, web_call_url=web_call_url)

@app.route("/vapi_widget")
def vapi_widget():
    return render_template_string(f"""
        <html>
        <head>
            <title>Test Vapi Assistant Widget</title>
        </head>
        <body style="font-family:sans-serif; padding: 40px;">
            <h2>🎙️ Vapi Voice Assistant Widget Test</h2>
            <!-- Vapi Widget will appear here -->
            <script>
                var vapiInstance = null;
                const assistant = '{ASSISTANT_ID}'; // Your assistant ID
                const apiKey = '{SHARE_KEY}'; // Your Public key from Vapi Dashboard
                const buttonConfig = {{}}; // Optional configuration

                (function (d, t) {{
                  var g = document.createElement(t),
                    s = d.getElementsByTagName(t)[0];
                  g.src =
                    "https://cdn.jsdelivr.net/gh/VapiAI/html-script-tag@latest/dist/assets/index.js";
                  g.defer = true;
                  g.async = true;
                  s.parentNode.insertBefore(g, s);

                  g.onload = function () {{
                    vapiInstance = window.vapiSDK.run({{
                      apiKey: apiKey,
                      assistant: assistant,
                      config: buttonConfig,
                    }});
                  }};
                }})(document, "script");
            </script>
        </body>
        </html>
    """)

if __name__ == "__main__":
    app.run(debug=True)