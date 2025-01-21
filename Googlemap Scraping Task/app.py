# app.py
from flask import Flask, render_template, request, send_file
from waitress import serve
from scraper import scrape_google_maps
from config import Config
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    details_cnt = request.form['details_cnt']
    keywords = request.form['keywords']
    
    output_file = scrape_google_maps(keywords, int(details_cnt))
    
    return render_template('download.html', file_name=output_file)

@app.route('/download/<file_name>')
def download_file(file_name):
    return send_file(
        os.path.join(Config.UPLOAD_FOLDER, file_name),
        as_attachment=True
    )

if __name__ == "__main__":
    # Development
    app.run(host=Config.HOST, port=Config.PORT, debug=True)
    
    # Production
    # serve(app, host=Config.HOST, port=Config.PORT)