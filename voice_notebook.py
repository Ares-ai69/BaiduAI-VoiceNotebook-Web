# -*- coding: utf-8 -*-
# AI语音记事本（网页版·修复播放版）
# 开发者：郑淇元  学号：423830124
from flask import Flask, request, jsonify, send_from_directory
import webbrowser
from aip import AipSpeech
import os
import uuid

app = Flask(__name__, static_folder='static')
os.makedirs('static', exist_ok=True)  # 自动创建静态文件目录

# ===================== 你的百度AI密钥（已填好）=====================
APP_ID = '122671678'
API_KEY = '2ODlxkfIlMhqxoTMSZIK9ETW'
SECRET_KEY = 'bWvYTrnv7SDpKSprlosX9GNP2KubBTLu'
# ================================================================

client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)


# 首页
@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AI语音记事本 - 郑淇元 423830124</title>
    <style>
        * {box-sizing: border-box; font-family: "Microsoft Yahei", sans-serif;}
        body {padding: 30px; max-width: 800px; margin: 0 auto; background: #f5f5f5;}
        .card {background: #fff; padding: 25px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);}
        h2 {color: #2c3e50; margin-top: 0;}
        .info {color: #7f8c8d; margin-bottom: 20px;}
        textarea {width: 100%; height: 80px; padding: 10px; font-size: 16px; border: 1px solid #ddd; border-radius: 4px; resize: vertical;}
        button {padding: 10px 20px; margin: 15px 0; background: #3498db; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 16px;}
        button:hover {background: #2980b9;}
        .result {margin: 10px 0; padding: 12px; background: #f8f9fa; border-radius: 4px; min-height: 20px;}
        audio {width: 100%; margin-top: 10px; display: none;}
        input[type="file"] {padding: 8px 0;}
    </style>
</head>
<body>
    <div class="card">
        <h2>AI语音记事本（网页版）</h2>
        <div class="info">开发者：郑淇元 &nbsp;&nbsp; 学号：423830124</div>
    </div>

    <div class="card">
        <h3>1. 文字转语音</h3>
        <textarea id="text" placeholder="输入要合成的文字...">今天天气真好</textarea>
        <br>
        <button onclick="tts()">生成语音</button>
        <div class="result" id="tts_result"></div>
        <audio id="player" controls>
    </div>

    <div class="card">
        <h3>2. 语音转文字（上传WAV音频）</h3>
        <input type="file" id="audiofile" accept=".wav">
        <button onclick="asr()">开始识别</button>
        <div class="result" id="asr_result"></div>
    </div>

    <script>
        // 文字转语音
        async function tts() {
            const text = document.getElementById("text").value.trim();
            if (!text) {
                alert("请输入要合成的文字！");
                return;
            }
            const resultEl = document.getElementById("tts_result");
            const playerEl = document.getElementById("player");
            resultEl.innerText = "语音生成中...";
            playerEl.style.display = "none";

            try {
                const res = await fetch("/tts", {
                    method: "POST",
                    headers: {"Content-Type": "application/x-www-form-urlencoded"},
                    body: "text=" + encodeURIComponent(text)
                });
                const data = await res.json();
                resultEl.innerText = data.msg;

                if (data.code === 200 && data.url) {
                    // 正确挂载音频并显示播放器
                    playerEl.src = data.url;
                    playerEl.style.display = "block";
                    playerEl.load(); // 强制加载音频
                }
            } catch (err) {
                resultEl.innerText = "请求失败，请重试";
                console.error(err);
            }
        }

        // 语音转文字
        async function asr() {
            const fileInput = document.getElementById("audiofile");
            const file = fileInput.files[0];
            if (!file) {
                alert("请先选择WAV音频文件！");
                return;
            }
            const resultEl = document.getElementById("asr_result");
            resultEl.innerText = "语音识别中...";

            const formData = new FormData();
            formData.append("audio", file);

            try {
                const res = await fetch("/asr", {method: "POST", body: formData});
                const data = await res.json();
                resultEl.innerText = data.text || data.msg;
            } catch (err) {
                resultEl.innerText = "识别失败，请重试";
                console.error(err);
            }
        }
    </script>
</body>
</html>
'''


# 文字转语音接口
@app.route('/tts', methods=['POST'])
def tts():
    text = request.form.get('text', '').strip()
    if not text:
        return jsonify({"code": 400, "msg": "请输入文字"})

    # 调用百度TTS
    result = client.synthesis(text, 'zh', 1, {
        'vol': 5, 'spd': 5, 'pit': 5, 'per': 0
    })

    if not isinstance(result, dict):
        # 生成唯一文件名，保存到static目录（Flask默认静态目录）
        filename = f"{uuid.uuid4().hex}.mp3"
        save_path = os.path.join('static', filename)
        with open(save_path, 'wb') as f:
            f.write(result)
        # 返回正确的静态文件访问路径
        return jsonify({
            "code": 200,
            "msg": "语音生成成功",
            "url": f"/static/{filename}"
        })
    # 错误处理
    return jsonify({
        "code": 500,
        "msg": f"生成失败：{result.get('err_msg', '未知错误')}"
    })


# 语音转文字接口
@app.route('/asr', methods=['POST'])
def asr():
    if 'audio' not in request.files:
        return jsonify({"code": 400, "msg": "请上传音频文件"})

    audio_file = request.files['audio']
    audio_data = audio_file.read()

    # 调用百度ASR
    result = client.asr(audio_data, 'wav', 16000, {'dev_pid': 1537})

    if result.get('err_no') == 0:
        return jsonify({"code": 200, "text": result['result'][0]})
    return jsonify({"code": 500, "msg": f"识别失败：{result.get('err_msg', '未知错误')}"})


# 静态文件访问（Flask自动处理static目录，此路由为兜底）
@app.route('/static/<filename>')
def serve_static(filename):
    return send_from_directory('static', filename)


# 自动打开浏览器
if __name__ == '__main__':
    webbrowser.open("http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)