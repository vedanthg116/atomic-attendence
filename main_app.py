import datetime
import os
import pickle

import face_recognition
from flask import Flask, render_template, request, send_file, redirect, url_for
from openpyxl import Workbook

app = Flask(__name__)

student_images_folder = os.path.join(app.root_path, 'student_images')

# Global variables
selected_image_paths = []
subject = ""
class_info = ""


@app.route('/')
def index():
    return redirect(url_for('home'))


@app.route('/home')
def home():
    return render_template('home.html')


# Process images route
@app.route('/process_images', methods=['GET', 'POST'])
def process_images():
    global selected_image_paths, subject, class_info
    if request.method == 'POST':
        subject = request.form.get('subject')
        class_info = request.form.get('class_info')
        selected_image_paths = request.files.getlist('selected_images')

        try:
            # Load roll numbers and known encodings from encodings
            with open("encodings.pickle", "rb") as f:
                data = pickle.load(f)
            roll_numbers = data["roll_numbers"]
            known_face_encodings = data["encodings"]

            # Create Excel sheet and save
            wb = Workbook()
            ws = wb.active
            ws.title = f"{subject}_{class_info}"
            ws.column_dimensions["A"].width = 15
            ws.append(["Student USN", "Student Name"])

            unique_unknown_faces = set()  # Keep track of unique unknown faces

            for selected_image in selected_image_paths:
                recognized_faces = {}
                unknown_faces = {}

                image = face_recognition.load_image_file(selected_image)
                face_locations = face_recognition.face_locations(image)
                face_encodings = face_recognition.face_encodings(image, face_locations)

                for face_encoding in face_encodings:
                    roll_number_match = "Unknown"
                    student_name = "---"
                    for i, roll_number in enumerate(roll_numbers):
                        matches = face_recognition.compare_faces(known_face_encodings[i], face_encoding)
                        if any(matches):
                            folder_name_parts = roll_number.split('_')
                            if len(folder_name_parts) >= 2:
                                student_name = folder_name_parts[1]
                                roll_number_match = folder_name_parts[0]
                            break

                    if roll_number_match != "Unknown":
                        recognized_faces[roll_number_match] = student_name
                    else:
                        face_bytes = face_encoding.tobytes()
                        if face_bytes not in unique_unknown_faces:
                            unknown_faces[face_bytes] = 0
                            unique_unknown_faces.add(face_bytes)

                # Add recognized faces to Excel sheet
                for roll_number in recognized_faces:
                    student_name = recognized_faces[roll_number]
                    ws.append([roll_number, student_name])

                # Add unique unknown faces to Excel sheet
                for face_bytes in unknown_faces:
                    ws.append(["Unknown"])

            current_date = datetime.datetime.now().strftime("%d_%m_%Y")
            excel_file_path = os.path.join(app.root_path,
                                           f"attendance_sheet_{subject}_{class_info}_{current_date}.xlsx")
            wb.save(excel_file_path)
            return redirect(url_for('download_page', excel_file_path=excel_file_path))
        except Exception as e:
            result = "Recognition failed."
            print(str(e))
            return result

    else:
        return render_template('process_images.html')


# Train face route
@app.route('/train_face', methods=['GET', 'POST'])
def train_face():
    if request.method == 'POST':
        try:
            student_usn = request.form.get('student_usn')
            student_name = request.form.get('student_name')
            student_images = request.files.getlist('student_images')

            student_folder_name = f"{student_usn}_{student_name}"
            inner_student_images_folder = os.path.join(app.root_path, 'student_images', student_folder_name)
            os.makedirs(inner_student_images_folder, exist_ok=True)

            # Save student images and train the model
            known_face_encodings = []
            known_roll_numbers = []

            for student_image in student_images:
                image_path = os.path.join(inner_student_images_folder, student_image.filename)
                student_image.save(image_path)

                # Load and encode the student face
                student_face = face_recognition.load_image_file(image_path)
                student_face_encodings = face_recognition.face_encodings(student_face)

                if len(student_face_encodings) > 0:
                    student_face_encoding = student_face_encodings[0]
                    known_face_encodings.append(student_face_encoding)
                    known_roll_numbers.append(f"{student_usn}_{student_name}") 
                else:
                    print("No face found in the image:", image_path)

            # Load existing encodings
            encodings_file_path = os.path.join(app.root_path, 'encodings.pickle')
            if os.path.exists(encodings_file_path):
                with open(encodings_file_path, 'rb') as f:
                    data = pickle.load(f)
                    existing_face_encodings = data.get('encodings', [])
                    existing_roll_numbers = data.get('roll_numbers', [])
                    known_face_encodings.extend(existing_face_encodings)
                    known_roll_numbers.extend(existing_roll_numbers)

            encodings_data = {
                'encodings': known_face_encodings,
                'roll_numbers': known_roll_numbers
            }

            with open(encodings_file_path, 'wb') as f:
                pickle.dump(encodings_data, f)

            thank_you_message = f"Thank you for providing training data for {student_usn} - {student_name}!"
            return render_template('thank_you.html', message=thank_you_message)

        except Exception as e:
            error_message = "An error occurred during face recognition training."
            print(str(e))
            return error_message

    else:
        return render_template('train_face.html')


# Download page route
@app.route('/download_page/<excel_file_path>')
def download_page(excel_file_path):
    return render_template('download_page.html', excel_file_path=excel_file_path)


@app.route('/thank_you')
def thank_you():
    return render_template('thank_you.html')  # Create a thank_you.html template


# Download Excel sheet route
@app.route('/download_excel')
def download_excel():
    filename = request.args.get('file')
    return send_file(filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
