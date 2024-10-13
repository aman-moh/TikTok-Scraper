from flask import Flask, render_template, request, flash, url_for

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for flashing messages

@app.route('/', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        tiktok_link = request.form.get('tiktok_link')
        if tiktok_link:
            # Here you would typically process the TikTok link
            # For now, we'll just print it and flash a message
            print(f"Received TikTok link: {tiktok_link}")
            flash('Link submitted successfully!', 'success')
        else:
            flash('Please enter a TikTok link.', 'error')
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)