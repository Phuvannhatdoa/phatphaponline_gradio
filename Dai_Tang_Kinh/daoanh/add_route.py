with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the '@app.route('/daoanh/panorama/')' line and add home route after it
for i in range(len(lines)):
    if "@app.route('/daoanh/panorama/')" in lines[i]:
        # Insert home route after this line (at i+1)
        home_route = '''@app.route('/daoanh/home')
def home_page():
    from flask import send_from_directory
    return send_from_directory('static', 'home.html')'''

        # Insert after this line
        new_lines = lines[:i+1] + [home_route + '\n'] + lines[i+1:]
        with open('app.py', 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print("SUCCESS: Home route added at line", i+2)
        break
else:
    print("Could not find panorama route")
PYEOF