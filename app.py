from flask import Flask, request, render_template_string
import trimesh

app = Flask(__name__)

# Prices per gram
PRICES = {'PLA': 0.12, 'PETG': 0.12, 'TPU': 0.20}
DENSITY = {'PLA': 1.24, 'PETG': 1.27, 'TPU': 1.20}  # g/cm³

# HTML template with polished styling
HTML = '''
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>3D Print Quote</title>
<style>
body { font-family: Arial, sans-serif; margin: 20px; background-color: #f9f9f9; }
h2 { color: #333; }

#drop-area {
    border: 2px dotted green; /* green dotted border */
    border-radius: 12px;
    padding: 50px;
    text-align: center;
    color: #555;
    cursor: pointer;
    transition: background-color 0.2s, border-color 0.2s;
    background-color: #fff;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    font-size: 18px;
}

#drop-area.dragover {
    background-color: #e6ffe6; /* light green when dragging */
    border-color: darkgreen;
}

select { font-size: 16px; margin-top: 10px; padding: 5px; border-radius: 5px; }

input[type=file] { display: none; }

#submitBtn {
    margin-top: 15px;
    padding: 10px 20px;
    font-size: 16px;
    background-color: #007bff; /* blue button */
    color: #fff;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: background-color 0.2s;
}

#submitBtn:hover {
    background-color: #0056b3;
}

#quote { 
    margin-top: 20px; 
    font-size: 18px; 
    font-weight: bold; 
    display: flex; 
    align-items: center; 
    color: #333;
}

.spinner { 
    border: 4px solid #f3f3f3; 
    border-top: 4px solid #555; 
    border-radius: 50%; 
    width: 20px; 
    height: 20px; 
    animation: spin 1s linear infinite; 
    margin-right: 10px; 
}

@keyframes spin { 
    0% { transform: rotate(0deg); } 
    100% { transform: rotate(360deg); } 
}
</style>
</head>
<body>

<h2>3D Print Instant Quote</h2>

<div id="drop-area">
    Drag & drop your 3D file here or click to select.
    <input type="file" id="fileInput" accept=".stl,.obj,.3mf">
</div>

<div>
Material: 
<select id="materialSelect">
    <option value="PLA">PLA ($0.12/g)</option>
    <option value="PETG">PETG ($0.12/g)</option>
    <option value="TPU">TPU ($0.20/g)</option>
</select>
</div>

<button id="submitBtn">Get Quote</button>

<div id="quote">Quote will appear here</div>

<script>
const dropArea = document.getElementById('drop-area');
const fileInput = document.getElementById('fileInput');
const submitBtn = document.getElementById('submitBtn');
const quoteDiv = document.getElementById('quote');

let selectedFile = null;

dropArea.addEventListener('click', () => fileInput.click());

dropArea.addEventListener('dragover', e => { e.preventDefault(); dropArea.classList.add('dragover'); });
dropArea.addEventListener('dragleave', e => { e.preventDefault(); dropArea.classList.remove('dragover'); });
dropArea.addEventListener('drop', e => {
    e.preventDefault();
    dropArea.classList.remove('dragover');
    if (e.dataTransfer.files.length) selectedFile = e.dataTransfer.files[0];
    quoteDiv.innerText = selectedFile ? `File selected: ${selectedFile.name}` : 'Quote will appear here';
});

fileInput.addEventListener('change', e => {
    if (e.target.files.length) selectedFile = e.target.files[0];
    quoteDiv.innerText = selectedFile ? `File selected: ${selectedFile.name}` : 'Quote will appear here';
});

submitBtn.addEventListener('click', () => {
    if (!selectedFile) { alert('Please select a file first'); return; }
    const material = document.getElementById('materialSelect').value;
    quoteDiv.innerHTML = '<div class="spinner"></div>Calculating...';

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('material', material);

    fetch('/upload', { method: 'POST', body: formData })
    .then(resp => resp.json())
    .then(data => {
        if (data.error) quoteDiv.innerText = `Error: ${data.error}`;
        else quoteDiv.innerText = `${data.weight} g — $${data.price}`;
    })
    .catch(err => quoteDiv.innerText = `Error: ${err}`);
});
</script>

</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files['file']
        material = request.form['material']
        filename = file.filename.lower()

        # Determine file type
        if filename.endswith('.stl'):
            file_type = 'stl'
        elif filename.endswith('.obj'):
            file_type = 'obj'
        elif filename.endswith('.3mf'):
            file_type = '3mf'
        else:
            return {'error': 'Unsupported file type'}

        # Load mesh with Trimesh
        mesh = trimesh.load(file.stream, file_type=file_type)

        # Calculate volume, weight, and price
        volume_cm3 = mesh.volume / 1000  # mm³ → cm³
        weight = round(volume_cm3 * DENSITY[material], 1)
        price = round(weight * PRICES[material], 2)

        return {'weight': weight, 'price': price}

    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':
    app.run(debug=True)
