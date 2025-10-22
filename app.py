import streamlit as st
import qrcode
import pandas as pd
from datetime import datetime
import cv2
import tempfile
import os

st.set_page_config(page_title="Điểm danh học sinh bằng QR", page_icon="🎓")

st.title("🎓 Hệ thống điểm danh học sinh bằng mã QR")

menu = st.sidebar.selectbox("Chọn chức năng", ["Tạo mã QR", "Điểm danh"])

# --- Sinh mã QR ---
if menu == "Tạo mã QR":
    st.subheader("📇 Sinh mã QR cho học sinh")
    name = st.text_input("Tên học sinh")
    student_id = st.text_input("Mã học sinh")
    classroom = st.text_input("Lớp")
    
    if st.button("Tạo mã QR"):
        if name and student_id:
            data = f"{student_id} - {name} - {classroom}"
            qr = qrcode.make(data)
            temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            qr.save(temp.name)
            st.image(temp.name)
            st.success("✅ Đã tạo mã QR!")
            st.download_button("Tải QR xuống", open(temp.name, "rb"), file_name=f"{student_id}.png")
        else:
            st.warning("Vui lòng nhập đủ thông tin!")

# --- Điểm danh ---
elif menu == "Điểm danh":
    st.subheader("📸 Quét mã QR để điểm danh")
    attendance_file = "attendance.csv"
    if not os.path.exists(attendance_file):
        pd.DataFrame(columns=["ID", "Tên học sinh", "Lớp", "Thời gian"]).to_csv(attendance_file, index=False)
    
    run = st.checkbox("Bật camera")
    FRAME_WINDOW = st.image([])

    cap = None
    if run:
        cap = cv2.VideoCapture(0)
        detector = cv2.QRCodeDetector()
        while run:
            ret, frame = cap.read()
            data, bbox, _ = detector.detectAndDecode(frame)
            if data:
                ID, name, classroom = data.split(" - ")
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                df = pd.read_csv(attendance_file)
                if not ((df["ID"] == ID) & (df["Thời gian"].str.contains(datetime.now().strftime("%Y-%m-%d")))).any():
                    df.loc[len(df)] = [ID, name, classroom, timestamp]
                    df.to_csv(attendance_file, index=False)
                    st.success(f"✅ {name} ({classroom}) đã điểm danh lúc {timestamp}")
                else:
                    st.info(f"⚠️ {name} đã điểm danh hôm nay.")
            FRAME_WINDOW.image(frame, channels="BGR")
        cap.release()

    st.write("📋 Dữ liệu điểm danh:")
    st.dataframe(pd.read_csv(attendance_file))
