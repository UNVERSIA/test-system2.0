"""全局悬浮的烷仔 3D 助手。

该组件只负责展示和导航，不直接请求 Coze，避免在浏览器中暴露 PAT。
点击“开始对话”会打开 app.py 中现有的数字人助手标签页。
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

import streamlit as st
from streamlit.components.v1 import html


MODULE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = MODULE_DIR / "assets" / "models" / "wanzi_web.glb"


@st.cache_data(show_spinner=False)
def _model_data_uri(model_path: str, modified_ns: int, size: int) -> str:
    """读取 GLB 并缓存为浏览器可直接加载的 data URI。"""
    del modified_ns, size  # 仅用于文件改变后自动刷新缓存。
    data = Path(model_path).read_bytes()
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:model/gltf-binary;base64,{encoded}"


def _build_html(model_uri: str) -> str:
    model_uri_json = json.dumps(model_uri)

    return f"""
<!doctype html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <script type="importmap">
    {{
      "imports": {{
        "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
        "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"
      }}
    }}
    </script>
    <style>
        :root {{ color-scheme: dark; }}
        * {{ box-sizing: border-box; }}
        html, body {{
            width: 100%; height: 100%; margin: 0; overflow: hidden;
            background: transparent; font-family: Inter, "Microsoft YaHei", sans-serif;
        }}
        #assistant {{
            position: absolute; inset: 0;
            border: 1px solid rgba(151, 137, 255, .48);
            border-radius: 22px;
            background: rgba(16, 18, 28, .94);
            box-shadow: 0 18px 55px rgba(0, 0, 0, .38);
            backdrop-filter: blur(18px);
            overflow: hidden;
        }}
        #dragBar {{
            height: 48px; display: flex; align-items: center; gap: 9px;
            padding: 0 12px; cursor: move; user-select: none;
            background: linear-gradient(135deg, rgba(102,126,234,.92), rgba(118,75,162,.92));
        }}
        #title {{ flex: 1; font-size: 15px; font-weight: 700; color: white; }}
        .status {{ width: 9px; height: 9px; border-radius: 50%; background: #42e695; box-shadow: 0 0 10px #42e695; }}
        .iconBtn {{
            width: 29px; height: 29px; border: 0; border-radius: 9px;
            color: white; background: rgba(255,255,255,.14); cursor: pointer;
        }}
        .iconBtn:hover {{ background: rgba(255,255,255,.25); }}
        #viewer {{ width: 100%; height: 330px; position: relative; touch-action: none; }}
        #viewer canvas {{ display: block; width: 100%; height: 100%; }}
        #loading {{
            position: absolute; inset: 0; display: grid; place-items: center;
            color: #ddd; font-size: 13px; pointer-events: none;
        }}
        #hint {{
            position: absolute; left: 50%; bottom: 8px; transform: translateX(-50%);
            padding: 5px 10px; border-radius: 12px; white-space: nowrap;
            background: rgba(0,0,0,.45); color: #ddd; font-size: 11px; pointer-events: none;
        }}
        #actions {{ padding: 10px 14px 14px; }}
        #greeting {{ margin: 0 0 10px; color: #e9e7ff; font-size: 13px; line-height: 1.55; }}
        #openChat {{
            width: 100%; height: 40px; border: 0; border-radius: 12px; cursor: pointer;
            color: white; font-weight: 700; font-size: 14px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            box-shadow: 0 8px 20px rgba(102,126,234,.25);
        }}
        #openChat:hover {{ filter: brightness(1.1); }}
        #collapsed {{ display: none; position: absolute; inset: 0; cursor: pointer; }}
        #collapsedViewer {{ width: 100%; height: 112px; }}
        #collapsedLabel {{
            position: absolute; left: 5px; right: 5px; bottom: 5px;
            padding: 5px 3px; border-radius: 10px; text-align: center;
            color: white; font-size: 11px; font-weight: 700;
            background: linear-gradient(135deg, rgba(102,126,234,.94), rgba(118,75,162,.94));
        }}
        body.is-collapsed #assistant {{ display: none; }}
        body.is-collapsed #collapsed {{ display: block; }}
        #error {{ display:none; padding: 30px 18px; color:#ffb4b4; text-align:center; font-size:12px; }}
    </style>
</head>
<body>
    <section id="assistant" aria-label="烷仔3D助手">
        <div id="dragBar">
            <span class="status"></span><span id="title">烷仔 · 污水处理助手</span>
            <button id="resetView" class="iconBtn" title="恢复视角">↻</button>
            <button id="minimize" class="iconBtn" title="收起">−</button>
        </div>
        <div id="viewer">
            <div id="loading">正在加载烷仔…</div>
            <div id="error">3D模型加载失败，请检查 wanzi_web.glb。</div>
            <div id="hint">拖动模型旋转 · 滚轮缩放 · 拖动顶部移动窗口</div>
        </div>
        <div id="actions">
            <p id="greeting">你好，我是烷仔。点击下方按钮，随时向我咨询污水处理和网站使用问题。</p>
            <button id="openChat">💬 开始对话</button>
        </div>
    </section>
    <section id="collapsed" title="展开烷仔助手">
        <div id="collapsedViewer"></div>
        <div id="collapsedLabel">点击唤起烷仔</div>
    </section>

    <script type="module">
        import * as THREE from 'three';
        import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
        import {{ GLTFLoader }} from 'three/addons/loaders/GLTFLoader.js';
        import {{ DRACOLoader }} from 'three/addons/loaders/DRACOLoader.js';

        const MODEL_URI = {model_uri_json};
        const frame = window.frameElement;
        const FRAME_EXPANDED = {{ width: 360, height: 500 }};
        const FRAME_COLLAPSED = {{ width: 122, height: 146 }};

        function setFrameBox(width, height) {{
            if (!frame) return;
            Object.assign(frame.style, {{
                position: 'fixed', right: frame.style.right || '22px', bottom: frame.style.bottom || '22px',
                width: width + 'px', height: height + 'px', border: '0',
                background: 'transparent', zIndex: '2147483000', overflow: 'visible'
            }});
            frame.setAttribute('allow', 'fullscreen');
            const wrapper = frame.parentElement;
            if (wrapper) {{
                wrapper.style.height = '0'; wrapper.style.minHeight = '0';
                wrapper.style.margin = '0'; wrapper.style.padding = '0';
            }}
        }}

        function createViewer(host, interactive) {{
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(30, 1, 0.01, 100);
            camera.position.set(0, 0.7, 3.3);
            const renderer = new THREE.WebGLRenderer({{ alpha: true, antialias: true, powerPreference: 'high-performance' }});
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            renderer.outputColorSpace = THREE.SRGBColorSpace;
            renderer.toneMapping = THREE.ACESFilmicToneMapping;
            renderer.toneMappingExposure = 1.05;
            host.prepend(renderer.domElement);

            scene.add(new THREE.HemisphereLight(0xffffff, 0x334155, 2.2));
            const key = new THREE.DirectionalLight(0xffffff, 3.0); key.position.set(3, 4, 4); scene.add(key);
            const rim = new THREE.DirectionalLight(0x8fa7ff, 2.0); rim.position.set(-4, 2, -3); scene.add(rim);

            const controls = new OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true; controls.dampingFactor = .08;
            controls.enablePan = false; controls.enableZoom = interactive;
            controls.autoRotate = !interactive; controls.autoRotateSpeed = 1.1;
            controls.minDistance = 1.5; controls.maxDistance = 5.5;

            let mixer = null;
            const clock = new THREE.Clock();
            const loader = new GLTFLoader();
            const draco = new DRACOLoader();
            draco.setDecoderPath('https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/libs/draco/');
            loader.setDRACOLoader(draco);

            function fitModel(object) {{
                const box = new THREE.Box3().setFromObject(object);
                const size = box.getSize(new THREE.Vector3());
                const center = box.getCenter(new THREE.Vector3());
                object.position.sub(center);
                const maxSize = Math.max(size.x, size.y, size.z) || 1;
                const distance = maxSize / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)));
                camera.position.set(0, maxSize * .08, distance * 1.18);
                camera.near = Math.max(distance / 100, .01); camera.far = distance * 100;
                camera.updateProjectionMatrix(); controls.target.set(0, 0, 0); controls.update();
            }}

            loader.load(MODEL_URI, (gltf) => {{
                const object = gltf.scene; scene.add(object); fitModel(object);
                if (interactive) document.getElementById('loading').style.display = 'none';
                if (gltf.animations?.length) {{
                    mixer = new THREE.AnimationMixer(object);
                    mixer.clipAction(gltf.animations[0]).play();
                }}
            }}, undefined, (error) => {{
                console.error('烷仔模型加载失败', error);
                if (interactive) {{
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('hint').style.display = 'none';
                    document.getElementById('error').style.display = 'block';
                }}
            }});

            function resize() {{
                const width = Math.max(host.clientWidth, 1), height = Math.max(host.clientHeight, 1);
                camera.aspect = width / height; camera.updateProjectionMatrix(); renderer.setSize(width, height, false);
            }}
            new ResizeObserver(resize).observe(host); resize();
            function animate() {{
                requestAnimationFrame(animate); const delta = clock.getDelta();
                if (mixer) mixer.update(delta); controls.update(); renderer.render(scene, camera);
            }}
            animate();
            return {{ reset: () => {{ camera.position.set(0, .7, 3.3); controls.target.set(0,0,0); controls.update(); }} }};
        }}

        setFrameBox(FRAME_EXPANDED.width, FRAME_EXPANDED.height);
        const mainViewer = createViewer(document.getElementById('viewer'), true);
        createViewer(document.getElementById('collapsedViewer'), false);

        document.getElementById('resetView').addEventListener('click', (event) => {{ event.stopPropagation(); mainViewer.reset(); }});
        document.getElementById('minimize').addEventListener('click', () => {{
            document.body.classList.add('is-collapsed'); setFrameBox(FRAME_COLLAPSED.width, FRAME_COLLAPSED.height);
        }});
        document.getElementById('collapsed').addEventListener('click', () => {{
            document.body.classList.remove('is-collapsed'); setFrameBox(FRAME_EXPANDED.width, FRAME_EXPANDED.height);
        }});

        document.getElementById('openChat').addEventListener('click', () => {{
            try {{
                const buttons = [...window.parent.document.querySelectorAll('button[data-baseweb="tab"]')];
                const target = buttons.find(button => button.textContent.includes('数字人助手'));
                if (!target) throw new Error('没有找到数字人助手标签页');
                target.click(); window.parent.scrollTo({{ top: 0, behavior: 'smooth' }});
                document.body.classList.add('is-collapsed'); setFrameBox(FRAME_COLLAPSED.width, FRAME_COLLAPSED.height);
            }} catch (error) {{ console.error(error); alert('请点击页面上方的“数字人助手”标签页。'); }}
        }});

        let dragging = false, startX = 0, startY = 0, startLeft = 0, startTop = 0;
        const dragBar = document.getElementById('dragBar');
        dragBar.addEventListener('pointerdown', (event) => {{
            if (event.target.closest('button') || !frame) return;
            dragging = true; dragBar.setPointerCapture(event.pointerId);
            const rect = frame.getBoundingClientRect(); startX = event.clientX; startY = event.clientY;
            startLeft = rect.left; startTop = rect.top;
        }});
        dragBar.addEventListener('pointermove', (event) => {{
            if (!dragging || !frame) return;
            const maxLeft = Math.max(0, window.parent.innerWidth - frame.offsetWidth);
            const maxTop = Math.max(0, window.parent.innerHeight - frame.offsetHeight);
            const left = Math.min(maxLeft, Math.max(0, startLeft + event.clientX - startX));
            const top = Math.min(maxTop, Math.max(0, startTop + event.clientY - startY));
            frame.style.left = left + 'px'; frame.style.top = top + 'px'; frame.style.right = 'auto'; frame.style.bottom = 'auto';
        }});
        dragBar.addEventListener('pointerup', () => {{ dragging = false; }});
        dragBar.addEventListener('pointercancel', () => {{ dragging = false; }});
    </script>
</body>
</html>
"""


def render_wanzi_3d_assistant(model_path: str | Path = DEFAULT_MODEL_PATH) -> None:
    """在整个 Streamlit 页面右下角挂载一个全局悬浮助手。"""
    path = Path(model_path).resolve()
    if not path.is_file():
        # 只在服务器日志提示，避免破坏原页面布局。
        print(f"[Wanzi3D] 模型不存在：{path}")
        return

    stat = path.stat()
    model_uri = _model_data_uri(str(path), stat.st_mtime_ns, stat.st_size)
    html(_build_html(model_uri), height=1, scrolling=False)

