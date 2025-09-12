from flask import Flask, render_template, request
import requests
import sqlite3
from datetime import datetime
app=Flask(__name__)
def init_db():
    conn=sqlite3.connect('visitors.db')
    c=conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS visitors
               (ip TEXT, asn TEXT, isp TEXT, city TEXT, country TEXT, latitude REAL, longitude REAL,
              user_agent TEXT, browser TEXT, os TEXT, device TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()
def get_stats():
    conn=sqlite3.connect('visitors.db')
    c=conn.cursor()
    c.execute('SELECT country, COUNT(*) as count FROM visitors GROUP BY country')
    country_results=c.fetchall()
    total_visitors=sum(row[1] for row in country_results)
    country_percentages= []
    for country, count in country_results:
        if country and country != 'N/A':
            percentage=(count / total_visitors * 100) if total_visitors > 0 else 0
            country_percentages.append({'country': country, 'count': count, 'percentage': round(percentage, 2)})
    c.execute('SELECT browser, COUNT(*) as count FROM visitors GROUP BY browser')
    browser_results=c.fetchall()
    browser_percentages=[]
    for browser, count in browser_results:
        if browser and browser != 'N/A':
            percentage=(count / total_visitors * 100) if total_visitors > 0 else 0
            browser_percentages.append({'browser': browser, 'count': count, 'percentage': round(percentage, 2)})
    c.execute('SELECT os, COUNT(*) as count FROM visitors GROUP BY os')
    os_results=c.fetchall()
    os_percentages=[]
    for os, count in os_results:
        if os and os != 'N/A':
            percentage=(count / total_visitors * 100) if total_visitors > 0 else 0
            os_percentages.append({'os': os, 'count': count, 'percentage': round(percentage, 2)})
    c.execute('SELECT device, COUNT(*) as count FROM visitors GROUP BY device')
    device_results=c.fetchall()
    device_percentages=[]
    for device, count in device_results:
        if device and device != 'N/A':
            percentage=(count / total_visitors * 100) if total_visitors > 0 else 0
            device_percentages.append({'device': device, 'count': count, 'percentage': round(percentage, 2)})
    conn.close()
    return {
        'country': country_percentages,
        'browser': browser_percentages,
        'os': os_percentages,
        'device': device_percentages,
        'total_visitors': total_visitors
    }
@app.route('/')
def index():
    init_db()
    user_ip=request.remote_addr
    if user_ip == '127.0.0.1':
        try:
            response=requests.get('https://api.ipify.org?format=json')
            response.raise_for_status()
            user_ip=response.json().get('ip', '127.0.0.1')
            print(f"Detected public IP: {user_ip}")
        except Exception as e:
            print(f"Failed to get public IP: {str(e)}")
            user_ip='127.0.0.1'
    try:
        response=requests.get(f'https://ipapi.co/{user_ip}/json/')
        response.raise_for_status()
        ip_data=response.json()
        print(f"API Response: {ip_data}")
    except Exception as e:
        print(f"API Error: {str(e)}")
        ip_data={'error': f"Unable to fetch IP data: {str(e)}"}
    asn=ip_data.get('asn', 'N/A')
    isp=ip_data.get('org', 'N/A')
    city=ip_data.get('city', 'N/A')
    country=ip_data.get('country_name', 'N/A')
    latitude=ip_data.get('latitude', 0)
    longitude=ip_data.get('longitude', 0)
    conn=sqlite3.connect('visitors.db')
    c=conn.cursor()
    c.execute('''INSERT INTO visitors (ip, asn, isp, city, country, latitude, longitude, user_agent, browser, os, device, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (user_ip, asn, isp, city, country, latitude, longitude, 'Unknown', 'Unknown', 'Unknown', 'Unknown',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
    stats=get_stats()
    return render_template('index.html', ip_data=ip_data, stats=stats)
@app.route('/log-user-agent', methods=['POST'])
def log_user_agent():
    data=request.get_json()
    user_agent=data.get('user_agent', 'Unknown')
    browser=data.get('browser', 'Unknown')
    os=data.get('os', 'Unknown')
    device=data.get('device', 'Unknown')
    user_ip=request.remote_addr
    if user_ip =='127.0.0.1':
        try:
            response=requests.get('https://api.ipify.org?format=json')
            user_ip=response.json().get('ip', '127.0.0.1')
        except:
            user_ip='127.0.0.1'
    conn=sqlite3.connect('visitors.db')
    c=conn.cursor()
    c.execute('''UPDATE visitors
                 SET user_agent=?, browser=?, os=?, device=?
                 WHERE ip=? AND timestamp=(SELECT MAX(timestamp) FROM visitors WHERE ip=?)''',
              (user_agent, browser, os, device, user_ip, user_ip))
    conn.commit()
    conn.close()
    return {'status': 'success'}
if __name__ == '__main__':
    app.run(debug=True)
