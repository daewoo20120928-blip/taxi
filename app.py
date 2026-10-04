from flask import Flask, render_template_string, request, jsonify
import os

app = Flask(__name__)

rides_db = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>택시 미터기 & 공유</title>
    <style>
        body { font-family: sans-serif; margin: 20px; background: #f4f4f9; text-align: center; }
        h1 { color: #333; }
        .box { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }
        button { padding: 12px 20px; font-size: 16px; margin: 5px; cursor: pointer; border: none; border-radius: 5px; }
        .btn-start { background: #28a745; color: white; }
        .btn-end { background: #dc3545; color: white; }
        .btn-surcharge { background: #ffc107; color: black; }
        ul { list-style: none; padding: 0; text-align: left; }
        li { background: #e9ecef; padding: 10px; margin-bottom: 5px; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>🚗 실시간 택시 미터기</h1>
    
    <div class="box">
        <h3>상태: <span id="status" style="color: blue;">대기 중</span></h3>
        <p>요금: <span id="fare" style="font-size: 24px; font-weight: bold;">0</span>원</p>
        <button class="btn-start" onclick="startRide()">운행 시작</button>
        <button class="btn-surcharge" onclick="toggleSurcharge()">할증 켜기/끄기</button>
        <button class="btn-end" onclick="endRide()">운행 종료 및 저장</button>
    </div>

    <div class="box">
        <h3>📋 서버에 저장된 운행 기록</h3>
        <ul id="ride-list"></ul>
    </div>

    <script>
        let isRunning = false;
        let fare = 0;
        let surcharge = false;
        let timer = null;

        function updateUI() {
            document.getElementById('fare').innerText = fare.toLocaleString();
            document.getElementById('status').innerText = isRunning ? (surcharge ? "운행 중 (할증 적용)" : "운행 중") : "대기 중";
        }

        function startRide() {
            if (isRunning) return;
            isRunning = true;
            fare = 3800;
            updateUI();
            timer = setInterval(() => {
                if (isRunning) {
                    fare += surcharge ? 130 : 100;
                    updateUI();
                }
            }, 1000);
        }

        function toggleSurcharge() {
            surcharge = !surcharge;
            alert(surcharge ? "할증이 켜졌습니다." : "할증이 꺼졌습니다.");
            updateUI();
        }

        function endRide() {
            if (!isRunning) return;
            isRunning = false;
            clearInterval(timer);

            fetch('/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fare: fare, surcharge: surcharge })
            })
            .then(res => res.json())
            .then(data => {
                alert("운행이 저장되었습니다!");
                loadRides();
                fare = 0;
                updateUI();
            });
        }

        function loadRides() {
            fetch('/rides')
            .then(res => res.json())
            .then(data => {
                let listHtml = '';
                data.forEach((r, index) => {
                    listHtml += `<li>기록 #${index+1} - 요금: ${r.fare.toLocaleString()}원 (${r.time})</li>`;
                });
                document.getElementById('ride-list').innerHTML = listHtml;
            });
        }

        loadRides();
        setInterval(loadRides, 3000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/save', methods=['POST'])
def save_ride():
    data = request.json
    from datetime import datetime
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    ride_record = {
        'fare': data.get('fare'),
        'surcharge': data.get('surcharge'),
        'time': current_time
    }
    rides_db.append(ride_record)
    return jsonify({'success': True})

@app.route('/rides', methods=['GET'])
def get_rides():
    return jsonify(rides_db)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
