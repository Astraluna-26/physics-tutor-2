import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
from PIL import Image

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

st.set_page_config(page_title="物理智慧助教", page_icon="⚛️", layout="centered")

@st.cache_resource
def load_avatar(image_path, width=40):
    img = Image.open(image_path)
    w_percent = width / float(img.size[0])
    height = int((float(img.size[1]) * float(w_percent)))
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    return img

st.title("⚛️ 大学物理智慧助教")
st.markdown("> Hi,我是Tina老师,有什么可以帮到你吗？我将通过苏格拉底式提问引导你思考，直到给出正确答案")

with st.sidebar:
    st.header("⚙️ 状态")
    if DEEPSEEK_API_KEY:
        st.success("✅ API已就绪")
    else:
        st.error("❌ 未检测到API Key，请在.env文件中配置")
    st.markdown("---")
    st.caption("📖 使用提示：")
    st.caption("• 输入你的问题")
    st.caption("• 我会用苏格拉底式提问引导你")

if "messages" not in st.session_state:
    st.session_state.messages = []

def display_message(role, content):
    if role == "user":
        col1, col2 = st.columns([8, 1])
        with col1:
            st.markdown(
                f'''
                <div style="text-align: right;">
                    <div style="background-color: #e9ecef; border-radius: 18px; padding: 10px 15px; display: inline-block; text-align: left; max-width: 80%; margin: 5px 0;">
                        {content}
                    </div>
                </div>
                ''',
                unsafe_allow_html=True
            )
        with col2:
            st.image(load_avatar("user.png", width=40), width=40)
    else:
        col1, col2 = st.columns([1, 8])
        with col1:
            st.image(load_avatar("AI.png", width=50), width=50)
        with col2:
            st.markdown(
                f'''
                <div style="background-color: #f1f3f5; border-radius: 18px; padding: 10px 15px; display: inline-block; text-align: left; max-width: 80%; margin: 5px 0;">
                    {content}
                </div>
                ''',
                unsafe_allow_html=True
            )

for msg in st.session_state.messages:
    display_message(msg["role"], msg["content"])

if prompt := st.chat_input("例如：一个质量为2kg的物体从10m高处自由下落，求落地时的速度"):
    if not DEEPSEEK_API_KEY:
        st.error("请先在.env中配置DEEPSEEK_API_KEY")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    display_message("user", prompt)

    system_prompt = """你是一位经验丰富的大学物理教师。请遵循以下原则回答学生的问题：
1. 不要直接给出完整答案，而是通过一系列问题引导学生自己发现解题思路。
2. 鼓励学生先明确已知条件、未知量，选择合适的物理定律。
3. 使用LaTeX格式展示公式，例如 $F=ma$ 或 $$\\int F dt = \\Delta p$$。
4. 如果学生思路有偏差，要温和指出并解释为什么。
5. 讲解要分步骤，每步结束后可以问“你理解了吗？”或者“下一步应该怎么做？”。
6. 回答的最后，可以给一个类似的简单练习供学生巩固。
请开始辅导。"""

    messages_for_api = [{"role": "system", "content": system_prompt}]
    messages_for_api.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-10:]])

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": messages_for_api,
        "temperature": 0.7,
        "max_tokens": 2048,
        "stream": True
    }

    try:
        response = requests.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            stream=True
        )
        if response.status_code != 200:
            st.error(f"API调用失败：{response.status_code}")
            st.stop()

        with st.container():
            col1, col2 = st.columns([1, 8])
            with col1:
                st.image(load_avatar("AI.png", width=50), width=50)
            with col2:
                msg_placeholder = st.empty()
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith("data: "):
                            data_str = line_str[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    full_response += content
                                    msg_placeholder.markdown(
                                        f'''
                                        <div style="background-color: #f1f3f5; border-radius: 18px; padding: 10px 15px; display: inline-block; text-align: left; max-width: 80%; margin: 5px 0;">
                                            {full_response}▌
                                        </div>
                                        ''',
                                        unsafe_allow_html=True
                                    )
                            except:
                                pass
                msg_placeholder.markdown(
                    f'''
                    <div style="background-color: #f1f3f5; border-radius: 18px; padding: 10px 15px; display: inline-block; text-align: left; max-width: 80%; margin: 5px 0;">
                        {full_response}
                    </div>
                    ''',
                    unsafe_allow_html=True
                )

        st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        st.error(f"网络错误：{e}")

if st.button("🗑️ 清空对话"):
    st.session_state.messages = []
    st.rerun()

st.divider()
st.caption("⚛️ created by Tina老师")