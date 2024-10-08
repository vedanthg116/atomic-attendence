import os
import face_recognition
import pickle
from openpyxl import Workbook
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import re
import datetime
import tkinter.messagebox as messagebox


directory_path = ""
selected_image_paths = []  # List to store selected image paths
processing_message_displayed = False
subject = ""
class_info = ""
output_folder = ""

def set_output_folder():
    global output_folder
    output_folder = filedialog.askdirectory(title="Select Output Folder")

subject = ""  # Initialize subject as an empty string
class_info = ""  # Initialize class_info as an empty string


def process_images():
    global output_folder
    global directory_path, selected_image_paths, processing_message_displayed, subject, class_info

    if not directory_path or not selected_image_paths:
        result_label.config(text="Please select both the group photos folder and images.")
        return

    # Get the subject and class information from the Entry widgets
    subject = subject_entry.get()
    class_info = class_entry.get()

    try:
        with open("encodings.pickle", "rb") as f:
            data = pickle.load(f)
        known_face_encodings = data["encodings"]
        roll_numbers = data["roll_numbers"]

        # Create dictionaries to store unique recognized faces and unknown faces
        recognized_faces = {}
        unknown_faces = {}

        for selected_image_path in selected_image_paths:
            image_path = os.path.join(directory_path, os.path.basename(selected_image_path))
            print("Image Path:", image_path)

            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image)
            face_encodings = face_recognition.face_encodings(image, face_locations)

            for face_encoding in face_encodings:
                roll_number_match = "Unknown"
                student_name = "---"
                for i, known_encoding_list in enumerate(known_face_encodings):
                    matches = face_recognition.compare_faces(known_encoding_list, face_encoding)
                    if any(matches):
                        roll_number_match = roll_numbers[i]
                        folder_name_parts = roll_number_match.split('_')
                        if len(folder_name_parts) >= 2:
                            student_name = folder_name_parts[1]
                            roll_number_match = folder_name_parts[0]
                        break

                if roll_number_match != "Unknown":
                    recognized_faces[roll_number_match] = student_name
                else:
                    unknown_faces[face_encoding.tobytes()] = unknown_faces.get(face_encoding.tobytes(), 0) + 1

        # Sort and process recognized faces
        sorted_roll_numbers = sorted(recognized_faces.keys())

        wb = Workbook()
        ws = wb.active
        ws.title = f"{subject}_{class_info}"  # Set Excel sheet name
        ws.column_dimensions["A"].width = 15
        ws.append(["Student USN", "Student Name"])

        for roll_number in sorted_roll_numbers:
            student_name = recognized_faces[roll_number]
            ws.append([roll_number, student_name])

        # Add unknown faces to the Excel sheet
        for _ in unknown_faces.keys():
            ws.append(["Unknown", "---"])

        # Save the workbook and show the success message
        current_date = datetime.datetime.now().strftime("%d_%m_%Y")
        excel_file_path = os.path.join(output_folder, f"attendance_sheet_{subject}_{class_info}_{current_date}.xlsx")
        wb.save(excel_file_path)

        result_label.config(text=f"Recognition complete. Attendance saved to {excel_file_path}")
        messagebox.showinfo("Success", "Image processing and attendance saving completed successfully.")
    except Exception as e:
        result_label.config(text="Recognition failed.")
        messagebox.showerror("Error", f"Recognition failed: {str(e)}")
    finally:
        processing_message_displayed = False
def browse_photos_and_folder():
    global directory_path, selected_image_paths
    directory_path = filedialog.askdirectory(title="Select Group Photos Folder")
    selected_image_paths = filedialog.askopenfilenames(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
    if directory_path and selected_image_paths:
        result_label.config(
            text=f"Selected folder: {directory_path}\nSelected images: {', '.join([os.path.basename(path) for path in selected_image_paths])}")
    else:
        result_label.config(text="No folder or images selected.")


def validate_filename(filename):
    allowed_extensions = ['.jpg', '.jpeg', '.png']
    _, extension = os.path.splitext(filename)
    return extension.lower() in allowed_extensions

def browse_file():
    filename = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
    if filename:
        image_entry.delete(0, tk.END)
        image_entry.insert(0, os.path.basename(filename))

# Create UI
root = tk.Tk()
root.title("Group Photo Recognizer")

# Set the width and height of the UI
width = 350
height = 190
root.geometry(f"{width}x{height}")

# Subject Entry
subject_label = ttk.Label(root, text="Enter Subject:")
subject_label.pack()
subject_entry = ttk.Entry(root)
subject_entry.pack()

# Class Entry
class_label = ttk.Label(root, text="Enter Class:")
class_label.pack()
class_entry = ttk.Entry(root)
class_entry.pack()

# Select Photo & Folder Button
select_button = ttk.Button(root, text="Select Photos & Folder", command=browse_photos_and_folder)
select_button.pack()

# Add a button to set the output folder
output_folder_button = ttk.Button(root, text="Set Output Folder", command=set_output_folder)
output_folder_button.pack()

# Process Images Button
process_button = ttk.Button(root, text="Process Images", command=process_images)
process_button.pack()


# Result Label
result_label = ttk.Label(root, text="")
result_label.pack()

root.mainloop()




