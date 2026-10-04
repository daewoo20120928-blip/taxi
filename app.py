`        from flask import Flask, render_template_string, request, jsonify
import os

app = Flask(__name__)

rides_db = []
dispatches_db = []

# 기사별 담당 차량 번호판 정보
DRIVERS_INFO = {
    "김기사": "충남 34하 1234",
    "박기사": "충남 72조 5678",
    "이지은 기사": "충남 15보 9012"
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>주식회사 총알택시 - 통합 시스템</title>
    <style>
        body { font-family: sans-serif; margin: 15px; background: #f4f4f9; text-align: center; }
        h1 { color: #333; font-size: 22px; margin-bottom: 5px; }
        .notice { background: #e2e8f0; color: #1a202c; padding: 8px; font-size: 13px; border-radius: 5px; margin-bottom: 15px; font-weight: bold; }
        .box { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 15px; text-align: left; }
        .box h3 { margin-top: 0; color: #0056b3; font-size: 16px; border-bottom: 2px solid #eee; padding-bottom: 5px; }
        input, select { width: 100%; padding: 10px; margin: 5px 0 10px 0; box-sizing: border-box; border: 1px solid #ccc; border-radius: 5px; }
        button { width: 100%; padding: 12px; font-size: 15px; margin: 5px 0; cursor: pointer; border: none; border-radius: 5px; font-weight: bold; }
        .btn-primary { background: #007bff; color: white; }
        .btn-start { background: #28a745; color: white; }
        .btn-stop { background: #dc3545; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        ul { list-style: none; padding: 0; }
        li { background: #e9ecef; padding: 8px; margin-bottom: 6px; border-radius: 5px; font-size: 13px; }
        .center { text-align: center; }
        .surcharge-group { display: flex; gap: 5px; margin-bottom: 10px; }
        .surcharge-btn { flex: 1; padding: 8px; font-size: 12px; border: 1px solid #ccc; background: #fff; border-radius: 5px; cursor: pointer; }
        .surcharge-btn.active { background: #ffc107; font-weight: bold; border-color: #e0a800; }
        .slider-container { margin: 15px 0; text-align: left; }
        .slider-container label { font-size: 13px; font-weight: bold; }
        input[type=range] { width: 100%; cursor: pointer; }
        .hidden { display: none; }
        .badge { background: #17a2b8; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px; }
    </style>
</head>
<body>
    <h1>🚗 주식회사 총알택시</h1>
    <div class="notice">"주식회사 총알택시 - 상업적 이득을 취하지 않는 비영리 공익 서비스"</div>

    <!-- [1] 직원 로그인 섹션 -->
    <div class="box" id="login-section">
        <h3>👤 직원(기사) 로그인</h3>
        <label>기사 선택</label>
        <select id="login-driver">
            <option value="김기사">김기사</option>
            <option value="박기사">박기사</option>
            <option value="이지은 기사">이지은 기사</option>
        </select>
        <button class="btn-primary" onclick="driverLogin()">기사 로그인</button>
        <button class="btn-secondary" onclick="openAdminMode()">관리자 모드 접속</button>
    </div>

    <!-- [2] 기사 전용 업무 화면 (로그인 후 표시) -->
    <div class="box hidden" id="driver-workspace">
        <h3>🚕 기사 업무 전용 화면</h3>
        <p>접속 기사: <span id="current-driver-name" style="font-weight:bold; color:#0056b3;"></span></p>
        <p>내 담당 차량 번호판: <span id="current-plate" class="badge"></span></p>
        <button class="btn-secondary" onclick="driverLogout()" style="margin-top:10px;">로그아웃 / 다른 기사 선택</button>
    </div>

    <!-- [3] 스마트 미터기 & 시뮬레이터 -->
    <div class="box center">
        <h3>⏱️ 스마트 미터기 & 시뮬레이터</h3>
        <p style="margin:5px 0; font-size:14px;">상태: <span id="status" style="color: blue; font-weight:bold;">대기 중</span></p>
        <p style="margin:5px 0;">요금: <span id="fare" style="font-size: 26px; font-weight: bold; color: #d9534f;">4,800</span>원</p>
        <p style="margin:3px 0; font-size:13px; color:#555;">이동 거리: <span id="distance">0.0</span> km</p>

        <div style="margin-top: 10px;">
            <p style="font-size:12px; font-weight:bold; margin-bottom:5px; text-align:left;">할증 설정:</p>
            <div class="surcharge-group">
                <button type="button" class="surcharge-btn active" id="s-normal" onclick="setSurcharge(1)">일반(100%)</button>
                <button type="button" class="surcharge-btn" id="s-night" onclick="setSurcharge(1.2)">심야/시계외(20%)</button>
                <button type="button" class="surcharge-btn" id="s-complex" onclick="setSurcharge(1.4)">복합할증(40%)</button>
            </div>
        </div>

        <div class="slider-container">
            <label>주행 시뮬레이터 속도: <span id="speed-val">0</span> km/h</label>
            <input type="range" id="speed-slider" min="0" max="100" value="0" oninput="updateSpeed(this.value)">
        </div>

        <button class="btn-start" onclick="startRide()">운행 시작</button>
        <button class="btn-stop" onclick="endRide()">운행 종료 및 저장</button>
    </div>

    <!-- [4] 관리자 모드 섹션 (관리자 접속 시에만 표시) -->
    <div class="box hidden" id="admin-section" style="border: 2px solid #007bff;">
        <h3 style="color: #dc3545;">🛠️ 관리자 모드 시스템</h3>
        <button class="btn-secondary" onclick="closeAdminMode()" style="margin-bottom:15px;">관리자 모드 닫기</button>
        
        <h4 style="font-size:14px; margin-bottom:5px;">📞 신규 배차 등록 (관리자용)</h4>
        <label>출발지</label>
        <input type="text" id="admin-start" placeholder="예: 온양온천역">
        <label>목적지</label>
        <input type="text" id="admin-end" placeholder="예: 아산 시청">
        <label>담당 기사 배정</label>
        <select id="admin-driver">
            <option value="김기사">김기사 (충남 34하 1234)</option>
            <option value="박기사">박기사 (충남 72조 5678)</option>
            <option value="이지은 기사">이지은 기사 (충남 15보 9012)</option>
        </select>
        <button class="btn-primary" onclick="adminCreateDispatch()">배차 접수 등록</button>

        <h4 style="font-size:14px; margin-top:20px; margin-bottom:5px;">📋 전체 배차 현황 관리</h4>
        <ul id="admin-dispatch-list">불러오는 중...</ul>

        <h4 style="font-size:14px; margin-top:20px; margin-bottom:5px;">📋 전체 운행 완료 기록</h4>
        <ul id="admin-ride-list">불러오는 중...</ul>
    </div>

    <script>
        let isRunning = false;
        let baseFare = 4800;
        let fare = 4800;
        let distance = 0.0;
        let rate = 1.0;
        let speed = 0;
        let timer = null;

        function driverLogin() {
            const driver = document.getElementById('login-driver').value;
            fetch('/get_plate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ driver: driver })
            })
            .then(res => res.json())
            .then(data => {
                document.getElementById('current-driver-name').innerText = data.driver;
                document.getElementById('current-plate').innerText = data.plate;
                document.getElementById('login-section').classList.add('hidden');
                document.getElementById('driver-workspace').classList.remove('hidden');
                alert(data.driver + "님 환영합니다! 배정된 차량 번호판: " + data.plate);
            });
        }

        function driverLogout() {
            document.getElementById('login-section').classList.remove('hidden');
            document.getElementById('driver-workspace').classList.add('hidden');
        }

        function openAdminMode() {
            const pwd = prompt("관리자 비밀번호를 입력하세요 (기본: 1234):");
            if (pwd === "1234") {
                document.getElementById('admin-section').classList.remove('hidden');
                loadAdminData();
                alert("관리자 모드로 접속되었습니다.");
            } else if (pwd !== null) {
                alert("비밀번호가 틀렸습니다!");
            }
        }

        function closeAdminMode() {
            document.getElementById('admin-section').classList.add('hidden');
        }

        function setSurcharge(val) {
            rate = val;
            document.querySelectorAll('.surcharge-btn').forEach(btn => btn.classList.remove('active'));
            if(val === 1) document.getElementById('s-normal').classList.add('active');
            else if(val === 1.2) document.getElementById('s-night').classList.add('active');
            else if(val === 1.4) document.getElementById('s-complex').classList.add('active');
        }

        function updateSpeed(val) {
            speed = parseInt(val);
            document.getElementById('speed-val').innerText = speed;
        }

        function updateUI() {
            document.getElementById('fare').innerText = Math.floor(fare).toLocaleString();
            document.getElementById('distance').innerText = distance.toFixed(1);
            document.getElementById('status').innerText = isRunning ? "운행 중" : "대기 중";
        }

        function startRide() {
            if (isRunning) return;
            isRunning = true;
            fare = baseFare;
            distance = 0.0;
            updateUI();

            timer = setInterval(() => {
                if (isRunning) {
                    if (speed > 0) {
                        let addKm = (speed / 3600) * 3;
                        distance += addKm;
                        fare = baseFare + (distance * 1200 * rate);
                    }
                    updateUI();
                }
            }, 1000);
        }

        function endRide() {
            if (!isRunning) return;
            isRunning = false;
            clearInterval(timer);

            let activeDriver = document.getElementById('current-driver-name').innerText || "미지정 기사";

            fetch('/save_ride', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fare: Math.floor(fare), distance: distance.toFixed(1), driver: activeDriver })
            })
            .then(res => res.json())
            .then(data => {
                alert("운행 기록이 저장되었습니다!");
                if(!document.getElementById('admin-section').classList.contains('hidden')) {
                    loadAdminData();
                }
                fare = 4800;
                distance = 0.0;
                updateUI();
            });
        }

        function adminCreateDispatch() {
            const start = document.getElementById('admin-start').value;
            const end = document.getElementById('admin-end').value;
            const driver = document.getElementById('admin-driver').value;

            if(!start || !end) {
                alert("출발지와 목적지를 입력해주세요!");
                return;
            }

            fetch('/save_dispatch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ start: start, end: end, driver: driver })
            })
            .then(res => res.json())
            .then(data => {
                alert("배차가 등록되었습니다!");
                document.getElementById('admin-start').value = '';
                document.getElementById('admin-end').value = '';
                loadAdminData();
            });
        }

        function loadAdminData() {
            // 배차 목록 불러오기
            fetch('/dispatches')
            .then(res => res.json())
            .then(data => {
                let listHtml = '';
                if(data.length === 0) listHtml = '<li>등록된 배차가 없습니다.</li>';
                data.forEach((d) => {
                    listHtml += `<li><b>[담당: ${d.driver}]</b> ${d.start} ➔ ${d.end} <br><span style="color:#666; font-size:11px;">접수: ${d.time}</span></li>`;
                });
                document.getElementById('admin-dispatch-list').innerHTML = listHtml;
            });

            // 운행 기록 불러오기
            fetch('/rides')
            .then(res => res.json())
            .then(data => {
                let listHtml = '';
                if(data.length === 0) listHtml = '<li>저장된 운행 기록이 없습니다.</li>';
                data.forEach((r, index) => {
                    listHtml += `<li>기록 #${index+1} [기사: ${r.driver}] - 요금: ${r.fare.toLocaleString()}원 (${r.distance}km) <br><span style="color:#666; font-size:11px;">${r.time}</span></li>`;
                });
                document.getElementById('admin-ride-list').innerHTML = listHtml;
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_plate', methods=['POST'])
def get_plate():
    data = request.json
    driver = data.get('driver')
    plate = DRIVERS_INFO.get(driver, "차량 번호 미등록")
    return jsonify({'driver': driver, 'plate': plate})

@app.route('/save_ride', methods=['POST'])
def save_ride():
    data = request.json
    from datetime import datetime
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    ride_record = {
        'fare': data.get('fare'),
        'distance': data.get('distance'),
        'driver': data.get('driver'),
        'time': current_time
    }
    rides_db.append(ride_record)
    return jsonify({'success': True})

@app.route('/rides', methods=['GET'])
def get_rides():
    return jsonify(rides_db)

@app.route('/save_dispatch', methods=['POST'])
def save_dispatch():
    data = request.json
    from datetime import datetime
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    dispatch_record = {
        'start': data.get('start'),
        'end': data.get('end'),
        'driver': data.get('driver'),
        'time': current_time
    }
    dispatches_db.append(dispatch_record)
    return jsonify({'success': True})

@app.route('/dispatches', methods=['GET'])
def get_dispatches():
    return jsonify(dispatches_db)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
