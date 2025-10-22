import streamlit as st
import qrcode
import pandas as pd
from datetime import datetime
import cv2
import os
import time

# -------------------- CẤU HÌNH TRANG --------------------
st.set_page_config(page_title="Điểm danh QR", page_icon="🎓", layout="wide")
st.title("🎓 HỆ THỐNG ĐIỂM DANH HỌC SINH BẰNG MÃ QR")

menu = st.sidebar.radio("📌 Chọn chức năng", ["🏷️ Tạo mã QR", "📸 Điểm danh", "📅 Thống kê"])

# -------------------- 1️⃣ TẠO MÃ QR --------------------
if menu == "🏷️ Tạo mã QR":
    st.subheader("📇 Tạo mã QR cho học sinh")

    name = st.text_input("Tên học sinh")
    student_id = st.text_input("Mã học sinh (VD: HS001)")
    classroom = st.text_input("Lớp (VD: 10A1)")

    if st.button("🎁 Tạo mã QR"):
        if name and student_id and classroom:
            data = f"{student_id} - {name} - {classroom}"
            qr = qrcode.make(data)
            os.makedirs("qr_codes", exist_ok=True)
            qr_path = f"qr_codes/{student_id}_{name}.png"
            qr.save(qr_path)

            st.image(qr_path, caption=f"Mã QR của {name}", width=250)
            with open(qr_path, "rb") as f:
                st.download_button("⬇️ Tải mã QR", f, file_name=f"{student_id}_{name}.png")
            st.success("✅ Đã tạo mã QR thành công!")
        else:
            st.warning("⚠️ Vui lòng nhập đủ thông tin!")

# -------------------- 2️⃣ ĐIỂM DANH --------------------
elif menu == "📸 Điểm danh":
    st.subheader("📷 Quét mã QR để điểm danh")

    # ---- Chọn hoặc nhập môn học ----
    st.markdown("### 📚 Chọn hoặc nhập tên môn học")
    default_subjects = ["Toán", "Lý", "Hóa", "Anh", "Sinh", "Tin", "Sử", "Địa"]
    selected_subject = st.selectbox("Chọn môn học có sẵn:", default_subjects)
    custom_subject = st.text_input("Hoặc nhập tên môn học khác:")
    subject = custom_subject if custom_subject else selected_subject

    teacher = st.text_input("👨‍🏫 Nhập tên giáo viên", placeholder="Ví dụ: ThayAn, CoHien")

    # ✅ Duy trì session state (để tiếp tục điểm danh sau reload)
    if "subject" not in st.session_state:
        st.session_state["subject"] = None
    if "teacher" not in st.session_state:
        st.session_state["teacher"] = None
    if "attendance_file" not in st.session_state:
        st.session_state["attendance_file"] = None

    # Nếu người dùng nhập mới, cập nhật lại session
    if subject and teacher:
        st.session_state["subject"] = subject
        st.session_state["teacher"] = teacher
        st.session_state["attendance_file"] = f"attendance_{subject}_{teacher}.csv"

    # Dùng session để giữ thông tin giữa các lần reload
    if st.session_state["attendance_file"]:
        attendance_file = st.session_state["attendance_file"]
        subject = st.session_state["subject"]
        teacher = st.session_state["teacher"]

        if not os.path.exists(attendance_file):
            pd.DataFrame(columns=["ID", "Tên học sinh", "Lớp", "Môn học", "Giáo viên", "Thời gian"]).to_csv(attendance_file, index=False)

        run = st.checkbox("📸 Bật camera")
        FRAME_WINDOW = st.image([])
        status_placeholder = st.empty()
        list_placeholder = st.empty()

        if run:
            cap = cv2.VideoCapture(0)
            time.sleep(1)
            detector = cv2.QRCodeDetector()

            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    status_placeholder.warning("⚠️ Không nhận được hình ảnh từ camera. Kiểm tra lại webcam!")
                    time.sleep(0.5)
                    continue

                data, bbox, _ = detector.detectAndDecode(frame)
                if data:
                    try:
                        ID, name, classroom = data.split(" - ")
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        df = pd.read_csv(attendance_file)
                        today = datetime.now().strftime("%Y-%m-%d")
                        already = ((df["ID"] == ID) & (df["Thời gian"].str.contains(today))).any()

                        if not already:
                            df.loc[len(df)] = [ID, name, classroom, subject, teacher, timestamp]
                            df.to_csv(attendance_file, index=False)
                            status_placeholder.success(f"✅ {name} ({classroom}) điểm danh {subject} - {teacher} lúc {timestamp}")
                        else:
                            status_placeholder.info(f"⚠️ {name} đã điểm danh hôm nay.")
                    except Exception as e:
                        status_placeholder.error(f"❌ Lỗi khi đọc mã QR: {e}")

                    time.sleep(1)

                FRAME_WINDOW.image(frame, channels="BGR")

                df = pd.read_csv(attendance_file)
                today_df = df[df["Thời gian"].str.contains(datetime.now().strftime("%Y-%m-%d"))]
                list_placeholder.dataframe(today_df.sort_values(by="Thời gian", ascending=False))

                if not run:
                    break

            cap.release()

        else:
            df = pd.read_csv(attendance_file)
            today_df = df[df["Thời gian"].str.contains(datetime.now().strftime("%Y-%m-%d"))]
            st.dataframe(today_df.sort_values(by="Thời gian", ascending=False))
    else:
        st.warning("⚠️ Vui lòng nhập đủ thông tin môn học và tên giáo viên trước khi bật camera.")

# -------------------- 3️⃣ THỐNG KÊ --------------------
elif menu == "📅 Thống kê":
    st.subheader("📊 Thống kê điểm danh")

    files = [f for f in os.listdir() if f.startswith("attendance_") and f.endswith(".csv")]
    if len(files) == 0:
        st.info("❗ Chưa có dữ liệu điểm danh nào.")
    else:
        selected_file = st.selectbox("📂 Chọn file dữ liệu để xem", files)
        df = pd.read_csv(selected_file)
        st.write(f"📁 **File đang xem:** `{selected_file}`")
        st.metric("👨‍🎓 Tổng lượt điểm danh", len(df))
        st.metric("📅 Số ngày có điểm danh", df["Thời gian"].str[:10].nunique())

        selected_day = st.date_input("📆 Chọn ngày để xem chi tiết", datetime.now().date())
        selected_day_str = selected_day.strftime("%Y-%m-%d")
        filtered = df[df["Thời gian"].str.contains(selected_day_str)]

        if len(filtered) > 0:
            st.success(f"📋 Danh sách học sinh điểm danh ngày {selected_day_str}:")
            st.dataframe(filtered)
        else:
            st.warning(f"Không có dữ liệu cho ngày {selected_day_str}.")

        st.download_button("📥 Tải file này (CSV)", open(selected_file, "rb"), file_name=selected_file)
